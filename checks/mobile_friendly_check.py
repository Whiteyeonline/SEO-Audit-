from bs4 import BeautifulSoup

# FIX: Changed function name and arguments to match the spider's requirement
def run_audit(response, audit_level):
    """
    Simple mobile-friendliness check:
    - Looks for viewport meta tag
    - Checks if 'width=device-width' is defined
    
    The audit_level argument is mandatory but not used in this specific check.
    """
    # Use response.text to get the HTML content
    soup = BeautifulSoup(response.text, "lxml")
    
    viewport = soup.find("meta", attrs={"name": "viewport"})
    issues = []

    if not viewport:
        issues.append("Missing viewport meta tag")
    elif "width=device-width" not in viewport.get("content", ""):
        issues.append("Viewport meta does not define width=device-width")

    is_mobile_friendly = (not issues)

    return {
        "mobile_friendly": is_mobile_friendly,
        "mobile_unfriendly_count": 0 if is_mobile_friendly else 1,
        "issues": issues,
        "note": "Basic check for mobile-friendliness using viewport meta tag."
    }
    
