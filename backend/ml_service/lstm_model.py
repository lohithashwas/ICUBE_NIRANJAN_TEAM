import os
import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import joblib
from datetime import datetime, timedelta

class TouristSafetyLSTM:
    """LSTM Model for predicting tourist safety metrics"""
    def __init__(self, firebase_credentials_path=None):
        self.db = None
        if firebase_credentials_path:
            self._initialize_firebase(firebase_credentials_path)
        self.model = None
        self.scaler = MinMaxScaler()
        self.label_encoder = LabelEncoder()
        self.sequence_length = 24
        self.feature_columns = []

    def _initialize_firebase(self, credentials_path):
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
        except Exception as e:
            print(f"Firebase init error: {e}")
            self.db = None

    def fetch_training_data(self):
        if not self.db:
            print("No Firebase DB, returning empty data frames.")
            return {
                'tourists': pd.DataFrame(),
                'alerts': pd.DataFrame(),
                'zones': pd.DataFrame()
            }
        tourists = []
        alerts = []
        zones = []
        for doc in self.db.collection('tourists').stream():
            d = doc.to_dict(); d['doc_id'] = doc.id; tourists.append(d)
        for doc in self.db.collection('alerts').stream():
            d = doc.to_dict(); d['doc_id'] = doc.id; alerts.append(d)
        for doc in self.db.collection('zones').stream():
            d = doc.to_dict(); d['doc_id'] = doc.id; zones.append(d)
        return {
            'tourists': pd.DataFrame(tourists),
            'alerts': pd.DataFrame(alerts),
            'zones': pd.DataFrame(zones)
        }

    def preprocess_data(self, data_dict):
        tourists_df = data_dict['tourists']
        alerts_df = data_dict['alerts']
        # Ensure location columns
        tourists_df['lat'] = tourists_df['location'].apply(lambda x: x.get('lat', 0) if isinstance(x, dict) else 0)
        tourists_df['lng'] = tourists_df['location'].apply(lambda x: x.get('lng', 0) if isinstance(x, dict) else 0)
        # Timestamp handling
        ts_field = next((f for f in ['lastUpdate', 'lastSeen', 'checkInDate', 'timestamp'] if f in tourists_df.columns), None)
        if ts_field:
            try:
                tourists_df['timestamp'] = pd.to_datetime(tourists_df[ts_field])
            except Exception:
                tourists_df['timestamp'] = pd.Timestamp.now()
        else:
            tourists_df['timestamp'] = pd.Timestamp.now()
        # Alerts preprocessing
        if not alerts_df.empty:
            if 'timestamp' in alerts_df.columns:
                try:
                    alerts_df['timestamp'] = pd.to_datetime(alerts_df['timestamp'])
                except Exception:
                    alerts_df['timestamp'] = pd.Timestamp.now()
            else:
                alerts_df['timestamp'] = pd.Timestamp.now()
            if 'type' in alerts_df.columns:
                alerts_df['type_encoded'] = self.label_encoder.fit_transform(alerts_df['type'])
            else:
                alerts_df['type_encoded'] = 0
            if 'priority' in alerts_df.columns:
                alerts_df['priority_encoded'] = alerts_df['priority'].map({'low':0,'medium':1,'high':2,'critical':3}).fillna(0)
            else:
                alerts_df['priority_encoded'] = 0
        # Time features
        tourists_df['hour'] = tourists_df['timestamp'].dt.hour
        tourists_df['day_of_week'] = tourists_df['timestamp'].dt.dayofweek
        tourists_df['day_of_month'] = tourists_df['timestamp'].dt.day
        tourists_df['month'] = tourists_df['timestamp'].dt.month
        # Location risk
        location_risk = self._calculate_location_risk(tourists_df, alerts_df)
        tourists_df = tourists_df.merge(location_risk, on=['lat','lng'], how='left')
        tourists_df['risk_score'] = tourists_df['risk_score'].fillna(0)
        return tourists_df, alerts_df

    def _calculate_location_risk(self, tourists_df, alerts_df):
        if alerts_df.empty:
            return pd.DataFrame({'lat':tourists_df['lat'].unique(),'lng':tourists_df['lng'].unique(),'risk_score':[0.0]*len(tourists_df['lat'].unique())})
        alerts_df['alert_lat'] = alerts_df['location'].apply(lambda x: x.get('lat',0) if isinstance(x, dict) else 0)
        alerts_df['alert_lng'] = alerts_df['location'].apply(lambda x: x.get('lng',0) if isinstance(x, dict) else 0)
        rows = []
        for _, row in tourists_df.iterrows():
            lat, lng = row['lat'], row['lng']
            if lat==0 and lng==0:
                rows.append({'lat':lat,'lng':lng,'risk_score':0.0}); continue
            nearby = alerts_df[(abs(alerts_df['alert_lat']-lat)<0.01)&(abs(alerts_df['alert_lng']-lng)<0.01]
            risk = len(nearby)*0.1
            if not nearby.empty and 'priority_encoded' in nearby.columns:
                risk += nearby['priority_encoded'].mean()*0.3
            rows.append({'lat':lat,'lng':lng,'risk_score':min(risk,1.0)})
        return pd.DataFrame(rows).drop_duplicates()

    def create_sequences(self, df, target='risk_score'):
        self.feature_columns = ['lat','lng','hour','day_of_week','day_of_month','month','risk_score']
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp')
        elif 'checkInDate' in df.columns:
            df = df.sort_values('checkInDate')
        features = df[self.feature_columns].values
        if len(features) < self.sequence_length + 1:
            self.sequence_length = max(1, len(features)//2)
        scaled = self.scaler.fit_transform(features)
        X, y = [], []
        for i in range(len(scaled)-self.sequence_length):
            X.append(scaled[i:i+self.sequence_length])
            y.append(scaled[i+self.sequence_length, -1])
        if not X:
            raise ValueError('Not enough data to create sequences')
        return np.array(X), np.array(y)

    def build_model(self, input_shape):
        model = Sequential([
            Bidirectional(LSTM(128, return_sequences=True), input_shape=input_shape),
            Dropout(0.3),
            Bidirectional(LSTM(64, return_sequences=True)),
            Dropout(0.3),
            LSTM(32),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss='mse', metrics=['mae','mse'])
        return model

    def train(self, epochs=30, batch_size=32, val_split=0.2):
        data = self.fetch_training_data()
        tourists_df, alerts_df = self.preprocess_data(data)
        X, y = self.create_sequences(tourists_df)
        self.model = self.build_model((X.shape[1], X.shape[2]))
        early = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        checkpoint = ModelCheckpoint('models/best_lstm.h5', monitor='val_loss', save_best_only=True)
        self.model.fit(X, y, epochs=epochs, batch_size=batch_size, validation_split=val_split, callbacks=[early, checkpoint])
        return self.model

    def predict_risk(self, tourist_data):
        if self.model is None:
            raise RuntimeError('Model not trained')
        feats = [tourist_data.get(col,0) for col in self.feature_columns]
        seq = np.array([feats]*self.sequence_length)
        seq_scaled = self.scaler.transform(seq).reshape(1, self.sequence_length, len(self.feature_columns))
        pred = self.model.predict(seq_scaled, verbose=0)
        return float(pred[0][0])

    def save_model(self, model_path='models/lstm_model.h5', scaler_path='models/scaler.pkl'):
        os.makedirs('models', exist_ok=True)
        self.model.save(model_path)
        joblib.dump(self.scaler, scaler_path)
        joblib.dump(self.feature_columns, 'models/feature_columns.pkl')
        print(f"Model saved to {model_path}")

    def load_model(self, model_path='models/lstm_model.h5', scaler_path='models/scaler.pkl'):
        self.model = load_model(model_path)
        self.scaler = joblib.load(scaler_path)
        self.feature_columns = joblib.load('models/feature_columns.pkl')
        print(f"Model loaded from {model_path}")
