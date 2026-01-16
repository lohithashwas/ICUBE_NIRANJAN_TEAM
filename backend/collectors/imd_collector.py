import requests
from bs4 import BeautifulSoup
import logging
import os

logger = logging.getLogger(__name__)

# Try to import pdf_manager, handle failure
try:
    from .pdf_manager import pdf_manager
except ImportError:
    pdf_manager = None
except Exception:
    pdf_manager = None

class IMDCollector:
    def __init__(self):
        self.base_url = "https://mausam.imd.gov.in"
        self.bulletin_url = "https://mausam.imd.gov.in/responsive/all_india_forcast_bulletin.php"

    def fetch_data(self):
        """Scrapes IMD website for the latest weather bulletin PDF."""
        try:
            logger.info("Fetching IMD data...")
            # Real-time scraping using verified selector
            try:
                 response = requests.get(self.bulletin_url, verify=False, timeout=30)
                 soup = BeautifulSoup(response.content, 'html.parser')
            except Exception as e:
                 logger.error(f"IMD Request failed: {e}")
                 return {"error": "Connection error"}
            
            pdf_link = None
            
            # Precise selector attempt
            target_link = soup.select_one('a#default-block-btn')
            if target_link and 'pdf' in target_link.get('href', '').lower():
                pdf_link = target_link['href']
            
            # Fallback scan
            if not pdf_link:
                for a in soup.find_all('a', href=True):
                    if 'all india weather forecast bulletin' in a.get_text().lower() or 'all_india_forcast_bulletin' in a['href']:
                         pdf_link = a['href']
                         break

            if pdf_link:
                if not pdf_link.startswith('http'):
                    pdf_link = self.base_url + "/" + pdf_link.lstrip('/')

                logger.info(f"Verified IMD PDF Link: {pdf_link}")
                
                 # Handle missing pdf_manager
                if pdf_manager:
                    pdf_path = pdf_manager.download_pdf(pdf_link, "imd_weather")
                    if pdf_path:
                        images = pdf_manager.convert_to_images(pdf_path, "imd_weather")
                        return {
                            "source": "IMD",
                            "type": "weather_bulletin",
                            "images": images,
                            "original_pdf": pdf_link,
                            "timestamp": "Live"
                        }
                else:
                     return {
                        "source": "IMD",
                        "type": "weather_bulletin",
                        "images": [],
                        "original_pdf": pdf_link,
                        "timestamp": "Live PDF (Conversion Unavailable)"
                    }
            
            return None

        except Exception as e:
            logger.error(f"IMD Collection failed: {e}")
            return {"error": str(e)}
