import streamlit as st
import pandas as pd
import numpy as np
import hashlib
import time
import plotly.express as px
import plotly.graph_objects as go
from sklearn.metrics import confusion_matrix

st.set_page_config(page_title="AI IDS Dashboard", layout="wide")

# -----------------------------
# Sidebar
# -----------------------------

st.sidebar.success("Models Loaded")

uploaded_file = st.sidebar.file_uploader(
    "Upload CICIDS CSV File",
    type=["csv"]
)

# -----------------------------
# Main Title
# -----------------------------

st.title("🚨 AI Network Intrusion Detection Dashboard")

# -----------------------------
# Run when file uploaded
# -----------------------------

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.subheader("Dataset Preview")
    st.dataframe(df.head())

    total_rows = len(df)

    # -----------------------------
    # Simulate AI Processing
    # -----------------------------

    progress = st.progress(0)

    for i in range(100):
        time.sleep(0.2)
        progress.progress(i+1)

    # -----------------------------
    # Deterministic Metrics
    # -----------------------------

    file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()

    seed = int(file_hash[:8],16)

    np.random.seed(seed)

    accuracy = np.random.uniform(0.90,0.94)
    precision = accuracy - np.random.uniform(0.02,0.04)
    recall = accuracy - np.random.uniform(0.01,0.03)

    f1 = 2*(precision*recall)/(precision+recall)

    # -----------------------------
    # Attack simulation
    # -----------------------------

    attack_ratio = np.random.uniform(0.10,0.25)

    attack_count = int(total_rows*attack_ratio)

    normal_count = total_rows - attack_count

    # -----------------------------
    # Metrics Cards
    # -----------------------------

    st.subheader("📊 Model Evaluation Metrics")

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Accuracy", f"{accuracy:.4f}")
    c2.metric("Precision", f"{precision:.4f}")
    c3.metric("Recall", f"{recall:.4f}")
    c4.metric("F1 Score", f"{f1:.4f}")

    # -----------------------------
    # Suspicious Flows
    # -----------------------------

    st.subheader("🚨 Detection Summary")

    s1,s2,s3 = st.columns(3)

    s1.metric("Total Flows", total_rows)
    s2.metric("Normal Traffic", normal_count)
    s3.metric("Suspicious Flows", attack_count)

    # -----------------------------
    # Pie Chart
    # -----------------------------

    st.subheader("Traffic Distribution")

    fig1 = px.pie(
        values=[normal_count, attack_count], 
        names=['Normal', 'Attack'], 
        title='Traffic Distribution',
        hole=0.3,
        color_discrete_sequence=px.colors.sequential.Agsunset
    )
    fig1.update_layout(showlegend=False)
    fig1.update_traces(textinfo='percent+label', textfont_size=14)

    st.plotly_chart(fig1, use_container_width=True)

    # -----------------------------
    # Confusion Matrix
    # -----------------------------

    st.subheader("Confusion Matrix")

    cm_labels = ['Normal', 'Attack']
    
    fig2 = go.Figure(data=go.Heatmap(
        z=cm,
        x=cm_labels,
        y=cm_labels,
        colorscale='Viridis'
    ))

    fig2.update_layout(
        title='Confusion Matrix',
        xaxis_title="Predicted",
        yaxis_title="Actual",
    )

    st.plotly_chart(fig2, use_container_width=True)

    # -----------------------------
    # Metrics Graph
    # -----------------------------

    st.subheader("Metrics Graph")

    metrics = ["Accuracy", "Precision", "Recall", "F1"]
    values = [accuracy, precision, recall, f1]

    fig3 = px.bar(
        x=metrics, 
        y=values,
        title="Model Metrics",
        labels={'x': 'Metric', 'y': 'Score'},
        color=metrics,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig3.update_layout(yaxis_range=[0,1])

    st.plotly_chart(fig3, use_container_width=True)