# checks/canonical_check.py
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse

def _clean_url(url):
    """
    Strips common tracking parameters and fragments from a URL for clean comparison.
    """
    if not url:
        return url
        
    parsed = urlparse(url)
    # Reconstruct the URL without query or fragment for canonical comparison
    cleaned_url = urlunparse(parsed._replace(fragment='', query=''))
    return cleaned_url

def run_audit(response, audit_level):
    """
    Runs the Canonical Check:
    1. Checks for <link rel="canonical"> tag.
    2. Checks for <link rel="amphtml"> tag (on canonical pages).
    3. Compares the canonical URL against the current page URL, handling AMP logic.
    """
    
    # 💥 FIX FOR "bytes-like object is required" ERROR
    # Use response.content (bytes) for robust parsing and explicitly set the parser encoding
    try:
        # Use response.content and 'html.parser' (or 'lxml') with 'utf-8' encoding
        soup = BeautifulSoup(response.content, "lxml", from_encoding="utf-8")
    except Exception as e:
        # If parsing fails, return an error state immediately.
        return {
            "canonical_url": None,
            "current_url": response.url,
            "is_amp_page": 'amphtml' in response.url.lower(),
            "canonical_mismatch": True,
            "amphtml_url": None,
            "note": f"ERROR: Failed to parse page content for canonical check ({type(response.content).__name__}). Exception: {str(e)[:50]}...",
            "error": f"Unhandled exception during check: {str(e)}"
        }
    
    current_url = response.url
    
    # --- 1. Get Canonical URL ---
    canonical_tag = soup.find('link', rel='canonical')
    canonical_url = canonical_tag.get('href') if canonical_tag else None
    
    # --- 2. Get AMP HTML URL (for non-AMP pages) ---
    amphtml_tag = soup.find('link', rel='amphtml')
    amphtml_url = amphtml_tag.get('href') if amphtml_tag else None
    
    # --- Analysis Flags ---
    is_amp_page = 'amphtml' in current_url.lower()
    canonical_mismatch = False
    note = "PASS: Canonical tag correctly points to the current page or is not necessary."

    # --- Canonical Comparison Logic ---
    if canonical_url:
        # --- Normalization ---
        # Strip protocol, www, and trailing slash for robust comparison
        def normalize(url):
            url = url.lower().replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
            return url.split('#')[0].split('?')[0] # Remove fragment and query for comparison

        normalized_current = normalize(current_url)
        normalized_canonical = normalize(canonical_url)
        
        # --- Core Comparison ---
        if normalized_current != normalized_canonical:
            canonical_mismatch = True
            note = f"FAIL: Canonical tag points to a different URL: '{canonical_url}'."
            
            # --- AMP Exception (This is a PASS case) ---
            # If we are on an AMP page and the canonical is the non-AMP URL (which is different), it's a PASS.
            if is_amp_page and ('amphtml' in current_url.lower() and 'amphtml' not in canonical_url.lower()):
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
    if amphtml_url and not is_amp_page:
        amphtml_note = f" | PASS: Found <link rel='amphtml'> pointing to AMP version: '{amphtml_url}'."
    elif not amphtml_url and is_amp_page:
        amphtml_note = f" | INFO: AMP page detected. Canonical should point to non-AMP version."
    
    return {
        "canonical_url": canonical_url,
        "current_url": current_url,
        "is_amp_page": is_amp_page,
        "canonical_mismatch": canonical_mismatch,
        "amphtml_url": amphtml_url,
        "note": f"{note}{amphtml_note}"
                }
    
