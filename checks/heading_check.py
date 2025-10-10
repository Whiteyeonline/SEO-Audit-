from bs4 import BeautifulSoup

# FIX: Changed function name and arguments to match the spider's requirement
def run_audit(response, audit_level):
    """
    Checks for H1 tag presence and count (should be exactly one).
    Also checks for missing H2 and H3 tags.
    """
    # Use response.text to get the HTML content
    soup = BeautifulSoup(response.text, "lxml")
    
    # 1. H1 Check
    h1_tags = soup.find_all('h1')
    h1_count = len(h1_tags)
    h1_fail = False
    
    if h1_count == 0:
        h1_fail = True
        h1_message = "MISSING: Page has no H1 tag."
    elif h1_count > 1:
        h1_fail = True
        h1_message = f"FAIL: Page has {h1_count} H1 tags (should be only one)."
    else:
        h1_message = "PASS: Page has exactly one H1 tag."

    # 2. H2 and H3 presence check (basic level)
    h2_present = len(soup.find_all('h2')) > 0
    h3_present = len(soup.find_all('h3')) > 0
    
    # Simple check for skipping major levels
    skipped_levels = False
    if h1_count > 0 and not h2_present and h3_present:
        skipped_levels = True

    # The audit_level argument is mandatory but not used in this specific check.
    return {
        "h1_count": h1_count,
        "h1_fail": h1_fail,
        "h1_status": h1_message,
        "h2_present": h2_present,
        "h3_present": h3_present,
        "skipped_major_level": skipped_levels,
        "note": "Best practice is exactly one H1 and sequential use of H2, H3, etc."
    }
    
