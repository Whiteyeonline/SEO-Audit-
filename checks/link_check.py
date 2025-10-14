# checks/link_check.py

import requests 
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# Use a requests Session for slight efficiency and connection pooling across checks
# This is still synchronous and a potential bottleneck, but it is the cleaner way
# to perform synchronous external checks.
session = requests.Session()

def run_audit(response, audit_level):
    """
    Finds all links on the page and performs a live check on unique, absolute, external links 
    (HTTP/HTTPS) to identify 4xx/5xx broken links.
    
    WARNING: This check performs synchronous network requests, which can severely slow 
    down the audit.
    """
    
    # 1. Parsing the Rendered HTML
    try:
        # 💡 FIX: Use response.body for robust, encoding-safe parsing of the rendered HTML
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to parse content for link check: {str(e)}"}
    
    # 2. Extracting and Classifying Links
    links = [a.get("href") for a in soup.find_all("a", href=True) if a.get("href")]
    
    internal_count = 0
    external_links_to_check = set() # Use a set to check unique external links only
    current_netloc = urlparse(response.url).netloc

    for href in links:
        url = urljoin(response.url, href)
        parsed_url = urlparse(url)
        
        # Ignore non-HTTP/HTTPS links (e.g., mailto, tel, javascript)
        if parsed_url.scheme not in ['http', 'https']:
            continue
            
        # Ignore links that are only a fragment (e.g., #section)
        if not parsed_url.netloc and parsed_url.fragment:
            continue

        # Check if the link is internal (same domain)
        if parsed_url.netloc == current_netloc:
            internal_count += 1
            continue
            
        # Link is external, so add it to the check set
        external_links_to_check.add(url)


    broken = []
    
    # 3. Live Check Execution (Conditional and Synchronous)
    if audit_level in ['standard', 'advanced']:
        for link in external_links_to_check:
            try:
                # Use HEAD request for speed, follow redirects, use a reasonable timeout
                r = session.head(link, allow_redirects=True, timeout=10)
                
                # Flag hard failures (4xx/5xx)
                if r.status_code >= 400:
                    broken.append((link, r.status_code))
                    
            except requests.exceptions.Timeout:
                broken.append((link, 'TIMEOUT'))
            except requests.exceptions.ConnectionError:
                broken.append((link, 'CONNECTION_ERROR'))
            except requests.exceptions.TooManyRedirects:
                broken.append((link, 'TOO_MANY_REDIRECTS'))
            except Exception as e:
                # Catch all other request exceptions as a failure
                broken.append((link, f'GENERIC_ERROR: {str(e)}'))
    
    # Extract one sample broken link for the report
    sample_broken_link = f"{broken[0][0]} ({broken[0][1]})" if broken else 'N/A'
    
    total_links = internal_count + len(external_links_to_check)
            
    return {
        "total_links_on_page": total_links, 
        "internal_links_count": internal_count,
        "external_links_count": len(external_links_to_check),
        "broken_link_count": len(broken),
        "sample_broken_link": sample_broken_link,
        "note": "Live broken link check is ACTIVE on external links. This synchronous check may slow the audit significantly."
        }
                
