from bs4 import BeautifulSoup

# FIX: Changed function name and arguments to match the spider's requirement
def run_audit(response, audit_level):
    """
    Checks for the presence and correctness of the canonical tag.
    
    The check compares the canonical URL found on the page against the page's actual URL.
    """
    soup = BeautifulSoup(response.text, "lxml")
    canonical_url = None
    canonical_mismatch = False

    # 1. Find the canonical link tag in the head
    canonical_tag = soup.find('link', rel='canonical')

    if canonical_tag:
        canonical_url = canonical_tag.get('href', None)
        
        if canonical_url:
            # Clean and normalize URLs before comparison
            # The response.url is the URL Scrapy crawled
            crawled_url = response.url.split('#')[0].rstrip('/')
            
            # The canonical URL from the tag
            tag_url = canonical_url.split('#')[0].rstrip('/')
            
            # Check for mismatch between the URL crawled and the canonical tag's target
            if crawled_url != tag_url:
                canonical_mismatch = True

    # Check for cases where a page should likely have a canonical tag but doesn't
    # In a real system, you might flag non-canonical URLs (e.g., filtered results) here.
    # For now, we simply report its presence and match status.
    
    # The audit_level argument is mandatory but not used in this specific check.
    return {
        "canonical_url": canonical_url,
        "canonical_mismatch": canonical_mismatch,
        "canonical_check": "FAIL" if canonical_mismatch or not canonical_url else "PASS",
        "note": "Canonical tag should point to the preferred, indexable version of the page (usually itself)."
    }
    
