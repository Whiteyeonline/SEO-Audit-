import requests
import validators
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def fetch_html(url):
    """
    Fetch HTML content with retries and return status code.
    """
    if not validators.url(url):
        print(f"[Error] Invalid URL: {url}")
        return {"html": None, "status_code": None}

    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500,502,503,504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return {"html": response.text, "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        print(f"[Error] Failed to fetch {url}: {e}")
        return {"html": None, "status_code": None}
