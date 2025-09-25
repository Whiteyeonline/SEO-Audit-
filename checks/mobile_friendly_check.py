from bs4 import BeautifulSoup

def run(url, html_content):
    """
    Simple mobile-friendliness check:
    - Looks for viewport meta tag
    - Checks if 'width=device-width' is defined
    """
    soup = BeautifulSoup(html_content, "lxml")
    viewport = soup.find("meta", attrs={"name": "viewport"})
    issues = []

    if not viewport:
        issues.append("Missing viewport meta tag")
    elif "width=device-width" not in viewport.get("content", ""):
        issues.append("Viewport meta does not define width=device-width")

    is_mobile_friendly = (not issues)

    return {
        "mobile_friendly": is_mobile_friendly,
        "issues": issues,
        "note": "Basic check for mobile-friendliness using viewport meta tag."
    }
