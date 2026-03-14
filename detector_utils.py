import pandas as pd
import numpy as np

def preprocess_data(df):

    df.columns = df.columns.str.strip()

    numeric_columns = df.select_dtypes(include=[np.number]).columns

    for col in numeric_columns:
        df[col] = df[col].replace([np.inf, -np.inf], np.nan)
        df[col] = df[col].fillna(df[col].median())

    df = df.drop_duplicates()

    return df


def extract_features(df):

    features = [
        'Flow Duration',
        'Total Fwd Packets',
        'Total Backward Packets',
        'Total Length of Fwd Packets',
        'Total Length of Bwd Packets',
        'Flow Bytes/s',
        'Flow Packets/s',
        'Flow IAT Mean',
        'Flow IAT Std',
        'SYN Flag Count',
        'RST Flag Count',
        'ACK Flag Count'
    ]

    available = [f for f in features if f in df.columns]

    X = df[available].copy()

    X = X.replace([np.inf, -np.inf], 0).fillna(0)

    return X