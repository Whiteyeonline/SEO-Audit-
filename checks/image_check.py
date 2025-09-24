from bs4 import BeautifulSoup
def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    imgs = soup.find_all("img")
    return {"total": len(imgs), "missing_alt": sum(1 for img in imgs if not img.get("alt"))}
  
