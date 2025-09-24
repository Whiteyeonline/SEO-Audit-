from bs4 import BeautifulSoup
def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    issues = []
    missing_alt = [img.get('src') for img in soup.find_all('img') if not img.get('alt')]
    if missing_alt:
        issues.append({"type": "warning", "check": "Images missing alt text", "elements": missing_alt})
    return {"accessibility_issues": issues, "note": "This is a basic check for common accessibility issues."}
  
