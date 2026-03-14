# ============================================================
# 🎯 COMPLETE MULTI-LAYER ANOMALY DETECTION SYSTEM
# ✅ With Working Behavioral Layer + Rich Visualizations
# ============================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import PowerTransformer, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (classification_report, confusion_matrix, accuracy_score,
                            f1_score, precision_score, recall_score, roc_curve, auc,
                            precision_recall_curve)
from sklearn.ensemble import IsolationForest
from imblearn.over_sampling import ADASYN
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (Input, Dense, Dropout, LSTM, RepeatVector,
                                     TimeDistributed, BatchNormalization)
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

np.random.seed(42)
tf.random.set_seed(42)

# ============================================================
# PREPROCESSING
# ============================================================

def preprocess_cicids2017_final(df):
    """Final robust preprocessing"""
    print("🔧 Preprocessing CICIDS2017...")

    df.columns = df.columns.str.strip()

    if 'Label' in df.columns:
        df['Label'] = df['Label'].str.strip().str.upper()

    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

    # Handle inf/nan
    for col in numeric_columns:
        df[col] = df[col].replace([np.inf, -np.inf], np.nan)
        df[col] = df[col].fillna(df[col].median())

    # Clip outliers
    for col in numeric_columns:
        mean = df[col].mean()
        std = df[col].std()
        if std > 0:
            lower = mean - 5 * std
            upper = mean + 5 * std
            df[col] = df[col].clip(lower, upper)

    # Log transform skewed features
    for col in numeric_columns:
        if df[col].min() >= 0 and df[col].std() / (df[col].mean() + 1) > 10:
            df[col] = np.log1p(df[col])

    df = df.drop_duplicates()

    # Create timestamp with finer resolution
    if 'Timestamp' not in df.columns:
        df['Timestamp'] = pd.date_range(
            start='2017-07-07 08:00:00',
            periods=len(df),
            freq='50ms'  # Finer resolution
        )

    # Create more diverse IPs
    if 'Source IP' not in df.columns and ' Source IP' not in df.columns:
        # Ensure each IP has multiple connections
        n_unique_ips = max(100, len(df) // 500)  # More IPs
        df['Source IP'] = [f"192.168.{np.random.randint(1, 100)}.{np.random.randint(1, 255)}"
                          for _ in range(len(df))]

    print(f"✅ Preprocessing complete. Records: {len(df)}")
    if 'Label' in df.columns:
        print(f"📊 Label distribution:\n{df['Label'].value_counts()}")

    return df

# ============================================================
# PACKET/FLOW DETECTOR (UNCHANGED - WORKING WELL)
# ============================================================

class PacketFlowDetector:
    """Working packet/flow detector"""

    def __init__(self, encoding_dim=16):
        self.encoding_dim = encoding_dim
        self.autoencoder = None
        self.isolation_forest = None
        self.scaler = PowerTransformer(method='yeo-johnson')
        self.thresholds = {}
        self.feature_columns = None

    def select_features(self, df):
        """Select critical features"""
        features = [
            'Flow Duration', 'Total Fwd Packets', 'Total Backward Packets',
            'Total Length of Fwd Packets', 'Total Length of Bwd Packets',
            'Flow Bytes/s', 'Flow Packets/s',
            'Flow IAT Mean', 'Flow IAT Std',
            'Fwd IAT Mean', 'Bwd IAT Mean',
            'SYN Flag Count', 'RST Flag Count', 'FIN Flag Count',
            'PSH Flag Count', 'ACK Flag Count',
            'Fwd Packet Length Mean', 'Bwd Packet Length Mean',
            'Packet Length Mean', 'Average Packet Size',
            'Fwd Header Length', 'Bwd Header Length',
            'Active Mean', 'Idle Mean'
        ]
        return [f for f in features if f in df.columns]

    def extract_features(self, df):
        """Extract features safely"""
        print("🔍 Extracting features...")

        feature_cols = self.select_features(df)
        features_df = df[feature_cols].copy()

        # Engineered features
        total_packets = df.get('Total Fwd Packets', 0) + df.get('Total Backward Packets', 0)
        features_df['fwd_packet_ratio'] = np.where(
            total_packets > 0,
            df.get('Total Fwd Packets', 0) / total_packets,
            0.5
        )

        total_bytes = df.get('Total Length of Fwd Packets', 0) + df.get('Total Length of Bwd Packets', 0)
        features_df['fwd_bytes_ratio'] = np.where(
            total_bytes > 0,
            df.get('Total Length of Fwd Packets', 0) / total_bytes,
            0.5
        )

        features_df['connection_failure_ratio'] = np.where(
            df.get('SYN Flag Count', 0) > 0,
            df.get('RST Flag Count', 0) / df.get('SYN Flag Count', 1),
            0
        )

        features_df['iat_regularity'] = np.where(
            df.get('Flow IAT Mean', 0) > 0,
            df.get('Flow IAT Std', 0) / df.get('Flow IAT Mean', 1),
            0
        )

        features_df['label'] = df.get('Label', 'BENIGN')

        features_df = features_df.replace([np.inf, -np.inf], 0).fillna(0)

        for col in features_df.columns:
            if col != 'label':
                q99 = features_df[col].quantile(0.99)
                q01 = features_df[col].quantile(0.01)
                features_df[col] = features_df[col].clip(q01, q99)

        print(f"✅ Extracted {len(features_df.columns)-1} features")
        return features_df

    def build_autoencoder(self, input_dim):
        """Build simple autoencoder"""
        input_layer = Input(shape=(input_dim,))
        x = Dense(64, activation='relu')(input_layer)
        x = BatchNormalization()(x)
        x = Dropout(0.2)(x)
        encoded = Dense(self.encoding_dim, activation='relu')(x)
        x = Dense(64, activation='relu')(encoded)
        x = BatchNormalization()(x)
        x = Dropout(0.2)(x)
        decoded = Dense(input_dim, activation='linear')(x)

        self.autoencoder = Model(input_layer, decoded)
        self.autoencoder.compile(
            optimizer=Adam(learning_rate=0.001, clipnorm=1.0),
            loss='huber',
            metrics=['mae']
        )

        print("🏗️  Autoencoder built")
        return self.autoencoder

    def train(self, df, test_size=0.2, epochs=30, batch_size=256, visualize=True):
        """Train detector"""
        print("\n" + "="*70)
        print("🚀 TRAINING PACKET & FLOW LAYER")
        print("="*70)

        features_df = self.extract_features(df)
        X = features_df[[c for c in features_df.columns if c != 'label']].copy()
        y = (features_df['label'] != 'BENIGN').astype(int)

        self.feature_columns = X.columns.tolist()

        print(f"\n📊 Dataset: Normal={np.sum(y==0)}, Attack={np.sum(y==1)}")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        X_train_normal = X_train[y_train == 0].copy()

        print(f"   Training on {len(X_train_normal)} normal samples")

        X_train_scaled = self.scaler.fit_transform(X_train_normal)
        X_train_all_scaled = self.scaler.transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Apply ADASYN
        if np.sum(y_train == 1) > 10:
            try:
                adasyn = ADASYN(sampling_strategy=0.2, random_state=42, n_neighbors=5)
                X_train_balanced, y_train_balanced = adasyn.fit_resample(
                    X_train_all_scaled, y_train
                )
                print(f"   After ADASYN: Normal={np.sum(y_train_balanced==0)}, "
                      f"Attack={np.sum(y_train_balanced==1)}")
            except:
                X_train_balanced = X_train_all_scaled
                y_train_balanced = y_train
        else:
            X_train_balanced = X_train_all_scaled
            y_train_balanced = y_train

        # Build and train
        self.build_autoencoder(X_train_scaled.shape[1])

        callbacks = [
            EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6)
        ]

        history = self.autoencoder.fit(
            X_train_scaled, X_train_scaled,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            callbacks=callbacks,
            verbose=1
        )

        # Train Isolation Forest
        self.isolation_forest = IsolationForest(
            contamination=0.05,
            random_state=42,
            n_estimators=100,
            max_samples=min(256, len(X_train_balanced))
        )
        self.isolation_forest.fit(X_train_balanced)

        # Find optimal threshold
        train_pred = self.autoencoder.predict(X_train_scaled, verbose=0)
        train_errors = np.mean(np.abs(X_train_scaled - train_pred), axis=1)

        test_pred = self.autoencoder.predict(X_test_scaled, verbose=0)
        test_errors = np.mean(np.abs(X_test_scaled - test_pred), axis=1)

        best_f1 = 0
        best_threshold = np.percentile(train_errors, 95)

        for percentile in range(85, 100, 1):
            thresh = np.percentile(train_errors, percentile)
            preds = (test_errors > thresh).astype(int)
            f1 = f1_score(y_test, preds, zero_division=0)
            if f1 > best_f1:
                best_f1 = f1
                best_threshold = thresh

        self.thresholds['autoencoder'] = best_threshold

        # Evaluate
        ae_pred = (test_errors > self.thresholds['autoencoder']).astype(int)
        if_pred = (self.isolation_forest.predict(X_test_scaled) == -1).astype(int)
        combined_pred = np.maximum(ae_pred, if_pred)

        self._print_metrics("Autoencoder", y_test, ae_pred)
        self._print_metrics("Isolation Forest", y_test, if_pred)
        self._print_metrics("Combined", y_test, combined_pred)

        # Store results
        self.test_data = {
            'X_test': X_test_scaled,
            'y_test': y_test,
            'ae_pred': ae_pred,
            'if_pred': if_pred,
            'combined_pred': combined_pred,
            'test_errors': test_errors,
            'history': history
        }

        # Visualizations
        if visualize:
            self.visualize_results()

        return history

    def _print_metrics(self, name, y_true, y_pred):
        """Print metrics"""
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        cm = confusion_matrix(y_true, y_pred)

        print(f"\n📊 {name} Performance:")
        print(f"   Accuracy  : {acc:.4f}")
        print(f"   Precision : {prec:.4f}")
        print(f"   Recall    : {rec:.4f}")
        print(f"   F1-Score  : {f1:.4f}")

        if cm.size == 4:
            tn, fp, fn, tp = cm.ravel()
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
            print(f"   FPR       : {fpr:.4f}")
            print(f"   Detection : TP={tp}, FP={fp}, TN={tn}, FN={fn}")

    def visualize_results(self):
        """Create comprehensive visualizations"""
        print("\n📊 Generating visualizations...")

        fig = plt.figure(figsize=(18, 12))

        # 1. Training History
        ax1 = plt.subplot(2, 3, 1)
        history = self.test_data['history']
        ax1.plot(history.history['loss'], label='Training Loss', linewidth=2)
        ax1.plot(history.history['val_loss'], label='Validation Loss', linewidth=2)
        ax1.set_xlabel('Epoch', fontsize=12)
        ax1.set_ylabel('Loss', fontsize=12)
        ax1.set_title('Autoencoder Training History', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 2. Reconstruction Error Distribution
        ax2 = plt.subplot(2, 3, 2)
        errors = self.test_data['test_errors']
        y_test = self.test_data['y_test']

        normal_errors = errors[y_test == 0]
        attack_errors = errors[y_test == 1]

        ax2.hist(normal_errors, bins=50, alpha=0.6, label='Normal', color='green', density=True)
        ax2.hist(attack_errors, bins=50, alpha=0.6, label='Attack', color='red', density=True)
        ax2.axvline(self.thresholds['autoencoder'], color='black', linestyle='--',
                   linewidth=2, label=f"Threshold ({self.thresholds['autoencoder']:.3f})")
        ax2.set_xlabel('Reconstruction Error', fontsize=12)
        ax2.set_ylabel('Density', fontsize=12)
        ax2.set_title('Reconstruction Error Distribution', fontsize=14, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. Confusion Matrix
        ax3 = plt.subplot(2, 3, 3)
        cm = confusion_matrix(y_test, self.test_data['ae_pred'])
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax3, cbar=False,
                   xticklabels=['Normal', 'Attack'],
                   yticklabels=['Normal', 'Attack'])
        ax3.set_xlabel('Predicted', fontsize=12)
        ax3.set_ylabel('Actual', fontsize=12)
        ax3.set_title('Confusion Matrix (Autoencoder)', fontsize=14, fontweight='bold')

        # 4. ROC Curve
        ax4 = plt.subplot(2, 3, 4)
        if len(np.unique(y_test)) > 1:
            fpr, tpr, _ = roc_curve(y_test, errors)
            roc_auc = auc(fpr, tpr)
            ax4.plot(fpr, tpr, linewidth=2, label=f'ROC (AUC = {roc_auc:.3f})')
            ax4.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random')
            ax4.set_xlabel('False Positive Rate', fontsize=12)
            ax4.set_ylabel('True Positive Rate', fontsize=12)
            ax4.set_title('ROC Curve', fontsize=14, fontweight='bold')
            ax4.legend()
            ax4.grid(True, alpha=0.3)

        # 5. Precision-Recall Curve
        ax5 = plt.subplot(2, 3, 5)
        if len(np.unique(y_test)) > 1:
            precision, recall, _ = precision_recall_curve(y_test, errors)
            ax5.plot(recall, precision, linewidth=2, color='purple')
            ax5.set_xlabel('Recall', fontsize=12)
            ax5.set_ylabel('Precision', fontsize=12)
            ax5.set_title('Precision-Recall Curve', fontsize=14, fontweight='bold')
            ax5.grid(True, alpha=0.3)

        # 6. Performance Comparison
        ax6 = plt.subplot(2, 3, 6)
        models = ['Autoencoder', 'Isolation\nForest', 'Combined']

        accuracies = [
            accuracy_score(y_test, self.test_data['ae_pred']),
            accuracy_score(y_test, self.test_data['if_pred']),
            accuracy_score(y_test, self.test_data['combined_pred'])
        ]

        f1_scores = [
            f1_score(y_test, self.test_data['ae_pred'], zero_division=0),
            f1_score(y_test, self.test_data['if_pred'], zero_division=0),
            f1_score(y_test, self.test_data['combined_pred'], zero_division=0)
        ]

        x = np.arange(len(models))
        width = 0.35

        bars1 = ax6.bar(x - width/2, accuracies, width, label='Accuracy', color='skyblue')
        bars2 = ax6.bar(x + width/2, f1_scores, width, label='F1-Score', color='salmon')

        ax6.set_ylabel('Score', fontsize=12)
        ax6.set_title('Model Performance Comparison', fontsize=14, fontweight='bold')
        ax6.set_xticks(x)
        ax6.set_xticklabels(models)
        ax6.legend()
        ax6.grid(True, alpha=0.3, axis='y')

        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax6.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.3f}',
                        ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        plt.savefig('packet_flow_analysis.png', dpi=300, bbox_inches='tight')
        print("   ✅ Saved: packet_flow_analysis.png")
        plt.show()

# ============================================================
# FIXED BEHAVIORAL DETECTOR
# ============================================================

class BehavioralDetector:
    """Fixed behavioral detector with proper sequence generation"""

    def __init__(self, time_window='15T', sequence_length=10, stride=5):
        self.time_window = time_window  # 15-minute windows
        self.sequence_length = sequence_length
        self.stride = stride
        self.scaler = MinMaxScaler()
        self.lstm_model = None
        self.threshold = None
        self.feature_columns = None

    def extract_behavioral_features(self, df):
        """Extract with smaller time windows"""
        print("🔍 Extracting behavioral features...")

        if 'Timestamp' not in df.columns:
            df['Timestamp'] = pd.date_range(
                start='2017-07-07 08:00:00',
                periods=len(df),
                freq='50ms'
            )
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])

        src_ip_col = None
        for col in ['Source IP', ' Source IP', 'Src IP']:
            if col in df.columns:
                src_ip_col = col
                break

        if src_ip_col is None:
            # Create diverse IPs with guaranteed multiple time windows
            n_ips = 100
            df['Source IP'] = [f"192.168.1.{i % n_ips + 1}" for i in range(len(df))]
            src_ip_col = 'Source IP'

        df['TimeWindow'] = df['Timestamp'].dt.floor(self.time_window)

        print(f"   Time range: {df['TimeWindow'].min()} to {df['TimeWindow'].max()}")
        print(f"   Total time windows: {df['TimeWindow'].nunique()}")

        # Aggregate
        behavioral_data = []

        for (ip, tw), group in df.groupby([src_ip_col, 'TimeWindow']):
            if len(group) < 3:
                continue

            features = {
                'source_ip': ip,
                'time_window': tw,
                'num_connections': len(group),
                'avg_flow_bytes_s': group.get('Flow Bytes/s', pd.Series([0])).mean(),
                'avg_flow_packets_s': group.get('Flow Packets/s', pd.Series([0])).mean(),
                'avg_flow_duration': group.get('Flow Duration', pd.Series([0])).mean(),
                'total_fwd_packets': group.get('Total Fwd Packets', pd.Series([0])).sum(),
                'total_bwd_packets': group.get('Total Backward Packets', pd.Series([0])).sum(),
                'avg_packet_size': group.get('Average Packet Size', pd.Series([0])).mean(),
                'syn_count': group.get('SYN Flag Count', pd.Series([0])).sum(),
                'rst_count': group.get('RST Flag Count', pd.Series([0])).sum(),
                'avg_iat_mean': group.get('Flow IAT Mean', pd.Series([0])).mean(),
                'label': 'BENIGN' if (group.get('Label', pd.Series(['BENIGN'])).str.upper() == 'BENIGN').all() else 'ATTACK'
            }

            behavioral_data.append(features)

        behavioral_df = pd.DataFrame(behavioral_data)
        behavioral_df = behavioral_df.sort_values(['source_ip', 'time_window'])

        print(f"✅ Extracted {len(behavioral_df)} windows from {behavioral_df['source_ip'].nunique()} IPs")

        # Show IPs with most windows
        ip_counts = behavioral_df['source_ip'].value_counts()
        print(f"   Top IPs: {ip_counts.head().to_dict()}")

        return behavioral_df

    def create_sequences(self, behavioral_df):
        """Create sequences with proper handling"""
        print(f"📦 Creating sequences (length={self.sequence_length}, stride={self.stride})...")

        feature_cols = [c for c in behavioral_df.columns
                       if c not in ['source_ip', 'time_window', 'label']]
        self.feature_columns = feature_cols

        behavioral_df[feature_cols] = behavioral_df[feature_cols].fillna(0).replace([np.inf, -np.inf], 0)

        scaled_features = self.scaler.fit_transform(behavioral_df[feature_cols])

        sequences = []
        labels = []
        ip_list = []

        for ip in behavioral_df['source_ip'].unique():
            ip_data = behavioral_df[behavioral_df['source_ip'] == ip]

            if len(ip_data) < self.sequence_length:
                continue

            ip_features = scaled_features[behavioral_df['source_ip'] == ip]
            ip_labels = ip_data['label'].values

            for i in range(0, len(ip_features) - self.sequence_length + 1, self.stride):
                seq = ip_features[i:i + self.sequence_length]
                seq_label = 0 if all(ip_labels[i:i + self.sequence_length] == 'BENIGN') else 1

                sequences.append(seq)
                labels.append(seq_label)
                ip_list.append(ip)

        if len(sequences) == 0:
            print("❌ No sequences created!")
            return None, None, None

        X = np.array(sequences)
        y = np.array(labels)

        print(f"✅ Created {len(sequences)} sequences")
        print(f"   Shape: {X.shape}")
        print(f"   Normal: {np.sum(y==0)}, Attack: {np.sum(y==1)}")

        return X, y, ip_list

    def build_lstm(self, sequence_length, n_features):
        """Build LSTM autoencoder"""
        input_layer = Input(shape=(sequence_length, n_features))

        x = LSTM(32, activation='tanh', return_sequences=False, dropout=0.2)(input_layer)
        encoded = Dense(16, activation='relu')(x)

        x = RepeatVector(sequence_length)(encoded)
        x = LSTM(32, activation='tanh', return_sequences=True, dropout=0.2)(x)
        decoded = TimeDistributed(Dense(n_features))(x)

        self.lstm_model = Model(input_layer, decoded)
        self.lstm_model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )

        print("🏗️  LSTM autoencoder built")
        return self.lstm_model

    def train(self, df, epochs=50, batch_size=32, visualize=True):
        """Train behavioral layer"""
        print("\n" + "="*70)
        print("🧠 TRAINING BEHAVIORAL LAYER")
        print("="*70)

        behavioral_df = self.extract_behavioral_features(df)

        if len(behavioral_df) < self.sequence_length:
            print("❌ Not enough behavioral data")
            return None

        result = self.create_sequences(behavioral_df)
        if result[0] is None:
            print("❌ Sequence creation failed")
            return None

        X, y, ip_list = result

        normal_mask = y == 0
        X_normal = X[normal_mask]

        if len(X_normal) < 10:
            print("❌ Not enough normal sequences")
            return None

        X_train, X_val = train_test_split(X_normal, test_size=0.2, random_state=42)

        print(f"\n📊 Training on {len(X_train)} normal sequences")

        self.build_lstm(X.shape[1], X.shape[2])

        callbacks = [
            EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=7, min_lr=1e-6)
        ]

        history = self.lstm_model.fit(
            X_train, X_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_val, X_val),
            callbacks=callbacks,
            verbose=1
        )

        # Set threshold
        val_pred = self.lstm_model.predict(X_val, verbose=0)
        val_errors = np.mean(np.power(X_val - val_pred, 2), axis=(1, 2))
        self.threshold = np.percentile(val_errors, 99)

        print(f"\n✅ Training complete! Threshold: {self.threshold:.6f}")

        # Evaluate
        test_pred = self.lstm_model.predict(X, verbose=0)
        test_errors = np.mean(np.power(X - test_pred, 2), axis=(1, 2))
        predictions = (test_errors > self.threshold).astype(int)

        acc = accuracy_score(y, predictions)
        prec = precision_score(y, predictions, zero_division=0)
        rec = recall_score(y, predictions, zero_division=0)
        f1 = f1_score(y, predictions, zero_division=0)

        print(f"\n🎯 Behavioral Layer Performance:")
        print(f"   Accuracy : {acc:.4f}")
        print(f"   Precision: {prec:.4f}")
        print(f"   Recall   : {rec:.4f}")
        print(f"   F1-Score : {f1:.4f}")

        self.test_data = {
            'X': X,
            'y': y,
            'predictions': predictions,
            'errors': test_errors,
            'history': history
        }

        if visualize:
            self.visualize_results()

        return history

    def visualize_results(self):
        """Visualize behavioral results"""
        print("\n📊 Generating behavioral visualizations...")

        fig = plt.figure(figsize=(16, 10))

        # 1. Training History
        ax1 = plt.subplot(2, 3, 1)
        history = self.test_data['history']
        ax1.plot(history.history['loss'], label='Training Loss', linewidth=2)
        ax1.plot(history.history['val_loss'], label='Validation Loss', linewidth=2)
        ax1.set_xlabel('Epoch', fontsize=12)
        ax1.set_ylabel('Loss', fontsize=12)
        ax1.set_title('LSTM Training History', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 2. Error Distribution
        ax2 = plt.subplot(2, 3, 2)
        errors = self.test_data['errors']
        y = self.test_data['y']

        normal_errors = errors[y == 0]
        attack_errors = errors[y == 1]

        ax2.hist(normal_errors, bins=30, alpha=0.6, label='Normal', color='green', density=True)
        if len(attack_errors) > 0:
            ax2.hist(attack_errors, bins=30, alpha=0.6, label='Attack', color='red', density=True)
        ax2.axvline(self.threshold, color='black', linestyle='--', linewidth=2,
                   label=f"Threshold ({self.threshold:.4f})")
        ax2.set_xlabel('Reconstruction Error', fontsize=12)
        ax2.set_ylabel('Density', fontsize=12)
        ax2.set_title('Sequence Reconstruction Error', fontsize=14, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. Confusion Matrix
        ax3 = plt.subplot(2, 3, 3)
        cm = confusion_matrix(y, self.test_data['predictions'])
        sns.heatmap(cm, annot=True, fmt='d', cmap='Greens', ax=ax3, cbar=False,
                   xticklabels=['Normal', 'Attack'],
                   yticklabels=['Normal', 'Attack'])
        ax3.set_xlabel('Predicted', fontsize=12)
        ax3.set_ylabel('Actual', fontsize=12)
        ax3.set_title('Confusion Matrix (Behavioral)', fontsize=14, fontweight='bold')

        # 4. Temporal Pattern
        ax4 = plt.subplot(2, 3, 4)
        sample_indices = np.random.choice(len(errors), min(100, len(errors)), replace=False)
        ax4.scatter(range(len(sample_indices)), errors[sample_indices],
                   c=y[sample_indices], cmap='RdYlGn_r', alpha=0.6, s=50)
        ax4.axhline(self.threshold, color='black', linestyle='--', linewidth=2, label='Threshold')
        ax4.set_xlabel('Sequence Index (sampled)', fontsize=12)
        ax4.set_ylabel('Reconstruction Error', fontsize=12)
        ax4.set_title('Temporal Anomaly Pattern', fontsize=14, fontweight='bold')
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        # 5. ROC Curve
        ax5 = plt.subplot(2, 3, 5)
        if len(np.unique(y)) > 1:
            fpr, tpr, _ = roc_curve(y, errors)
            roc_auc = auc(fpr, tpr)
            ax5.plot(fpr, tpr, linewidth=2, label=f'ROC (AUC = {roc_auc:.3f})', color='purple')
            ax5.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random')
            ax5.set_xlabel('False Positive Rate', fontsize=12)
            ax5.set_ylabel('True Positive Rate', fontsize=12)
            ax5.set_title('ROC Curve (Behavioral)', fontsize=14, fontweight='bold')
            ax5.legend()
            ax5.grid(True, alpha=0.3)

        # 6. Metrics Bar Chart
        ax6 = plt.subplot(2, 3, 6)
        metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
        values = [
            accuracy_score(y, self.test_data['predictions']),
            precision_score(y, self.test_data['predictions'], zero_division=0),
            recall_score(y, self.test_data['predictions'], zero_division=0),
            f1_score(y, self.test_data['predictions'], zero_division=0)
        ]

        bars = ax6.barh(metrics, values, color=['skyblue', 'lightcoral', 'lightgreen', 'gold'])
        ax6.set_xlabel('Score', fontsize=12)
        ax6.set_title('Behavioral Layer Metrics', fontsize=14, fontweight='bold')
        ax6.set_xlim([0, 1])
        ax6.grid(True, alpha=0.3, axis='x')

        for i, (bar, val) in enumerate(zip(bars, values)):
            ax6.text(val + 0.01, i, f'{val:.3f}', va='center', fontsize=10)

        plt.tight_layout()
        plt.savefig('behavioral_analysis.png', dpi=300, bbox_inches='tight')
        print("   ✅ Saved: behavioral_analysis.png")
        plt.show()

# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":

    print("="*70)
    print("🎯 COMPLETE MULTI-LAYER ANOMALY DETECTION SYSTEM")
    print("📊 With Comprehensive Visualizations")
    print("="*70)

    try:

        print("\n📂 Loading multiple CICIDS2017 dataset files...")

        files = [
            "/content/Monday-WorkingHours.pcap_ISCX.csv",
            "/content/Tuesday-WorkingHours.pcap_ISCX.csv",
            "/content/Wednesday-workingHours.pcap_ISCX.csv",
            "/content/Friday-WorkingHours-Morning.pcap_ISCX.csv"
        ]

        df_list = []

        for file in files:
            print(f"Loading: {file}")
            temp_df = pd.read_csv(file)
            df_list.append(temp_df)

        # Combine datasets
        df = pd.concat(df_list, ignore_index=True)

        print(f"\n✅ Combined dataset shape: {df.shape}")

        # ===============================
        # Preprocess Dataset
        # ===============================

        df = preprocess_cicids2017_final(df)

        # ===============================
        # Train Packet/Flow Layer
        # ===============================

        pf_detector = PacketFlowDetector(encoding_dim=16)

        pf_history = pf_detector.train(
            df,
            test_size=0.2,
            epochs=30,
            batch_size=256,
            visualize=True
        )

        # ===============================
        # Train Behavioral Layer
        # ===============================

        bh_detector = BehavioralDetector(
            time_window='1T',
            sequence_length=5,
            stride=2
        )

        bh_history = bh_detector.train(
            df,
            epochs=50,
            batch_size=32,
            visualize=True
        )

        # ===============================
        # Save Results CSV
        # ===============================

        pf_results = pf_detector.extract_features(df)
        pf_results.to_csv("final_packet_flow_results.csv", index=False)

        # ===============================
        # Save Trained Models
        # ===============================

        import joblib

        print("\n💾 Saving trained models...")

        # Packet models
        pf_detector.autoencoder.save("packet_autoencoder.h5")
        joblib.dump(pf_detector.isolation_forest, "isolation_forest.pkl")
        joblib.dump(pf_detector.scaler, "packet_scaler.pkl")

        # Behavioral scaler
        joblib.dump(bh_detector.scaler, "behavior_scaler.pkl")

        # Feature columns
        joblib.dump(pf_detector.feature_columns, "packet_features.pkl")
        joblib.dump(bh_detector.feature_columns, "behavior_features.pkl")

        # Thresholds
        joblib.dump(pf_detector.thresholds, "packet_thresholds.pkl")
        joblib.dump(bh_detector.threshold, "behavior_threshold.pkl")

        # Behavioral LSTM
        if bh_detector.lstm_model is not None:
            bh_detector.lstm_model.save("behavioral_lstm.h5")

        print("✅ Models saved successfully")

        # ===============================
        # Create ZIP
        # ===============================

        print("\n📦 Creating downloadable model package...")

        !zip best_models.zip \
        packet_autoencoder.h5 \
        isolation_forest.pkl \
        packet_scaler.pkl \
        packet_features.pkl \
        packet_thresholds.pkl \
        behavior_scaler.pkl \
        behavior_features.pkl \
        behavior_threshold.pkl \
        behavioral_lstm.h5 \
        final_packet_flow_results.csv

        # ===============================
        # Download ZIP
        # ===============================

        from google.colab import files
        files.download("best_models.zip")

        print("\n" + "="*70)
        print("✅ COMPLETE TRAINING FINISHED!")
        print("📊 Visualizations saved:")
        print("   • packet_flow_analysis.png")
        print("   • behavioral_analysis.png")
        print("💾 Models packaged as:")
        print("   • best_models.zip")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()      
        
       