# checks/mobile_friendly_check.py

from bs4 import BeautifulSoup

def run_audit(response, audit_level):
    """
    Checks if the page is mobile-friendly by verifying the presence
    of responsive meta viewport and mobile-optimized structure.
    This version matches perfectly with report_writer.py.
    """

    try:
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to parse content for mobile-friendly check: {str(e)}"}

    issues = []
    has_viewport = False

    # 1️⃣ Check for viewport tag (most critical)
    viewport_tag = soup.find("meta", attrs={"name": "viewport"})
    if viewport_tag and "width=device-width" in viewport_tag.get("content", "").lower():
        has_viewport = True
    else:
        issues.append("Missing or incorrect <meta name='viewport'> tag")

    # 2️⃣ Optional check for responsive layout indicators
    # (like media queries or bootstrap responsive meta tags)
    style_tags = soup.find_all("style")
    responsive_found = any("@media" in s.get_text().lower() for s in style_tags)
    if not responsive_found:
        issues.append("No responsive CSS detected (@media rules missing)")

    # 3️⃣ Build note and return
    if has_viewport and responsive_found:
        note = "PASS: Page appears mobile-friendly."
    else:
        note = "FAIL: Page not optimized for mobile or missing responsive tags."

    return {
        "mobile_friendly": has_viewport and responsive_found,
        "issues": issues,
        "note": note
    }
