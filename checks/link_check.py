# In checks/link_check.py

import requests 
from bs4 import BeautifulSoup

# FIX: Changed function name and arguments to match the spider's requirement
def run_audit(response, audit_level):
    """
    Finds all links on the page and performs a live check on absolute links 
    (HTTP/HTTPS) to identify 4xx/5xx broken links.
    """
    # Use response.text to get the HTML content
    soup = BeautifulSoup(response.text, "lxml")
    
    # Extract all href attributes from <a> tags
    links = [a.get("href") for a in soup.find_all("a", href=True)]
    broken = []
    
    # Only perform the live check if the audit level is 'advanced' or 'standard'
    # 'basic' audits often skip this time-consuming check
    if audit_level in ['standard', 'advanced']:
        for link in links:
            # Only check absolute external links (must start with http)
            if not link.startswith("http"):
                continue
            
            try:
                # Set a low timeout (e.g., 5 seconds) to prevent total deadlock
                r = requests.head(link, allow_redirects=True, timeout=5)
                
                # Only flag hard failures (4xx/5xx)
                if r.status_code >= 400:
                    broken.append(link)
            except Exception:
                # Catch timeouts and connection errors as broken
                broken.append(link)
    
    # Extract one sample broken link for the report writer
    sample_broken_link = broken[0] if broken else 'N/A'
            
    return {
        "total_links_found": len(links), 
        "broken_link_count": len(broken),
        "sample_broken_link": sample_broken_link,
        "note": "Live broken link check is ACTIVE but may increase audit time."
            }
    
