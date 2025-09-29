from bs4 import BeautifulSoup
import re

def run(url, html_content):
    """
    Performs basic Local SEO checks: NAP consistency and GMB integration proxy.
    """
    soup = BeautifulSoup(html_content, "lxml")
    
    # 1. NAP (Name, Address, Phone) Proxy Detection
    # Look for common patterns. This is a simple proxy, not a full NAP validator.
    nap_data = {
        "phone_format_found": False,
        "address_keywords_found": False,
        "gmb_link_found": False,
    }

    # Phone Number Pattern (Basic: at least 7 digits, common separators)
    # Note: Using content_quality.py's text to search for general text info
    text = soup.get_text(separator=' ', strip=True)
    if re.search(r'\(\d{3}\)\s*\d{3}-\d{4}|\d{3}\s*\d{3}\s*\d{4}|\d{7,10}', text):
        nap_data["phone_format_found"] = True
    
    # Address Keywords (P.O. boxes, Street, City, State, Zip)
    address_keywords = r'street|avenue|road|st\b|ave\b|rd\b|city|state|zip|post\s*code|p\.o\.\s*box'
    if re.search(address_keywords, text, re.IGNORECASE):
        nap_data["address_keywords_found"] = True

    # 2. Google My Business (GMB) Integration Proxy
    # Look for Google Maps iframe or link
    if soup.find("iframe", src=re.compile(r'maps\.google\.com|google\.com/maps')):
        nap_data["gmb_link_found"] = True
    
    return {
        "status": "pass",
        "nap_found": nap_data,
        "note": "Local SEO check is a simple proxy for NAP format and GMB map integration."
  }
  
