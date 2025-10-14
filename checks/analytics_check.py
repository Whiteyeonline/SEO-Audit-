# checks/analytics_check.py
import re
from bs4 import BeautifulSoup

# Regex to find Google Analytics (UA- or G-) and Google Tag Manager (GTM-) IDs
GA_RE = re.compile(r'UA-\d{4,9}-\d{1,4}|G-[A-Z0-9]{8}')
GTM_RE = re.compile(r'GTM-[A-Z0-9]{5,7}')

def run_audit(response, audit_level):
    """
    Detects the presence of common Google Analytics and Google Tag Manager scripts
    using the fully rendered HTML provided by the Spider (Scrapy-Playwright).
    """
    try:
        # 💡 FIX: Use response.body for robust, encoding-safe parsing of the rendered HTML
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to parse content for analytics check: {str(e)}"}
    
    tracking = {
        "google_analytics_found": False,
        "google_tag_manager_found": False,
        "other_analytics_found": False,
        "ga_id": None,
        "gtm_id": None
    }
    
    # Check all <script> tags for GTM/GA codes
    for script in soup.find_all("script"):
        
        # 1. Check for GTM by src attribute
        src = script.get("src", "")
        if "gtm.js" in src:
            match = GTM_RE.search(src)
            if match:
                tracking["google_tag_manager_found"] = True
                tracking["gtm_id"] = match.group(0)
            
        # 2. Check for GA/GTM/Other in the script content
        script_content = script.string if script.string else ""
        
        # Check for Google Analytics ID (UA- or G-)
        if not tracking["google_analytics_found"]:
            match = GA_RE.search(script_content)
            if match:
                tracking["google_analytics_found"] = True
                tracking["ga_id"] = match.group(0)
            
        # Check for Google Tag Manager ID in dataLayer initialization
        if not tracking["google_tag_manager_found"]:
            match = GTM_RE.search(script_content)
            if match:
                tracking["google_tag_manager_found"] = True
                tracking["gtm_id"] = match.group(0)

        # Check for other common third-party scripts (e.g., Facebook Pixel, Hotjar)
        if "fbq" in script_content or "_hj" in script_content:
             tracking["other_analytics_found"] = True
            
    
    # Final Note
    if tracking["google_analytics_found"] or tracking["google_tag_manager_found"]:
        note = "PASS: Tracking detected. GTM or GA code is present. Event tracking cannot be verified."
    else:
        note = "FAIL: No Google Analytics or Google Tag Manager code detected. Tracking may be missing."
        
    return {
        "tracking_setup": tracking,
        "analytics_missing": not (tracking["google_analytics_found"] or tracking["google_tag_manager_found"]),
        "note": note
    }
    
