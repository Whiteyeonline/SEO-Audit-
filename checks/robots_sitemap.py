# checks/robots_sitemap.py
import requests
from urllib.parse import urlparse

# FIX: Changed function name and arguments to match the spider's requirement
def run_audit(response, audit_level):
    """
    Checks for the presence of /robots.txt and /sitemap.xml using a separate 
    requests call, as these files are not part of the current page's HTML.
    
    This check relies on file existence and does not require HTML parsing.
    """
    
    # Get the base domain from the current URL
    parsed_url = urlparse(response.url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    robots_url = f"{base_url}/robots.txt"
    sitemap_url = f"{base_url}/sitemap.xml"
    
    # --- Robots.txt Check ---
    try:
        # Use HEAD request for speed, check for a 200 OK status
        r_status = "found" if requests.head(robots_url, timeout=5).status_code == 200 else "not found"
    except: 
        r_status = "error or timeout"
        
    # --- Sitemap.xml Check ---
    try:
        # Use HEAD request for speed, check for a 200 OK status
        s_status = "found" if requests.head(sitemap_url, timeout=5).status_code == 200 else "not found"
    except: 
        s_status = "error or timeout"
        
    # Calculate failure count
    fail_count = 0
    if r_status != 'found':
        fail_count += 1
    if s_status != 'found':
        fail_count += 1
        
    # The audit_level argument is mandatory but not used in this specific check.
    return {
        "robots.txt_status": r_status, 
        "sitemap.xml_status": s_status,
        "robots_sitemap_fail_count": fail_count,
        "note": "Both files are crucial for search engine communication and crawl efficiency. Ensure they are correctly configured."
    }
    
