from bs4 import BeautifulSoup
def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    text = soup.get_text(separator=' ', strip=True)
    return {"word_count": len(text.split()), "note": "A higher word count can indicate more detailed content."}
  
