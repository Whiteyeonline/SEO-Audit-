# checks/url_structure.py
from urllib.parse import urlparse

def run_audit(response, audit_level):
    """
    Checks the URL structure for cleanliness, primarily focusing on directory depth,
    URL length, and the presence of query parameters.
    
    This check relies on the URL from the response object and does not require HTML parsing.
    """
    url = response.url
    parsed_url = urlparse(url)
    
    # 1. Check for excessive directory depth
    # Count the number of slashes in the path (excluding the leading and trailing slash)
    path_segments = [s for s in parsed_url.path.strip('/').split('/') if s]
    path_depth = len(path_segments)
    
    # Heuristic: Depth > 2 is often considered deep (e.g., /1/2/3/page.html)
    is_deep = path_depth > 2
    
    # 2. Check for query parameters (a sign of dynamic, potentially messy URLs)
    has_query_params = bool(parsed_url.query)
    
    # 3. Check URL Length
    url_length = len(url)
    # Heuristic: URLs over 100 characters can be less friendly for sharing/indexing
    is_too_long = url_length > 100

    fail_count = 0
    note = "PASS: URL is clean and follows best practices."

    if is_too_long:
        fail_count += 1
        note = f"FAIL: URL is too long ({url_length} chars). Keep URLs under 100 chars."
    elif is_deep:
        fail_count += 1
        note = f"WARNING: URL has excessive path depth ({path_depth} levels). Aim for shallow structures."
    elif has_query_params:
        fail_count += 1
        note = "WARNING: URL contains query parameters. Use clean slugs instead of parameters when possible."
        
    return {
        "full_url": url,
        "url_length": url_length,
        "is_too_long": is_too_long,
        "path_depth": path_depth,
        "is_deep_structure": is_deep,
        "has_query_params": has_query_params,
        "url_structure_fail_count": fail_count,
        "note": note
    }
    
