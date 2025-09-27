from bs4 import BeautifulSoup
from urllib.parse import urlparse

def run(url, html_content):
    """Checks for the presence and matching of the canonical tag."""
    soup = BeautifulSoup(html_content, "lxml")
    canonical = soup.find("link", rel="canonical")
    c_url = canonical.get("href") if canonical else None
    
    # Simple check for match, ignoring fragments and case (mostly)
    url_normalized = urlparse(url)._replace(query="", fragment="").geturl().strip('/')
    c_url_normalized = urlparse(c_url)._replace(query="", fragment="").geturl().strip('/') if c_url else None
    
    return {
        "canonical_url": c_url, 
        "match": (c_url_normalized == url_normalized) if c_url else False,
        "note": "Canonical check only verifies the tag's existence and if it matches the audited URL."
    }
    
