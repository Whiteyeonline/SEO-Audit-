import requests
from bs4 import BeautifulSoup

def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    links = [a.get("href") for a in soup.find_all("a", href=True)]
    broken = []
    for link in links:
        if not link.startswith("http"):
            continue
        try:
            r = requests.head(link, allow_redirects=True, timeout=5)
            if r.status_code >= 400:
                broken.append(link)
        except:
            broken.append(link)
    return {"total": len(links), "broken": broken}
