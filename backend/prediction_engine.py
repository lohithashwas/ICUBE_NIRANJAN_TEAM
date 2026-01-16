import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

class DisasterPredictor:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100)
        self.scaler = StandardScaler()
        self._train_mock_model()

    def _train_mock_model(self):
        # Simulated historical data for India (Features: Rainfall, Seismic Activity, Soil Moisture, river_level)
        # Target: 0=Safe, 1=Flood, 2=Landslide, 3=Earthquake
        data = {
            'rainfall_mm': np.random.normal(100, 30, 1000),
            'seismic_magnitude': np.random.normal(2, 1, 1000),
            'soil_moisture': np.random.normal(50, 15, 1000),
            'river_level_m': np.random.normal(5, 2, 1000),
            'risk_level': []
        }
        
        # Generate logic-based labels for training
        for i in range(1000):
            r = data['rainfall_mm'][i]
            s = data['seismic_magnitude'][i]
            rv = data['river_level_m'][i]
            
            if s > 5.5: label = 3 # Quake
            elif r > 180 or rv > 8: label = 1 # Flood
            elif r > 150 and data['soil_moisture'][i] > 70: label = 2 # Landslide
            else: label = 0 # Safe
            data['risk_level'].append(label)

        df = pd.DataFrame(data)
        X = df[['rainfall_mm', 'seismic_magnitude', 'soil_moisture', 'river_level_m']]
        y = df['risk_level']
        
        self.model.fit(X, y)

    def predict_state_risk(self, state_name):
        # Simulate live features for the state (In real app, fetch from IMD/USGS)
        # Mocking values based on typical state profiles
        profiles = {
            "Tamil Nadu": [45, 1.2, 30, 4], # Currently calm
            "Assam": [160, 3.4, 85, 7.8],   # Flood risk
            "Uttarakhand": [140, 4.1, 75, 5], # Landslide risk
            "Gujarat": [10, 2.1, 20, 2],    # Safe
            "Maharashtra": [80, 2.5, 40, 5], # Moderate
            "Kerala": [120, 1.5, 65, 6],     # Watch
            "Delhi": [25, 1.1, 10, 3],       # Safe
            "Odisha": [90, 1.3, 50, 6],      # Moderate
        }
        
        features = profiles.get(state_name, [50, 2.0, 40, 4]) # Default
        
        # Predict probabilities
        risk_probs = self.model.predict_proba([features])[0]
        # risk_probs order: [Safe, Flood, Landslide, Earthquake] (roughly)
        
        # Calculate Logic-based Safety Score (0-100) based on 'Safe' probability
        safety_score = int(risk_probs[0] * 100) 
        
        # Determine likely disaster
        disaster_types = ["None", "Flood", "Landslide", "Earthquake"]
        likely_idx = np.argmax(risk_probs)
        prediction = disaster_types[likely_idx] if likely_idx > 0 else "Safe"
        
        return {
            "state": state_name,
            "safety_score": safety_score,
            "prediction": prediction,
            "confidence": int(max(risk_probs) * 100),
            "drivers": {
                "rainfall": f"{features[0]}mm",
                "seismic": f"{features[1]} M",
                "soil_moisture": f"{features[2]}%",
                "river_level": f"{features[3]}m"
            }
        }
