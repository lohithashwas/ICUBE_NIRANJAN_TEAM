import requests
from bs4 import BeautifulSoup
from .pdf_manager import pdf_manager
import logging
import os
import shutil

logger = logging.getLogger(__name__)

class ISROCollector:
    def __init__(self):
        self.base_url = "https://bhuvan-app1.nrsc.gov.in"
        self.disaster_url = "https://bhuvan-app1.nrsc.gov.in/disaster/disaster.php"

    def fetch_data(self):
        """Fetches latest Satellite Image from IMD/ISRO Bhuvan feed."""
        try:
            logger.info("Fetching Satellite data...")
            # Verified Stable URL for Asia Sector IR1 (Commonly used for cyclones/cloud cover)
            satellite_url = "https://mausam.imd.gov.in/Satellite/3Dasiasec_ir1.jpg"
            
            # Since it's a JPG, we can just download it directly or serve the URL
            # To be consistent with "Antigravity App" serving its own assets:
            
            import shutil
            local_filename = "satellite_live.jpg"
            image_path = os.path.join("assets/images", local_filename)
            
            response = requests.get(satellite_url, verify=False, stream=True, timeout=15)
            if response.status_code == 200:
                with open(image_path, 'wb') as f:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, f)
                
                return {
                    "source": "IMD Satellite",
                    "type": "satellite_map",
                    "images": [f"/assets/images/{local_filename}?t={os.path.getmtime(image_path)}"], # Cache bust
                    "original_url": satellite_url
                }
            
            return None

        except Exception as e:
            logger.error(f"Satellite Collection failed: {e}")
            return {"error": str(e)}
