# checks/mobile_friendly_check.py

from bs4 import BeautifulSoup

def run_audit(response, audit_level):
    """
    Simple mobile-friendliness check:
    - Looks for viewport meta tag
    - Checks if 'width=device-width' is defined
    """
    # Use response.text to get the HTML content
    # Note: Use lxml for speed if available, or 'html.parser' for robust standard parsing.
    soup = BeautifulSoup(response.text, "lxml")
    
    # Check for viewport meta tag case-insensitively
    viewport = soup.find("meta", attrs={"name": "viewport"})
    issues = []

    # Check 1: Is the viewport tag present?
    if not viewport:
        issues.append("Missing viewport meta tag")
    else:
        content = viewport.get("content", "").lower()
        
        # Check 2: Does the content include width=device-width?
        if "width=device-width" not in content:
            issues.append("Viewport meta does not define width=device-width")
        
        # Check 3: Does the content include initial-scale? (Common best practice)
        if "initial-scale" not in content:
            issues.append("Viewport meta missing 'initial-scale' definition.")

    is_mobile_friendly = (len(issues) == 0)

    # Note: The original report said 'Mobile-Friendly Status: NOT FRIENDLY. Viewport Tag: False'
    # The JSON's 'mobile_friendly': true is likely an error in the audit pipeline's aggregation.
    
    return {
        "mobile_friendly": is_mobile_friendly,
        # Set count to 1 if not friendly, 0 otherwise, to match aggregated_issues structure
        "mobile_unfriendly_count": 0 if is_mobile_friendly else 1, 
        "issues": issues,
        "note": "Basic check for mobile-friendliness using viewport meta tag. Requires 'width=device-width'."
            }
    
