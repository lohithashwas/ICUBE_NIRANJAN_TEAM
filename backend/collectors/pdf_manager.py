import requests
# from pdf2image import convert_from_path
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PDFManager:
    def __init__(self, storage_dir="assets/images"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs("temp_pdfs", exist_ok=True)

    def download_pdf(self, url: str, filename: str) -> str:
        """Downloads a PDF from a URL."""
        try:
            response = requests.get(url, verify=False, timeout=30)
            response.raise_for_status()
            pdf_path = os.path.join("temp_pdfs", f"{filename}.pdf")
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Downloaded PDF: {url}")
            return pdf_path
        except Exception as e:
            logger.error(f"Failed to download PDF {url}: {e}")
            return None

    def convert_to_images(self, pdf_path: str, base_filename: str):
        """Converts PDF to images and saves them."""
        if not pdf_path:
            return []
        
        try:
            # Import here to avoid top-level crash if library/poppler is missing
            from pdf2image import convert_from_path
        except ImportError:
            logger.warning("pdf2image module not found. Skipping conversion.")
            return []
        except Exception as e:
            logger.warning(f"pdf2image import failed (likely missing Poppler): {e}")
            return []

        try:
            # Poppler path might need configuration on Windows if not in PATH
            # Assuming it's in a standard location or PATH for now
            images = convert_from_path(pdf_path)
            saved_paths = []
            
            for i, image in enumerate(images):
                # Save as timestamped file to avoid caching issues
                timestamp = int(datetime.now().timestamp())
                image_name = f"{base_filename}_page_{i+1}_{timestamp}.png"
                image_path = os.path.join(self.storage_dir, image_name)
                image.save(image_path, "PNG")
                saved_paths.append(f"/assets/images/{image_name}")
            
            return saved_paths
        except Exception as e:
            logger.error(f"Failed to convert PDF {pdf_path}: {e}")
            return []
        finally:
            # Cleanup PDF
            if os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except:
                    pass

try:
    pdf_manager = PDFManager()
except Exception as e:
    print(f"PDFManager Instantiation Failed: {e}")
    pdf_manager = None
