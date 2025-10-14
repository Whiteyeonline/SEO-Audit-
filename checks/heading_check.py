# checks/heading_check.py
from bs4 import BeautifulSoup

def run_audit(response, audit_level):
    """
    Checks for H1 tag presence and count (should be exactly one) and
    provides basic feedback on heading structure.
    
    This check uses the fully rendered HTML provided by the Spider (Scrapy-Playwright).
    """
    try:
        # Use response.body for robust, encoding-safe parsing of the rendered HTML
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to parse content for heading check: {str(e)}"}
    
    # 1. H1 Check
    h1_tags = soup.find_all('h1')
    h1_count = len(h1_tags)
    h1_fail = False
    
    # Extract the text content of the H1 tags for the report
    h1_content = [tag.get_text(strip=True) for tag in h1_tags]
    
    if h1_count == 0:
        h1_fail = True
        h1_status = "MISSING: Page has no H1 tag."
    elif h1_count > 1:
        h1_fail = True
        h1_status = f"FAIL: Page has {h1_count} H1 tags (should be only one)."
    else:
        h1_status = "PASS: Page has exactly one H1 tag."

    # 2. H2 and H3 presence check (basic structural level)
    h2_present = len(soup.find_all('h2')) > 0
    h3_present = len(soup.find_all('h3')) > 0
    
    # Simple check for skipping major levels (e.g., H1 -> H3 without H2)
    skipped_levels = False
    if h1_count > 0 and not h2_present and h3_present:
        skipped_levels = True

    note = "Best practice is exactly one H1 and sequential use of H2, H3, etc."
    if skipped_levels:
        note = "WARNING: Major heading level skipped (e.g., H1 to H3). Ensure semantic order (H1 -> H2 -> H3)."

    return {
        "h1_count": h1_count,
        "h1_fail": h1_fail,
        "h1_status": h1_status,
        "h1_content_list": h1_content, # Added for more detail in the report
        "h2_present": h2_present,
        "h3_present": h3_present,
        "skipped_major_level": skipped_levels,
        "note": note
        }
        
