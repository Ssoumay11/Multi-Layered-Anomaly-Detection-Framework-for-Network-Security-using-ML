import logging
import threading
from collections import deque, defaultdict
from datetime import datetime
from typing import Dict, Deque, List
import asyncio
import joblib
import numpy as np
import pyshark
import tensorflow as tf
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ============================================================
# CONFIG
# ============================================================

# Change this to your actual Wi‑Fi interface name
# On Windows it is often "Wi-Fi" or "WiFi"
INTERFACE = "Wi-Fi"

# How many recent events to keep in memory for the dashboard
MAX_EVENTS = 500

# Packet / flow / behaviour buffers for dynamic thresholds
PACKET_ERROR_HISTORY = 2000
FLOW_SCORE_HISTORY = 2000

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("realtime-backend")

logger.info("Starting 3-layer realtime backend...")

# ============================================================
# LOAD TRAINED MODELS
# ============================================================

logger.info("Loading trained models and scalers...")

# ----- Layer 1: Packet autoencoder -----
packet_ae = tf.keras.models.load_model("packet_layer_autoencoder.h5",compile=False)
packet_scaler = joblib.load("packet_layer_scaler.pkl")
packet_feature_names: List[str] = joblib.load("packet_layer_features.pkl")

logger.info("Loaded packet autoencoder with %d features", len(packet_feature_names))

# ----- Layer 2: Flow scaler (unsupervised anomaly) -----
flow_scaler = joblib.load("flow_layer_scaler.pkl")

# flow_layer_all_columns.pkl was saved from training.
# Your file name might have a space; try both.
try:
    flow_all_columns: List[str] = joblib.load("flow_layer_all_columns.pkl")
except FileNotFoundError:
    flow_all_columns = joblib.load("flow_layer_all column.pkl")

FLOW_CANDIDATES = [
    "Flow Duration",
    "Total Fwd Packet",
    "Total Bwd packets",
    "Total Length of Fwd Packet",
    "Total Length of Bwd Packet",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Flow IAT Mean",
    "Flow IAT Std",
]

FLOW_FEATURES: List[str] = [f for f in FLOW_CANDIDATES if f in flow_all_columns]
logger.info("Flow layer will use %d features: %s", len(FLOW_FEATURES), FLOW_FEATURES)

# ----- Layer 3: Behaviour GRU -----
behavior_gru = tf.keras.models.load_model("behavior_layer_gru.h5", compile=False)
behavior_scaler = joblib.load("behavior_layer_scaler.pkl")
n_beh_features: int = joblib.load("behavior_layer_n_features.pkl")

SEQ_LEN = 10  # same window used during training

logger.info("Loaded behaviour GRU with %d features and sequence length %d",
            n_beh_features, SEQ_LEN)

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(title="Realtime 3-Layer Network Anomaly Detection")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# IN-MEMORY STATE
# ============================================================

# Recent events for dashboard
RECENT_EVENTS: Deque[Dict] = deque(maxlen=MAX_EVENTS)

# Per-source-IP statistics for flow & behaviour layers
flow_state: Dict[str, Dict] = defaultdict(
    lambda: {"first_ts": None, "last_ts": None, "bytes": 0, "packets": 0}
)

# Per-source-IP behaviour sequences
behavior_sequences: Dict[str, Deque[np.ndarray]] = defaultdict(
    lambda: deque(maxlen=SEQ_LEN)
)

# Histories for adaptive thresholds
packet_errors: Deque[float] = deque(maxlen=PACKET_ERROR_HISTORY)
flow_scores: Deque[float] = deque(maxlen=FLOW_SCORE_HISTORY)

# ============================================================
# FEATURE ENGINEERING HELPERS
# ============================================================

def update_flow_state(src_ip: str, ts: float, length: int) -> Dict:
    """
    Update aggregate stats for this source IP and return the state.
    """
    st = flow_state[src_ip]
    if st["first_ts"] is None:
        st["first_ts"] = ts
    st["last_ts"] = ts
    st["bytes"] += length
    st["packets"] += 1
    return st


def build_packet_features(src_ip: str, ts: float, length: int) -> np.ndarray:
    """
    Approximate the packet-level feature vector used during training.
    """
    st = update_flow_state(src_ip, ts, length)

    duration = max(st["last_ts"] - st["first_ts"], 0.001)
    total_packets = st["packets"]
    total_bytes = st["bytes"]
    flow_bytes_per_sec = total_bytes / duration
    flow_packets_per_sec = total_packets / duration
    avg_packet_size = total_bytes / max(total_packets, 1)

    syn_count = 0.0
    rst_count = 0.0
    conn_fail_ratio = rst_count / (syn_count + 1.0)

    feat_dict = {
        "flow_duration": duration,
        "total_packets": total_packets,
        "total_bytes": total_bytes,
        "flow_bytes_per_sec": flow_bytes_per_sec,
        "flow_packets_per_sec": flow_packets_per_sec,
        "avg_packet_size": avg_packet_size,
        "syn_count": syn_count,
        "rst_count": rst_count,
        "connection_failure_ratio": conn_fail_ratio,
    }

    vec = np.array(
        [feat_dict.get(name, 0.0) for name in packet_feature_names],
        dtype=float,
    )
    return vec


def run_packet_layer(src_ip: str, ts: float, length: int):
    """
    Run packet autoencoder, compute reconstruction error,
    and classify as attack if above 95th percentile of history.
    """
    vec = build_packet_features(src_ip, ts, length)
    X_scaled = packet_scaler.transform(vec.reshape(1, -1))

    recon = packet_ae.predict(X_scaled, verbose=0)
    error = float(np.mean((X_scaled - recon) ** 2))

    packet_errors.append(error)
    if len(packet_errors) > 50:
        threshold = float(np.percentile(packet_errors, 95))
    else:
        threshold = float("inf")  # warm up

    label = "attack" if error > threshold else "normal"
    return label, error, threshold


def build_flow_features(src_ip: str) -> np.ndarray:
    """
    Build flow-level features matching FLOW_FEATURES.
    """
    st = flow_state[src_ip]
    if st["first_ts"] is None:
        return np.zeros(len(FLOW_FEATURES), dtype=float)

    duration = max(st["last_ts"] - st["first_ts"], 0.001)
    total_packets = st["packets"]
    total_bytes = st["bytes"]

    flow_bytes_per_sec = total_bytes / duration
    flow_packets_per_sec = total_packets / duration
    avg_iat_mean = duration / max(total_packets, 1)

    feat_dict = {
        "Flow Duration": duration,
        "Total Fwd Packet": total_packets,
        "Total Bwd packets": 0.0,
        "Total Length of Fwd Packet": total_bytes,
        "Total Length of Bwd Packet": 0.0,
        "Flow Bytes/s": flow_bytes_per_sec,
        "Flow Packets/s": flow_packets_per_sec,
        "Flow IAT Mean": avg_iat_mean,
        "Flow IAT Std": 0.0,
    }

    vec = np.array([feat_dict.get(name, 0.0) for name in FLOW_FEATURES], dtype=float)
    return vec


def run_flow_layer(src_ip: str):
    """
    Unsupervised flow anomaly: use the trained scaler to compute a
    mean absolute z-score; attack if above 95th percentile of history.
    """
    vec = build_flow_features(src_ip)
    X_scaled = flow_scaler.transform(vec.reshape(1, -1))

    score = float(np.mean(np.abs(X_scaled)))
    flow_scores.append(score)

    if len(flow_scores) > 50:
        threshold = float(np.percentile(flow_scores, 95))
    else:
        threshold = float("inf")

    label = "attack" if score > threshold else "normal"
    return label, score, threshold


def build_behavior_vector(src_ip: str) -> np.ndarray:
    """
    Simple per-IP behaviour vector to feed into GRU sequence.
    First few dimensions: total packets, total bytes, bytes/s, packets/s.
    Remaining dims are zeros if n_beh_features > 4.
    """
    st = flow_state[src_ip]
    if st["first_ts"] is None:
        duration = 0.001
    else:
        duration = max(st["last_ts"] - st["first_ts"], 0.001)

    bytes_per_s = st["bytes"] / duration
    packets_per_s = st["packets"] / duration

    vec = np.zeros(n_beh_features, dtype=float)
    vec[0] = st["packets"]
    if n_beh_features > 1:
        vec[1] = st["bytes"]
    if n_beh_features > 2:
        vec[2] = bytes_per_s
    if n_beh_features > 3:
        vec[3] = packets_per_s

    return vec

def run_behavior_layer(src_ip: str):
    """
    Maintain a sliding window of SEQ_LEN behaviour vectors for each IP.
    Once we have SEQ_LEN, run GRU and return label & probability.
    """
    seq_deque = behavior_sequences[src_ip]
    vec = build_behavior_vector(src_ip)
    seq_deque.append(vec)

    if len(seq_deque) < SEQ_LEN:
        # Not enough history yet
        return "unknown", 0.0

    # Build raw sequence
    X_raw = np.vstack(seq_deque)  # shape (SEQ_LEN, n_beh_features)

    # ---- NEW: fit scaler on first use if needed ----
    # StandardScaler must see data once via fit() before transform()[web:109]
    if not hasattr(behavior_scaler, "mean_"):
        logger.info("Fitting behaviour scaler on first sequence for IP %s", src_ip)
        behavior_scaler.fit(X_raw)

    X_scaled = behavior_scaler.transform(X_raw)  # now safe
    X_scaled = X_scaled.reshape(1, SEQ_LEN, n_beh_features)

    prob = float(behavior_gru.predict(X_scaled, verbose=0)[0][0])

    if "beh_probs" not in globals():
        globals()["beh_probs"] = deque(maxlen=2000)
    beh_probs = globals()["beh_probs"]
    beh_probs.append(prob)
    if len(beh_probs) > 50:
        beh_thresh = float(np.percentile(beh_probs, 90))
    else:
        beh_thresh = 0.7  # fixed warm‑up threshold


    
    label = "attack" if prob >= beh_thresh else "normal"
    return label, prob, beh_thresh



# ============================================================
# PACKET CAPTURE LOOP
# ============================================================

def capture_loop():
    """
    Background thread: create an event loop for PyShark, then sniff packets.
    """
    logger.info("Starting PyShark LiveCapture on interface '%s'...", INTERFACE)

    try:
        # Create and set an event loop for this thread (Python 3.11+ requirement)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Pass loop into PyShark so it uses this thread's event loop
        cap = pyshark.LiveCapture(
            interface=INTERFACE,
            display_filter="ip",
            eventloop=loop,
        )
    except Exception as e:
        logger.exception("Unable to start capture on '%s': %s", INTERFACE, e)
        return

    # Normal packet processing loop
    for pkt in cap.sniff_continuously():
        try:
            if not hasattr(pkt, "ip"):
                continue

            src_ip = pkt.ip.src
            ts = pkt.sniff_time.timestamp()

            # Packet length
            length = None
            if hasattr(pkt, "length"):
                try:
                    length = int(pkt.length)
                except Exception:
                    pass
            if length is None and hasattr(pkt.ip, "len"):
                try:
                    length = int(pkt.ip.len)
                except Exception:
                    pass
            if length is None:
                length = 0

            # Run three layers
            packet_label, packet_err, packet_thresh = run_packet_layer(src_ip, ts, length)
            flow_label, flow_score, flow_thresh = run_flow_layer(src_ip)
            behavior_label, behavior_prob, behavior_thresh = run_behavior_layer(src_ip)

            final_label = "attack" if (
                flow_label == "attack" or behavior_label == "attack"
            ) else "normal"

            st = flow_state[src_ip]
            duration = max(
                (st["last_ts"] - st["first_ts"]) if st["first_ts"] else 0.001,
                0.001,
            )
            bytes_per_s = st["bytes"] / duration
            packets_per_s = st["packets"] / duration

            event = {
                "timestamp": ts,
                "src_ip": src_ip,
                "packet_size": length,
                "flow_bytes_s": float(bytes_per_s),
                "flow_packets_s": float(packets_per_s),
                "packet_layer_label": packet_label,
                "packet_layer_score": float(packet_err),
                "packet_layer_threshold": float(packet_thresh)
                if np.isfinite(packet_thresh)
                else None,
                "flow_layer_label": flow_label,
                "flow_layer_score": float(flow_score),
                "flow_layer_threshold": float(flow_thresh)
                if np.isfinite(flow_thresh)
                else None,
                "behavior_layer_label": behavior_label,
                "behavior_layer_prob": float(behavior_prob),
                "behavior_layer_threshold": float(behavior_thresh) if behavior_thresh is not None else None,
                "final_label": final_label,
            }

            RECENT_EVENTS.append(event)

            if final_label == "attack":
                logger.info(
                    "ATTACK src=%s size=%d pkt_err=%.4f flow_score=%.3f beh_prob=%.3f",
                    src_ip,
                    length,
                    packet_err,
                    flow_score,
                    behavior_prob,
                )

        except Exception as e:
            logger.exception("Error processing packet: %s", e)

# Start capture thread when module is imported
capture_thread = threading.Thread(target=capture_loop, daemon=True)
capture_thread.start()

# ============================================================
# API SCHEMAS & ENDPOINTS
# ============================================================

class Event(BaseModel):
    timestamp: float
    src_ip: str
    packet_size: int
    flow_bytes_s: float
    flow_packets_s: float
    packet_layer_label: str
    packet_layer_score: float
    packet_layer_threshold: float | None
    flow_layer_label: str
    flow_layer_score: float
    flow_layer_threshold: float | None
    behavior_layer_label: str
    behavior_layer_prob: float
    behavior_layer_threshold: float | None

    final_label: str


@app.get("/events", response_model=list[Event])
def get_events():
    """
    Return recent events for dashboard.
    """
    return list(RECENT_EVENTS)


@app.get("/health")
def health():
    """
    Simple liveness endpoint.
    """
    return {
        "status": "ok",
        "events": len(RECENT_EVENTS),
        "current_time": datetime.utcnow().isoformat() + "Z",
    }