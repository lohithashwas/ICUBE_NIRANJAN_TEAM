import requests

class WeatherCollector:
    def __init__(self):
        self.api_url = "https://api.open-meteo.com/v1/forecast"

    def fetch_weather(self, lat, lon):
        """
        Fetches current weather and short-term forecast for a specific location.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m,wind_direction_10m,soil_moisture_0_to_1cm",
            "hourly": "visibility",
            "forecast_days": 1
        }
        
        try:
            response = requests.get(self.api_url, params=params)
            if response.status_code == 200:
                data = response.json()
                current = data.get('current', {})
                
                weather_data = {
                    "lat": lat,
                    "lon": lon,
                    "temp_c": current.get('temperature_2m'),
                    "humidity": current.get('relative_humidity_2m'),
                    "precip_mm": current.get('precipitation'),
                    "wind_kph": current.get('wind_speed_10m'),
                    "soil_moisture": current.get('soil_moisture_0_to_1cm'),
                    "timestamp": current.get('time')
                }
                # Simple Risk logic
                risk_level = "Low"
                if weather_data['wind_kph'] > 50 or weather_data['precip_mm'] > 50:
                    risk_level = "High"
                elif weather_data['wind_kph'] > 30 or weather_data['precip_mm'] > 20:
                    risk_level = "Medium"
                
                weather_data['risk_level'] = risk_level
                
                return weather_data
            else:
                print(f"Weather: API Error {response.status_code}")
                return None
        except Exception as e:
            print(f"Weather: Exception - {e}")
            return None

if __name__ == "__main__":
    # Test for Kolkata
    collector = WeatherCollector()
    print(collector.fetch_weather(22.5726, 88.3639))
