import requests
from bs4 import BeautifulSoup
from .pdf_manager import pdf_manager
import logging

logger = logging.getLogger(__name__)

class CWCCollector:
    def __init__(self):
        self.base_url = "http://cewacor.nic.in"
        # CWC Bulletins page (example ID, might need updating)
        self.bulletin_url = "http://cewacor.nic.in/index2.php?lang=1&sublinkid=1130&linkid=1174&lid=754" 
        # Better robust link for Flood Forecast
        self.flood_url = "https://ffms.mowr.gov.in/" 

    def fetch_data(self):
        """Scrapes CWC website for the latest flood situation report using dynamic date."""
        try:
            logger.info("Fetching CWC data...")
            
            # Strategy: Generate URL for Today and Yesterday
            # Pattern: https://cwc.gov.in/en/daily-flood-bulletin-report-dated-[DD][MM][YYYY]
            # PDF Pattern: https://cwc.gov.in/yoursites/default/files/cfcrcwcdfb[DD]-[MM]-[YYYY].pdf
            # Note: The 'yoursites/default/files' part can be tricky, so better to hit the page first.
            
            from datetime import datetime, timedelta
            
            dates_to_try = [datetime.now(), datetime.now() - timedelta(days=1)]
            
            found_data = None
            
            for date_obj in dates_to_try:
                date_str = date_obj.strftime("%d%m%Y")
                report_page_url = f"https://cwc.gov.in/en/daily-flood-bulletin-report-dated-{date_str}"
                
                logger.info(f"Checking CWC Report Page: {report_page_url}")
                try:
                    res = requests.get(report_page_url, verify=False, timeout=10)
                    if res.status_code == 200:
                        soup = BeautifulSoup(res.content, 'html.parser')
                        # Find PDF link in this page
                        pdf_link = None
                        for a in soup.find_all('a', href=True):
                            if '.pdf' in a['href'].lower():
                                pdf_link = a['href']
                                break
                        
                        if pdf_link:
                             found_data = (pdf_link, date_str)
                             break # Found the latest available
                except Exception as e:
                    logger.warning(f"Failed to check CWC URL {report_page_url}: {e}")
                    continue

            if found_data:
                pdf_link, date_str = found_data
                if not pdf_link.startswith('http'):
                     # CWC relative links can be messy, usually relative to domain root
                     pdf_link = "https://cwc.gov.in" + pdf_link if pdf_link.startswith('/') else "https://cwc.gov.in/" + pdf_link

                logger.info(f"Found Verified CWC PDF: {pdf_link}")
                pdf_path = pdf_manager.download_pdf(pdf_link, f"cwc_flood_{date_str}")
                
                if pdf_path:
                    images = pdf_manager.convert_to_images(pdf_path, "cwc_flood")
                    return {
                        "source": "CWC",
                        "type": "flood_report",
                        "images": images,
                        "original_pdf": pdf_link,
                        "date": date_str
                    }
            
            return {"error": "No recent CWC reports found."}

        except Exception as e:
            logger.error(f"CWC Collection failed: {e}")
            return {"error": str(e)}
