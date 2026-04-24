"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   REAL-TIME AI-SOC BACKEND  —  Live WiFi Packet Capture + ML Detection     ║
║   Paper: Multi-Layered Anomaly Detection Framework for Network Security     ║
║   Architecture: Scapy Capture → Packet Layer → Flow Layer →               ║
║                 Behavioural Layer → Fusion Engine → WebSocket → Dashboard  ║
╚══════════════════════════════════════════════════════════════════════════════╝

INSTALL:
    pip install fastapi uvicorn websockets scapy tensorflow
               scikit-learn joblib numpy pandas pyshark psutil

RUN (as Administrator/root — required for raw packet capture):
    sudo python live_capture_backend.py      # Linux/Mac
    python live_capture_backend.py           # Windows (Run as Admin)
"""

import os, sys, time, uuid, json, threading, asyncio, collections, math
import numpy as np
import pandas as pd
import joblib
import psutil
import logging
from datetime import datetime
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field, asdict

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Scapy (packet capture) ────────────────────────────────────────────────────
try:
    from scapy.all import sniff, IP, TCP, UDP, ICMP, ARP, get_if_list, conf
    from scapy.layers.http import HTTP
    SCAPY_OK = True
except ImportError:
    SCAPY_OK = False
    print("⚠  scapy not found. Install: pip install scapy")

# ── TensorFlow (optional) ─────────────────────────────────────────────────────
try:
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    import tensorflow as tf
    tf.get_logger().setLevel("ERROR")
    TF_OK = True
except ImportError:
    TF_OK = False

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S")
log = logging.getLogger("AI-SOC")

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════════════════
MODEL_DIR         = os.getenv("MODEL_DIR", ".")
FLOW_TIMEOUT_SEC  = 30          # expire inactive flows after 30 s
BEH_WINDOW_SEC    = 60          # behavioural window = 60 s
MAX_EVENTS        = 300         # rolling event buffer
INFERENCE_EVERY   = 3           # run ML every N packets in a flow
IFACE             = None        # None = auto-detect WiFi interface
PACKET_FILTER     = "ip"        # BPF filter — only IP packets

# ── Thresholds (from paper Table IV / Youden's J) ─────────────────────────────
AE_THRESHOLD   = 0.68
IF_THRESHOLD   = 0.55
GRU_THRESHOLD  = 0.62

# ══════════════════════════════════════════════════════════════════════════════
#  MODEL STORE  — load once, reuse forever
# ══════════════════════════════════════════════════════════════════════════════
class ModelStore:
    def __init__(self):
        self._ae = self._if = self._lstm = None
        self._ps = self._bs = None
        self._pt = self._bf = None
        self._pkf = self._bhf = None
        self._loaded = False

    def _try(self, loader, path, name):
        full = os.path.join(MODEL_DIR, path)
        if not os.path.exists(full):
            log.warning(f"  {name} not found at {full}")
            return None
        try:
            r = loader(full)
            log.info(f"  ✅ {name}")
            return r
        except Exception as e:
            log.error(f"  ❌ {name}: {e}")
            return None

    def load(self):
        if self._loaded: return
        log.info("🔧 Loading trained models…")
        self._if  = self._try(joblib.load, "isolation_forest.pkl",  "Isolation Forest")
        self._ps  = self._try(joblib.load, "packet_scaler.pkl",     "Packet Scaler")
        self._bs  = self._try(joblib.load, "behavior_scaler.pkl",   "Behaviour Scaler")
        self._pkf = self._try(joblib.load, "packet_features.pkl",   "Packet Features List")
        self._bhf = self._try(joblib.load, "behavior_features.pkl", "Behaviour Features List")
        self._pt  = self._try(joblib.load, "packet_thresholds.pkl", "Packet Thresholds")
        self._bt  = self._try(joblib.load, "behavior_threshold.pkl","Behaviour Threshold")

        if TF_OK:
            self._ae   = self._try(lambda p: tf.keras.models.load_model(p, compile=False),
                                   "packet_autoencoder.h5", "Packet Autoencoder")
            self._lstm = self._try(lambda p: tf.keras.models.load_model(p, compile=False),
                                   "behavioral_lstm.h5", "Behavioural LSTM")

        if self._pt  is None: self._pt  = {"autoencoder": AE_THRESHOLD}
        if self._bt  is None: self._bt  = GRU_THRESHOLD
        if self._pkf is None: self._pkf = PKT_FALLBACK_FEATS
        if self._bhf is None: self._bhf = BEH_FALLBACK_FEATS
        self._loaded = True
        log.info("✅ Models ready.\n")

    @property
    def ae(self):   self.load(); return self._ae
    @property
    def iforest(self): self.load(); return self._if
    @property
    def lstm(self): self.load(); return self._lstm
    @property
    def pscaler(self): self.load(); return self._ps
    @property
    def bscaler(self): self.load(); return self._bs
    @property
    def pthresh(self): self.load(); return self._pt
    @property
    def bthresh(self): self.load(); return self._bt

MODELS = ModelStore()

PKT_FALLBACK_FEATS = [
    "flow_duration","total_fwd_pkts","total_bwd_pkts",
    "total_len_fwd","total_len_bwd","flow_bytes_s","flow_pkts_s",
    "iat_mean","iat_std","fwd_iat_mean","bwd_iat_mean",
    "syn_cnt","rst_cnt","fin_cnt","psh_cnt","ack_cnt",
    "fwd_pkt_len_mean","bwd_pkt_len_mean","pkt_len_mean","avg_pkt_size",
    "fwd_hdr_len","bwd_hdr_len","active_mean","idle_mean",
    "fwd_pkt_ratio","fwd_bytes_ratio","conn_fail_ratio","iat_regularity",
]

BEH_FALLBACK_FEATS = [
    "num_connections","avg_bytes_s","avg_pkts_s","avg_duration",
    "total_fwd_pkts","total_bwd_pkts","avg_pkt_size",
    "syn_cnt","rst_cnt","avg_iat",
]

# ══════════════════════════════════════════════════════════════════════════════
#  FLOW TRACKER  — aggregate packets → flow records
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class FlowRecord:
    key:         tuple
    src_ip:      str
    dst_ip:      str
    src_port:    int
    dst_port:    int
    proto:       str
    start_time:  float = field(default_factory=time.time)
    last_time:   float = field(default_factory=time.time)

    pkt_count:   int   = 0
    fwd_pkts:    int   = 0
    bwd_pkts:    int   = 0
    fwd_bytes:   int   = 0
    bwd_bytes:   int   = 0
    total_bytes: int   = 0

    syn_cnt:     int   = 0
    ack_cnt:     int   = 0
    fin_cnt:     int   = 0
    rst_cnt:     int   = 0
    psh_cnt:     int   = 0

    iats:        list  = field(default_factory=list)
    fwd_iats:    list  = field(default_factory=list)
    bwd_iats:    list  = field(default_factory=list)
    pkt_sizes:   list  = field(default_factory=list)

    last_fwd:    float = 0.0
    last_bwd:    float = 0.0

    def add_packet(self, ts: float, size: int, direction: str, flags: int = 0):
        now = ts
        if self.pkt_count > 0:
            iat = now - self.last_time
            self.iats.append(iat)
        self.last_time = now
        self.pkt_count += 1
        self.total_bytes += size
        self.pkt_sizes.append(size)

        if direction == "fwd":
            self.fwd_pkts  += 1
            self.fwd_bytes += size
            if self.last_fwd > 0:
                self.fwd_iats.append(now - self.last_fwd)
            self.last_fwd = now
        else:
            self.bwd_pkts  += 1
            self.bwd_bytes += size
            if self.last_bwd > 0:
                self.bwd_iats.append(now - self.last_bwd)
            self.last_bwd = now

        # TCP flags
        if flags & 0x02: self.syn_cnt += 1
        if flags & 0x10: self.ack_cnt += 1
        if flags & 0x01: self.fin_cnt += 1
        if flags & 0x04: self.rst_cnt += 1
        if flags & 0x08: self.psh_cnt += 1

    def to_features(self) -> np.ndarray:
        dur   = max(self.last_time - self.start_time, 1e-6)
        iats  = self.iats or [0]
        fwd_i = self.fwd_iats or [0]
        bwd_i = self.bwd_iats or [0]
        psizes= self.pkt_sizes or [0]

        def safe_mean(lst): return float(np.mean(lst)) if lst else 0.0
        def safe_std(lst):  return float(np.std(lst))  if len(lst)>1 else 0.0

        tp = max(self.fwd_pkts + self.bwd_pkts, 1)
        tb = max(self.fwd_bytes + self.bwd_bytes, 1)

        vec = [
            dur * 1e6,                                          # flow_duration (μs)
            self.fwd_pkts, self.bwd_pkts,                      # packet counts
            self.fwd_bytes, self.bwd_bytes,                    # byte counts
            self.total_bytes / dur,                            # flow_bytes_s
            self.pkt_count / dur,                              # flow_pkts_s
            safe_mean(iats) * 1e6, safe_std(iats) * 1e6,      # IAT mean/std
            safe_mean(fwd_i) * 1e6, safe_mean(bwd_i) * 1e6,   # fwd/bwd IAT
            self.syn_cnt, self.rst_cnt, self.fin_cnt,          # flags
            self.psh_cnt, self.ack_cnt,
            safe_mean([s for s in psizes if s > 0]),           # fwd pkt len mean (approx)
            safe_mean([s for s in psizes if s > 0]) * 0.6,    # bwd pkt len mean (approx)
            safe_mean(psizes), safe_mean(psizes),              # pkt_len_mean, avg_pkt_size
            20.0, 20.0,                                         # fwd/bwd header len (approx)
            0.0, 0.0,                                           # active/idle mean
            self.fwd_pkts / tp,                                # fwd_pkt_ratio
            self.fwd_bytes / tb,                               # fwd_bytes_ratio
            self.rst_cnt / max(self.syn_cnt, 1),               # conn_fail_ratio
            safe_std(iats) / max(safe_mean(iats), 1e-9),       # iat_regularity
        ]
        return np.array(vec, dtype=np.float32).reshape(1, -1)


class FlowTracker:
    def __init__(self):
        self._flows:  Dict[tuple, FlowRecord] = {}
        self._lock    = threading.Lock()
        self._expired: List[FlowRecord]       = []

    def update(self, pkt) -> Optional[FlowRecord]:
        """Feed one scapy packet; return updated FlowRecord."""
        if not pkt.haslayer(IP): return None
        ip   = pkt[IP]
        ts   = float(pkt.time)
        size = len(pkt)

        src_ip, dst_ip = ip.src, ip.dst
        proto = "OTHER"
        src_port = dst_port = 0
        flags = 0

        if pkt.haslayer(TCP):
            proto    = "TCP"
            src_port = pkt[TCP].sport
            dst_port = pkt[TCP].dport
            flags    = int(pkt[TCP].flags)
        elif pkt.haslayer(UDP):
            proto    = "UDP"
            src_port = pkt[UDP].sport
            dst_port = pkt[UDP].dport
        elif pkt.haslayer(ICMP):
            proto = "ICMP"

        fwd_key = (src_ip, dst_ip, src_port, dst_port, proto)
        bwd_key = (dst_ip, src_ip, dst_port, src_port, proto)

        with self._lock:
            if fwd_key in self._flows:
                flow = self._flows[fwd_key]
                flow.add_packet(ts, size, "fwd", flags)
            elif bwd_key in self._flows:
                flow = self._flows[bwd_key]
                flow.add_packet(ts, size, "bwd", flags)
            else:
                # New flow
                flow = FlowRecord(
                    key=fwd_key, src_ip=src_ip, dst_ip=dst_ip,
                    src_port=src_port, dst_port=dst_port, proto=proto
                )
                flow.add_packet(ts, size, "fwd", flags)
                self._flows[fwd_key] = flow

            self._expire_old(ts)
            return flow

    def _expire_old(self, now: float):
        dead = [k for k, f in self._flows.items()
                if now - f.last_time > FLOW_TIMEOUT_SEC]
        for k in dead:
            self._expired.append(self._flows.pop(k))

    def get_all_flows(self) -> List[FlowRecord]:
        with self._lock:
            return list(self._flows.values())

    def flow_count(self) -> int:
        with self._lock:
            return len(self._flows)


# ══════════════════════════════════════════════════════════════════════════════
#  BEHAVIOURAL TRACKER  — per-IP rolling window
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class BehRecord:
    ip: str
    window_start: float = field(default_factory=time.time)
    connections:  int   = 0
    unique_dsts:  Set[str] = field(default_factory=set)
    unique_dports: Set[int] = field(default_factory=set)
    total_bytes:  int   = 0
    total_pkts:   int   = 0
    syn_burst:    int   = 0
    rst_burst:    int   = 0
    durations:    list  = field(default_factory=list)
    byte_rate_samples: list = field(default_factory=list)

    def to_features(self) -> np.ndarray:
        dur = max(time.time() - self.window_start, 1.0)
        vec = [
            self.connections,
            self.total_bytes / dur,               # avg_bytes_s
            self.total_pkts  / dur,               # avg_pkts_s
            float(np.mean(self.durations)) if self.durations else 0.0,
            self.total_pkts * 0.6,                # approx fwd_pkts
            self.total_pkts * 0.4,                # approx bwd_pkts
            self.total_bytes / max(self.total_pkts, 1),  # avg_pkt_size
            self.syn_burst,
            self.rst_burst,
            float(np.mean(self.byte_rate_samples)) if self.byte_rate_samples else 0.0,
        ]
        return np.array(vec, dtype=np.float32).reshape(1, -1)


class BehaviouralTracker:
    def __init__(self):
        self._records: Dict[str, BehRecord] = {}
        self._lock = threading.Lock()

    def update_from_flow(self, flow: FlowRecord):
        dur = flow.last_time - flow.start_time
        with self._lock:
            r = self._records.get(flow.src_ip)
            now = time.time()
            # Reset window if expired
            if r is None or (now - r.window_start) > BEH_WINDOW_SEC:
                r = BehRecord(ip=flow.src_ip, window_start=now)
                self._records[flow.src_ip] = r

            r.connections += 1
            r.unique_dsts.add(flow.dst_ip)
            r.unique_dports.add(flow.dst_port)
            r.total_bytes += flow.total_bytes
            r.total_pkts  += flow.pkt_count
            r.syn_burst   += flow.syn_cnt
            r.rst_burst   += flow.rst_cnt
            r.durations.append(dur)
            brate = flow.total_bytes / max(dur, 1e-6)
            r.byte_rate_samples.append(brate)
            return r

    def get(self, ip: str) -> Optional[BehRecord]:
        with self._lock:
            return self._records.get(ip)

    def all_records(self) -> List[BehRecord]:
        with self._lock:
            return list(self._records.values())


# ══════════════════════════════════════════════════════════════════════════════
#  ML INFERENCE ENGINE  — 3 layers + fusion
# ══════════════════════════════════════════════════════════════════════════════
def _scale(scaler, X: np.ndarray) -> np.ndarray:
    if scaler is None: return X
    try:
        n = getattr(scaler, "n_features_in_", X.shape[1])
        if X.shape[1] != n:
            Xr = np.zeros((1, n), dtype=np.float32)
            Xr[0, :min(X.shape[1], n)] = X[0, :min(X.shape[1], n)]
            return scaler.transform(Xr)
        return scaler.transform(X)
    except Exception as e:
        log.debug(f"Scale error: {e}")
        return X

def infer_packet_layer(feat: np.ndarray):
    """Layer 1: Autoencoder reconstruction + Isolation Forest (OR fusion)"""
    X = _scale(MODELS.pscaler, feat)
    ae_pred, ae_prob = 0, 0.0
    if_pred, if_prob = 0, 0.0

    if MODELS.ae is not None:
        try:
            recon = MODELS.ae.predict(X, verbose=0)
            err   = float(np.mean(np.abs(X - recon)))
            thr   = MODELS.pthresh.get("autoencoder", AE_THRESHOLD)
            ae_prob = min(err / (thr * 2 + 1e-9), 1.0)
            ae_pred = int(err > thr)
        except Exception as e: log.debug(f"AE: {e}")

    if MODELS.iforest is not None:
        try:
            score   = float(MODELS.iforest.decision_function(X)[0])
            if_pred = int(MODELS.iforest.predict(X)[0] == -1)
            if_prob = float(np.clip((-score + 0.3) / 0.8, 0, 1))
        except Exception as e: log.debug(f"IF: {e}")

    pred = int(ae_pred or if_pred)
    prob = float(max(ae_prob, if_prob))
    # Fallback heuristic when models not loaded
    if MODELS.ae is None and MODELS.iforest is None:
        raw = float(np.clip(feat[0, 0] / 5e8, 0, 1))   # normalised flow duration
        prob = raw; pred = int(raw > 0.5)
    return pred, round(prob, 4)

def infer_flow_layer(feat: np.ndarray):
    """Layer 2: Autoencoder on flow-level aggregation"""
    X = _scale(MODELS.pscaler, feat)
    if MODELS.ae is not None:
        try:
            recon = MODELS.ae.predict(X, verbose=0)
            err   = float(np.mean(np.abs(X - recon)))
            thr   = MODELS.pthresh.get("autoencoder", AE_THRESHOLD) * 0.85
            prob  = min(err / (thr * 2 + 1e-9), 1.0)
            return int(err > thr), round(prob, 4)
        except Exception as e: log.debug(f"Flow AE: {e}")
    # Heuristic: high bytes/s or high syn ratio = suspicious
    bps   = float(feat[0, 5]) if feat.shape[1] > 5 else 0
    syn   = float(feat[0, 11]) if feat.shape[1] > 11 else 0
    prob  = float(np.clip(bps / 1e6 * 0.4 + syn / 100 * 0.6, 0, 1))
    return int(prob > 0.5), round(prob, 4)

def infer_behavioural_layer(bfeat: np.ndarray, seq_len: int = 5):
    """Layer 3: LSTM Autoencoder on behavioural window"""
    X = _scale(MODELS.bscaler, bfeat)
    if MODELS.lstm is not None:
        try:
            seq   = np.tile(X, (seq_len, 1))[np.newaxis, ...]
            recon = MODELS.lstm.predict(seq, verbose=0)
            err   = float(np.mean(np.power(seq - recon, 2)))
            thr   = MODELS.bthresh if MODELS.bthresh else GRU_THRESHOLD
            prob  = min(err / (thr * 5 + 1e-9), 1.0)
            return int(err > thr), round(prob, 4)
        except Exception as e: log.debug(f"LSTM: {e}")
    # Heuristic: high connections/s + syn burst = attack
    conns = float(bfeat[0, 0]) if bfeat.shape[1] > 0 else 0
    syn   = float(bfeat[0, 7]) if bfeat.shape[1] > 7 else 0
    prob  = float(np.clip(conns / 200 * 0.5 + syn / 500 * 0.5, 0, 1))
    return int(prob > 0.6), round(prob, 4)

def majority_vote(pp, pf, pb) -> int:
    """Paper eq.(1): D_final = mode(Pp, Pf, Pb) — alarm if ≥2 agree"""
    return int(pp + pf + pb >= 2)

def fuse_prob(pp, pf, pb) -> float:
    return round(float(np.clip(0.30*pp + 0.30*pf + 0.40*pb, 0, 1)), 4)

def classify_attack(flow: FlowRecord, pkt_prob: float) -> str:
    """Rule-based attack type classification (for display)."""
    syn = flow.syn_cnt; rst = flow.rst_cnt
    bps = flow.total_bytes / max(flow.last_time - flow.start_time, 1e-6)

    if pkt_prob < 0.4:           return "Normal"
    if syn > 50 and bps > 50000: return "DDoS / SYN Flood"
    if rst > 20:                 return "Port Scan"
    if syn > 10 and flow.fwd_pkts > 30 and bps < 5000:
                                  return "Brute Force"
    if bps > 500000:             return "Data Exfiltration"
    if flow.dst_port in (80,443) and flow.pkt_count > 100:
                                  return "HTTP Flood"
    return "Anomalous Traffic"


# ══════════════════════════════════════════════════════════════════════════════
#  EVENT STORE
# ══════════════════════════════════════════════════════════════════════════════
event_buffer: collections.deque = collections.deque(maxlen=MAX_EVENTS)
ev_lock = threading.Lock()
pkt_counter     = 0
pkt_counter_lock = threading.Lock()

def build_detection_event(flow: FlowRecord,
                           beh: Optional[BehRecord]) -> dict:
    pkt_feat = flow.to_features()
    beh_feat = beh.to_features() if beh else np.zeros((1,10), dtype=np.float32)

    pp, pp_prob = infer_packet_layer(pkt_feat)
    pf, pf_prob = infer_flow_layer(pkt_feat)
    pb, pb_prob = infer_behavioural_layer(beh_feat)

    final = majority_vote(pp, pf, pb)
    fprob = fuse_prob(pp_prob, pf_prob, pb_prob)
    atype = classify_attack(flow, fprob)

    dur = flow.last_time - flow.start_time

    return {
        "id":               str(uuid.uuid4())[:8],
        "timestamp":        time.time(),
        "src_ip":           flow.src_ip,
        "dst_ip":           flow.dst_ip,
        "src_port":         flow.src_port,
        "dst_port":         flow.dst_port,
        "proto":            flow.proto,
        "attack_type":      atype,
        "packet_size":      int(flow.total_bytes / max(flow.pkt_count, 1)),
        "pkt_count":        flow.pkt_count,
        "flow_bytes":       flow.total_bytes,
        "flow_duration_s":  round(dur, 3),
        "bytes_per_s":      round(flow.total_bytes / max(dur, 1e-6), 1),

        # Layer 1 – Packet
        "packet_label":     "attack" if pp else "normal",
        "packet_prob":      pp_prob,
        "packet_model":     "Autoencoder + Isolation Forest",

        # Layer 2 – Flow
        "flow_label":       "attack" if pf else "normal",
        "flow_prob":        pf_prob,
        "flow_model":       "Autoencoder",

        # Layer 3 – Behaviour
        "behaviour_label":  "attack" if pb else "normal",
        "behaviour_prob":   pb_prob,
        "behaviour_model":  "LSTM Autoencoder",

        # Fusion (paper eq.1)
        "label":            "attack" if final else "normal",
        "attack_probability": fprob,

        # Raw flag counts (for display)
        "syn_cnt":          flow.syn_cnt,
        "rst_cnt":          flow.rst_cnt,
        "fin_cnt":          flow.fin_cnt,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  PACKET CAPTURE ENGINE
# ══════════════════════════════════════════════════════════════════════════════
flow_tracker = FlowTracker()
beh_tracker  = BehaviouralTracker()

# WebSocket clients
ws_clients: Set[WebSocket] = set()
ws_lock = threading.Lock()

async def _broadcast(data: dict):
    msg = json.dumps(data)
    dead = set()
    with ws_lock:
        clients = set(ws_clients)
    for ws in clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    if dead:
        with ws_lock:
            ws_clients.difference_update(dead)

# Bridge: capture thread → asyncio event loop
_loop: Optional[asyncio.AbstractEventLoop] = None
_event_queue: asyncio.Queue = None

def _schedule_broadcast(data: dict):
    """Called from capture thread; schedules coroutine on main loop."""
    if _loop and _event_queue:
        _loop.call_soon_threadsafe(_event_queue.put_nowait, data)

FLOW_INFERENCE_COUNTER: Dict[tuple, int] = {}

def _handle_packet(pkt):
    """Scapy packet callback — runs in capture thread."""
    global pkt_counter
    with pkt_counter_lock:
        pkt_counter += 1

    flow = flow_tracker.update(pkt)
    if flow is None: return

    # Run inference every INFERENCE_EVERY packets to avoid CPU overload
    cnt = FLOW_INFERENCE_COUNTER.get(flow.key, 0) + 1
    FLOW_INFERENCE_COUNTER[flow.key] = cnt

    if cnt % INFERENCE_EVERY != 0: return

    # Behavioural update
    beh = beh_tracker.update_from_flow(flow)

    event = build_detection_event(flow, beh)

    with ev_lock:
        event_buffer.append(event)

    _schedule_broadcast({"type": "event", "data": event})


def _get_wifi_interface() -> Optional[str]:
    """Auto-detect the active WiFi/Ethernet interface."""
    if not SCAPY_OK: return None
    # Prefer interface with most traffic (non-loopback)
    try:
        stats = psutil.net_io_counters(pernic=True)
        addrs = psutil.net_if_addrs()
        best  = None
        best_bytes = 0
        for iface, s in stats.items():
            if iface == "lo" or iface.startswith("loop"): continue
            if iface in addrs:
                total = s.bytes_recv + s.bytes_sent
                if total > best_bytes:
                    best_bytes = total
                    best = iface
        if best: log.info(f"📡 Selected interface: {best}")
        return best
    except Exception:
        ifaces = get_if_list() if SCAPY_OK else []
        return ifaces[0] if ifaces else None

_capture_thread: Optional[threading.Thread] = None
_capturing = False

def start_capture(iface: Optional[str] = None):
    global _capture_thread, _capturing
    if not SCAPY_OK:
        log.error("❌ Scapy not installed. Cannot capture.")
        return
    if _capturing:
        log.warning("Capture already running.")
        return

    iface = iface or _get_wifi_interface() or IFACE
    log.info(f"🚀 Starting live capture on interface: {iface or 'default'}")

    _capturing = True

    def _run():
        sniff(
            iface=iface,
            filter=PACKET_FILTER,
            prn=_handle_packet,
            store=False,
        )

    _capture_thread = threading.Thread(target=_run, name="PacketCapture", daemon=True)
    _capture_thread.start()
    log.info("✅ Packet capture started.\n")

def stop_capture():
    global _capturing
    _capturing = False
    log.info("⛔ Capture stopped.")


# ══════════════════════════════════════════════════════════════════════════════
#  FASTAPI APPLICATION
# ══════════════════════════════════════════════════════════════════════════════
app = FastAPI(title="AI-SOC Live Capture API", version="2.0.0")
app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ─── WebSocket endpoint ────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    with ws_lock:
        ws_clients.add(ws)
    log.info(f"🔌 WebSocket client connected. Total: {len(ws_clients)}")
    try:
        # Send current buffer on connect
        with ev_lock:
            snapshot = list(event_buffer)[-50:]
        await ws.send_text(json.dumps({"type": "snapshot", "data": snapshot}))
        # Keep alive
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        with ws_lock:
            ws_clients.discard(ws)
        log.info(f"🔌 WebSocket client disconnected. Total: {len(ws_clients)}")

# ─── Background WebSocket broadcaster ─────────────────────────────────────────
async def _ws_broadcaster():
    while True:
        data = await _event_queue.get()
        await _broadcast(data)

# ─── REST endpoints ────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"service": "AI-SOC Live Capture", "version": "2.0.0", "status": "ok"}

@app.get("/health")
def health():
    with pkt_counter_lock:
        pkts = pkt_counter
    return {
        "capturing":    _capturing,
        "packets_seen": pkts,
        "active_flows": flow_tracker.flow_count(),
        "event_count":  len(event_buffer),
        "ws_clients":   len(ws_clients),
        "models": {
            "autoencoder":      MODELS._ae   is not None,
            "isolation_forest": MODELS._if   is not None,
            "lstm":             MODELS._lstm is not None,
        }
    }

@app.get("/events")
def get_events(limit: int = 80):
    with ev_lock:
        return list(event_buffer)[-limit:]

@app.get("/stats")
def get_stats():
    with ev_lock:
        evts = list(event_buffer)
    with pkt_counter_lock:
        pkts = pkt_counter

    if not evts:
        return {"total": 0, "packets_captured": pkts, "active_flows": flow_tracker.flow_count()}

    probs   = [e["attack_probability"] for e in evts]
    attacks = [e for e in evts if e["label"] == "attack"]

    type_counts: dict = {}
    for e in attacks:
        t = e.get("attack_type", "Unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    proto_counts: dict = {}
    for e in evts:
        p = e.get("proto", "OTHER")
        proto_counts[p] = proto_counts.get(p, 0) + 1

    return {
        "total":            len(evts),
        "attacks":          len(attacks),
        "normal":           len(evts) - len(attacks),
        "high_risk":        sum(1 for p in probs if p > 0.8),
        "attack_rate_pct":  round(len(attacks) / max(len(evts), 1) * 100, 1),
        "avg_threat_score": round(float(np.mean(probs)), 3),
        "attack_types":     type_counts,
        "proto_dist":       proto_counts,
        "packets_captured": pkts,
        "active_flows":     flow_tracker.flow_count(),
    }

@app.get("/flows")
def get_flows():
    """Live flow table."""
    flows = flow_tracker.get_all_flows()
    result = []
    for f in flows[:50]:
        dur = f.last_time - f.start_time
        result.append({
            "src": f.src_ip, "dst": f.dst_ip,
            "sport": f.src_port, "dport": f.dst_port,
            "proto": f.proto, "pkts": f.pkt_count,
            "bytes": f.total_bytes,
            "bps": round(f.total_bytes / max(dur, 1e-6), 0),
            "syn": f.syn_cnt, "rst": f.rst_cnt,
            "duration_s": round(dur, 2),
        })
    return result

@app.get("/behaviour")
def get_behaviour():
    """Per-IP behavioural summary."""
    return [
        {
            "ip": r.ip,
            "connections": r.connections,
            "unique_dsts": len(r.unique_dsts),
            "unique_ports": len(r.unique_dports),
            "total_bytes": r.total_bytes,
            "syn_burst": r.syn_burst,
            "rst_burst": r.rst_burst,
            "window_age_s": round(time.time() - r.window_start, 0),
        }
        for r in beh_tracker.all_records()
    ]

@app.post("/capture/start")
def api_start(iface: str = None):
    start_capture(iface)
    return {"started": True, "interface": iface or "auto"}

@app.post("/capture/stop")
def api_stop():
    stop_capture()
    return {"stopped": True}

@app.delete("/events")
def clear():
    with ev_lock: event_buffer.clear()
    return {"cleared": True}

# ══════════════════════════════════════════════════════════════════════════════
#  STARTUP
# ══════════════════════════════════════════════════════════════════════════════
@app.on_event("startup")
async def startup():
    global _loop, _event_queue
    _loop = asyncio.get_running_loop()
    _event_queue = asyncio.Queue()
    # Pre-load models
    MODELS.load()
    # Start broadcaster coroutine
    asyncio.create_task(_ws_broadcaster())
    # Start packet capture
    start_capture()


if __name__ == "__main__":
    print("=" * 64)
    print("  AI-SOC Real-Time Capture Backend")
    print("  ⚠  Run as Administrator/root for raw packet capture!")
    print("=" * 64)
    uvicorn.run("live_capture_backend:app",
        host="0.0.0.0", port=8000,
        reload=False, log_level="info")