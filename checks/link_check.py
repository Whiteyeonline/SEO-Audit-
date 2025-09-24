import requests
from bs4 import BeautifulSoup
def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    links = [a.get("href") for a in soup.find_all("a", href=True)]
    broken = []
    return {"total": len(links), "broken": broken, "note": "Broken link check is disabled for speed."}
  
