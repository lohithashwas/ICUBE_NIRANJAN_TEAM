import requests
import json

class OSMCollector:
    def __init__(self):
        self.overpass_url = "http://overpass-api.de/api/interpreter"

    def fetch_infrastructure(self, lat, lon, radius=5000):
        """
        Fetches critical infrastructure (Hospitals, Police, Fire) around a coordinate.
        Radius is in meters.
        """
        # Overpass QL Query
        query = f"""
        [out:json];
        (
          node["amenity"="hospital"](around:{radius},{lat},{lon});
          node["amenity"="police"](around:{radius},{lat},{lon});
          node["amenity"="fire_station"](around:{radius},{lat},{lon});
        );
        out body;
        >;
        out skel qt;
        """
        
        try:
            response = requests.post(self.overpass_url, data={'data': query}, timeout=25)
            if response.status_code == 200:
                data = response.json()
                elements = data.get('elements', [])
                
                infrastructure = []
                for el in elements:
                    infrastructure.append({
                        "type": "infrastructure",
                        "category": el.get('tags', {}).get('amenity', 'unknown'),
                        "name": el.get('tags', {}).get('name', 'Unknown Facility'),
                        "lat": el.get('lat'),
                        "lon": el.get('lon'),
                        "details": el.get('tags', {})
                    })
                    
                print(f"OSM: Found {len(infrastructure)} infrastructure points nearby.")
                return infrastructure
            else:
                print(f"OSM: API Error {response.status_code}")
                return []
                
        except Exception as e:
            print(f"OSM: Exception - {e}")
            return []

if __name__ == "__main__":
    # Test with coordinates for New Delhi
    collector = OSMCollector()
    results = collector.fetch_infrastructure(28.6139, 77.2090)
    print(results[:5])
