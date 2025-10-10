from bs4 import BeautifulSoup
from urllib.parse import urlparse

# FIX: Changed function name and arguments to match the spider's requirement
def run_audit(response, audit_level):
    """
    Identifies and counts internal links on the page.
    
    It uses the response URL to determine the domain for classification.
    """
    # Use response.text to get the HTML content
    soup = BeautifulSoup(response.text, "lxml")
    
    # Get the domain of the current page being crawled
    domain = urlparse(response.url).netloc
    
    internal_links = []
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        
        # Check if the link starts with '/' (relative path) OR contains the current domain
        if href.startswith('/'):
            # Relative link is always internal
            internal_links.append(href)
        else:
            # Absolute link check: check if the domain is present
            # Also ensures it's an http/https link to avoid confusion with mailto:, tel:, etc.
            if href.startswith('http') and domain in href:
                internal_links.append(href)
                
    return {
        "internal_link_count": len(internal_links), 
        "sample_internal_links": internal_links[:10]
        }
    
