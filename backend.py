"""
============================================================
 AI-SOC Backend  —  Multi-Layer Anomaly Detection API
 Paper: "Multi Layered Anomaly Detection Framework for
         Network Security using Machine Learning"
 Architecture: Packet → Flow → Behavioural → Fusion
============================================================
Run:
    pip install fastapi uvicorn tensorflow scikit-learn
                joblib numpy pandas
    python backend.py
"""

import os
import time
import uuid
import random
import asyncio
import threading
import collections
from datetime import datetime
from typing import List, Optional

import numpy as np
import pandas as pd
import joblib
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── optional TF import (graceful degradation) ─────────────────────────────────
try:
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    import tensorflow as tf
    tf.get_logger().setLevel("ERROR")
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("⚠  TensorFlow not found – autoencoder/LSTM layers disabled.")

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
MODEL_DIR        = os.getenv("MODEL_DIR", ".")          # folder with .pkl / .h5
EVENT_BUFFER_MAX = 200                                   # rolling window size
SIMULATE         = True                                  # generate synthetic traffic
SIM_INTERVAL_SEC = 1.5                                   # new event every N seconds

# ══════════════════════════════════════════════════════════════════════════════
#  MODEL LOADER
# ══════════════════════════════════════════════════════════════════════════════
class ModelStore:
    """Lazy-load all trained artefacts from MODEL_DIR."""

    def __init__(self, model_dir: str):
        self.dir = model_dir
        self._autoencoder      = None
        self._isolation_forest = None
        self._packet_scaler    = None
        self._lstm             = None
        self._behavior_scaler  = None
        self._packet_features  = None
        self._behavior_features= None
        self._packet_thresholds= None
        self._behavior_threshold=None
        self._loaded           = False

    def _load(self):
        if self._loaded:
            return
        print("🔧 Loading models from:", self.dir)

        def safe_load(loader, path, label):
            full = os.path.join(self.dir, path)
            if not os.path.exists(full):
                print(f"   ⚠  {label} not found at {full} – using fallback")
                return None
            try:
                result = loader(full)
                print(f"   ✅ {label}")
                return result
            except Exception as e:
                print(f"   ❌ {label}: {e}")
                return None

        self._isolation_forest  = safe_load(joblib.load, "isolation_forest.pkl",  "Isolation Forest")
        self._packet_scaler     = safe_load(joblib.load, "packet_scaler.pkl",     "Packet Scaler")
        self._behavior_scaler   = safe_load(joblib.load, "behavior_scaler.pkl",   "Behaviour Scaler")
        self._packet_features   = safe_load(joblib.load, "packet_features.pkl",   "Packet Features")
        self._behavior_features = safe_load(joblib.load, "behavior_features.pkl", "Behaviour Features")
        self._packet_thresholds = safe_load(joblib.load, "packet_thresholds.pkl", "Packet Thresholds")
        self._behavior_threshold= safe_load(joblib.load, "behavior_threshold.pkl","Behaviour Threshold")

        if TF_AVAILABLE:
            self._autoencoder = safe_load(
                lambda p: tf.keras.models.load_model(p, compile=False),
                "packet_autoencoder.h5", "Packet Autoencoder"
            )
            self._lstm = safe_load(
                lambda p: tf.keras.models.load_model(p, compile=False),
                "behavioral_lstm.h5", "Behavioural LSTM"
            )

        # Fallback defaults if files missing
        if self._packet_thresholds is None:
            self._packet_thresholds = {"autoencoder": 0.68}
        if self._behavior_threshold is None:
            self._behavior_threshold = 0.0005
        if self._packet_features is None:
            self._packet_features = FALLBACK_PACKET_FEATURES
        if self._behavior_features is None:
            self._behavior_features = FALLBACK_BEHAVIOR_FEATURES

        self._loaded = True
        print("✅ Model store ready.\n")

    # ── properties ─────────────────────────────────────────────────────────────
    @property
    def autoencoder(self):      self._load(); return self._autoencoder
    @property
    def isolation_forest(self): self._load(); return self._isolation_forest
    @property
    def packet_scaler(self):    self._load(); return self._packet_scaler
    @property
    def lstm(self):             self._load(); return self._lstm
    @property
    def behavior_scaler(self):  self._load(); return self._behavior_scaler
    @property
    def packet_features(self):  self._load(); return self._packet_features
    @property
    def behavior_features(self):self._load(); return self._behavior_features
    @property
    def packet_thresholds(self):self._load(); return self._packet_thresholds
    @property
    def behavior_threshold(self):self._load(); return self._behavior_threshold


FALLBACK_PACKET_FEATURES = [
    "Flow Duration","Total Fwd Packets","Total Backward Packets",
    "Total Length of Fwd Packets","Total Length of Bwd Packets",
    "Flow Bytes/s","Flow Packets/s","Flow IAT Mean","Flow IAT Std",
    "Fwd IAT Mean","Bwd IAT Mean","SYN Flag Count","RST Flag Count",
    "FIN Flag Count","PSH Flag Count","ACK Flag Count",
    "Fwd Packet Length Mean","Bwd Packet Length Mean",
    "Packet Length Mean","Average Packet Size",
    "Fwd Header Length","Bwd Header Length","Active Mean","Idle Mean",
    "fwd_packet_ratio","fwd_bytes_ratio",
    "connection_failure_ratio","iat_regularity",
]

FALLBACK_BEHAVIOR_FEATURES = [
    "num_connections","avg_flow_bytes_s","avg_flow_packets_s",
    "avg_flow_duration","total_fwd_packets","total_bwd_packets",
    "avg_packet_size","syn_count","rst_count","avg_iat_mean",
]


models = ModelStore(MODEL_DIR)

# ══════════════════════════════════════════════════════════════════════════════
#  INFERENCE ENGINE  —  3-layer + fusion
# ══════════════════════════════════════════════════════════════════════════════

def _safe_scale(scaler, X: np.ndarray) -> np.ndarray:
    """Scale or return raw if scaler unavailable."""
    if scaler is None:
        return X
    try:
        return scaler.transform(X)
    except Exception:
        # shape mismatch – resize features
        n_expected = scaler.n_features_in_ if hasattr(scaler, "n_features_in_") else X.shape[1]
        if X.shape[1] != n_expected:
            X_resized = np.zeros((X.shape[0], n_expected))
            cols = min(X.shape[1], n_expected)
            X_resized[:, :cols] = X[:, :cols]
            return scaler.transform(X_resized)
        return X


def run_packet_layer(features: np.ndarray) -> tuple[int, float]:
    """
    Layer 1 – Packet-level detection
    Uses: Isolation Forest + Autoencoder (combined OR)
    Returns: (prediction 0/1, probability)
    """
    X = _safe_scale(models.packet_scaler, features)

    ae_pred, if_pred = 0, 0
    ae_prob, if_prob = 0.0, 0.0

    # Autoencoder reconstruction error
    if models.autoencoder is not None:
        try:
            recon  = models.autoencoder.predict(X, verbose=0)
            error  = float(np.mean(np.abs(X - recon)))
            thresh = models.packet_thresholds.get("autoencoder", 0.68)
            ae_prob = min(error / (thresh * 2), 1.0)
            ae_pred = int(error > thresh)
        except Exception as e:
            print(f"  AE error: {e}")

    # Isolation Forest
    if models.isolation_forest is not None:
        try:
            score   = models.isolation_forest.decision_function(X)[0]  # negative = anomaly
            if_pred = int(models.isolation_forest.predict(X)[0] == -1)
            # normalise score to [0,1]: lower decision_function → more anomalous
            if_prob = float(np.clip((-score + 0.5) / 1.0, 0, 1))
        except Exception as e:
            print(f"  IF error: {e}")

    combined = int(ae_pred == 1 or if_pred == 1)
    prob     = float(max(ae_prob, if_prob))
    return combined, prob


def run_flow_layer(features: np.ndarray) -> tuple[int, float]:
    """
    Layer 2 – Flow-level detection
    Re-uses the same autoencoder on the same feature set
    (paper uses autoencoders for flow anomalies too)
    Returns: (prediction 0/1, probability)
    """
    X = _safe_scale(models.packet_scaler, features)

    if models.autoencoder is not None:
        try:
            recon  = models.autoencoder.predict(X, verbose=0)
            error  = float(np.mean(np.abs(X - recon)))
            thresh = models.packet_thresholds.get("autoencoder", 0.68) * 0.9
            prob   = min(error / (thresh * 2), 1.0)
            pred   = int(error > thresh)
            return pred, prob
        except Exception as e:
            print(f"  Flow AE error: {e}")

    # Fallback: derive heuristically from raw feature values
    raw_mean = float(np.mean(np.abs(features)))
    prob     = min(raw_mean / 500.0, 1.0)
    pred     = int(prob > 0.5)
    return pred, prob


def run_behavioural_layer(beh_features: np.ndarray,
                           seq_len: int = 5) -> tuple[int, float]:
    """
    Layer 3 – Behavioural-level detection
    Uses LSTM autoencoder on windowed behavioural sequences
    Returns: (prediction 0/1, probability)
    """
    X = _safe_scale(models.behavior_scaler, beh_features)

    if models.lstm is not None:
        try:
            # Pad/tile single sample into a sequence
            seq = np.tile(X, (seq_len, 1))[np.newaxis, ...]  # (1, seq_len, n_features)
            recon = models.lstm.predict(seq, verbose=0)
            error = float(np.mean(np.power(seq - recon, 2)))
            thresh = models.behavior_threshold if models.behavior_threshold else 0.0005
            prob   = min(error / (thresh * 5), 1.0)
            pred   = int(error > thresh)
            return pred, prob
        except Exception as e:
            print(f"  LSTM error: {e}")

    # Fallback heuristic
    raw = float(np.mean(np.abs(beh_features)))
    prob = min(raw / 200.0, 1.0)
    return int(prob > 0.6), prob


def majority_vote(pp: int, pf: int, pb: int) -> int:
    """Paper equation (1): D_final = mode(Pp, Pf, Pb)"""
    return int((pp + pf + pb) >= 2)


def fuse_probability(pp: float, pf: float, pb: float) -> float:
    """Weighted average – behavioural gets slightly more weight (temporal depth)."""
    return float(np.clip(0.30*pp + 0.30*pf + 0.40*pb, 0.0, 1.0))


def priority_color(prob: float) -> str:
    if prob > 0.8: return "#1a0a0f"
    if prob > 0.6: return "#1a100a"
    if prob > 0.4: return "#1a1600"
    return "#0a1a12"


# ══════════════════════════════════════════════════════════════════════════════
#  TRAFFIC SIMULATOR  (used when SIMULATE=True)
# ══════════════════════════════════════════════════════════════════════════════
IPLOOKUP = [
    "192.168.1.14","10.0.0.23","172.16.5.88","192.168.40.7",
    "10.10.8.201","203.0.113.45","198.51.100.9","185.220.101.12",
    "45.33.32.156","216.58.212.142","104.21.55.220","162.159.36.1",
    "198.18.0.52","10.8.0.1","172.20.10.3","192.168.0.100",
]

ATTACK_PROFILES = {
    "DDoS":        {"syn":200, "flow_bytes":50000, "pkt_size":64,  "rst":10},
    "PortScan":    {"syn":50,  "flow_bytes":200,   "pkt_size":40,  "rst":30},
    "Brute-Force": {"syn":15,  "flow_bytes":300,   "pkt_size":300, "rst":5},
    "Botnet":      {"syn":5,   "flow_bytes":8000,  "pkt_size":900, "rst":2},
    "DataBurst":   {"syn":2,   "flow_bytes":90000, "pkt_size":1400,"rst":0},
    "Normal":      {"syn":2,   "flow_bytes":1200,  "pkt_size":512, "rst":0},
}

def synthetic_packet_features(profile: dict) -> np.ndarray:
    """Generate a plausible feature vector matching FALLBACK_PACKET_FEATURES."""
    syn  = profile["syn"]  * random.uniform(0.7, 1.3)
    rst  = profile["rst"]  * random.uniform(0.5, 1.5)
    bps  = profile["flow_bytes"] * random.uniform(0.8, 1.2)
    pkt  = profile["pkt_size"]   * random.uniform(0.9, 1.1)
    dur  = random.uniform(0.1, 3.0) * 1e6   # microseconds
    fwd  = random.randint(1, 100)
    bwd  = random.randint(0, fwd)

    row = [
        dur,                         # Flow Duration
        fwd,                         # Total Fwd Packets
        bwd,                         # Total Backward Packets
        fwd*pkt,                     # Total Length of Fwd Packets
        bwd*pkt*0.6,                 # Total Length of Bwd Packets
        bps,                         # Flow Bytes/s
        (fwd+bwd)/max(dur/1e6, 0.001), # Flow Packets/s
        random.uniform(100,5000),    # Flow IAT Mean
        random.uniform(50,2000),     # Flow IAT Std
        random.uniform(100,3000),    # Fwd IAT Mean
        random.uniform(100,3000),    # Bwd IAT Mean
        syn,                         # SYN Flag Count
        rst,                         # RST Flag Count
        random.uniform(0, 5),        # FIN Flag Count
        random.uniform(0, 20),       # PSH Flag Count
        random.uniform(0, fwd),      # ACK Flag Count
        pkt,                         # Fwd Packet Length Mean
        pkt*0.6,                     # Bwd Packet Length Mean
        pkt*0.8,                     # Packet Length Mean
        pkt,                         # Average Packet Size
        random.uniform(20, 60),      # Fwd Header Length
        random.uniform(20, 60),      # Bwd Header Length
        random.uniform(0, 1000),     # Active Mean
        random.uniform(0, 5000),     # Idle Mean
        fwd / max(fwd+bwd, 1),       # fwd_packet_ratio
        (fwd*pkt) / max(fwd*pkt+bwd*pkt*0.6, 1),  # fwd_bytes_ratio
        rst / max(syn, 1),           # connection_failure_ratio
        0,                           # iat_regularity (simplified)
    ]
    # Pad/trim to match expected feature count
    target = len(FALLBACK_PACKET_FEATURES)
    row = row[:target] + [0.0] * max(0, target - len(row))
    return np.array(row, dtype=np.float32).reshape(1, -1)


def synthetic_behavior_features(profile: dict) -> np.ndarray:
    """Generate behavioural feature vector."""
    row = [
        random.randint(1, int(profile["syn"]*2)+1),   # num_connections
        profile["flow_bytes"] * random.uniform(0.8, 1.2),  # avg_flow_bytes_s
        profile["syn"] * random.uniform(0.5, 1.5),    # avg_flow_packets_s
        random.uniform(0.1, 5.0) * 1e6,               # avg_flow_duration
        random.randint(1, 100),                        # total_fwd_packets
        random.randint(0, 50),                         # total_bwd_packets
        profile["pkt_size"] * random.uniform(0.9,1.1),# avg_packet_size
        profile["syn"],                                # syn_count
        profile["rst"],                                # rst_count
        random.uniform(100, 5000),                     # avg_iat_mean
    ]
    target = len(FALLBACK_BEHAVIOR_FEATURES)
    row = row[:target] + [0.0] * max(0, target - len(row))
    return np.array(row, dtype=np.float32).reshape(1, -1)


# ══════════════════════════════════════════════════════════════════════════════
#  EVENT STORE
# ══════════════════════════════════════════════════════════════════════════════
event_store: collections.deque = collections.deque(maxlen=EVENT_BUFFER_MAX)
store_lock  = threading.Lock()

def build_event(src_ip: str, profile_name: str, profile: dict) -> dict:
    pkt_feats = synthetic_packet_features(profile)
    beh_feats = synthetic_behavior_features(profile)

    pkt_pred, pkt_prob = run_packet_layer(pkt_feats)
    flo_pred, flo_prob = run_flow_layer(pkt_feats)       # same feature set
    beh_pred, beh_prob = run_behavioural_layer(beh_feats)

    final_pred = majority_vote(pkt_pred, flo_pred, beh_pred)
    final_prob = fuse_probability(pkt_prob, flo_prob, beh_prob)

    label = "attack" if final_pred == 1 else "normal"

    return {
        "id":               str(uuid.uuid4())[:8],
        "timestamp":        time.time(),
        "src_ip":           src_ip,
        "attack_type":      profile_name if final_pred else "Normal",
        "packet_size":      int(profile["pkt_size"] * random.uniform(0.9, 1.1)),

        # Layer predictions
        "packet_label":     "attack" if pkt_pred else "normal",
        "packet_prob":      round(pkt_prob, 3),
        "flow_label":       "attack" if flo_pred else "normal",
        "flow_prob":        round(flo_prob, 3),
        "behaviour_label":  "attack" if beh_pred else "normal",
        "behaviour_prob":   round(beh_prob, 3),

        # Fusion
        "label":            label,
        "attack_probability": round(final_prob, 3),

        # UI helpers
        "color":            priority_color(final_prob),
    }


def simulator_loop():
    """Background thread – generates synthetic events."""
    attack_types  = list(ATTACK_PROFILES.keys())
    normal_weight = 0.55   # ~55% normal traffic

    while True:
        time.sleep(SIM_INTERVAL_SEC)
        ip     = random.choice(IPLOOKUP)
        p_name = random.choices(
            attack_types,
            weights=[normal_weight if n=="Normal" else (1-normal_weight)/(len(attack_types)-1)
                     for n in attack_types]
        )[0]
        profile = ATTACK_PROFILES[p_name]
        event   = build_event(ip, p_name, profile)
        with store_lock:
            event_store.append(event)


# ══════════════════════════════════════════════════════════════════════════════
#  FASTAPI APP
# ══════════════════════════════════════════════════════════════════════════════
app = FastAPI(
    title="AI-SOC API",
    description="Multi-layer anomaly detection backend (Packet + Flow + Behavioural + Fusion)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── schemas ──────────────────────────────────────────────────────────────────
class RawRecord(BaseModel):
    src_ip:                    str
    Flow_Duration:             float = 0
    Total_Fwd_Packets:         float = 0
    Total_Backward_Packets:    float = 0
    Total_Length_Fwd_Packets:  float = 0
    Total_Length_Bwd_Packets:  float = 0
    Flow_Bytes_s:              float = 0
    Flow_Packets_s:            float = 0
    Flow_IAT_Mean:             float = 0
    Flow_IAT_Std:              float = 0
    Fwd_IAT_Mean:              float = 0
    Bwd_IAT_Mean:              float = 0
    SYN_Flag_Count:            float = 0
    RST_Flag_Count:            float = 0
    Average_Packet_Size:       float = 0
    num_connections:           float = 1
    avg_flow_bytes_s:          float = 0
    syn_count:                 float = 0

# ─── routes ───────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "service": "AI-SOC API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {
        "status":    "healthy",
        "models": {
            "autoencoder":      models.autoencoder is not None,
            "isolation_forest": models.isolation_forest is not None,
            "lstm":             models.lstm is not None,
            "packet_scaler":    models.packet_scaler is not None,
            "behavior_scaler":  models.behavior_scaler is not None,
        },
        "event_count": len(event_store),
        "timestamp":   datetime.utcnow().isoformat(),
    }


@app.get("/events")
def get_events(limit: int = 50):
    """Return the most recent N events (used by the dashboard)."""
    with store_lock:
        evts = list(event_store)[-limit:]
    return evts


@app.post("/predict")
def predict(record: RawRecord):
    """
    Predict on a single raw network record.
    POST JSON matching RawRecord schema.
    """
    # Build packet feature vector
    pkt_row = np.array([[
        record.Flow_Duration, record.Total_Fwd_Packets, record.Total_Backward_Packets,
        record.Total_Length_Fwd_Packets, record.Total_Length_Bwd_Packets,
        record.Flow_Bytes_s, record.Flow_Packets_s,
        record.Flow_IAT_Mean, record.Flow_IAT_Std,
        record.Fwd_IAT_Mean, record.Bwd_IAT_Mean,
        record.SYN_Flag_Count, record.RST_Flag_Count,
        0, 0, 0,                                   # FIN, PSH, ACK flags
        0, 0, record.Average_Packet_Size, record.Average_Packet_Size,
        0, 0, 0, 0,                                # headers, active, idle
        0.5, 0.5, 0.0, 0.0,                        # engineered ratios
    ]], dtype=np.float32)

    beh_row = np.array([[
        record.num_connections, record.avg_flow_bytes_s, 0, 0, 0, 0,
        record.Average_Packet_Size, record.syn_count, record.RST_Flag_Count, 0,
    ]], dtype=np.float32)

    pkt_pred, pkt_prob = run_packet_layer(pkt_row)
    flo_pred, flo_prob = run_flow_layer(pkt_row)
    beh_pred, beh_prob = run_behavioural_layer(beh_row)

    final_pred = majority_vote(pkt_pred, flo_pred, beh_pred)
    final_prob = fuse_probability(pkt_prob, flo_prob, beh_prob)

    event = {
        "id":               str(uuid.uuid4())[:8],
        "timestamp":        time.time(),
        "src_ip":           record.src_ip,
        "packet_size":      int(record.Average_Packet_Size),
        "packet_label":     "attack" if pkt_pred else "normal",
        "packet_prob":      round(pkt_prob, 3),
        "flow_label":       "attack" if flo_pred else "normal",
        "flow_prob":        round(flo_prob, 3),
        "behaviour_label":  "attack" if beh_pred else "normal",
        "behaviour_prob":   round(beh_prob, 3),
        "label":            "attack" if final_pred else "normal",
        "attack_probability": round(final_prob, 3),
        "color":            priority_color(final_prob),
    }

    with store_lock:
        event_store.append(event)

    return event


@app.post("/ingest")
def ingest_batch(records: List[RawRecord]):
    """Batch ingest up to 100 records."""
    if len(records) > 100:
        raise HTTPException(status_code=400, detail="Max 100 records per batch.")
    results = [predict(r) for r in records]
    return {"processed": len(results), "events": results}


@app.get("/stats")
def get_stats():
    """Summary statistics over the current event buffer."""
    with store_lock:
        evts = list(event_store)

    if not evts:
        return {"total": 0}

    probs   = [e["attack_probability"] for e in evts]
    attacks = [e for e in evts if e["label"] == "attack"]

    type_counts: dict = {}
    for e in attacks:
        t = e.get("attack_type", "Unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        "total":            len(evts),
        "attacks":          len(attacks),
        "normal":           len(evts) - len(attacks),
        "high_risk":        sum(1 for p in probs if p > 0.8),
        "attack_rate_pct":  round(len(attacks) / len(evts) * 100, 1),
        "avg_threat_score": round(float(np.mean(probs)), 3),
        "attack_types":     type_counts,
        "window_start":     evts[0]["timestamp"],
        "window_end":       evts[-1]["timestamp"],
    }


@app.delete("/events")
def clear_events():
    """Clear the event buffer (admin use)."""
    with store_lock:
        event_store.clear()
    return {"cleared": True}


# ══════════════════════════════════════════════════════════════════════════════
#  STARTUP
# ══════════════════════════════════════════════════════════════════════════════
@app.on_event("startup")
async def startup():
    # Pre-load models
    _ = models.autoencoder

    if SIMULATE:
        print("🚀 Starting traffic simulator…")
        t = threading.Thread(target=simulator_loop, daemon=True)
        t.start()
    else:
        print("ℹ  Simulator disabled – send events via POST /predict or POST /ingest")


if __name__ == "__main__":
    print("=" * 60)
    print("  AI-SOC Backend — Multi-Layer Anomaly Detection")
    print("=" * 60)
    uvicorn.run(
        "backend:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )