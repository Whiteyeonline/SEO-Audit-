# checks/og_tags_check.py
from bs4 import BeautifulSoup

def run_audit(response, audit_level):
    """
    Checks for the presence of Open Graph (OG) and Twitter Card tags.
    """
    try:
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to parse content for OG tag check: {str(e)}"}
        
    og_tags = {}
    
    # CRITICAL FIX: Use 'property' and 'name' in a dictionary filter for robust tag finding.
    # The error was caused by passing multiple arguments incorrectly.
    required_og = ['og:title', 'og:description', 'og:type', 'og:url', 'og:image']
    required_twitter = ['twitter:card', 'twitter:title', 'twitter:description', 'twitter:image']
    
    all_tags = []
    
    # 1. Find Open Graph tags
    all_tags.extend(soup.find_all('meta', property=lambda x: x and x.startswith('og:')))
    
    # 2. Find Twitter tags
    all_tags.extend(soup.find_all('meta', name=lambda x: x and x.startswith('twitter:')))

    for tag in all_tags:
        # Prioritize 'property' for OG tags, fallback to 'name' for Twitter tags
        key = tag.get('property') or tag.get('name')
        content = tag.get('content')
        if key and content:
            og_tags[key] = content

    # 3. Validation Logic
    missing_og = [tag for tag in required_og if tag not in og_tags]
    missing_twitter = [tag for tag in required_twitter if tag not in og_tags]
    
    # Combine failures for aggregation
    og_tags_fail_count = len(missing_og) + len(missing_twitter)
    
    if og_tags_fail_count == 0:
        status = "PASS"
        note = "All critical Open Graph and Twitter Card tags are present."
    elif og_tags_fail_count < 3:
        status = "INFO"
        note = "Some key social tags are missing. Review missing tags for better social sharing."
    else:
        status = "FAIL"
        note = "Major failure: Most critical Open Graph or Twitter Card tags are missing or malformed."

    return {
        "status": status,
        "og_tags_present": bool(og_tags),
        "missing_og_tags": missing_og,
        "missing_twitter_tags": missing_twitter,
        "og_tags_fail_count": og_tags_fail_count,
        "note": note
    }
    
