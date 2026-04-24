import time
from datetime import datetime

import requests
import pandas as pd
import streamlit as st

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="3-Layer Network Anomaly Dashboard",
    layout="wide",
)

st.title("Realtime 3-Layer Network Anomaly Detection")

st.markdown(
    """
This dashboard shows **live packets** captured from your Wi‑Fi interface.
For each packet we run:
- **Packet Layer**: Autoencoder anomaly score.  
- **Flow Layer**: RandomForest classifier on flow features.  
- **Behaviour Layer**: GRU on a temporal sequence of behaviour vectors.  

The panels below update in real time and the table shows recent packets.
"""
)

top_placeholder = st.empty()
second_row_placeholder = st.empty()
table_placeholder = st.empty()

REFRESH_SECONDS = 1.0
MAX_ROWS = 150


def fetch_events():
    try:
        res = requests.get(f"{API_BASE}/events", timeout=1.0)
        if not res.ok:
            return []
        return res.json()
    except Exception as e:
        st.warning(f"Error calling /events: {e}")
        return []


while True:
    events = fetch_events()

    if events:
        latest = events[-1]
        ts = datetime.fromtimestamp(latest["timestamp"])
        final_label = latest["final_label"]

        final_color = "#ffcccc" if final_label == "attack" else "#e8f9e8"

        with top_placeholder.container():
            col_pkt, col_flow, col_beh = st.columns(3)

            # Packet layer card
            with col_pkt:
                color = "#ffcccc" if latest["packet_layer_label"] == "attack" else "#e8f9e8"
                st.markdown(
                    f"""
                    <div style="padding:10px;border-radius:8px;background:{color};">
                      <b>Packet Layer</b><br>
                      Label: <b>{latest["packet_layer_label"].upper()}</b><br>
                      Error: {latest["packet_layer_score"]:.4f}<br>
                      Threshold: {latest["packet_layer_threshold"] if latest["packet_layer_threshold"] is not None else "warming up"}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Flow layer card
            with col_flow:
                color = "#ffcccc" if latest["flow_layer_label"] == "attack" else "#e8f9e8"
                st.markdown(
                    f"""
                    <div style="padding:10px;border-radius:8px;background:{color};">
                      <b>Flow Layer</b><br>
                      Label: <b>{latest["flow_layer_label"].upper()}</b><br>
                      Attack probability: {latest["flow_layer_score"]:.3f}<br>
                      Threshold: {latest["flow_layer_threshold"] if latest["flow_layer_threshold"] is not None else "warming up"}<br>
                      Flow bytes/s: {latest["flow_bytes_s"]:.1f}<br>
                      Flow packets/s: {latest["flow_packets_s"]:.1f}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Behaviour layer card
            with col_beh:
                color = "#ffcccc" if latest["behavior_layer_label"] == "attack" else "#e8f9e8"
                st.markdown(
                    f"""
                    <div style="padding:10px;border-radius:8px;background:{color};">
                      <b>Behaviour Layer</b><br>
                      Label: <b>{latest["behavior_layer_label"].upper()}</b><br>
                      Attack probability: {latest["behavior_layer_prob"]:.3f}<br>
                      (Based on last {10} behaviour vectors for this IP)
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with second_row_placeholder.container():
            st.markdown(
                f"""
                <div style="padding:10px;border-radius:8px;background:{final_color};">
                  <b>Latest Packet</b><br>
                  Time: {ts.strftime("%H:%M:%S")}<br>
                  Source IP: {latest["src_ip"]}<br>
                  Packet size: {latest["packet_size"]} bytes<br>
                  <b>Final fused decision:</b> {final_label.upper()}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # recent packets table
        df = pd.DataFrame(events[-MAX_ROWS:])
        df["time"] = df["timestamp"].apply(
            lambda t: datetime.fromtimestamp(t).strftime("%H:%M:%S")
        )
        df = df[
            [
                "time",
                "src_ip",
                "packet_size",
                "flow_bytes_s",
                "flow_packets_s",
                "packet_layer_label",
                "flow_layer_label",
                "behavior_layer_label",
                "final_label",
                "packet_layer_score",
                "flow_layer_score",
                "behavior_layer_prob",
            ]
        ]

        with table_placeholder.container():
            st.subheader("Recent Packets")
            st.dataframe(df, use_container_width=True)

    else:
        with top_placeholder.container():
            st.info("No events yet. Make sure `realtime_backend.py` is running and capturing.")

        with second_row_placeholder.container():
            st.empty()

        with table_placeholder.container():
            st.empty()

    time.sleep(REFRESH_SECONDS)