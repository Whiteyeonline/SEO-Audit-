# In checks/link_check.py

import requests # <--- MUST be imported for this check
from bs4 import BeautifulSoup

def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    links = [a.get("href") for a in soup.find_all("a", href=True)]
    broken = []
    
    # --- UNCOMMENT THIS BLOCK TO RE-ENABLE THE LIVE CHECK ---
    for link in links:
        if not link.startswith("http"):
            continue
        try:
            # Set a low timeout (e.g., 5 seconds) to prevent total deadlock
            r = requests.head(link, allow_redirects=True, timeout=5)
            # Only flag hard failures (4xx/5xx)
            if r.status_code >= 400:
                broken.append(link)
        except:
            # Catch timeouts and connection errors as broken
            broken.append(link)
    # --- END UNCOMMENTED BLOCK ---
            
    return {
        "total": len(links), 
        "broken": broken,
        # Update the note to reflect the check is now active
        "note": "Live broken link check is ACTIVE but may cause long audit times or failures."
    }
    
