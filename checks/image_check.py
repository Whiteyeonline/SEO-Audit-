from bs4 import BeautifulSoup
def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    imgs = soup.find_all("img")
    missing_alt = [img.get("src") for img in imgs if not img.get("alt")]
    return {"total": len(imgs), "missing_alt": len(missing_alt), "missing_list": missing_alt}
