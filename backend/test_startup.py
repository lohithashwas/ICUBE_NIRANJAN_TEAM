try:
    print("Importing IMD...")
    from collectors.imd_collector import IMDCollector
    i = IMDCollector()
    print("IMD Init OK")

    print("Importing CWC...")
    from collectors.cwc_collector import CWCCollector
    c = CWCCollector()
    print("CWC Init OK")

    print("Importing ISRO...")
    from collectors.isro_collector import ISROCollector
    s = ISROCollector()
    print("ISRO Init OK")

    print("Importing SAFAR...")
    from collectors.safar_collector import SAFARCollector
    sa = SAFARCollector()
    print("SAFAR Init OK")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
