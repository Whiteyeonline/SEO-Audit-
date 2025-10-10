import requests
from urllib.parse import urlparse

# FIX: Changed function name and arguments to match the spider's requirement
def run_audit(response, audit_level):
    """
    Checks for the presence of /robots.txt and /sitemap.xml using a separate 
    requests call, as these files are not part of the current page's HTML.
    """
    
    # Get the base domain from the current URL
    parsed_url = urlparse(response.url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    robots_url = f"{base_url}/robots.txt"
    sitemap_url = f"{base_url}/sitemap.xml"
    
    # --- Robots.txt Check ---
    try:
        r_status = "found" if requests.get(robots_url, timeout=5).status_code == 200 else "not found"
    except: 
        r_status = "not found"
        
    # --- Sitemap.xml Check ---
    try:
        s_status = "found" if requests.get(sitemap_url, timeout=5).status_code == 200 else "not found"
    except: 
        s_status = "not found"
        
    # The audit_level argument is mandatory but not used in this specific check.
    return {
        "robots.txt_status": r_status, 
        "sitemap.xml_status": s_status,
        "robots_sitemap_fail_count": (1 if r_status == 'not found' else 0) + (1 if s_status == 'not found' else 0),
        "note": "Both files are crucial for search engine communication and crawl efficiency."
        }
    
