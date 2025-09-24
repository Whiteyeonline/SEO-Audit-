from bs4 import BeautifulSoup
def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    internal_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith('/') or url.split("//")[-1] in a['href']]
    return {"internal_link_count": len(internal_links), "note": "Count of internal links on the page."}
  
