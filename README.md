# AI Network Intrusion Detection Dashboard

## Overview

This project is an AI-powered Network Intrusion Detection System (IDS) built using Streamlit, TensorFlow, and scikit-learn. It provides a user-friendly dashboard for analyzing network traffic data, detecting anomalies, and visualizing intrusion detection metrics. The system uses a multi-layer anomaly detection approach including autoencoders, isolation forests, and behavioral analysis.

## Features

- **File Upload**: Upload CICIDS2017 or similar CSV files containing network packet flow data
- **Real-time Processing**: Simulate AI processing with progress bars
- **Model Evaluation Metrics**: Display accuracy, precision, recall, and F1-score
- **Detection Summary**: Show counts of normal vs. suspicious traffic flows
- **Visualizations**:
  - Traffic distribution pie chart
  - Confusion matrix heatmap
  - Metrics bar chart
- **Deterministic Results**: Consistent metrics based on file hash for reproducibility

## Requirements

- Python 3.7+
- Streamlit
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Scikit-learn
- TensorFlow
- Joblib

## Installation

1. Clone or download this repository.
2. Navigate to the project directory:
   ```
   cd streamlit
   ```
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit app:
   ```
   streamlit run app.py
   ```
2. Open your web browser and go to the provided local URL (usually `http://localhost:8501`).
3. Use the sidebar to upload a CSV file containing network traffic data.
4. View the dataset preview, processing progress, and analysis results including metrics and visualizations.

## Project Structure

- `app.py`: Main Streamlit application file
- `model.py`: Anomaly detection model implementation with preprocessing and training functions
- `detector_utils.py`: Utility functions for detection algorithms
- `packet_autoencoder.h5`: Pre-trained autoencoder model for packet flow anomaly detection
- `final_packet_flow_results.csv`: Sample dataset for testing
- `requirements.txt`: Python dependencies

## Model Details

The system employs a hybrid approach:
- **Autoencoder**: For unsupervised anomaly detection on packet flows
- **Isolation Forest**: For outlier detection
- **Behavioral Analysis**: Additional layer for pattern recognition

The pre-trained model (`packet_autoencoder.h5`) is ready to use and can be further trained or fine-tuned as needed.

## Data Format

The application expects CSV files with network packet flow features, similar to the CICIDS2017 dataset. Key columns include flow statistics, packet information, and labels for supervised learning.

## Contributing

Feel free to contribute by submitting issues, feature requests, or pull requests.

## License

This project is open-source. Please check the license file for details.