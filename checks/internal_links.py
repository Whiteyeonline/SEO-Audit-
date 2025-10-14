# checks/internal_links.py
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

def run_audit(response, audit_level):
    """
    Identifies and counts internal links on the page using the fully rendered HTML.
    
    It determines the domain of the current page for accurate classification.
    """
    try:
        # Use response.body for robust, encoding-safe parsing of the rendered HTML
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to parse content for internal links check: {str(e)}"}
    
    # Get the domain (netloc) of the current page being crawled
    current_netloc = urlparse(response.url).netloc
    
    internal_links = []
    
    # Find all anchor tags with an href attribute
    for a in soup.find_all('a', href=True):
        href = a['href']
        
        # 1. Resolve relative links to absolute URLs
        absolute_url = urljoin(response.url, href)
        parsed_url = urlparse(absolute_url)
        
        # Ignore non-standard links (mailto, tel, javascript)
        if parsed_url.scheme not in ['http', 'https']:
            continue

        # Ignore fragment-only links (e.g., #top)
        if not parsed_url.netloc and parsed_url.fragment:
            continue
            
        # 2. Check if the link's netloc matches the current page's netloc
        if parsed_url.netloc == current_netloc:
            # We only record the original href to see what was in the source
            internal_links.append(href)
                
    return {
        "current_page_domain": current_netloc,
        "internal_link_count": len(internal_links), 
        "sample_internal_links": internal_links[:10],
        "note": "A healthy page should have sufficient internal links (e.g., > 20) for navigation and link equity distribution."
        }
        
