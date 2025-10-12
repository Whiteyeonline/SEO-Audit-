# checks/canonical_check.py
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse

def _clean_url(url):
    """
    Strips common tracking parameters and fragments from a URL for clean comparison.
    Converts to lowercase and removes trailing slash.
    """
    if not url:
        return url
        
    # Strip protocol, www, and convert to lowercase for comparison
    url = url.lower().replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
    
    # Remove fragment and query for comparison
    parsed = urlparse(url)
    cleaned_url = urlunparse(parsed._replace(fragment='', query=''))
    
    return cleaned_url

def run_audit(response, audit_level):
    """
    Runs the Canonical Check:
    1. Checks for <link rel="canonical"> tag.
    2. Compares the canonical URL against the current page URL, handling AMP logic.
    """
    
    # Use response.content for robust parsing and explicitly set parser.
    # We must use response.text or response.body for BeautifulSoup parsing, depending on input.
    # response.content is better as it's the raw body (bytes) which helps with encoding.
    try:
        # Use response.body instead of response.content if response.content is causing issues
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
    except Exception as e:
        return {
            "canonical_url": None,
            "current_url": response.url,
            "is_amp_page": 'amp' in response.url.lower(),
            "canonical_mismatch": True,
            "amphtml_url": None,
            "note": f"ERROR: Failed to parse page content. Exception: {str(e)}",
            "error": f"Unhandled exception during check: {str(e)}"
        }
    
    current_url = response.url
    
    # --- 1. Get Canonical URL ---
    canonical_tag = soup.find('link', rel='canonical')
    canonical_url = canonical_tag.get('href') if canonical_tag and canonical_tag.get('href') else None
    
    # --- 2. Get AMP HTML URL (for non-AMP pages) ---
    amphtml_tag = soup.find('link', rel='amphtml')
    amphtml_url = amphtml_tag.get('href') if amphtml_tag and amphtml_tag.get('href') else None
    
    # --- Analysis Flags ---
    is_amp_page = '/amp/' in current_url.lower() # A more specific check for AMP in the URL
    canonical_mismatch = False
    note = "PASS: Canonical tag correctly points to the current page or is not necessary."

    # --- Canonical Comparison Logic ---
    if canonical_url:
        
        # --- Normalization ---
        # Use the utility function for clean and robust comparison
        normalized_current = _clean_url(current_url)
        normalized_canonical = _clean_url(canonical_url)
        
        # --- Core Comparison ---
        if normalized_current != normalized_canonical:
            canonical_mismatch = True
            note = f"FAIL: Canonical tag points to a different URL: '{canonical_url}'."
            
            # --- AMP Exception (This is a PASS case) ---
            # If we are on an AMP page, and the canonical is the non-AMP URL, it's a PASS.
            # We specifically look for the canonical URL NOT containing '/amp/'
            if is_amp_page and '/amp/' not in canonical_url.lower():
                canonical_mismatch = False
                note = f"PASS: AMP page correctly canonicalizes to non-AMP URL: '{canonical_url}'."
        
        else:
            note = f"PASS: Canonical tag correctly points to the page itself: '{canonical_url}'."
            
    else:
        # No canonical tag found
        canonical_mismatch = True
        note = "FAIL: No <link rel='canonical'> tag found. This is necessary for pages with filtering/sorting or where duplicate content is possible."
        

    # --- AMPhtml Link Check (only matters for non-AMP pages) ---
    amphtml_note = ""
    # The current URL is an AMP page, so the amphtml tag isn't strictly necessary, but can exist.
    if amphtml_url and not is_amp_page:
        amphtml_note = f" | INFO: Found <link rel='amphtml'> pointing to AMP version: '{amphtml_url}'."
    elif not amphtml_url and not is_amp_page:
        amphtml_note = " | INFO: Non-AMP page missing <link rel='amphtml'>. Consider adding one if an AMP version exists."
    
    return {
        "canonical_url": canonical_url,
        "current_url": current_url,
        "is_amp_page": is_amp_page,
        "canonical_mismatch": canonical_mismatch,
        "amphtml_url": amphtml_url,
        "note": f"{note}{amphtml_note}"
    }

