from bs4 import BeautifulSoup
def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    domain = url.split("//")[-1].split("/")[0]
    internal = [a['href'] for a in soup.find_all('a', href=True)
                if a['href'].startswith('/') or domain in a['href']]
    return {"internal_link_count": len(internal), "links": internal}
