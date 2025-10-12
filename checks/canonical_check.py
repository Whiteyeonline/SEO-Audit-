# checks/canonical_check.py
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse
import time # Added for demonstration of potential delay/fallback

# IMPORTANT: You must implement this function outside of the check,
# or ensure your environment allows synchronous calls to a rendering tool.
# This function is a placeholder for your Playwright/Selenium implementation.
def _get_rendered_html(url):
    """
    *** PLACEHOLDER FOR JAVASCRIPT RENDERING LOGIC ***
    
    In your actual environment, this function should:
    1. Launch a headless browser (e.g., Playwright's sync API).
    2. Navigate to the URL and wait for the page to load.
    3. Return the fully rendered HTML as a string.
    
    For now, we'll simulate a success on the second attempt.
    """
    print(f"INFO: Falling back to JS rendering for: {url}")
    # Simulate a delay for rendering
    time.sleep(1) 
    
    # In a real environment, you would call Playwright/Selenium here:
    # return page.content() 
    
    # Since we can't run Playwright, we return the original, static content
    # assuming the *actual* issue was the parsing error you saw, and we fix it below.
    # In the real world, you'd be returning the rendered content here.
    return None # Return None to force the error handling below

def _get_static_or_rendered_soup(response):
    """Tries static parsing, falls back to JS rendering if canonical tag is missing."""
    
    # 1. First Attempt: Static Parsing
    try:
        # Use response.body (bytes) for most robust parsing
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
        
        # Check if canonical tag is present in the static HTML
        if soup.find('link', rel='canonical'):
            return soup
        
        # If no canonical tag is found, it might be injected by JS, proceed to fallback
    except Exception as e:
        # If static parsing fails (e.g., the original 'bytes-like object' error)
        print(f"WARN: Static parsing failed or tag missing. Exception: {str(e)}")
        pass # Fall through to rendering
        
    # 2. Second Attempt: JS Rendering Fallback
    rendered_html = _get_rendered_html(response.url)
    
    if rendered_html:
        # Reparse the content from the headless browser
        return BeautifulSoup(rendered_html, "lxml", from_encoding="utf-8")
        
    # If rendering also fails (or we returned None in the placeholder)
    return BeautifulSoup("", "lxml") # Return empty soup to force a clear FAIL result


def _clean_url(url):
    """
    Strips protocol, www, query, and fragments for a clean comparison.
    """
    if not url:
        return url
        
    url = url.lower().replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
    parsed = urlparse(url)
    cleaned_url = urlunparse(parsed._replace(fragment='', query=''))
    return cleaned_url

def run_audit(response, audit_level):
    """
    Runs the Canonical Check, prioritizing a static fetch but falling back to JS rendering.
    """
    # Use the new helper to get the most complete content
    soup = _get_static_or_rendered_soup(response)

    current_url = response.url
    canonical_tag = soup.find('link', rel='canonical')
    canonical_url = canonical_tag.get('href') if canonical_tag and canonical_tag.get('href') else None
    
    amphtml_tag = soup.find('link', rel='amphtml')
    amphtml_url = amphtml_tag.get('href') if amphtml_tag and amphtml_tag.get('href') else None
    
    is_amp_page = '/amp/' in current_url.lower()
    canonical_mismatch = False
    note = "PASS: Canonical tag correctly points to the current page or is not necessary."

    # --- Canonical Comparison Logic (Unchanged) ---
    if canonical_url:
        normalized_current = _clean_url(current_url)
        normalized_canonical = _clean_url(canonical_url)
        
        if normalized_current != normalized_canonical:
            canonical_mismatch = True
            note = f"FAIL: Canonical tag points to a different URL: '{canonical_url}'."
            
            if is_amp_page and '/amp/' not in canonical_url.lower():
                canonical_mismatch = False
                note = f"PASS: AMP page correctly canonicalizes to non-AMP URL: '{canonical_url}'."
        
        else:
            note = f"PASS: Canonical tag correctly points to the page itself: '{canonical_url}'."
            
    else:
        canonical_mismatch = True
        note = "FAIL: No <link rel='canonical'> tag found. This is necessary for pages with filtering/sorting or where duplicate content is possible."
        
    # --- AMPhtml Link Check (Unchanged) ---
    amphtml_note = ""
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

