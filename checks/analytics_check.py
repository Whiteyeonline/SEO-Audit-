import re
from bs4 import BeautifulSoup

def run(url, html_content):
    """
    Detects the presence of common Google Analytics and Google Tag Manager scripts.
    """
    soup = BeautifulSoup(html_content, "lxml")
    
    tracking = {
        "google_analytics_found": False,
        "google_tag_manager_found": False,
        "other_analytics_found": False,
    }
    
    scripts = soup.find_all("script")
    
    for script in scripts:
        # Check for Google Tag Manager (GTM)
        if script.get("src") and "gtm.js" in script.get("src"):
            tracking["google_tag_manager_found"] = True
        
        # Check for Google Analytics (UA- or G- tracking ID)
        if script.string:
            # Universal Analytics (UA-XXXXX) or Google Analytics 4 (G-XXXXX)
            if re.search(r'UA-\d{4,9}-\d{1,4}|G-[A-Z0-9]{8}', script.string):
                tracking["google_analytics_found"] = True
            
            # Simple check for other common third-party scripts (e.g., Facebook Pixel)
            if "fbq" in script.string or "pixel" in script.string:
                 tracking["other_analytics_found"] = True
            
    return {
        "tracking_setup": tracking,
        "note": "Tracking detection is static (HTML only). Event tracking cannot be verified."
                }
    
