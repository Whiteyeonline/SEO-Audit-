from bs4 import BeautifulSoup
def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    canonical = soup.find("link", attrs={"rel": "canonical"})
    canonical_url = canonical.get("href") if canonical else None
    return {"canonical_url": canonical_url, "match": (canonical_url == url) if canonical_url else False}
  
