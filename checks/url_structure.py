from urllib.parse import urlparse

# FIX: Changed function name and arguments to match the spider's requirement
def run_audit(response, audit_level):
    """
    Checks the URL structure for cleanliness (e.g., shallow directory depth).
    
    The audit_level and html_content arguments are mandatory but not used in this specific check.
    """
    url = response.url
    parsed = urlparse(url)
    
    # 1. Check for excessive directory depth
    # A path like /category/page/ has 3 slashes. <= 2 is often considered "clean" (e.g., /page/ or just /)
    # NOTE: This is a customizable heuristic.
    path_depth = parsed.path.count("/")
    is_clean = path_depth <= 2
    
    # 2. Check for query parameters (a sign of dynamic, potentially messy URLs)
    has_query_params = bool(parsed.query)

    return {
        "url_path": parsed.path, 
        "path_depth": path_depth,
        "is_clean_structure": is_clean,
        "has_query_params": has_query_params,
        "url_not_clean_count": 1 if not is_clean or has_query_params else 0,
        "note": "Clean URLs (shallow, no query params) are generally preferred for SEO."
    }
    
