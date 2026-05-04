# Multi-Layered Anomaly Detection Framework for Network Security

**A real-time, AI-powered Security Operations Center (SOC) platform that detects network intrusions using a three-layer machine learning fusion engine — operating directly on live network traffic.**

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Detection Layers](#detection-layers)
4. [Components](#components)
   - [Backend — prepex_backend.py](#1-backend--prepex_backendpy)
   - [SOC Dashboard — front/](#2-soc-dashboard--front)
   - [Attacker Control Panel — attacker_panel.py](#3-attacker-control-panel--attacker_panelpy)
5. [Attack Types Supported](#attack-types-supported)
6. [Demo Mode](#demo-mode)
7. [API Reference](#api-reference)
8. [Trained Models](#trained-models)
9. [Setup & Installation](#setup--installation)
10. [Running the System](#running-the-system)
11. [Project Structure](#project-structure)

---

## Project Overview

Traditional signature-based intrusion detection systems (IDS) fail against zero-day attacks, encrypted traffic, and low-and-slow behavioral anomalies. This project addresses that gap by combining **three independent machine learning models** into a unified detection pipeline that operates at packet, flow, and behavioral levels simultaneously.

The framework captures live network packets, extracts features across three abstraction layers, runs independent ML inference on each, and applies **majority voting** (2-of-3 layers must agree) before raising a final alert. This design significantly reduces both false positives and false negatives compared to single-model approaches.

### Key Highlights

- **Three-layer fusion engine** — packet autoencoder, flow anomaly scorer, and behavioral GRU
- **Real-time packet capture** via PyShark/TShark, processing every IP packet on the wire
- **Adaptive thresholds** — dynamically recalibrated using the 95th percentile of rolling score history (no hard-coded cutoffs)
- **Full demo mode** — controlled simulation of 11 attack scenarios for presentations and evaluation
- **Mobile-first attacker panel** — trigger simulated attacks from a smartphone on the same Wi-Fi network
- **React SOC dashboard** — live threat table, KPI cards, trend charts, and per-event layer breakdown

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LIVE NETWORK INTERFACE                        │
│                        (Wi-Fi / wlan0 / eth0)                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │  PyShark LiveCapture
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      prepex_backend.py  (port 8000)                  │
│                                                                       │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │
│  │  LAYER 1       │  │  LAYER 2       │  │  LAYER 3               │  │
│  │  Packet        │  │  Flow          │  │  Behaviour             │  │
│  │  Autoencoder   │  │  Anomaly Score │  │  GRU Classifier        │  │
│  │  (recon error) │  │  (z-score MAE) │  │  (sequence prob)       │  │
│  └───────┬────────┘  └───────┬────────┘  └──────────┬─────────────┘  │
│          └──────────────────►│◄─────────────────────┘               │
│                              ▼                                        │
│              ┌───────────────────────────────┐                        │
│              │   MAJORITY VOTE  (>= 2 of 3)  │                        │
│              │   final_label = "attack"      │                        │
│              └───────────────────────────────┘                        │
│                              │                                        │
│                    ┌─────────▼──────────┐                             │
│                    │  RECENT_EVENTS     │  (deque, last 500)          │
│                    │  REST API          │  /events /stats /health     │
│                    └────────────────────┘                             │
└─────────────────────────────────────────────────────────────────────┘
          │                                          │
          ▼                                          ▼
┌──────────────────────┐               ┌──────────────────────────┐
│  React SOC Dashboard │               │  Attacker Control Panel  │
│  front/  (port 5173) │               │  attacker_panel.py       │
│  Recharts · KPIs     │               │  (port 8080)             │
│  Threat Table · Logs │               │  Mobile-first HTML       │
└──────────────────────┘               └──────────────────────────┘
```

---

## Detection Layers

### Layer 1 — Packet-Level Autoencoder

| Property | Detail |
|---|---|
| Model | TensorFlow/Keras Dense Autoencoder (`packet_layer_autoencoder.h5`) |
| Features | `flow_duration`, `total_packets`, `total_bytes`, `flow_bytes_per_sec`, `flow_packets_per_sec`, `avg_packet_size`, `syn_count`, `rst_count`, `connection_failure_ratio` |
| Anomaly Score | Mean Squared Reconstruction Error (MSE) |
| Threshold | 95th percentile of a rolling 2000-sample history (adaptive) |
| Detects | High-volume floods (SYN, HTTP, ICMP), malformed packet bursts |

### Layer 2 — Flow-Level Anomaly Scorer

| Property | Detail |
|---|---|
| Model | StandardScaler-based z-score deviation (`flow_layer_scaler.pkl`) |
| Features | `Flow Duration`, `Total Fwd/Bwd Packets`, `Total Length Fwd/Bwd`, `Flow Bytes/s`, `Flow Packets/s`, `Flow IAT Mean/Std` |
| Anomaly Score | Mean Absolute z-score across all flow features |
| Threshold | 95th percentile of a rolling 2000-sample history (adaptive) |
| Detects | Data exfiltration (high byte volumes), unusual traffic patterns, abnormal inter-arrival times |

### Layer 3 — Behavioral GRU Classifier

| Property | Detail |
|---|---|
| Model | Gated Recurrent Unit (GRU) sequence classifier (`behavior_layer_gru.h5`) |
| Input | Sliding window of 10 timesteps x N behavior features per source IP |
| Features | Cumulative packets, bytes, bytes/s, packets/s (per IP over time) |
| Output | Attack probability [0.0 to 1.0] |
| Threshold | 90th percentile of a rolling 2000-sample history (adaptive) |
| Detects | **Slow and stealthy attacks** — botnet C2 beacons, brute-force SSH, port scans, insider threats — that evade packet/flow layers |

### Fusion Decision

```
final_label = "attack"  if  (Layer1 == attack) + (Layer2 == attack) + (Layer3 == attack) >= 2
            = "normal"  otherwise
```

This majority-vote approach is the **critical differentiator**: a botnet beacon may register normal at Layer 1 and Layer 2 but will still be caught if Layer 3 fires, as long as another layer concurs.

---

## Components

### 1. Backend — `prepex_backend.py`

The core FastAPI application running on **port 8000**. It performs all ML inference and exposes the REST API consumed by both the dashboard and the attacker panel.

**Responsibilities:**
- Spawns a background thread that runs PyShark `LiveCapture` on the configured network interface
- On each captured IP packet: extracts features, runs all three ML layers, applies majority vote, appends the event to a 500-event in-memory deque
- Maintains per-source-IP state dictionaries (flow stats and behavior sequences)
- Exposes the `/demo/mode` endpoint so the attacker panel can override output with controlled attack profiles for live demonstrations

**Key configuration (top of `prepex_backend.py`):**
```python
INTERFACE = "Wi-Fi"       # Change to your interface name (e.g., "wlan0", "eth0")
MAX_EVENTS = 500          # In-memory event buffer
SEQ_LEN = 10              # GRU sequence window length
```

---

### 2. SOC Dashboard — `front/`

A **React + Vite** single-page application providing the analyst-facing interface.

**Stack:** React 18, Vite, Recharts

**Polls backend every 1 second** at `http://127.0.0.1:8000`.

**Dashboard panels:**

| Panel | Description |
|---|---|
| **KPI Cards** | Total Events, Attacks Detected, High-Risk Events (prob > 0.8), Average Threat Score |
| **Threat Table** | Per-event list sortable by threat probability; columns: Priority badge, Source IP, Attack Type, Layer indicators (PKT / FLOW / BEH), Score, Verdict, Timestamp |
| **Investigation Panel** | Click any event to see per-layer scores, model names, mini progress bars, and confidence |
| **Threat Score Trend** | Area chart showing average and peak threat score over time (8-second buckets) |
| **Attack Distribution** | Bar chart of detected attack types |
| **Risk Heatmap** | Grid of last 60 events color-coded by threat level |
| **Event Log** | Raw reverse-chronological log with per-layer probabilities |

**Priority classification:**

| Score | Level |
|---|---|
| > 0.80 | CRITICAL (red) |
| > 0.60 | HIGH (orange) |
| > 0.40 | MEDIUM (yellow) |
| <= 0.40 | LOW (green) |

---

### 3. Attacker Control Panel — `attacker_panel.py`

A FastAPI application running on **port 8080** that serves a **mobile-first hacker-aesthetic HTML interface**. Its purpose is to allow a presenter to trigger simulated attacks from their smartphone during live demonstrations, while the SOC dashboard (on the laptop/projector) reacts in real time.

**Access from phone:** Open `http://<LAPTOP_IP>:8080` on any device on the same Wi-Fi network.

**Features:**

| Feature | Description |
|---|---|
| **Attack Buttons (8 types)** | One-tap buttons for each attack type; shows which detection layers are expected to fire |
| **Layer Status Indicators** | Live display of PACKET / FLOW / BEHAVIOR status (NORMAL / ATTACK) |
| **Risk Bar** | Animated progress bar showing current threat level |
| **Insider Threat Sequence** | Auto-runs 3 phases (Normal Cover → Quiet Recon → Exfiltration) with 8-second intervals |
| **Full Judge Demo** | Automated sequence of 10 scenarios — runs unattended; ideal for project presentations |
| **Attack Log** | Timestamped activity log of all triggered attacks |
| **Stop / Normal** | Instantly revert backend to normal baseline or stop demo mode entirely |

The panel acts as a **proxy layer** — all attack triggers call `POST /api/attack/{mode}`, which the panel forwards to `POST http://localhost:8000/demo/mode` on the backend.

---

## Attack Types Supported

| Mode | Attack Name | Primary Layers Triggered | Description |
|---|---|---|---|
| `syn_flood` | SYN Flood (DDoS) | PKT + FLOW | TCP connection flooding, high packet/byte rate |
| `port_scan` | Port Scan (Recon) | PKT + BEH | Systematic port enumeration, behavioral anomaly |
| `brute_force` | Brute Force (SSH) | BEH only | Repeated low-volume auth attempts — stealth detection |
| `data_exfil` | Data Exfiltration | FLOW + BEH | Large outbound byte transfers, abnormal session behavior |
| `botnet` | Botnet C2 Beacon | BEH only | **Key demo** — passes Layers 1 and 2; only GRU detects |
| `http_flood` | HTTP Flood (DDoS) | PKT + FLOW | Layer-7 application-level flood |
| `icmp_flood` | ICMP Flood | PKT | Classic ping-of-death / ICMP echo flood |
| `insider_phase1` | Insider — Normal | None | Employee behaves normally (baseline cover) |
| `insider_phase2` | Insider — Recon | BEH | Quiet internal reconnaissance begins |
| `insider_phase3` | Insider — Exfil | PKT + FLOW + BEH | Active data theft; all three layers fire |
| `normal` | Normal Traffic | None | Baseline legitimate traffic |

The **Botnet C2** scenario is specifically designed as the key demonstration of the 3-layer architecture's value: Layers 1 and 2 both read normal (low packet volume, normal byte rates), but Layer 3's GRU detects the periodic beaconing pattern in the behavioral sequence — a detection that a single-layer or two-layer system would miss entirely.

---

## Demo Mode

The backend implements a controlled **Demo Mode** that allows live presentations without relying on real attack traffic or threshold calibration uncertainty.

When demo mode is active:
- The packet capture loop continues running (real packets still arrive)
- Instead of running ML inference, the backend returns **pre-defined label + score profiles** from `DEMO_PROFILES` with ±10% random noise added to scores
- The dashboard displays realistic, live-looking graphs because scores vary naturally
- Labels are 100% deterministic — the correct layers fire every time

**Example demo profile entry in `prepex_backend.py`:**
```python
DEMO_PROFILES = {
    # mode          pkt_lbl   flw_lbl   beh_lbl   final     pkt_base  flw_base  beh_base
    "botnet":     ("normal", "normal", "attack", "attack",  0.0090,   0.17,     0.85),
    "syn_flood":  ("attack", "attack", "normal", "attack",  0.0850,   0.92,     0.18),
}
```

Switching back to real ML inference is a single API call (`POST /demo/stop`) or tapping **STOP DEMO** on the attacker panel.

---

## API Reference

All endpoints served by `prepex_backend.py` at **`http://localhost:8000`**.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/events` | Returns the last 500 detected events as a JSON array |
| `GET` | `/health` | Liveness check; includes demo mode status and event count |
| `GET` | `/stats` | Aggregated statistics: total, attacks, normal, high-risk, attack rate %, avg threat score, attack type breakdown |
| `GET` | `/demo/mode` | Returns current demo mode name and active flag |
| `POST` | `/demo/mode` | Sets demo mode: `{"mode": "syn_flood", "active": true}` |
| `POST` | `/demo/stop` | Stops demo mode and returns backend to live ML inference |

**Example event payload (`/events` response item):**
```json
{
  "timestamp": 1714821600.123,
  "src_ip": "192.168.1.45",
  "packet_size": 1420,
  "flow_bytes_s": 25000.0,
  "flow_packets_s": 900.0,
  "packet_layer_label": "attack",
  "packet_layer_score": 0.085,
  "packet_layer_threshold": 0.030,
  "flow_layer_label": "attack",
  "flow_layer_score": 0.92,
  "flow_layer_threshold": 0.50,
  "behavior_layer_label": "normal",
  "behavior_layer_prob": 0.18,
  "behavior_layer_threshold": 0.70,
  "final_label": "attack",
  "attack_type": "SYN Flood (DDoS)"
}
```

---

## Trained Models

| File | Type | Purpose |
|---|---|---|
| `packet_layer_autoencoder.h5` | Keras Dense Autoencoder | Packet-level reconstruction error scoring |
| `behavior_layer_gru.h5` | Keras GRU Classifier | Per-IP behavioral sequence classification |
| `packet_layer_scaler.pkl` | sklearn StandardScaler | Normalizes packet feature vectors before inference |
| `packet_layer_features.pkl` | Python list | Ordered feature name list for packet layer |
| `flow_layer_scaler.pkl` | sklearn StandardScaler | Normalizes flow feature vectors before scoring |
| `flow_layer_all_columns.pkl` | Python list | All column names from flow training dataset |
| `behavior_layer_scaler.pkl` | sklearn StandardScaler | Normalizes behavioral feature vectors before GRU |
| `behavior_layer_n_features.pkl` | int | Number of features used in GRU input |

All model files must reside in the **same directory** as `prepex_backend.py` when the server starts.

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- Wireshark / TShark installed and accessible on system PATH (required by PyShark for packet capture)
- Administrator / root privileges for live packet capture

### Backend Setup

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn pyshark tensorflow joblib numpy pydantic httpx
```

### Frontend Setup

```bash
cd front
npm install
```

---

## Running the System

**Step 1 — Start the Backend** (requires admin/root for raw packet capture)

```bash
# Windows (run terminal as Administrator)
uvicorn prepex_backend:app --host 0.0.0.0 --port 8000

# Linux
sudo uvicorn prepex_backend:app --host 0.0.0.0 --port 8000
```

Verify it is running: `http://localhost:8000/health`

**Step 2 — Start the SOC Dashboard**

```bash
cd front
npm run dev
```

Open: `http://localhost:5173`

**Step 3 — Start the Attacker Panel** (optional; used for live demos)

```bash
python attacker_panel.py
```

Open on laptop: `http://localhost:8080`
Open on phone (same Wi-Fi): `http://<LAPTOP_IP>:8080`

Find your laptop IP:
- Windows: `ipconfig`
- Linux/macOS: `hostname -I`

---

## Project Structure

```
├── prepex_backend.py              # Core FastAPI backend — ML inference + REST API
├── attacker_panel.py              # Mobile attacker control panel (port 8080)
├── front/                         # React + Vite SOC dashboard
│   ├── src/
│   │   ├── App.jsx                # Main dashboard UI (KPIs, threat table, charts)
│   │   └── main.jsx               # React entry point
│   ├── index.html
│   └── vite.config.js
├── packet_layer_autoencoder.h5    # Trained packet autoencoder (Keras)
├── behavior_layer_gru.h5          # Trained behavioral GRU (Keras)
├── packet_layer_scaler.pkl        # Packet feature scaler (sklearn)
├── packet_layer_features.pkl      # Packet feature name list
├── flow_layer_scaler.pkl          # Flow feature scaler (sklearn)
├── flow_layer_all_columns.pkl     # Flow training column names
├── behavior_layer_scaler.pkl      # Behavior feature scaler (sklearn)
├── behavior_layer_n_features.pkl  # Behavior feature count
└── venv/                          # Python virtual environment
```

---

## Technical Notes

- **Interface name:** The default interface is `"Wi-Fi"` (Windows). Change `INTERFACE` in `prepex_backend.py` for Linux (`"wlan0"`, `"eth0"`) or macOS (`"en0"`).
- **Warm-up period:** Adaptive thresholds require at least 50 events before they activate. During warm-up, the threshold is set to `inf` (no alerts until enough data is collected).
- **Behavior layer warm-up:** The GRU requires `SEQ_LEN = 10` consecutive events per source IP before it can score that IP's behavior. It returns `"normal"` during the warm-up window.
- **Thread safety:** All shared state (`RECENT_EVENTS`, `flow_state`, `behavior_sequences`, `_demo_mode`) is protected appropriately. The `_demo_lock` ensures consistent demo state between the API handler thread and the packet capture thread.
- **CORS:** The backend allows all origins (`*`) for local development convenience. This should be restricted in any production or hardened deployment.
