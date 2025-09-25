import requests, re
from bs4 import BeautifulSoup

def run(url, html_content=None):
    """
    Simple backlinks check using DuckDuckGo search results (free).
    """
    domain = re.sub(r'https?://(?:www\.)?', '', url).split('/')[0]
    try:
        search_url = f"https://html.duckduckgo.com/html/?q=link:{domain}"
        r = requests.get(search_url, timeout=5)
        soup = BeautifulSoup(r.text, "lxml")
        links = [a['href'] for a in soup.find_all('a', href=True)][:5]  # top 5
        return {"found_backlinks": links}
    except:
        return {"found_backlinks": []}
