from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse

def normalize_url(url):
    """
    Normalizes a URL by enforcing lowercase scheme/netloc, stripping fragments, 
    and ensuring trailing slash consistency for reliable comparison.
    """
    if not url:
        return None
    
    # 1. Parse the URL
    parsed = urlparse(url)
    
    # 2. Normalize scheme and netloc (e.g., HTTPS, lowercase domain)
    # We use lower() to ignore case differences in domain name
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path
    
    # 3. Handle trailing slash consistency (remove it for comparison simplicity, unless it's just the root '/')
    if path.endswith('/') and len(path) > 1:
        path = path.rstrip('/')
    
    # 4. Rebuild the URL without query, params, or fragment (critical for canonical check)
    normalized_url = urlunparse((scheme, netloc, path, '', '', ''))
    
    return normalized_url

# FIX: Changed function name and arguments to match the spider's requirement
def run_audit(response, audit_level):
    """
    Checks for the presence and correctness of the canonical tag.
    
    The check compares the canonical URL found on the page against the page's actual URL, 
    using normalized versions to avoid false negatives on case/scheme/www differences.
    It also correctly handles AMP to non-AMP canonical relationships.
    """
    soup = BeautifulSoup(response.text, "lxml")
    canonical_url = None
    canonical_mismatch = False
    note = "Canonical tag should point to the preferred, indexable version of the page."

    # 1. Find the canonical link tag in the head
    canonical_tag = soup.find('link', rel='canonical')

    # Get the URL that was crawled (the source page)
    crawled_url_full = response.url
    
    if canonical_tag:
        canonical_url = canonical_tag.get('href', None)
        
        if canonical_url:
            # Normalize the crawled URL and the canonical tag URL for robust comparison
            normalized_crawled_url = normalize_url(crawled_url_full)
            normalized_tag_url = normalize_url(canonical_url)
            
            # Check for mismatch between the URL crawled and the canonical tag's target
            if normalized_crawled_url != normalized_tag_url:
                canonical_mismatch = True
                
                # FIX: Special Case - AMP to non-AMP is a necessary mismatch, so it's NOT a failure
                if normalized_crawled_url.endswith('/amp'):
                    # The canonical tag should point to the normalized non-AMP version
                    non_amp_normalized_url = normalize_url(crawled_url_full.replace('/amp', '').rstrip('/'))
                    
                    if normalized_tag_url == non_amp_normalized_url:
                        canonical_mismatch = False # This is an expected and correct 'mismatch'
                        note = "PASS: The crawled page is an AMP URL, and the canonical correctly points to the non-AMP version."

    # Final Status Determination
    status = "PASS"
    if not canonical_url:
        status = "FAIL"
        canonical_mismatch = True
        note = "FAIL: No canonical tag found. This can lead to duplicate content issues."
    elif canonical_mismatch:
        status = "FAIL"
        note = f"FAIL: Canonical URL ({canonical_url}) does not match the page's URL ({crawled_url_full}) after normalization."

    
    return {
        "canonical_url": canonical_url,
        "canonical_mismatch": canonical_mismatch,
        "canonical_check": status,
        "note": note
                }
    
