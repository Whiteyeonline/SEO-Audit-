import requests
import time

def run(url, html_content=None):
    try:
        start = time.time()
        r = requests.get(url, timeout=10)
        load_ms = int((time.time() - start)*1000)
        return {"load_time_ms": load_ms}
    except:
        return {"error": "Unable to measure performance"}
