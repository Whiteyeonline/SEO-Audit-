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
    # Reconstruct the URL without scheme, netloc, params, query, or fragment, 
    # to only compare the path (for relative canonicals) and clean up.
    # We strip the fragment (#anchor) and query (?param=value) for canonical comparison.
    cleaned_url = urlunparse(parsed._replace(fragment='', query=''))
    
    # Simple check for www. vs non-www and http vs https (often normalized by search engines)
    # The comparison logic below handles the full normalization needed for the check.
    return cleaned_url

def run_audit(response, audit_level):
    """
    Runs the Canonical Check:
    1. Checks for <link rel="canonical"> tag.
    2. Checks for <link rel="amphtml"> tag (on canonical pages).
    3. Compares the canonical URL against the current page URL.
    """
    soup = BeautifulSoup(response.text, "lxml")
    
    # --- 1. Get Canonical URL ---
    canonical_tag = soup.find('link', rel='canonical')
    canonical_url = canonical_tag.get('href') if canonical_tag else None
    
    # --- 2. Get AMP HTML URL (for non-AMP pages that have an AMP version) ---
    amphtml_tag = soup.find('link', rel='amphtml')
    amphtml_url = amphtml_tag.get('href') if amphtml_tag else None
    
    # --- 3. Get AMP Canonical URL (for AMP pages that link back to canonical) ---
    # AMP pages often include the attribute "html" instead of "canonical" on their canonical link
    amp_canonical_tag = soup.find('link', rel='canonical')
    # Use canonical_url found above, which will be the AMP page's canonical URL

    # The current URL being audited
    current_url = response.url

    # --- Analysis Flags ---
    is_amp_page = 'amphtml' in current_url.lower() or ('amp' in response.headers.get('Content-Type', '').lower())
    canonical_mismatch = False
    note = "PASS: Canonical tag correctly points to the current page or is not necessary."

    # --- Normalize Current URL for Comparison ---
    # Strip protocol for flexible comparison (e.g., http vs https)
    normalized_current_url = current_url.replace('https://', '').replace('http://', '').rstrip('/')
    
    if canonical_url:
        normalized_canonical_url = canonical_url.replace('https://', '').replace('http://', '').rstrip('/')
        
        # Remove "www." from both for flexibility in audit
        normalized_current_url = normalized_current_url.replace('www.', '')
        normalized_canonical_url = normalized_canonical_url.replace('www.', '')
        
        # --- 4. Core Canonical Comparison Logic ---
        if normalized_current_url != normalized_canonical_url:
            canonical_mismatch = True
            note = f"FAIL: Canonical tag points to a different URL: '{canonical_url}'. This indicates the current page is a duplicate version."
            
        else:
            note = f"PASS: Canonical tag correctly points to the page itself: '{canonical_url}'."
        
        # --- AMP Page Specific Check ---
        if is_amp_page:
            # On an AMP page, the canonical tag must point to the non-AMP version.
            # We must check if the current page URL (the AMP page) contains 'amp' but the canonical does not.
            if 'amp' in current_url.lower() and 'amp' not in canonical_url.lower() and canonical_mismatch:
                # This is actually a PASS: the AMP page correctly canonicalizes to the non-AMP page.
                canonical_mismatch = False
                note = f"PASS: AMP page correctly canonicalizes to non-AMP URL: '{canonical_url}'."
    else:
        # No canonical tag found
        canonical_mismatch = True
        note = "FAIL: No <link rel='canonical'> tag found. This page may be considered duplicate content if it has different URLs pointing to it."
        

    # --- 5. AMPhtml Link Check (only matters for non-AMP pages) ---
    amphtml_note = "INFO: No <link rel='amphtml'> tag found."
    if amphtml_url and not is_amp_page:
        amphtml_note = f"PASS: Found <link rel='amphtml'> pointing to AMP version: '{amphtml_url}'."
        
    return {
        "canonical_url": canonical_url,
        "current_url": current_url,
        "is_amp_page": is_amp_page,
        "canonical_mismatch": canonical_mismatch,
        "amphtml_url": amphtml_url,
        "note": f"{note} | {amphtml_note}"
    }
    
