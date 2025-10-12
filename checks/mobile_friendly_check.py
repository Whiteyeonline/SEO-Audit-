# checks/mobile_friendly_check.py
from bs4 import BeautifulSoup
import time # Added for demonstration of potential delay/fallback

# IMPORTANT: This is the same placeholder function as in canonical_check.py.
# You must ensure the environment implements the synchronous call to a headless browser.
def _get_rendered_html(url):
    """
    *** PLACEHOLDER FOR JAVASCRIPT RENDERING LOGIC ***
    
    In your actual environment, this function should:
    1. Launch a headless browser (e.g., Playwright's sync API).
    2. Navigate to the URL and wait for the page to load.
    3. Return the fully rendered HTML as a string.
    """
    print(f"INFO: Falling back to JS rendering for: {url}")
    time.sleep(1) 
    return None 

def _get_static_or_rendered_soup(response):
    """Tries static parsing, falls back to JS rendering if viewport tag is missing."""
    
    # 1. First Attempt: Static Parsing
    try:
        # Use response.text or body. Use 'html.parser' for robustness if 'lxml' is slow or fails
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
        
        # Check if viewport tag is present in the static HTML
        if soup.find("meta", attrs={"name": "viewport"}):
            return soup
        
    except Exception as e:
        print(f"WARN: Static parsing failed or viewport tag missing. Exception: {str(e)}")
        pass # Fall through to rendering
        
    # 2. Second Attempt: JS Rendering Fallback
    rendered_html = _get_rendered_html(response.url)
    
    if rendered_html:
        return BeautifulSoup(rendered_html, "lxml", from_encoding="utf-8")
        
    return BeautifulSoup("", "lxml") # Return empty soup if all fails


def run_audit(response, audit_level):
    """
    Simple mobile-friendliness check that falls back to JS rendering.
    """
    # Use the new helper to get the most complete content
    soup = _get_static_or_rendered_soup(response)
    
    viewport = soup.find("meta", attrs={"name": "viewport"})
    issues = []

    if not viewport:
        issues.append("Missing viewport meta tag (even after JS render attempt)")
    else:
        content = viewport.get("content", "").lower()
        
        if "width=device-width" not in content:
            issues.append("Viewport meta does not define width=device-width")
        
        if "initial-scale" not in content:
            issues.append("Viewport meta missing 'initial-scale' definition (best practice).")

    is_mobile_friendly = (len(issues) == 0)

    return {
        "mobile_friendly": is_mobile_friendly,
        "mobile_unfriendly_count": 0 if is_mobile_friendly else 1,
        "issues": issues,
        "note": "Basic check for mobile-friendliness using viewport meta tag, with JS fallback."
    }
    
