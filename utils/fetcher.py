import requests
import validators

def fetch_html(url):
    """Fetch HTML content from a URL."""
    if not validators.url(url):
        # Using 400 for a local client/URL validation failure
        return None, 400 
    try:
        r = requests.get(url, timeout=15) # Increased timeout for slow sites
        r.raise_for_status()
        return r.text, r.status_code
    except requests.exceptions.HTTPError as e:
        # Returns 4xx or 5xx code (e.g., 404, 500)
        return None, e.response.status_code
    except requests.exceptions.ConnectionError:
        # Using a custom status code (0) for network/DNS/timeout failures
        return None, 0 
    except requests.exceptions.Timeout:
        return None, 0
    except Exception:
        return None, 0
        
