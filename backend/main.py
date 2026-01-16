from fastapi import FastAPI, BackgroundTasks, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from collectors.gdacs_collector import GDACSCollector
from collectors.osm_collector import OSMCollector
from collectors.weather_collector import WeatherCollector
from prediction_engine import DisasterPredictor
import os
import json
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Antigravity Nexus - Real-Time Command Center")

# Initialize ML Engine
ml_engine = DisasterPredictor()

@app.get("/api/ml-prediction")
def get_ml_predictions():
    states = ["Tamil Nadu", "Assam", "Uttarakhand", "Gujarat", "Maharashtra", "Kerala", "Delhi", "Odisha"]
    results = []
    for state in states:
        pred = ml_engine.predict_state_risk(state)
        results.append(pred)
    return results

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static mounts
os.makedirs("assets/images", exist_ok=True)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Initialize Real-Time Collectors
gdacs = GDACSCollector()
osm = OSMCollector()
weather = WeatherCollector()

DATA_FILE = "assets/data_store.json"

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def run_collection_task():
    logger.info("Starting global data collection...")
    # Fetch Macro Data (Alerts)
    alerts = gdacs.fetch_data()
    
    # We can pre-fetch some major city weather
    major_cities = {
        "Delhi": (28.61, 77.20),
        "Mumbai": (19.07, 72.87),
        "Chennai": (13.08, 80.27),
        "Kolkata": (22.57, 88.36),
        "Guwahati": (26.11, 91.70) # North East focus
    }
    
    city_weather = {}
    for name, coords in major_cities.items():
        city_weather[name] = weather.fetch_weather(coords[0], coords[1])

    results = {
        "alerts": alerts,
        "key_metrics": city_weather,
        "last_updated": os.path.getmtime(DATA_FILE) if os.path.exists(DATA_FILE) else 0
    }
    save_data(results)
    logger.info("Global data collection complete.")

@app.get("/")
def read_root():
    return {"status": "Antigravity Nexus Online", "mode": "Real-Time Direct Feed"}

@app.get("/collect")
async def trigger_collection(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_collection_task)
    return {"message": "Global collection triggered"}

@app.get("/api/data")
def get_global_data():
    return load_data()

@app.get("/api/infrastructure")
def get_nearby_infrastructure(lat: float, lon: float, radius: int = 5000):
    """Real-time fetch of hospitals/police from OSM"""
    return osm.fetch_infrastructure(lat, lon, radius)

@app.get("/api/weather")
def get_local_weather(lat: float, lon: float):
    """Real-time fetch of weather from OpenMeteo"""
    return weather.fetch_weather(lat, lon)

if __name__ == "__main__":
    import uvicorn
    from apscheduler.schedulers.background import BackgroundScheduler

    # Initialize Scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_collection_task, 'interval', minutes=15)
    scheduler.start()
    print("Auto-Sync Scheduler Started: Running every 15 minutes.")

    # Initial Run
    run_collection_task()

    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

