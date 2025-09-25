from bs4 import BeautifulSoup

def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    issues = []
    missing_alt = [img.get("src") for img in soup.find_all("img") if not img.get("alt")]
    if missing_alt:
        issues.append({"type":"warning","check":"Missing alt text","elements":missing_alt})
    headings = [h.name for h in soup.find_all(["h1","h2","h3","h4","h5","h6"])]
    if headings != sorted(headings):
        issues.append({"type":"info","check":"Headings order may be incorrect"})
    return {"accessibility_issues": issues}
