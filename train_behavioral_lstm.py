import pandas as pd
import tensorflow as tf

# 1) Import your existing code
#    CHANGE this import to the actual filename where these are defined.
#    For example, if your big script is saved as "multi_layer_train.py":
#    from multi_layer_train import preprocess_cicids2017_final, BehavioralDetector
from model import preprocess_cicids2017_final, BehavioralDetector

if __name__ == "__main__":
    print("=== Training behavioural LSTM only ===")

    # 2) Load the CICIDS2017 CSVs (same paths you used in Colab)
    files = [
        "Monday-WorkingHours.pcap_ISCX.csv",
        "Tuesday-WorkingHours.pcap_ISCX.csv",
        "Wednesday-workingHours.pcap_ISCX.csv",
        "Friday-WorkingHours-Morning.pcap_ISCX.csv",
    ]
    df_list = []
    for f in files:
        print("Loading:", f)
        df_list.append(pd.read_csv(f))

    df = pd.concat(df_list, ignore_index=True)
    print("Combined shape:", df.shape)

    # 3) Preprocess (your function)
    df = preprocess_cicids2017_final(df)

    # 4) Train behavioural detector (you can reduce epochs for speed)
    bh_detector = BehavioralDetector(
        time_window="1T",
        sequence_length=5,
        stride=2,
    )

    bh_detector.train(
        df,
        epochs=20,      # reduce from 50 if needed
        batch_size=32,
        visualize=True  # or False if you don't want plots
    )

    # 5) Save LSTM model and related artefacts
    import joblib

    print("Saving behavioural model files...")

    # LSTM model
    if bh_detector.lstm_model is not None:
        bh_detector.lstm_model.save("behavioral_lstm.h5")

    # Scaler, feature list, threshold
    joblib.dump(bh_detector.scaler, "behavior_scaler.pkl")
    joblib.dump(bh_detector.feature_columns, "behavior_features.pkl")
    joblib.dump(bh_detector.threshold, "behavior_threshold.pkl")

    print("Done. Files created: behavioral_lstm.h5, behavior_scaler.pkl, behavior_features.pkl, behavior_threshold.pkl")