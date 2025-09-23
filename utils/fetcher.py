import requests
import validators

def fetch_html(url):
    try:
        if not validators.url(url):
            print(f"Invalid URL: {url}")
            return None
        r = requests.get(url, timeout=10)
        r.raise_for_status() # Raises an HTTPError for bad responses
        return r.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None
      
