from bs4 import BeautifulSoup

def run(url, html_content):
    """
    Extracts the title and meta description from the HTML content.
    """
    soup = BeautifulSoup(html_content, "lxml")
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else ""
    return {"title": title, "description": description}

