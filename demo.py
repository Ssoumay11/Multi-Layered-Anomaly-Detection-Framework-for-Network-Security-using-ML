# """
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║   ATTACK DEMO SIMULATOR  —  For Judge Demonstration                        ║
# ║   Generates 5 attack types vs normal traffic to show detection difference  ║
# ║                                                                              ║
# ║   ⚠  FOR LOCAL TESTING ONLY — only targets 127.0.0.1 / localhost           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# INSTALL:  pip install scapy requests colorama
# RUN:      python attack_demo.py

# The script gives a MENU — pick which attack to demo for the judges.
# """

# import time, sys, random, socket, threading, struct, os
# import requests
# from colorama import Fore, Style, init
# init(autoreset=True)

# TARGET = "127.0.0.1"   # ALWAYS localhost — never attack real hosts
# API    = "http://127.0.0.1:8000"

# try:
#     from scapy.all import (IP, TCP, UDP, ICMP, send, sendp, Ether,
#                             RandShort, RandIP, conf)
#     conf.verb = 0   # suppress scapy output
#     SCAPY_OK = True
# except ImportError:
#     SCAPY_OK = False

# # ─── helpers ──────────────────────────────────────────────────────────────────
# def banner(title: str, color=Fore.CYAN):
#     print(f"\n{color}{'═'*60}")
#     print(f"  {title}")
#     print(f"{'═'*60}{Style.RESET_ALL}\n")

# def info(msg):  print(f"{Fore.CYAN}  ℹ  {msg}{Style.RESET_ALL}")
# def ok(msg):    print(f"{Fore.GREEN}  ✅ {msg}{Style.RESET_ALL}")
# def warn(msg):  print(f"{Fore.YELLOW}  ⚠  {msg}{Style.RESET_ALL}")
# def err(msg):   print(f"{Fore.RED}  ❌ {msg}{Style.RESET_ALL}")

# def print_stats():
#     """Fetch and print current detection stats from backend."""
#     try:
#         r = requests.get(f"{API}/stats", timeout=2)
#         s = r.json()
#         print(f"\n{Fore.MAGENTA}  📊 Detection Stats:")
#         print(f"     Total Events  : {s.get('total',0)}")
#         print(f"     Attacks Found : {Fore.RED}{s.get('attacks',0)}{Fore.MAGENTA}")
#         print(f"     Normal Traffic: {Fore.GREEN}{s.get('normal',0)}{Fore.MAGENTA}")
#         print(f"     Avg Threat    : {s.get('avg_threat_score',0):.3f}")
#         types = s.get('attack_types', {})
#         if types:
#             print(f"     Attack Types  : {dict(list(types.items())[:5])}")
#         print(Style.RESET_ALL)
#     except Exception as e:
#         warn(f"Backend not reachable: {e}")


# # ══════════════════════════════════════════════════════════════════════════════
# #  ATTACK 1:  SYN FLOOD  (DDoS simulation)
# #  — Sends hundreds of TCP SYN packets with random source IPs
# #  — High syn_cnt in flow → triggers Packet + Flow layers
# # ══════════════════════════════════════════════════════════════════════════════
# def attack_syn_flood(count=500, delay=0.002):
#     banner("ATTACK 1: SYN FLOOD (DDoS Simulation)", Fore.RED)
#     if not SCAPY_OK:
#         _fallback_tcp_flood(count)
#         return
#     info(f"Sending {count} SYN packets to {TARGET}:80 from random source IPs…")
#     info("This simulates a volumetric DDoS — expect HIGH red alerts in dashboard.")

#     sent = 0
#     for i in range(count):
#         src = f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
#         pkt = IP(src=src, dst=TARGET) / TCP(
#             sport=RandShort(), dport=80,
#             flags="S",           # SYN only
#             seq=random.randint(0, 2**32)
#         )
#         send(pkt, verbose=False)
#         sent += 1
#         if sent % 50 == 0:
#             print(f"  → Sent {sent}/{count} SYN packets", end="\r")
#         time.sleep(delay)

#     ok(f"SYN Flood complete. Sent {sent} packets.")
#     print_stats()

# def _fallback_tcp_flood(count=500):
#     """Pure Python TCP fallback (without scapy raw sockets)."""
#     info("Using Python socket fallback for TCP flood…")
#     sent = 0
#     for _ in range(count):
#         try:
#             s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             s.settimeout(0.05)
#             s.connect_ex((TARGET, 80))
#             s.close()
#             sent += 1
#         except: pass
#         time.sleep(0.002)
#     ok(f"TCP flood complete ({sent} connections attempted)")


# # ══════════════════════════════════════════════════════════════════════════════
# #  ATTACK 2:  PORT SCAN  (Reconnaissance)
# #  — Rapid SYN to many ports → high rst_cnt, many unique dports
# #  — Triggers Packet + Behavioural layers
# # ══════════════════════════════════════════════════════════════════════════════
# def attack_port_scan(ports=None):
#     banner("ATTACK 2: PORT SCAN (Reconnaissance)", Fore.YELLOW)
#     ports = ports or list(range(1, 1025))  # scan first 1024 ports
#     info(f"Scanning {len(ports)} ports on {TARGET}…")
#     info("This simulates nmap -sS — expect MEDIUM/HIGH alerts for Packet + Behaviour layers.")

#     open_ports = []
#     scanned = 0
#     for port in ports:
#         if SCAPY_OK:
#             pkt = IP(dst=TARGET) / TCP(sport=RandShort(), dport=port, flags="S")
#             resp = send(pkt, verbose=False)
#         else:
#             s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             s.settimeout(0.02)
#             res = s.connect_ex((TARGET, port))
#             if res == 0: open_ports.append(port)
#             s.close()
#         scanned += 1
#         if scanned % 100 == 0:
#             print(f"  → Scanned {scanned}/{len(ports)} ports", end="\r")
#         time.sleep(0.003)

#     ok(f"Port scan complete. Scanned {scanned} ports.")
#     if open_ports: info(f"Open ports found: {open_ports[:10]}")
#     print_stats()


# # ══════════════════════════════════════════════════════════════════════════════
# #  ATTACK 3:  BRUTE FORCE  (Authentication attack simulation)
# #  — Many small connections to port 22/3389 with data payloads
# #  — High connection frequency, moderate bytes → Behavioural layer fires
# # ══════════════════════════════════════════════════════════════════════════════
# def attack_brute_force(count=200, target_port=22):
#     banner("ATTACK 3: BRUTE FORCE (SSH/RDP Simulation)", Fore.MAGENTA)
#     info(f"Sending {count} credential-stuffing connections to {TARGET}:{target_port}…")
#     info("High connection frequency → Behavioural LSTM fires HIGH alert.")

#     payloads = [
#         b"SSH-2.0-OpenSSH_8.4\r\n",
#         b"USER admin\r\nPASS 123456\r\n",
#         b"USER root\r\nPASS password\r\n",
#         b"USER administrator\r\nPASS admin123\r\n",
#     ]

#     sent = 0
#     for i in range(count):
#         if SCAPY_OK:
#             payload = random.choice(payloads)
#             pkt = IP(dst=TARGET) / TCP(
#                 sport=RandShort(), dport=target_port,
#                 flags="PA",   # PSH+ACK = data push
#                 seq=random.randint(0, 2**32)
#             ) / payload
#             send(pkt, verbose=False)
#         else:
#             try:
#                 s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#                 s.settimeout(0.1)
#                 s.connect_ex((TARGET, target_port))
#                 s.send(random.choice(payloads))
#                 s.close()
#             except: pass
#         sent += 1
#         if sent % 40 == 0:
#             print(f"  → Sent {sent}/{count} brute-force attempts", end="\r")
#         time.sleep(0.05)

#     ok(f"Brute force simulation complete. {sent} attempts sent.")
#     print_stats()


# # ══════════════════════════════════════════════════════════════════════════════
# #  ATTACK 4:  DATA EXFILTRATION  (Large burst transfers)
# #  — Large UDP packets at high rate → Flow bytes/s very high
# #  — Triggers Flow layer autoencoder
# # ══════════════════════════════════════════════════════════════════════════════
# def attack_data_exfil(mb=5):
#     banner("ATTACK 4: DATA EXFILTRATION (Large Burst)", Fore.YELLOW)
#     info(f"Simulating {mb}MB data exfiltration burst over UDP…")
#     info("Very high bytes/s → Flow Autoencoder reconstruction error spikes.")

#     chunk = b"X" * 1400        # MTU-sized chunks
#     total_bytes = mb * 1024 * 1024
#     sent_bytes  = 0

#     if SCAPY_OK:
#         dst_port = random.randint(10000, 65000)
#         while sent_bytes < total_bytes:
#             pkt = IP(dst=TARGET) / UDP(sport=RandShort(), dport=dst_port) / chunk
#             send(pkt, verbose=False)
#             sent_bytes += len(chunk)
#             if sent_bytes % (100 * 1400) == 0:
#                 print(f"  → Exfiltrated {sent_bytes//1024}KB / {mb*1024}KB", end="\r")
#     else:
#         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         while sent_bytes < total_bytes:
#             try:
#                 s.sendto(chunk, (TARGET, random.randint(10000, 65000)))
#                 sent_bytes += len(chunk)
#             except: pass
#         s.close()

#     ok(f"Exfiltration complete. Sent {sent_bytes // 1024} KB.")
#     print_stats()


# # ══════════════════════════════════════════════════════════════════════════════
# #  ATTACK 5:  MIXED SLOW ATTACK  (Low-and-slow / Botnet)
# #  — Slow, periodic connections to many IPs simulating botnet C&C
# #  — Low individual packet rate but persistent → Behavioural layer detects
# # ══════════════════════════════════════════════════════════════════════════════
# def attack_botnet(duration=30):
#     banner("ATTACK 5: BOTNET / LOW-AND-SLOW", Fore.CYAN)
#     info(f"Running slow botnet pattern for {duration}s…")
#     info("Low & slow — only Behavioural LSTM will detect this (Packet/Flow layers miss it).")
#     info("This demonstrates WHY we need 3 layers!")

#     end_time = time.time() + duration
#     sent = 0

#     while time.time() < end_time:
#         # Slow heartbeat to multiple destinations
#         dsts = [f"192.168.1.{random.randint(1,254)}" for _ in range(3)]
#         for dst in dsts:
#             if SCAPY_OK:
#                 pkt = IP(dst=TARGET) / TCP(
#                     sport=RandShort(), dport=random.choice([80,443,53,8080]),
#                     flags="PA", seq=random.randint(0, 2**32)
#                 ) / b"GET /beacon HTTP/1.1\r\nHost: c2server\r\n\r\n"
#                 send(pkt, verbose=False)
#             else:
#                 try:
#                     s = socket.socket()
#                     s.settimeout(0.1)
#                     s.connect_ex((TARGET, 80))
#                     s.close()
#                 except: pass
#             sent += 1
#         remaining = int(end_time - time.time())
#         print(f"  → Botnet beacons: {sent} | Time left: {remaining}s   ", end="\r")
#         time.sleep(random.uniform(0.5, 2.0))   # slow, irregular

#     ok(f"\nBotnet simulation complete. {sent} beacons sent.")
#     print_stats()


# # ══════════════════════════════════════════════════════════════════════════════
# #  NORMAL TRAFFIC GENERATOR  — baseline comparison
# # ══════════════════════════════════════════════════════════════════════════════
# def generate_normal_traffic(count=100):
#     banner("NORMAL TRAFFIC GENERATOR", Fore.GREEN)
#     info(f"Generating {count} normal HTTP-like requests…")
#     info("Should show GREEN / LOW scores in dashboard.")

#     sent = 0
#     for i in range(count):
#         try:
#             port = random.choice([80, 443, 8080, 53])
#             if SCAPY_OK:
#                 # Normal 3-way handshake pattern
#                 pkt = IP(dst=TARGET) / TCP(
#                     sport=RandShort(), dport=port, flags="S"
#                 )
#                 send(pkt, verbose=False)
#                 time.sleep(0.01)
#                 pkt = IP(dst=TARGET) / TCP(
#                     sport=pkt[TCP].sport, dport=port, flags="A"
#                 ) / b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
#                 send(pkt, verbose=False)
#                 time.sleep(0.01)
#                 pkt = IP(dst=TARGET) / TCP(
#                     sport=pkt[TCP].sport, dport=port, flags="FA"
#                 )
#                 send(pkt, verbose=False)
#             else:
#                 import urllib.request
#                 urllib.request.urlopen(
#                     f"http://{TARGET}:{port}/", timeout=0.5
#                 )
#         except: pass
#         sent += 1
#         if sent % 20 == 0:
#             print(f"  → Sent {sent}/{count} normal requests", end="\r")
#         time.sleep(random.uniform(0.05, 0.15))

#     ok(f"\nNormal traffic generation complete. {sent} requests sent.")
#     print_stats()


# # ══════════════════════════════════════════════════════════════════════════════
# #  FULL DEMO SEQUENCE  — for judges (automated)
# # ══════════════════════════════════════════════════════════════════════════════
# def full_judge_demo():
#     banner("FULL JUDGE DEMONSTRATION SEQUENCE", Fore.CYAN)
#     print(f"""{Fore.YELLOW}
#   This will run the following sequence:
#   1. [30s] Normal traffic (baseline — should show GREEN)
#   2. [20s] SYN Flood DDoS  (should spike RED immediately)
#   3. [20s] Back to Normal  (scores should drop)
#   4. [30s] Port Scan        (MEDIUM alerts — Packet layer)
#   5. [30s] Brute Force      (HIGH alerts — Behavioural layer)
#   6. [40s] Botnet (slow)    (MEDIUM — only Behavioural catches this)
#   7. [15s] Data Exfiltration (CRITICAL — Flow layer)

#   Dashboard at: http://localhost:5173  or  http://localhost:3000
# {Style.RESET_ALL}""")
#     input("  Press ENTER to start demo…")

#     steps = [
#         ("Normal Traffic (baseline)",   lambda: generate_normal_traffic(60),  0),
#         ("SYN Flood DDoS",              lambda: attack_syn_flood(300),         2),
#         ("Normal Recovery",             lambda: generate_normal_traffic(40),   2),
#         ("Port Scan",                   lambda: attack_port_scan(list(range(1,512))), 2),
#         ("Brute Force (SSH)",           lambda: attack_brute_force(150),       2),
#         ("Botnet / Low-and-Slow",       lambda: attack_botnet(30),             2),
#         ("Data Exfiltration",           lambda: attack_data_exfil(2),          2),
#     ]

#     for i, (name, fn, pause) in enumerate(steps, 1):
#         print(f"\n{Fore.CYAN}[{i}/{len(steps)}] {name}{Style.RESET_ALL}")
#         fn()
#         if pause:
#             info(f"Pausing {pause}s before next attack…")
#             time.sleep(pause)

#     banner("DEMO COMPLETE — Review the Dashboard!", Fore.GREEN)
#     print_stats()


# # ══════════════════════════════════════════════════════════════════════════════
# #  MENU
# # ══════════════════════════════════════════════════════════════════════════════
# MENU = [
#     ("Normal Traffic (baseline — shows GREEN scores)",       generate_normal_traffic),
#     ("SYN Flood DDoS (HIGH-CRITICAL — Packet + Flow)",       attack_syn_flood),
#     ("Port Scan (MEDIUM — Packet Layer)",                    attack_port_scan),
#     ("Brute Force / SSH (HIGH — Behavioural Layer)",         attack_brute_force),
#     ("Data Exfiltration (CRITICAL — Flow Autoencoder)",      attack_data_exfil),
#     ("Botnet / Low-and-Slow (MEDIUM — only Behaviour sees)", attack_botnet),
#     ("🎬 FULL JUDGE DEMO (automated sequence)",              full_judge_demo),
# ]

# def main():
#     print(f"""
# {Fore.CYAN}╔══════════════════════════════════════════════════════════╗
# ║   AI-SOC ATTACK DEMO — For Research Presentation        ║
# ║   Paper: Multi-Layered Anomaly Detection Framework      ║
# ╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
# {Fore.YELLOW}  ⚠  All attacks target 127.0.0.1 (localhost) only
#   ⚠  Run live_capture_backend.py first
#   ⚠  Open the dashboard at http://localhost:5173
# {Style.RESET_ALL}""")

#     # Check backend
#     try:
#         r = requests.get(f"{API}/health", timeout=2)
#         ok(f"Backend online — {r.json().get('packets_seen',0)} packets captured")
#     except:
#         err(f"Backend not reachable at {API}")
#         err("Start it first: sudo python live_capture_backend.py")
#         sys.exit(1)

#     if not SCAPY_OK:
#         warn("Scapy not installed. Using Python socket fallback (less realistic).")
#         warn("For best results: pip install scapy")

#     while True:
#         print(f"\n{Fore.CYAN}  ┌─ SELECT DEMO ───────────────────────────────────────")
#         for i, (label, _) in enumerate(MENU, 1):
#             print(f"  │  {Fore.WHITE}[{i}]{Style.RESET_ALL} {label}")
#         print(f"  │  {Fore.WHITE}[0]{Style.RESET_ALL} Exit")
#         print(f"  └──────────────────────────────────────────────────────{Style.RESET_ALL}")

#         choice = input(f"\n  {Fore.GREEN}Select option: {Style.RESET_ALL}").strip()
#         if choice == "0":
#             print(f"{Fore.GREEN}\n  Goodbye!\n{Style.RESET_ALL}")
#             break
#         try:
#             idx = int(choice) - 1
#             if 0 <= idx < len(MENU):
#                 _, fn = MENU[idx]
#                 fn()
#             else:
#                 warn("Invalid choice.")
#         except (ValueError, KeyboardInterrupt):
#             warn("Use Ctrl+C to cancel a running demo. Enter a number to select.")


# if __name__ == "__main__":
#     try:
#         main()
#     except KeyboardInterrupt:
#         print(f"\n{Fore.YELLOW}  Interrupted.{Style.RESET_ALL}")



"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          AI-SOC ATTACK DEMO  —  Judge Demonstration Script                 ║
║     Paper: Multi-Layered Anomaly Detection Framework for Network Security  ║
║                                                                              ║
║  This script simulates 8 attack types on localhost so the detection         ║
║  system can catch them in real-time on the dashboard.                        ║
║                                                                              ║
║  ⚠  All attacks target 127.0.0.1 (your own machine) ONLY.                  ║
║  ⚠  Run your backend (realtime_backend.py) BEFORE this script.              ║
╚══════════════════════════════════════════════════════════════════════════════╝

INSTALL:
    pip install colorama requests scapy

RUN:
    python demo.py
"""

import os, sys, time, socket, random, threading, struct
import requests
from colorama import Fore, Back, Style, init
init(autoreset=True)

# ─── Try Scapy (optional — better attack simulation) ──────────────────────────
try:
    from scapy.all import (
        IP, TCP, UDP, ICMP, send, conf,
        RandShort, Ether, sendp, get_if_list
    )
    conf.verb = 0
    SCAPY = True
except Exception:
    SCAPY = False

# ─── Config ────────────────────────────────────────────────────────────────────
TARGET  = "127.0.0.1"
API     = "http://127.0.0.1:8000"
PORTS   = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445,
           3306, 3389, 5900, 8080, 8443, 27017]

# ─── ANSI helpers ──────────────────────────────────────────────────────────────
def clr():          os.system("cls" if os.name == "nt" else "clear")
def cyan(s):        return f"{Fore.CYAN}{s}{Style.RESET_ALL}"
def green(s):       return f"{Fore.GREEN}{s}{Style.RESET_ALL}"
def red(s):         return f"{Fore.RED}{s}{Style.RESET_ALL}"
def yellow(s):      return f"{Fore.YELLOW}{s}{Style.RESET_ALL}"
def magenta(s):     return f"{Fore.MAGENTA}{s}{Style.RESET_ALL}"
def white(s):       return f"{Fore.WHITE}{Style.BRIGHT}{s}{Style.RESET_ALL}"
def dim(s):         return f"{Style.DIM}{s}{Style.RESET_ALL}"

def banner(title, color=Fore.CYAN, width=64):
    bar = "═" * width
    print(f"\n{color}{bar}")
    pad = (width - len(title) - 2) // 2
    print(f"  {' ' * pad}{title}")
    print(f"{bar}{Style.RESET_ALL}\n")

def step(msg):
    print(f"  {cyan('▶')} {msg}")

def ok(msg):
    print(f"  {green('✔')} {msg}")

def warn(msg):
    print(f"  {yellow('⚠')} {msg}")

def info(msg):
    print(f"  {dim('ℹ')} {msg}")

def pkt_sent(n, total):
    bar_len = 30
    filled  = int(bar_len * n / max(total, 1))
    bar     = cyan("█" * filled) + dim("░" * (bar_len - filled))
    pct     = int(100 * n / max(total, 1))
    print(f"\r  {bar} {white(str(pct).rjust(3)+'%')}  {cyan(str(n))}/{dim(str(total))} pkts", end="", flush=True)

def section(title, icon="◈"):
    print(f"\n  {cyan(icon)} {white(title)}")
    print(f"  {'─'*55}")

# ══════════════════════════════════════════════════════════════════════════════
#  API HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def check_backend():
    try:
        r = requests.get(f"{API}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False

def get_stats():
    try:
        r = requests.get(f"{API}/stats", timeout=2)
        return r.json() if r.ok else {}
    except Exception:
        return {}

def get_latest_events(n=5):
    try:
        r = requests.get(f"{API}/events", timeout=2)
        events = r.json() if r.ok else []
        return events[-n:]
    except Exception:
        return []

def print_stats():
    """Pull and pretty-print detection stats from the backend."""
    s = get_stats()
    if not s:
        warn("Backend not responding.")
        return

    total   = s.get("total", 0)
    attacks = s.get("attacks", 0)
    normal  = s.get("normal", 0)
    rate    = s.get("attack_rate_pct", 0)
    avg     = s.get("avg_threat_score", 0)

    section("Detection Results", "📊")
    print(f"    Total Events   : {white(str(total))}")
    print(f"    Attacks Found  : {red(str(attacks))}")
    print(f"    Normal Traffic : {green(str(normal))}")
    print(f"    Attack Rate    : {(red if rate > 50 else yellow)(f'{rate}%')}")
    print(f"    Avg Threat Score: {white(f'{avg:.3f}')}")

    # Show latest 3 events
    evts = get_latest_events(3)
    if evts:
        section("Latest Detections", "🔍")
        for e in reversed(evts):
            label = e.get("final_label", "?")
            ip    = e.get("src_ip", "?")
            pkt   = e.get("packet_layer_label", "?")
            flw   = e.get("flow_layer_label",   "?")
            beh   = e.get("behavior_layer_label","?")
            ps    = e.get("packet_layer_score",  0) or 0
            fs    = e.get("flow_layer_score",    0) or 0
            bs    = e.get("behavior_layer_prob", 0) or 0

            verdict_str = red("ATTACK ⚠") if label == "attack" else green("NORMAL ✓")
            print(f"    {dim('►')} {white(ip):20s}  {verdict_str}")
            print(f"        PKT={cyan(f'{ps:.3f}')}  FLW={magenta(f'{fs:.3f}')}  BEH={yellow(f'{bs:.3f}')}")
            print(f"        Layers: PKT→{_lbl(pkt)}  FLW→{_lbl(flw)}  BEH→{_lbl(beh)}")
    print()

def _lbl(l):
    return red("ATTACK") if l == "attack" else green("NORMAL")

def wait_for_detection(seconds=4, msg="Waiting for detection pipeline…"):
    """Show a countdown while the backend processes."""
    for i in range(seconds, 0, -1):
        print(f"\r  {cyan('⏱')} {msg} {white(str(i)+'s')} ", end="", flush=True)
        time.sleep(1)
    print()

# ══════════════════════════════════════════════════════════════════════════════
#  ATTACK 1 — SYN FLOOD  (DDoS Layer 1 + 2 trigger)
# ══════════════════════════════════════════════════════════════════════════════
def attack_syn_flood(count=400, delay=0.003):
    banner("ATTACK 1 — SYN FLOOD  (Volumetric DDoS)", Fore.RED)

    print(f"""  {yellow('What it is:')} Sends hundreds of TCP SYN packets with random source IPs.
  {yellow('What triggers:')} High syn_cnt in flow → Packet Layer AE error spikes.
  {yellow('Expected:')} CRITICAL alerts · packet_layer = ATTACK · flow_layer = ATTACK
  {yellow('Real world:')} Mirai botnet, Memcached reflection attacks.
    """)

    input(f"  {cyan('Press ENTER to launch…')}")
    step(f"Sending {count} SYN packets to {TARGET}:80 …")

    sent = 0
    if SCAPY:
        for i in range(count):
            src = f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
            pkt = IP(src=src, dst=TARGET) / TCP(sport=RandShort(), dport=80, flags="S")
            send(pkt, verbose=False)
            sent += 1
            if sent % 10 == 0: pkt_sent(sent, count)
            time.sleep(delay)
    else:
        # Socket fallback
        for i in range(count):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.05)
                s.connect_ex((TARGET, 80))
                s.close()
            except Exception: pass
            sent += 1
            if sent % 10 == 0: pkt_sent(sent, count)
            time.sleep(delay)

    print()
    ok(f"SYN Flood complete — {sent} packets sent.")
    wait_for_detection(4)
    print_stats()

# ══════════════════════════════════════════════════════════════════════════════
#  ATTACK 2 — PORT SCAN  (Reconnaissance trigger)
# ══════════════════════════════════════════════════════════════════════════════
def attack_port_scan(n_ports=512):
    banner("ATTACK 2 — PORT SCAN  (Reconnaissance)", Fore.YELLOW)

    print(f"""  {yellow('What it is:')} Rapid SYN to many ports — classic nmap -sS behaviour.
  {yellow('What triggers:')} High rst_cnt + many unique dst ports → Packet Layer.
  {yellow('Expected:')} HIGH alerts · packet_layer = ATTACK · behavior = ATTACK
  {yellow('Real world:')} First step of any targeted intrusion.
    """)

    input(f"  {cyan('Press ENTER to launch…')}")
    step(f"Scanning {n_ports} ports on {TARGET} …")

    ports = list(range(1, n_ports + 1))
    random.shuffle(ports)
    scanned = 0

    for port in ports:
        if SCAPY:
            pkt = IP(dst=TARGET) / TCP(sport=RandShort(), dport=port, flags="S")
            send(pkt, verbose=False)
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.015)
            s.connect_ex((TARGET, port))
            s.close()
        scanned += 1
        if scanned % 20 == 0: pkt_sent(scanned, n_ports)
        time.sleep(0.004)

    print()
    ok(f"Port scan complete — {scanned} ports probed.")
    wait_for_detection(4)
    print_stats()

# ══════════════════════════════════════════════════════════════════════════════
#  ATTACK 3 — BRUTE FORCE  (Behaviour Layer trigger)
# ══════════════════════════════════════════════════════════════════════════════
def attack_brute_force(count=200):
    banner("ATTACK 3 — BRUTE FORCE  (SSH / Login)", Fore.MAGENTA)

    print(f"""  {yellow('What it is:')} Rapid repeated connection attempts to SSH port 22.
  {yellow('What triggers:')} High connection frequency per IP → Behaviour Layer GRU fires.
  {yellow('Expected:')} Behaviour = ATTACK  (Packet may stay LOW — shows WHY 3 layers matter!)
  {yellow('Real world:')} Credential stuffing, Hydra, Medusa tools.
    """)

    input(f"  {cyan('Press ENTER to launch…')}")
    step(f"Sending {count} brute-force attempts to {TARGET}:22 …")

    payloads = [
        b"SSH-2.0-OpenSSH_8.4\r\n",
        b"USER admin\r\nPASS 123456\r\n",
        b"USER root\r\nPASS password\r\n",
        b"USER administrator\r\nPASS admin@123\r\n",
        b"USER pi\r\nPASS raspberry\r\n",
    ]

    sent = 0
    for i in range(count):
        if SCAPY:
            pkt = IP(dst=TARGET) / TCP(
                sport=RandShort(), dport=22, flags="PA",
                seq=random.randint(0, 2**32)
            ) / random.choice(payloads)
            send(pkt, verbose=False)
        else:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.1)
                s.connect_ex((TARGET, 22))
                s.send(random.choice(payloads))
                s.close()
            except Exception: pass
        sent += 1
        if sent % 20 == 0: pkt_sent(sent, count)
        time.sleep(0.04)

    print()
    ok(f"Brute force complete — {sent} attempts.")
    wait_for_detection(4)
    print_stats()

# ══════════════════════════════════════════════════════════════════════════════
#  ATTACK 4 — DATA EXFILTRATION  (Flow Layer trigger)
# ══════════════════════════════════════════════════════════════════════════════
def attack_data_exfil(mb=3):
    banner("ATTACK 4 — DATA EXFILTRATION  (Large Burst)", Fore.YELLOW)

    print(f"""  {yellow('What it is:')} Sends a large UDP burst — simulates data being stolen.
  {yellow('What triggers:')} Very high bytes/s → Flow Layer Autoencoder reconstruction error spikes.
  {yellow('Expected:')} CRITICAL · flow_layer = ATTACK · flow_bytes_s spikes in chart.
  {yellow('Real world:')} DNS tunnelling, HTTPS exfil, cloud upload abuse.
    """)

    input(f"  {cyan('Press ENTER to launch…')}")
    step(f"Exfiltrating {mb}MB burst over UDP …")

    chunk      = b"EXFIL:" + b"X" * 1394   # ~1400B chunks near MTU
    total_b    = mb * 1024 * 1024
    sent_bytes = 0
    dst_port   = random.randint(10000, 60000)

    if SCAPY:
        while sent_bytes < total_b:
            pkt = IP(dst=TARGET) / UDP(sport=RandShort(), dport=dst_port) / chunk
            send(pkt, verbose=False)
            sent_bytes += len(chunk)
            pkt_sent(sent_bytes, total_b)
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while sent_bytes < total_b:
            try:
                s.sendto(chunk, (TARGET, dst_port))
                sent_bytes += len(chunk)
                pkt_sent(sent_bytes, total_b)
            except Exception:
                time.sleep(0.01)
        s.close()

    print()
    ok(f"Exfiltration complete — {sent_bytes // 1024} KB sent.")
    wait_for_detection(4)
    print_stats()

# ══════════════════════════════════════════════════════════════════════════════
#  ATTACK 5 — BOTNET / LOW-AND-SLOW  (Behaviour-only trigger)
# ══════════════════════════════════════════════════════════════════════════════
def attack_botnet(duration=25):
    banner("ATTACK 5 — BOTNET / LOW-AND-SLOW  (C2 Heartbeat)", Fore.CYAN)

    print(f"""  {yellow('What it is:')} Slow, irregular beacons to many IPs — classic C2 heartbeat.
  {yellow('What triggers:')} Persistent low-rate to many unique destinations → Behaviour GRU.
  {yellow('KEY POINT for judges:')} Packet Layer = LOW  ·  Flow Layer = LOW
                        BUT  Behaviour Layer = ATTACK
  {yellow('This proves WHY a 3-layer system beats single-layer IDS!')}
  {yellow('Real world:')} Emotet, TrickBot, Cobalt Strike beacons.
    """)

    input(f"  {cyan('Press ENTER to launch…')}")
    step(f"Running slow botnet C2 heartbeat for {duration}s …")

    end_time = time.time() + duration
    sent = 0

    while time.time() < end_time:
        dst_port = random.choice([80, 443, 53, 8080, 4444, 6667])
        if SCAPY:
            payload = b"GET /beacon?id=" + str(random.randint(1000, 9999)).encode() + b" HTTP/1.1\r\n"
            pkt     = IP(dst=TARGET) / TCP(
                sport=RandShort(), dport=dst_port, flags="PA",
                seq=random.randint(0, 2**32)
            ) / payload
            send(pkt, verbose=False)
        else:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.08)
                s.connect_ex((TARGET, dst_port))
                s.close()
            except Exception: pass
        sent += 1
        remaining = max(0, int(end_time - time.time()))
        print(f"\r  {cyan('⏱')} Beacons sent: {white(str(sent))}  |  Time left: {yellow(str(remaining)+'s')}  ", end="", flush=True)
        time.sleep(random.uniform(0.4, 1.8))   # slow + irregular

    print()
    ok(f"Botnet simulation complete — {sent} beacons.")
    wait_for_detection(5)
    print_stats()

# ══════════════════════════════════════════════════════════════════════════════
#  ATTACK 6 — HTTP FLOOD  (Application Layer DDoS)
# ══════════════════════════════════════════════════════════════════════════════
def attack_http_flood(count=300):
    banner("ATTACK 6 — HTTP FLOOD  (App-Layer DDoS)", Fore.RED)

    print(f"""  {yellow('What it is:')} Floods HTTP GET requests to port 80 — Layer 7 DDoS.
  {yellow('What triggers:')} High pkt_count + high flow_packets_s → Flow + Packet layers.
  {yellow('Expected:')} flow_packets_s spikes · ATTACK verdict across all layers.
  {yellow('Real world:')} LOIC, Slowloris, HTTP/2 Rapid Reset (CVE-2023-44487).
    """)

    input(f"  {cyan('Press ENTER to launch…')}")
    step(f"Flooding {TARGET}:80 with {count} HTTP requests …")

    http_req = (
        b"GET /index.html?r=" + str(random.randint(0, 99999)).encode() +
        b" HTTP/1.1\r\nHost: localhost\r\n"
        b"User-Agent: Mozilla/5.0\r\nConnection: keep-alive\r\n\r\n"
    )

    sent = 0
    threads = []

    def flood_worker(n):
        nonlocal sent
        for _ in range(n):
            if SCAPY:
                pkt = IP(dst=TARGET) / TCP(
                    sport=RandShort(), dport=80, flags="PA"
                ) / http_req
                send(pkt, verbose=False)
            else:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.1)
                    s.connect_ex((TARGET, 80))
                    s.send(http_req)
                    s.close()
                except Exception: pass
            sent += 1
            time.sleep(0.01)

    for _ in range(4):  # 4 threads
        t = threading.Thread(target=flood_worker, args=(count // 4,), daemon=True)
        threads.append(t)
        t.start()

    while any(t.is_alive() for t in threads):
        pkt_sent(sent, count)
        time.sleep(0.1)
    for t in threads:
        t.join()

    print()
    ok(f"HTTP flood complete — {sent} requests sent.")
    wait_for_detection(4)
    print_stats()

# ══════════════════════════════════════════════════════════════════════════════
#  ATTACK 7 — ICMP FLOOD  (Ping Flood / Smurf)
# ══════════════════════════════════════════════════════════════════════════════
def attack_icmp_flood(count=300):
    banner("ATTACK 7 — ICMP FLOOD  (Ping Flood)", Fore.YELLOW)

    print(f"""  {yellow('What it is:')} Rapid large ICMP echo requests — old-school ping flood.
  {yellow('What triggers:')} Unusual protocol + high pkt rate → Packet Layer anomaly.
  {yellow('Expected:')} packet_layer_score spikes · ATTACK verdict.
  {yellow('Real world:')} Smurf attack, ping of death variants.
    """)

    input(f"  {cyan('Press ENTER to launch…')}")
    step(f"Sending {count} ICMP flood packets to {TARGET} …")

    sent = 0
    if SCAPY:
        payload = b"AAAA" * 250    # oversized ping payload
        for i in range(count):
            pkt = IP(dst=TARGET) / ICMP() / payload
            send(pkt, verbose=False)
            sent += 1
            if sent % 10 == 0: pkt_sent(sent, count)
            time.sleep(0.005)
    else:
        # OS ping flood fallback
        flag = "-n" if os.name == "nt" else "-c"
        for i in range(count):
            os.system(f"ping {flag} 1 -l 1000 {TARGET} > nul 2>&1" if os.name == "nt"
                      else f"ping -c 1 -s 1000 {TARGET} > /dev/null 2>&1")
            sent += 1
            if sent % 10 == 0: pkt_sent(sent, count)

    print()
    ok(f"ICMP flood complete — {sent} packets.")
    wait_for_detection(4)
    print_stats()

# ══════════════════════════════════════════════════════════════════════════════
#  ATTACK 8 — MIXED INSIDER THREAT  (all 3 layers in sequence)
# ══════════════════════════════════════════════════════════════════════════════
def attack_insider_threat():
    banner("ATTACK 8 — INSIDER THREAT SIMULATION  (Full 3-Layer)", Fore.MAGENTA)

    print(f"""  {yellow('What it is:')} Mimics an insider — starts normal, then reconnaissance,
                  then slow data exfil. All 3 layers activate at different times.
  {yellow('What triggers:')} ALL THREE LAYERS fire at different moments.
  {yellow('Key demo value:')} Shows temporal detection — Behaviour layer catches
                  the pattern even when individual packets look benign.
  {yellow('Real world:')} Edward Snowden scenario, supply-chain compromise.
    """)

    input(f"  {cyan('Press ENTER to start 3-phase insider simulation…')}")

    # Phase 1: Normal browsing
    section("Phase 1 / 3 — Normal Browsing (30s)", "✓")
    step("Generating normal HTTP traffic (GREEN expected)…")
    for i in range(60):
        try:
            if SCAPY:
                pkt = IP(dst=TARGET) / TCP(sport=RandShort(), dport=80, flags="S")
                send(pkt, verbose=False)
            else:
                s = socket.socket()
                s.settimeout(0.05)
                s.connect_ex((TARGET, 80))
                s.close()
        except Exception: pass
        pkt_sent(i + 1, 60)
        time.sleep(0.4)
    print()
    ok("Phase 1 complete — dashboard should show GREEN / NORMAL")
    time.sleep(2)

    # Phase 2: Quiet reconnaissance
    section("Phase 2 / 3 — Quiet Reconnaissance (Behaviour layer fires)", "👁")
    step("Starting slow port scan on sensitive ports…")
    sensitive = [22, 23, 3306, 3389, 5432, 5900, 6379, 27017, 9200, 8080]
    for port in sensitive * 3:     # repeat 3 times = suspicious persistence
        if SCAPY:
            pkt = IP(dst=TARGET) / TCP(sport=RandShort(), dport=port, flags="S")
            send(pkt, verbose=False)
        else:
            s = socket.socket()
            s.settimeout(0.03)
            s.connect_ex((TARGET, port))
            s.close()
        time.sleep(random.uniform(1.0, 2.5))   # slow — evades packet-only IDS
        print(f"\r  {cyan('→')} Probing port {yellow(str(port)):8s}  (slow & quiet…)", end="", flush=True)
    print()
    ok("Phase 2 done — Behaviour GRU should start FIRING even though packets look normal")
    time.sleep(2)

    # Phase 3: Silent exfiltration
    section("Phase 3 / 3 — Silent Data Exfiltration (Flow layer fires)", "📤")
    step("Exfiltrating data in small encrypted-looking chunks…")
    chunk  = b"ENC:" + bytes([random.randint(0, 255) for _ in range(800)])
    target_port = 443   # disguised as HTTPS
    total  = 800
    sent   = 0
    if SCAPY:
        for _ in range(total):
            pkt = IP(dst=TARGET) / UDP(sport=RandShort(), dport=target_port) / chunk
            send(pkt, verbose=False)
            sent += 1
            pkt_sent(sent, total)
            time.sleep(0.02)
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for _ in range(total):
            try:
                s.sendto(chunk, (TARGET, target_port))
                sent += 1
                pkt_sent(sent, total)
            except Exception: pass
            time.sleep(0.02)
        s.close()

    print()
    ok("Phase 3 done — all 3 layers should now show ATTACK")
    wait_for_detection(5)
    print_stats()

# ══════════════════════════════════════════════════════════════════════════════
#  NORMAL TRAFFIC  — baseline for comparison
# ══════════════════════════════════════════════════════════════════════════════
def generate_normal(count=80):
    banner("BASELINE — Normal Web Traffic  (Should show GREEN)", Fore.GREEN)

    print(f"""  {yellow('What it is:')} Simulates regular HTTP browsing — GET requests with
                  proper handshake + FIN teardown.
  {yellow('Expected:')} ALL LAYERS = NORMAL · Dashboard stays GREEN.
  {yellow('Use this:')} Before any attack to show the baseline contrast.
    """)

    input(f"  {cyan('Press ENTER to generate normal traffic…')}")
    step(f"Sending {count} normal HTTP requests …")

    sent = 0
    for i in range(count):
        port = random.choice([80, 443, 8080])
        if SCAPY:
            # SYN → ACK+DATA → FIN (normal 3-way)
            sport = random.randint(1024, 65535)
            send(IP(dst=TARGET) / TCP(sport=sport, dport=port, flags="S"),  verbose=False)
            time.sleep(0.01)
            send(IP(dst=TARGET) / TCP(sport=sport, dport=port, flags="PA") /
                 b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n", verbose=False)
            time.sleep(0.01)
            send(IP(dst=TARGET) / TCP(sport=sport, dport=port, flags="FA"), verbose=False)
        else:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.2)
                s.connect_ex((TARGET, port))
                s.send(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
                s.close()
            except Exception: pass
        sent += 1
        pkt_sent(sent, count)
        time.sleep(random.uniform(0.06, 0.15))   # normal human-speed pacing

    print()
    ok(f"Normal traffic done — {sent} requests.")
    wait_for_detection(3)
    print_stats()

# ══════════════════════════════════════════════════════════════════════════════
#  FULL JUDGE DEMO  — automated sequence for live presentation
# ══════════════════════════════════════════════════════════════════════════════
def full_judge_demo():
    banner("FULL AUTOMATED JUDGE DEMO SEQUENCE", Fore.CYAN)

    print(f"""
  {white('SEQUENCE PLAN:')}

  {green('[Step 1]')}  {white('Normal traffic')}   →  Dashboard stays GREEN   (30s)
  {red('[Step 2]')}  {white('SYN Flood')}        →  CRITICAL RED spike      (15s)
  {yellow('[Step 3]')}  {white('Back to normal')}   →  Scores drop back down  (20s)
  {magenta('[Step 4]')}  {white('Port Scan')}        →  MEDIUM-HIGH alerts     (15s)
  {magenta('[Step 5]')}  {white('Brute Force')}      →  Behaviour layer fires  (20s)
  {cyan('[Step 6]')}  {white('Botnet heartbeat')} →  Only Behaviour fires   (25s)
  {red('[Step 7]')}  {white('Data Exfil')}       →  Flow layer spikes      (10s)

  {yellow('KEY TALKING POINT → Step 6:')}
  The botnet attack has LOW packet score and LOW flow score
  but HIGH behaviour score. Without the 3rd layer, this attack
  would be {red('COMPLETELY MISSED')} by a traditional IDS!

  {dim('Dashboard:')} http://localhost:5173  (or wherever you opened the JSX)
  {dim('API:')}       http://localhost:8000/events
    """)

    input(f"  {cyan('Press ENTER to start the full demo…')}")

    steps = [
        ("Generating normal baseline traffic…",  lambda: _auto_normal(50),   0),
        ("Launching SYN Flood DDoS…",            lambda: _auto_syn(250),      3),
        ("Returning to normal (recovery)…",      lambda: _auto_normal(40),   2),
        ("Launching Port Scan…",                 lambda: _auto_portscan(300), 3),
        ("Launching Brute Force…",               lambda: _auto_brute(120),    3),
        ("Launching Botnet (low-and-slow)…",     lambda: _auto_botnet(20),    4),
        ("Launching Data Exfiltration burst…",   lambda: _auto_exfil(1),      3),
    ]

    for i, (msg, fn, pause) in enumerate(steps, 1):
        print(f"\n  {cyan(f'[{i}/{len(steps)}]')} {white(msg)}")
        fn()
        if pause:
            wait_for_detection(pause, "Letting detection pipeline process…")
        print_stats()
        time.sleep(1)

    banner("DEMO COMPLETE!", Fore.GREEN)
    print(f"  {green('✔')} Open the dashboard to show the full timeline to judges.")
    print(f"  {cyan('📊')} Go to '≡ PACKET TABLE' tab to show all individual events.\n")

# ─── Quiet versions for automated demo ────────────────────────────────────────
def _auto_normal(n):
    for _ in range(n):
        try:
            if SCAPY:
                send(IP(dst=TARGET)/TCP(sport=RandShort(),dport=80,flags="S"), verbose=False)
            else:
                s=socket.socket(); s.settimeout(0.05); s.connect_ex((TARGET,80)); s.close()
        except Exception: pass
        time.sleep(0.12)

def _auto_syn(n):
    for _ in range(n):
        if SCAPY:
            src=f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
            send(IP(src=src,dst=TARGET)/TCP(sport=RandShort(),dport=80,flags="S"), verbose=False)
        else:
            s=socket.socket(); s.settimeout(0.02); s.connect_ex((TARGET,80)); s.close()
        time.sleep(0.003)

def _auto_portscan(n):
    for port in random.sample(range(1,1025),min(n,1024)):
        if SCAPY:
            send(IP(dst=TARGET)/TCP(sport=RandShort(),dport=port,flags="S"), verbose=False)
        else:
            s=socket.socket(); s.settimeout(0.01); s.connect_ex((TARGET,port)); s.close()
        time.sleep(0.004)

def _auto_brute(n):
    for _ in range(n):
        if SCAPY:
            send(IP(dst=TARGET)/TCP(sport=RandShort(),dport=22,flags="PA")/b"USER root\r\n", verbose=False)
        else:
            s=socket.socket(); s.settimeout(0.05); s.connect_ex((TARGET,22)); s.close()
        time.sleep(0.05)

def _auto_botnet(n):
    for _ in range(n):
        port=random.choice([80,443,53])
        if SCAPY:
            send(IP(dst=TARGET)/TCP(sport=RandShort(),dport=port,flags="PA")/b"GET /beacon\r\n", verbose=False)
        else:
            s=socket.socket(); s.settimeout(0.05); s.connect_ex((TARGET,port)); s.close()
        time.sleep(random.uniform(0.8, 2.0))

def _auto_exfil(mb):
    chunk=b"X"*1400; total=mb*1024*1024; sent=0
    if SCAPY:
        while sent<total:
            send(IP(dst=TARGET)/UDP(sport=RandShort(),dport=9999)/chunk, verbose=False); sent+=len(chunk)
    else:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        while sent<total:
            s.sendto(chunk,(TARGET,9999)); sent+=len(chunk)
        s.close()

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN MENU
# ══════════════════════════════════════════════════════════════════════════════
MENU_ITEMS = [
    ("🟢  Normal Baseline Traffic",                       generate_normal),
    ("🔴  Attack 1 — SYN Flood          (DDoS / CRITICAL)",      attack_syn_flood),
    ("🟡  Attack 2 — Port Scan          (Recon / HIGH)",          attack_port_scan),
    ("🟣  Attack 3 — Brute Force        (SSH / HIGH)",            attack_brute_force),
    ("🟡  Attack 4 — Data Exfiltration  (Flow / CRITICAL)",       attack_data_exfil),
    ("🔵  Attack 5 — Botnet Heartbeat   (Behaviour-only / MED)",  attack_botnet),
    ("🔴  Attack 6 — HTTP Flood         (App-Layer DDoS)",        attack_http_flood),
    ("🟡  Attack 7 — ICMP Flood         (Ping Flood)",            attack_icmp_flood),
    ("🟣  Attack 8 — Insider Threat     (All 3 Layers / FULL)",   attack_insider_threat),
    ("🎬  FULL JUDGE DEMO               (Automated sequence)",    full_judge_demo),
]

def draw_menu(backend_ok):
    clr()
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║   AI-SOC ATTACK DEMO  ·  Judge Presentation Tool            ║
║   Paper: Multi-Layered Anomaly Detection Framework          ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

  {dim('Dashboard')} → {cyan('http://localhost:5173')}   {dim('(or wherever you opened JSX)')}
  {dim('Backend API')} → {cyan('http://localhost:8000')}
  {dim('Scapy')} → {green('AVAILABLE') if SCAPY else yellow('NOT INSTALLED — using socket fallback')}
  {dim('Backend')} → {green('ONLINE ✔') if backend_ok else red('OFFLINE ✘  (start realtime_backend.py first)')}

{Fore.CYAN}  ┌────────────────────────────────────────────────────────────┐{Style.RESET_ALL}""")

    for i, (label, _) in enumerate(MENU_ITEMS, 1):
        num = white(f"[{i:2d}]")
        print(f"{Fore.CYAN}  │{Style.RESET_ALL}  {num}  {label}")

    print(f"""{Fore.CYAN}  │{Style.RESET_ALL}  {white('[ 0]')}  🚪 Exit
{Fore.CYAN}  └────────────────────────────────────────────────────────────┘{Style.RESET_ALL}

  {dim('TIP: Run option 1 (Normal) FIRST, then any attack to show contrast.')}
  {dim('The FULL JUDGE DEMO (option 10) runs everything automatically.')}
""")

def main():
    backend_ok = check_backend()

    if not backend_ok:
        warn(f"Backend not reachable at {API}")
        warn("Start your backend first:  python realtime_backend.py")
        warn("Then rerun this demo script.")
        print()
        cont = input(f"  Continue anyway (for dry-run)? {cyan('[y/N]')} ").strip().lower()
        if cont != "y":
            sys.exit(0)

    while True:
        draw_menu(backend_ok)

        try:
            choice = input(f"  {cyan('Select [0-{len(MENU_ITEMS)}]:')} ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n  {yellow('Interrupted. Goodbye!')}\n")
            break

        if choice == "0":
            print(f"\n  {green('Goodbye!')}\n")
            break

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(MENU_ITEMS):
                _, fn = MENU_ITEMS[idx]
                try:
                    fn()
                except KeyboardInterrupt:
                    print(f"\n\n  {yellow('Attack interrupted (Ctrl+C). Returning to menu…')}\n")
                    time.sleep(1)
                # Refresh backend status
                backend_ok = check_backend()
            else:
                warn("Invalid choice — enter a number from the menu.")
                time.sleep(1)
        except ValueError:
            warn("Enter a number.")
            time.sleep(1)


if __name__ == "__main__":
    main()