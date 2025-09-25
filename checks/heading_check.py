from bs4 import BeautifulSoup
def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    counts = {h: len(soup.find_all(h)) for h in ["h1","h2","h3","h4","h5","h6"]}
    return counts
