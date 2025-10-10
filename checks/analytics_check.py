import re
from bs4 import BeautifulSoup

# FIX: Changed function name and arguments to match the spider's requirement
def run_audit(response, audit_level):
    """
    Detects the presence of common Google Analytics and Google Tag Manager scripts
    using the Scrapy response object.
    """
    # Use response.text to get the HTML content
    soup = BeautifulSoup(response.text, "lxml")
    
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
            
    # The audit_level argument is mandatory but not used in this specific check.
    return {
        "tracking_setup": tracking,
        "analytics_missing": not (tracking["google_analytics_found"] or tracking["google_tag_manager_found"]),
        "note": "Tracking detection is static (HTML only). Event tracking cannot be verified."
    }
    
