import sys
import os

print("Starting Debug")
try:
    print("Attempting to import pdf_manager...")
    from collectors.pdf_manager import PDFManager, pdf_manager
    print(f"PDFManager imported. Instance: {pdf_manager}")
    
    print("Attempting to import IMDCollector...")
    from collectors.imd_collector import IMDCollector
    print("IMDCollector imported.")
    
    print("Attempting to instantiate IMDCollector...")
    imd = IMDCollector()
    print("IMDCollector instantiated.")
    
except Exception as e:
    print(f"CRASH: {e}")
    import traceback
    traceback.print_exc()
