from bs4 import BeautifulSoup
from urllib.parse import urlparse

# FIX: Changed function name and arguments to match the spider's requirement
def run_audit(response, audit_level):
    """
    Free backlink-like check. Counts internal/external links using the
    Scrapy response object.
    """
    # Use response.url to get the current page's URL and response.text for HTML
    soup = BeautifulSoup(response.text, "lxml")
    domain = urlparse(response.url).netloc

    internal_links = []
    external_links = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if href.startswith("http"):
            if domain in href:
                internal_links.append(href)
            else:
                external_links.append(href)

    unique_external_domains = list(set(urlparse(link).netloc for link in external_links))

    # The audit_level argument is mandatory but not used in this specific check.
    return {
        "status": "pass",
        "internal_link_count": len(internal_links),
        "external_link_count": len(external_links),
        "sample_external_domains": unique_external_domains[:10],
        "note": "Basic free check. Real backlink data needs premium APIs."
    }
    
