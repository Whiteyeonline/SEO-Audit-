# checks/canonical_check.py
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse

def _get_soup(response):
    """
    Creates a BeautifulSoup object from the response body.
    NOTE: When the spider uses Playwright, response.body contains the 
    fully JavaScript-rendered content, making this check robust for 
    all page types (static, dynamic, JS-driven).
    """
    # Use 'lxml' for speed and response.text (or response.body) for content
    return BeautifulSoup(response.body, "lxml", from_encoding="utf-8")


def _clean_url(url):
    """
    Strips protocol, www, query, and fragments for a clean comparison.
    """
    if not url:
        return None
        
    url = url.lower()
    parsed = urlparse(url)
    
    # Remove fragments and queries for the comparison
    cleaned_url = urlunparse(parsed._replace(fragment='', query=''))
    
    # Strip protocol, www, and trailing slash for a true canonical comparison
    cleaned_url = cleaned_url.replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
    
    return cleaned_url

def run_audit(response, audit_level):
    """
    Runs the Canonical Check against the fully rendered HTML provided by the Spider.
    """
    try:
        soup = _get_soup(response)
    except Exception as e:
        return {"error": f"Failed to parse content for canonical check: {str(e)}"}


    current_url = response.url
    # Find the canonical tag using a CSS selector for robustness
    canonical_tag = soup.find('link', rel='canonical')
    canonical_url = canonical_tag.get('href') if canonical_tag and canonical_tag.get('href') else None
    
    amphtml_tag = soup.find('link', rel='amphtml')
    amphtml_url = amphtml_tag.get('href') if amphtml_tag and amphtml_tag.get('href') else None
    
    is_amp_page = '/amp/' in current_url.lower()
    canonical_mismatch = False
    note = "PASS: No canonical tag found, but this is acceptable only if the page has no duplicate content risk."

    # --- Canonical Comparison Logic ---
    if canonical_url:
        normalized_current = _clean_url(current_url)
        normalized_canonical = _clean_url(canonical_url)
        
        # Check for absolute URL format
        if not urlparse(canonical_url).netloc:
             canonical_mismatch = True
             note = f"FAIL: Canonical tag must use an absolute URL (e.g., must include 'http/https'). Found: '{canonical_url}'."
        elif normalized_current != normalized_canonical:
            # Check for standard mismatch
            canonical_mismatch = True
            note = f"FAIL: Canonical tag points to a different URL: '{canonical_url}'. This indicates duplication or a rel=canonical implementation error."
            
            # Special case: AMP to non-AMP is a *passing* mismatch
            if is_amp_page and '/amp/' not in canonical_url.lower():
                canonical_mismatch = False
                note = f"PASS: AMP page correctly canonicalizes to non-AMP URL: '{canonical_url}'."
        
        else:
            note = f"PASS: Canonical tag correctly points to the page itself: '{canonical_url}'."
            
    else:
        # If no canonical URL is present
        canonical_mismatch = True
        note = "FAIL: No <link rel='canonical'> tag found. This is necessary for pages with filtering/sorting or where duplicate content is possible."
        
    # --- AMPhtml Link Check ---
    amphtml_note = ""
    if amphtml_url and not is_amp_page:
        amphtml_note = f" | INFO: Found <link rel='amphtml'> pointing to AMP version: '{amphtml_url}'."
    elif not amphtml_url and is_amp_page:
        amphtml_note = " | WARNING: AMP page detected, but no `rel='canonical'` back to the non-AMP page was found."
    
    return {
        "canonical_url": canonical_url,
        "current_url": current_url,
        "is_amp_page": is_amp_page,
        "canonical_mismatch": canonical_mismatch,
        "amphtml_url": amphtml_url,
        "note": f"{note}{amphtml_note}"
            }
        
