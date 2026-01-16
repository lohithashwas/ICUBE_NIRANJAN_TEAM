import os
import sys
import json
import time

# Add backend to path
sys.path.append(os.getcwd())

from collectors.imd_collector import IMDCollector
from collectors.cwc_collector import CWCCollector
from collectors.isro_collector import ISROCollector
# from collectors.safar_collector import SAFARCollector

def run_manual():
    print("Starting Manual Collection...")
    
    # Instantiate Collectors
    imd = IMDCollector()
    cwc = CWCCollector()
    isro = ISROCollector()
    
    # Fetch Data
    print("Fetching ISRO...")
    isro_data = isro.fetch_data()
    print("ISRO Done.")

    print("Fetching IMD...")
    imd_data = imd.fetch_data()
    print("IMD Done.")

    print("Fetching CWC...")
    cwc_data = cwc.fetch_data()
    print("CWC Done.")
    
    safar_data = {"error": "Skipped for speed"}
    
    results = {
        "imd": imd_data,
        "cwc": cwc_data,
        "isro": isro_data,
        "safar": safar_data,
        "last_updated": time.time()
    }
    
    print("Saving Data...")
    with open("assets/data_store.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print("Done.")

if __name__ == "__main__":
    run_manual()
