# checks/mobile_friendly_check.py
from bs4 import BeautifulSoup
import re

def run_audit(response, audit_level):
    """
    Checks for the presence and correct definition of the viewport meta tag, 
    the core requirement for mobile-friendliness.
    
    This check uses the fully rendered HTML provided by the Spider (Scrapy-Playwright).
    """
    try:
        # Use response.body for robust, encoding-safe parsing of the rendered HTML
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to parse content for mobile check: {str(e)}"}
    
    viewport = soup.find("meta", attrs={"name": "viewport"})
    issues = []
    
    # Critical Check: Presence of the tag
    if not viewport:
        issues.append("ERROR: Missing viewport meta tag.")
    else:
        content = viewport.get("content", "").lower()
        
        # 1. Check for width=device-width (Most Critical)
        if "width=device-width" not in content.replace(" ", ""):
            issues.append("ERROR: Viewport meta does not define 'width=device-width'.")
        
        # 2. Check for initial-scale (Highly Recommended)
        if "initial-scale" not in content.replace(" ", ""):
            issues.append("WARNING: Viewport meta missing 'initial-scale' definition.")
            
        # 3. Check for disabling user scaling (Bad Practice)
        if re.search(r'user-scalable\s*=\s*no', content.replace(" ", "")):
            issues.append("WARNING: `user-scalable=no` found. This is bad for accessibility.")


    is_mobile_friendly = (len(issues) == 0)

    note = "PASS: Viewport meta tag is correctly defined."
    if not is_mobile_friendly:
        note = "FAIL: Missing or incorrect viewport configuration. Critical for mobile-first indexing."

    return {
        "viewport_content": viewport.get("content") if viewport else "MISSING",
        "is_mobile_friendly": is_mobile_friendly,
        "mobile_unfriendly_count": 0 if is_mobile_friendly else 1,
        "issues_list": issues,
        "note": note
        }
    
