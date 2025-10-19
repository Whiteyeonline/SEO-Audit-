# checks/og_tags_check.py

from bs4 import BeautifulSoup

def run_audit(response, audit_level):
    """
    Checks for essential Open Graph (OG) meta tags.
    Works seamlessly with report_writer.py formatting.
    """

    try:
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to parse content for OG tags check: {str(e)}"}

    required_tags = ["og:title", "og:description", "og:image", "og:url"]
    missing_tags = []

    for tag in required_tags:
        if not soup.find("meta", property=tag):
            missing_tags.append(tag)

    og_tags_missing = len(missing_tags) > 0

    if og_tags_missing:
        note = f"FAIL: Missing OG tags: {', '.join(missing_tags)}"
    else:
        note = "PASS: All essential OG tags present."

    return {
        "og_tags_missing": og_tags_missing,
        "missing_tags_list": missing_tags,
        "note": note
    }
