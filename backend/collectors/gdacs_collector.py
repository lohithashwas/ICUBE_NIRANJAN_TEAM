import requests
import logging
from datetime import datetime

class GDACSCollector:
    def __init__(self):
        self.feed_url = "https://www.gdacs.org/xml/rss.xml"
        # Rough Bounding Box for India
        self.india_lat_min = 6.0
        self.india_lat_max = 37.0
        self.india_lon_min = 68.0
        self.india_lon_max = 98.0

    def fetch_data(self):
        """Fetches live disaster alerts from GDACS and filters for India."""
        try:
            # Note: GDACS RSS is the most stable public feed.
            # Ideally we would use the GeoJSON API but it's often rate-limited or requires specific event IDs.
            # For this MVP, we parse the RSS feed or use their public JSON endpoint if available.
            # Let's try the JSON endpoint first which is cleaner.
            
            response = requests.get("https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?eventlist=EQ,TC,FL,DR&alertlevel=Green,Orange,Red")
            
            if response.status_code == 200:
                data = response.json()
                features = data.get('features', [])
                
                india_events = []
                for feature in features:
                    props = feature.get('properties', {})
                    geometry = feature.get('geometry', {})
                    if not geometry:
                        continue
                        
                    coords = geometry.get('coordinates', [0, 0])
                    lon, lat = coords[0], coords[1]

                    # Filter for India Region
                    if (self.india_lat_min <= lat <= self.india_lat_max and 
                        self.india_lon_min <= lon <= self.india_lon_max):
                        
                        india_events.append({
                            "type": "disaster",
                            "source": "GDACS",
                            "event_type": props.get('eventtype'),
                            "name": props.get('name'),
                            "description": props.get('description'),
                            "severity": props.get('alertlevel'),
                            "lat": lat,
                            "lon": lon,
                            "time": props.get('fromdate'), # or todate
                            "metadata": {
                                "country": props.get('country'),
                                "episode_id": props.get('episodeid')
                            }
                        })
                
                print(f"GDACS: Found {len(india_events)} events in India region.")
                return india_events
            else:
                print(f"GDACS: Error fetching data {response.status_code}")
                return []
                
        except Exception as e:
            print(f"GDACS: Exception occurred - {e}")
            return []

if __name__ == "__main__":
    collector = GDACSCollector()
    results = collector.fetch_data()
    print(results)
