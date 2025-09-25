from bs4 import BeautifulSoup
def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    canonical = soup.find("link", rel="canonical")
    c_url = canonical.get("href") if canonical else None
    return {"canonical_url": c_url, "match": (c_url==url) if c_url else False}
