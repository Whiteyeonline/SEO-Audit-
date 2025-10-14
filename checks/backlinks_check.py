# checks/backlinks_check.py
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re

def run_audit(response, audit_level):
    """
    Free backlink-like check. Counts internal/external links found on the page 
    to provide a rough proxy for link volume.
    
    NOTE: Real backlink data requires external APIs (e.g., Ahrefs, Moz).
    """
    try:
        # Use response.body for robust, encoding-safe parsing of the rendered HTML
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to parse content for backlink proxy check: {str(e)}"}
        
    current_netloc = urlparse(response.url).netloc

    internal_links = []
    external_links = []

    for tag in soup.find_all("a", href=True):
        href = tag.get("href")
        
        if not href or re.match(r'^(mailto|tel|javascript):', href):
            continue

        # Resolve the URL to handle relative paths
        absolute_url = urljoin(response.url, href)
        parsed_url = urlparse(absolute_url)

        # Skip links without a network location (e.g., #fragments)
        if not parsed_url.netloc:
            continue
            
        # Check if the link's domain matches the current page's domain
        if parsed_url.netloc == current_netloc:
            internal_links.append(href)
        else:
            external_links.append(href)

    # Use a set to count unique domains linked to externally
    unique_external_domains = list(set(urlparse(link).netloc for link in external_links))

    # The audit_level argument is mandatory but not used in this specific check.
    return {
        "status": "INFO",
        "internal_link_count": len(internal_links),
        "external_link_count": len(external_links),
        "unique_external_domains_count": len(unique_external_domains),
        "sample_external_domains": unique_external_domains[:5],
        "note": "Basic free check. This counts outgoing links on the page. For true backlink analysis (inbound links), you must integrate a premium API."
    }
    
