import requests
import validators

def fetch_html(url):
    """Fetch HTML content from a URL."""
    if not validators.url(url):
        return None, "Invalid URL"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text, r.status_code
    except Exception as e:
        return None, str(e)
