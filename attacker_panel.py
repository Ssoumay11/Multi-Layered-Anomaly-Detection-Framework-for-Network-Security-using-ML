"""
╔══════════════════════════════════════════════════════╗
║       AI-SOC ATTACKER CONTROL PANEL                  ║
║       Mobile-first attack simulation interface       ║
║       Connect your phone to same WiFi, open URL      ║
╚══════════════════════════════════════════════════════╝

Run:  python attacker_panel.py
Then: Open http://<YOUR_LAPTOP_IP>:8080 on your phone

Find your laptop IP:
  Windows: ipconfig
  Linux:   hostname -I
  macOS:   ipconfig getifaddr en0
"""

import os
import socket
import asyncio
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ── CONFIG ─────────────────────────────────────────────
BACKEND_URL = "http://localhost:8000"   # Your main backend
PANEL_PORT  = 8080                      # Port for this attacker panel
# ────────────────────────────────────────────────────────

app = FastAPI(title="AI-SOC Attacker Panel")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Helper: get local IP for display ───────────────────
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# ── Proxy endpoints to main backend ────────────────────

@app.get("/api/health")
async def proxy_health():
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{BACKEND_URL}/health")
            return JSONResponse(r.json())
    except Exception as e:
        return JSONResponse({"status": "offline", "error": str(e)}, status_code=503)

@app.get("/api/stats")
async def proxy_stats():
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{BACKEND_URL}/stats")
            return JSONResponse(r.json())
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=503)

@app.get("/api/events")
async def proxy_events():
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{BACKEND_URL}/events")
            return JSONResponse(r.json())
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=503)

@app.post("/api/attack/{mode}")
async def trigger_attack(mode: str):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(
                f"{BACKEND_URL}/demo/mode",
                json={"mode": mode, "active": True}
            )
            return JSONResponse({"success": True, "mode": mode, "backend": r.json()})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=503)

@app.post("/api/stop")
async def stop_attack():
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(f"{BACKEND_URL}/demo/stop")
            return JSONResponse({"success": True, "backend": r.json()})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=503)

@app.post("/api/normal")
async def set_normal():
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(
                f"{BACKEND_URL}/demo/mode",
                json={"mode": "normal", "active": True}
            )
            return JSONResponse({"success": True, "backend": r.json()})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=503)

# ── Main HTML Panel ─────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"/>
<meta name="apple-mobile-web-app-capable" content="yes"/>
<meta name="theme-color" content="#000000"/>
<title>ATTACKER PANEL</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&display=swap" rel="stylesheet">
<style>
  :root {
    --green:   #00ff41;
    --dkgreen: #00c030;
    --red:     #ff2020;
    --amber:   #ffb000;
    --blue:    #00cfff;
    --bg:      #000000;
    --panel:   #050f05;
    --border:  #003a10;
    --glow:    0 0 8px #00ff41, 0 0 20px #00ff4130;
    --glow-r:  0 0 8px #ff2020, 0 0 20px #ff202030;
    --glow-a:  0 0 8px #ffb000, 0 0 20px #ffb00030;
    --glow-b:  0 0 8px #00cfff, 0 0 20px #00cfff30;
    --mono: 'Share Tech Mono', monospace;
    --display: 'Orbitron', sans-serif;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }

  html, body {
    background: var(--bg);
    color: var(--green);
    font-family: var(--mono);
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* CRT scanline overlay */
  body::before {
    content: '';
    position: fixed; inset: 0; z-index: 9999;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0,0,0,0.08) 2px,
      rgba(0,0,0,0.08) 4px
    );
    pointer-events: none;
  }

  /* Flicker animation */
  @keyframes flicker {
    0%,19%,21%,23%,25%,54%,56%,100% { opacity: 1; }
    20%,22%,24%,55% { opacity: 0.85; }
  }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
  @keyframes pulse-green { 0%,100%{box-shadow:var(--glow)} 50%{box-shadow:0 0 4px #00ff41} }
  @keyframes pulse-red   { 0%,100%{box-shadow:var(--glow-r)} 50%{box-shadow:0 0 4px #ff2020} }
  @keyframes slide-in    { from{transform:translateX(-100%);opacity:0} to{transform:translateX(0);opacity:1} }
  @keyframes attack-flash {
    0%   { background: #ff2020; color: #000; box-shadow: 0 0 30px #ff2020; }
    50%  { background: #aa0000; color: #ff2020; }
    100% { background: var(--panel); color: var(--red); }
  }
  @keyframes ripple {
    0%   { transform: scale(1); opacity: 0.7; }
    100% { transform: scale(2.5); opacity: 0; }
  }
  @keyframes matrix-scroll {
    0% { transform: translateY(0); }
    100% { transform: translateY(-50%); }
  }

  /* HEADER */
  .header {
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    padding: 12px 16px 10px;
    position: sticky; top: 0; z-index: 100;
    animation: flicker 8s infinite;
  }
  .header-top {
    display: flex; align-items: center; justify-content: space-between;
  }
  .logo {
    font-family: var(--display);
    font-size: 14px;
    font-weight: 900;
    color: var(--red);
    text-shadow: var(--glow-r);
    letter-spacing: 2px;
  }
  .logo span { color: var(--green); text-shadow: var(--glow); }
  .status-pill {
    display: flex; align-items: center; gap: 6px;
    font-size: 10px; letter-spacing: 1px;
    padding: 4px 10px;
    border: 1px solid var(--border);
    border-radius: 2px;
  }
  .status-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--green);
    box-shadow: var(--glow);
    animation: blink 1.5s step-end infinite;
  }
  .status-dot.offline { background: var(--red); box-shadow: var(--glow-r); }

  /* TICKER */
  .ticker {
    margin-top: 8px;
    font-size: 10px;
    color: var(--dkgreen);
    letter-spacing: 1px;
    white-space: nowrap;
    overflow: hidden;
  }
  .ticker-inner {
    display: inline-block;
    animation: slide-in 0.5s ease;
  }

  /* STATS BAR */
  .stats-bar {
    display: grid; grid-template-columns: repeat(3,1fr);
    gap: 1px;
    background: var(--border);
    border-bottom: 1px solid var(--border);
  }
  .stat-cell {
    background: var(--panel);
    padding: 8px;
    text-align: center;
  }
  .stat-val {
    font-family: var(--display);
    font-size: 18px;
    font-weight: 700;
    color: var(--green);
    text-shadow: var(--glow);
    display: block;
  }
  .stat-val.danger { color: var(--red); text-shadow: var(--glow-r); }
  .stat-val.warn   { color: var(--amber); text-shadow: var(--glow-a); }
  .stat-label {
    font-size: 8px;
    color: #00602a;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-top: 2px;
    display: block;
  }

  /* SECTION */
  .section-title {
    font-family: var(--display);
    font-size: 9px;
    letter-spacing: 3px;
    color: #005a20;
    padding: 10px 16px 6px;
    border-bottom: 1px solid #001a08;
    text-transform: uppercase;
  }

  /* ATTACK GRID */
  .attack-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    padding: 12px 14px;
  }

  .atk-btn {
    position: relative;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 14px 10px 12px;
    cursor: pointer;
    transition: all 0.15s;
    overflow: hidden;
    text-align: left;
    -webkit-user-select: none; user-select: none;
    touch-action: manipulation;
  }
  .atk-btn:active { transform: scale(0.96); }

  .atk-btn::after {
    content: '';
    position: absolute;
    top: 50%; left: 50%;
    width: 10px; height: 10px;
    background: var(--red);
    border-radius: 50%;
    transform: translate(-50%,-50%) scale(0);
    opacity: 0;
  }
  .atk-btn.firing::after {
    animation: ripple 0.5s ease-out forwards;
  }

  .atk-btn.active-attack {
    border-color: var(--red);
    background: #1a0000;
    animation: pulse-red 1s infinite;
  }
  .atk-btn.active-attack .atk-icon { filter: drop-shadow(0 0 6px #ff2020); }

  .atk-icon {
    font-size: 24px;
    display: block;
    margin-bottom: 6px;
    line-height: 1;
  }
  .atk-name {
    font-family: var(--display);
    font-size: 10px;
    font-weight: 700;
    color: var(--green);
    letter-spacing: 1px;
    display: block;
  }
  .atk-sub {
    font-size: 8px;
    color: #005020;
    letter-spacing: 0.5px;
    margin-top: 3px;
    display: block;
  }
  .atk-layers {
    display: flex; gap: 3px; margin-top: 8px;
    flex-wrap: wrap;
  }
  .layer-tag {
    font-size: 7px;
    padding: 2px 5px;
    border-radius: 2px;
    letter-spacing: 0.5px;
    font-weight: bold;
  }
  .lt-pkt { background: #001e3c; color: var(--blue); border: 1px solid #003a6b; }
  .lt-flw { background: #1e1a00; color: var(--amber); border: 1px solid #4a3f00; }
  .lt-beh { background: #1a0000; color: var(--red); border: 1px solid #4a0000; }

  /* Special: insider is wide */
  .atk-btn.wide { grid-column: span 2; }

  /* CONTROL STRIP */
  .control-strip {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 10px;
    padding: 0 14px 12px;
  }
  .ctrl-btn {
    padding: 14px;
    border-radius: 3px;
    border: 1px solid;
    font-family: var(--display);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    cursor: pointer;
    touch-action: manipulation;
    transition: all 0.15s;
    text-align: center;
  }
  .ctrl-btn:active { transform: scale(0.96); opacity: 0.8; }
  .ctrl-normal {
    border-color: var(--green);
    color: var(--green);
    background: transparent;
    box-shadow: inset 0 0 20px #00ff4110;
  }
  .ctrl-stop {
    border-color: var(--amber);
    color: var(--amber);
    background: transparent;
    box-shadow: inset 0 0 20px #ffb00010;
  }

  /* AUTO DEMO */
  .auto-btn {
    margin: 0 14px 12px;
    display: block;
    width: calc(100% - 28px);
    padding: 16px;
    background: transparent;
    border: 1px solid var(--blue);
    border-radius: 3px;
    font-family: var(--display);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 3px;
    color: var(--blue);
    text-shadow: var(--glow-b);
    box-shadow: inset 0 0 30px #00cfff08, var(--glow-b);
    cursor: pointer;
    touch-action: manipulation;
    transition: all 0.2s;
  }
  .auto-btn:active { transform: scale(0.98); }

  /* LOG */
  .log-area {
    margin: 0 14px 20px;
    border: 1px solid var(--border);
    background: #020802;
    border-radius: 3px;
    height: 130px;
    overflow-y: auto;
    padding: 8px;
    font-size: 10px;
    color: #008030;
    line-height: 1.6;
  }
  .log-area::-webkit-scrollbar { width: 3px; }
  .log-area::-webkit-scrollbar-thumb { background: var(--border); }
  .log-entry { animation: slide-in 0.2s ease; }
  .log-entry.atk { color: var(--red); }
  .log-entry.ok  { color: var(--green); }
  .log-entry.warn{ color: var(--amber); }
  .log-entry.info{ color: var(--blue); }

  /* LAYER STATUS */
  .layer-status {
    display: grid; grid-template-columns: repeat(3,1fr);
    gap: 8px;
    padding: 10px 14px 14px;
  }
  .layer-card {
    border: 1px solid var(--border);
    background: var(--panel);
    border-radius: 3px;
    padding: 10px 8px;
    text-align: center;
  }
  .layer-name {
    font-family: var(--display);
    font-size: 8px;
    letter-spacing: 1px;
    color: #006030;
    display: block;
    margin-bottom: 6px;
  }
  .layer-state {
    font-family: var(--display);
    font-size: 11px;
    font-weight: 700;
    display: block;
  }
  .layer-state.normal { color: var(--green); text-shadow: var(--glow); }
  .layer-state.attack { color: var(--red); text-shadow: var(--glow-r); animation: blink 0.7s step-end infinite; }

  /* PROGRESS BAR */
  .risk-bar-wrap {
    margin: 0 14px 14px;
    border: 1px solid var(--border);
    background: #010a01;
    border-radius: 2px;
    height: 20px;
    position: relative;
    overflow: hidden;
  }
  .risk-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #00ff41, #ffb000, #ff2020);
    transition: width 0.8s ease;
    position: relative;
  }
  .risk-bar-fill::after {
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(90deg, transparent 70%, #ffffff20);
    animation: slide-in 1s infinite;
  }
  .risk-label {
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    display: flex; align-items: center; justify-content: center;
    font-family: var(--display);
    font-size: 9px;
    font-weight: 700;
    color: #000;
    letter-spacing: 2px;
    mix-blend-mode: difference;
    filter: invert(1);
  }

  /* FOOTER */
  .footer {
    text-align: center;
    padding: 12px;
    font-size: 9px;
    color: #003018;
    letter-spacing: 2px;
    border-top: 1px solid #001008;
  }

  /* ATTACK FLASH OVERLAY */
  .attack-overlay {
    position: fixed; inset: 0; z-index: 1000;
    pointer-events: none;
    border: 3px solid var(--red);
    opacity: 0;
    transition: opacity 0.1s;
    box-shadow: inset 0 0 80px #ff202030;
  }
  .attack-overlay.show { opacity: 1; }
</style>
</head>
<body>

<div class="attack-overlay" id="attackOverlay"></div>

<!-- HEADER -->
<div class="header">
  <div class="header-top">
    <div class="logo">⚠ <span>ATTACK</span>CTRL</div>
    <div class="status-pill">
      <div class="status-dot" id="statusDot"></div>
      <span id="statusText">CONNECTING</span>
    </div>
  </div>
  <div class="ticker" id="ticker">▶ INITIALIZING ATTACK PANEL... LOADING MODULES...</div>
</div>

<!-- STATS -->
<div class="stats-bar">
  <div class="stat-cell">
    <span class="stat-val" id="statEvents">—</span>
    <span class="stat-label">EVENTS</span>
  </div>
  <div class="stat-cell">
    <span class="stat-val danger" id="statAttacks">—</span>
    <span class="stat-label">ATTACKS</span>
  </div>
  <div class="stat-cell">
    <span class="stat-val warn" id="statRisk">—</span>
    <span class="stat-label">RISK %</span>
  </div>
</div>

<!-- RISK BAR -->
<div class="risk-bar-wrap">
  <div class="risk-bar-fill" id="riskBar" style="width:0%"></div>
  <div class="risk-label" id="riskLabel">RISK SCORE: 0%</div>
</div>

<!-- LAYER STATUS -->
<div class="section-title">▸ DETECTION LAYERS</div>
<div class="layer-status">
  <div class="layer-card">
    <span class="layer-name">PACKET</span>
    <span class="layer-state normal" id="layerPkt">NORMAL</span>
  </div>
  <div class="layer-card">
    <span class="layer-name">FLOW</span>
    <span class="layer-state normal" id="layerFlw">NORMAL</span>
  </div>
  <div class="layer-card">
    <span class="layer-name">BEHAVIOR</span>
    <span class="layer-state normal" id="layerBeh">NORMAL</span>
  </div>
</div>

<!-- ATTACKS -->
<div class="section-title">▸ ATTACK ARSENAL</div>
<div class="attack-grid">

  <button class="atk-btn" onclick="launchAttack('syn_flood', this)" id="btn-syn_flood">
    <span class="atk-icon">🌊</span>
    <span class="atk-name">SYN FLOOD</span>
    <span class="atk-sub">TCP volumetric</span>
    <div class="atk-layers">
      <span class="layer-tag lt-pkt">PKT</span>
      <span class="layer-tag lt-flw">FLOW</span>
    </div>
  </button>

  <button class="atk-btn" onclick="launchAttack('port_scan', this)" id="btn-port_scan">
    <span class="atk-icon">🔍</span>
    <span class="atk-name">PORT SCAN</span>
    <span class="atk-sub">Recon sweep</span>
    <div class="atk-layers">
      <span class="layer-tag lt-beh">BEHAV</span>
    </div>
  </button>

  <button class="atk-btn" onclick="launchAttack('brute_force', this)" id="btn-brute_force">
    <span class="atk-icon">🔓</span>
    <span class="atk-name">BRUTE FORCE</span>
    <span class="atk-sub">SSH credential</span>
    <div class="atk-layers">
      <span class="layer-tag lt-beh">BEHAV</span>
    </div>
  </button>

  <button class="atk-btn" onclick="launchAttack('data_exfil', this)" id="btn-data_exfil">
    <span class="atk-icon">📤</span>
    <span class="atk-name">DATA EXFIL</span>
    <span class="atk-sub">Theft exfiltration</span>
    <div class="atk-layers">
      <span class="layer-tag lt-flw">FLOW</span>
      <span class="layer-tag lt-beh">BEHAV</span>
    </div>
  </button>

  <button class="atk-btn" onclick="launchAttack('botnet', this)" id="btn-botnet">
    <span class="atk-icon">🤖</span>
    <span class="atk-name">BOTNET C2</span>
    <span class="atk-sub">Stealth beacon</span>
    <div class="atk-layers">
      <span class="layer-tag lt-beh">BEHAV</span>
    </div>
  </button>

  <button class="atk-btn" onclick="launchAttack('http_flood', this)" id="btn-http_flood">
    <span class="atk-icon">💥</span>
    <span class="atk-name">HTTP FLOOD</span>
    <span class="atk-sub">Layer 7 DDoS</span>
    <div class="atk-layers">
      <span class="layer-tag lt-pkt">PKT</span>
      <span class="layer-tag lt-flw">FLOW</span>
    </div>
  </button>

  <button class="atk-btn" onclick="launchAttack('icmp_flood', this)" id="btn-icmp_flood">
    <span class="atk-icon">📡</span>
    <span class="atk-name">ICMP FLOOD</span>
    <span class="atk-sub">Ping of death</span>
    <div class="atk-layers">
      <span class="layer-tag lt-pkt">PKT</span>
      <span class="layer-tag lt-flw">FLOW</span>
    </div>
  </button>

  <button class="atk-btn" onclick="launchAttack('insider_phase1', this)" id="btn-insider_phase1">
    <span class="atk-icon">🕵️</span>
    <span class="atk-name">INSIDER P1</span>
    <span class="atk-sub">Normal cover</span>
    <div class="atk-layers">
      <span class="layer-tag lt-beh">BEHAV</span>
    </div>
  </button>

  <button class="atk-btn wide" onclick="launchInsider(this)">
    <span class="atk-icon">👤➡️💀</span>
    <span class="atk-name">INSIDER THREAT — FULL 3-PHASE ESCALATION</span>
    <span class="atk-sub">Phase 1 → Recon → Exfiltration (auto-sequence, 8s each)</span>
    <div class="atk-layers">
      <span class="layer-tag lt-beh">BEHAV</span>
      <span class="layer-tag lt-flw">FLOW</span>
      <span class="layer-tag lt-pkt">PKT</span>
    </div>
  </button>

</div>

<!-- CONTROLS -->
<div class="control-strip">
  <button class="ctrl-btn ctrl-normal" onclick="setNormal()">◼ NORMAL</button>
  <button class="ctrl-btn ctrl-stop" onclick="stopDemo()">⊗ STOP DEMO</button>
</div>

<!-- AUTO DEMO -->
<button class="auto-btn" onclick="runFullDemo()">
  ▶▶ FULL JUDGE DEMO (AUTO)
</button>

<!-- LOG -->
<div class="section-title">▸ ATTACK LOG</div>
<div class="log-area" id="logArea">
  <div class="log-entry info">[ SYSTEM ] Panel initializing...</div>
</div>

<!-- FOOTER -->
<div class="footer">AI-SOC 3-LAYER DETECTION SYSTEM &nbsp;|&nbsp; DEMO MODE</div>

<script>
const BASE = '';
let currentAttack = null;
let autoRunning = false;

// ── LOGGING ─────────────────────────────────────────
function log(msg, type='ok') {
  const el = document.getElementById('logArea');
  const t = new Date().toLocaleTimeString('en',{hour12:false});
  const div = document.createElement('div');
  div.className = `log-entry ${type}`;
  div.textContent = `[${t}] ${msg}`;
  el.appendChild(div);
  el.scrollTop = el.scrollHeight;
  // keep last 60 lines
  while(el.children.length > 60) el.removeChild(el.firstChild);
}

function setTicker(msg) {
  const el = document.getElementById('ticker');
  el.textContent = '▶ ' + msg;
}

// ── FLASH ────────────────────────────────────────────
function flashOverlay(color='#ff2020') {
  const o = document.getElementById('attackOverlay');
  o.style.borderColor = color;
  o.style.boxShadow = `inset 0 0 80px ${color}30`;
  o.classList.add('show');
  setTimeout(() => o.classList.remove('show'), 400);
}

// ── CLEAR ACTIVE BUTTONS ─────────────────────────────
function clearActiveButtons() {
  document.querySelectorAll('.atk-btn.active-attack')
    .forEach(b => b.classList.remove('active-attack'));
}

// ── ATTACK ───────────────────────────────────────────
async function launchAttack(mode, btnEl) {
  if (autoRunning) return;
  clearActiveButtons();
  btnEl.classList.add('active-attack', 'firing');
  setTimeout(() => btnEl.classList.remove('firing'), 600);
  currentAttack = mode;

  flashOverlay();
  setTicker(`LAUNCHING ${mode.toUpperCase().replace('_',' ')} ATTACK...`);
  log(`Firing: ${mode.toUpperCase()}`, 'atk');

  try {
    const r = await fetch(`${BASE}/api/attack/${mode}`, {method:'POST'});
    const d = await r.json();
    if (d.success) {
      log(`Backend confirmed: ${mode} active`, 'ok');
      setTicker(`ATTACK ACTIVE: ${mode.toUpperCase().replace('_',' ')} — CHECK DASHBOARD`);
    } else {
      log(`ERROR: ${d.error}`, 'warn');
    }
  } catch(e) {
    log(`Network error: ${e.message}`, 'warn');
  }
  updateLayersForMode(mode);
}

// ── INSIDER 3-PHASE AUTO ─────────────────────────────
async function launchInsider(btnEl) {
  if (autoRunning) return;
  autoRunning = true;
  clearActiveButtons();
  btnEl.classList.add('active-attack');
  const phases = [
    {mode:'insider_phase1', label:'PHASE 1: EMPLOYEE COVER'},
    {mode:'insider_phase2', label:'PHASE 2: QUIET RECON'},
    {mode:'insider_phase3', label:'PHASE 3: EXFILTRATION'}
  ];
  for (const p of phases) {
    setTicker(`INSIDER → ${p.label}`);
    log(`INSIDER: ${p.label}`, 'atk');
    flashOverlay('#ffb000');
    await fetch(`${BASE}/api/attack/${p.mode}`, {method:'POST'});
    updateLayersForMode(p.mode);
    await sleep(8000);
  }
  btnEl.classList.remove('active-attack');
  autoRunning = false;
  setTicker('INSIDER THREAT SEQUENCE COMPLETE');
  log('Insider sequence finished', 'info');
}

// ── FULL AUTO DEMO ───────────────────────────────────
async function runFullDemo() {
  if (autoRunning) { log('Auto demo already running', 'warn'); return; }
  autoRunning = true;
  log('=== FULL JUDGE DEMO STARTED ===', 'info');

  const sequence = [
    {mode:'normal',      wait:4000, label:'BASELINE NORMAL TRAFFIC'},
    {mode:'syn_flood',   wait:6000, label:'SYN FLOOD ATTACK'},
    {mode:'normal',      wait:3000, label:'RECOVERY...'},
    {mode:'port_scan',   wait:6000, label:'PORT SCAN RECON'},
    {mode:'brute_force', wait:6000, label:'BRUTE FORCE SSH'},
    {mode:'botnet',      wait:8000, label:'BOTNET C2 BEACON'},
    {mode:'data_exfil',  wait:6000, label:'DATA EXFILTRATION'},
    {mode:'insider_phase1', wait:4000, label:'INSIDER P1'},
    {mode:'insider_phase2', wait:4000, label:'INSIDER P2: RECON'},
    {mode:'insider_phase3', wait:5000, label:'INSIDER P3: EXFIL'},
  ];

  for (const step of sequence) {
    clearActiveButtons();
    const btn = document.getElementById(`btn-${step.mode}`);
    if (btn) { btn.classList.add('active-attack'); }

    setTicker(`AUTO DEMO: ${step.label}`);
    log(`[ AUTO ] ${step.label}`, 'atk');
    if (step.mode !== 'normal') flashOverlay();
    await fetch(`${BASE}/api/attack/${step.mode}`, {method:'POST'}).catch(()=>{});
    updateLayersForMode(step.mode);
    await sleep(step.wait);
  }

  clearActiveButtons();
  await fetch(`${BASE}/api/stop`, {method:'POST'}).catch(()=>{});
  log('=== JUDGE DEMO COMPLETE ===', 'info');
  setTicker('FULL DEMO COMPLETE — SYSTEM BACK TO LIVE MODE');
  autoRunning = false;
  resetLayers();
}

// ── NORMAL / STOP ────────────────────────────────────
async function setNormal() {
  if (autoRunning) return;
  clearActiveButtons();
  currentAttack = null;
  await fetch(`${BASE}/api/normal`, {method:'POST'}).catch(()=>{});
  log('Set to NORMAL baseline traffic', 'ok');
  setTicker('MODE: NORMAL BASELINE TRAFFIC');
  resetLayers();
}

async function stopDemo() {
  if (autoRunning) return;
  clearActiveButtons();
  currentAttack = null;
  await fetch(`${BASE}/api/stop`, {method:'POST'}).catch(()=>{});
  log('Demo stopped — live ML inference restored', 'warn');
  setTicker('DEMO STOPPED — LIVE MODE ACTIVE');
  resetLayers();
}

// ── LAYER DISPLAY LOGIC ──────────────────────────────
const LAYER_MAP = {
  normal:         {pkt:'NORMAL', flw:'NORMAL', beh:'NORMAL'},
  idle:           {pkt:'NORMAL', flw:'NORMAL', beh:'NORMAL'},
  syn_flood:      {pkt:'ATTACK', flw:'ATTACK', beh:'NORMAL'},
  http_flood:     {pkt:'ATTACK', flw:'ATTACK', beh:'NORMAL'},
  icmp_flood:     {pkt:'ATTACK', flw:'ATTACK', beh:'NORMAL'},
  port_scan:      {pkt:'NORMAL', flw:'NORMAL', beh:'ATTACK'},
  brute_force:    {pkt:'NORMAL', flw:'NORMAL', beh:'ATTACK'},
  botnet:         {pkt:'NORMAL', flw:'NORMAL', beh:'ATTACK'},
  data_exfil:     {pkt:'NORMAL', flw:'ATTACK', beh:'ATTACK'},
  insider_phase1: {pkt:'NORMAL', flw:'NORMAL', beh:'NORMAL'},
  insider_phase2: {pkt:'NORMAL', flw:'NORMAL', beh:'ATTACK'},
  insider_phase3: {pkt:'NORMAL', flw:'ATTACK', beh:'ATTACK'},
};

function updateLayersForMode(mode) {
  const m = LAYER_MAP[mode] || {pkt:'NORMAL', flw:'NORMAL', beh:'NORMAL'};
  setLayer('layerPkt', m.pkt);
  setLayer('layerFlw', m.flw);
  setLayer('layerBeh', m.beh);
}

function setLayer(id, state) {
  const el = document.getElementById(id);
  el.textContent = state;
  el.className = 'layer-state ' + (state === 'ATTACK' ? 'attack' : 'normal');
}

function resetLayers() {
  ['layerPkt','layerFlw','layerBeh'].forEach(id => setLayer(id, 'NORMAL'));
}

// ── POLL BACKEND STATS ───────────────────────────────
async function pollStats() {
  try {
    const [hRes, sRes] = await Promise.all([
      fetch(`${BASE}/api/health`),
      fetch(`${BASE}/api/stats`)
    ]);
    const h = await hRes.json();
    const s = await sRes.json();

    const dot = document.getElementById('statusDot');
    const txt = document.getElementById('statusText');
    if (h.status && h.status !== 'offline') {
      dot.className = 'status-dot';
      txt.textContent = 'BACKEND LIVE';
    } else {
      dot.className = 'status-dot offline';
      txt.textContent = 'OFFLINE';
    }

    document.getElementById('statEvents').textContent  = s.total_events ?? '—';
    document.getElementById('statAttacks').textContent = s.total_attacks ?? '—';

    const risk = Math.round(s.risk_score ?? 0);
    document.getElementById('statRisk').textContent = risk + '%';
    document.getElementById('riskBar').style.width = risk + '%';
    document.getElementById('riskLabel').textContent = `RISK SCORE: ${risk}%`;

  } catch(e) {
    document.getElementById('statusDot').className = 'status-dot offline';
    document.getElementById('statusText').textContent = 'OFFLINE';
  }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── BOOT ─────────────────────────────────────────────
(async function boot() {
  await sleep(500);
  log('Attacker panel online', 'info');
  log('Backend polling started', 'info');
  setTicker('PANEL READY — SELECT AN ATTACK OR RUN FULL DEMO');
  pollStats();
  setInterval(pollStats, 3000);
})();
</script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def panel():
    return HTMLResponse(HTML)

# ── STARTUP ─────────────────────────────────────────────

if __name__ == "__main__":
    ip = get_local_ip()
    print("\n" + "═"*55)
    print("  AI-SOC ATTACKER CONTROL PANEL")
    print("═"*55)
    print(f"\n  ✅ Panel running at:")
    print(f"\n     💻 Laptop  →  http://localhost:{PANEL_PORT}")
    print(f"     📱 Phone   →  http://{ip}:{PANEL_PORT}")
    print(f"\n  ⚠️  Make sure phone & laptop are on SAME WiFi!")
    print(f"\n  📡 Backend expected at: {BACKEND_URL}")
    print("\n" + "═"*55 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",   # Listen on all interfaces so phone can connect
        port=PANEL_PORT,
        log_level="warning"
    )