from bs4 import BeautifulSoup
def run(url, html_content): # url parameter added to match main.py signature
    soup = BeautifulSoup(html_content, "lxml")
    imgs = soup.find_all("img")
    # Only count images that have a source attribute (i.e., real images)
    missing_alt = [img.get("src") for img in imgs if not img.get("alt") and img.get("src")]
    return {"total": len(imgs), "missing_alt": len(missing_alt), "missing_list": missing_alt}
    
