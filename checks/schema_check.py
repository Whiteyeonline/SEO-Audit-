from bs4 import BeautifulSoup
def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    schemas = [s.get("type") for s in soup.find_all("script") if s.get("type") and "json" in s.get("type")]
    return {"schema_tags": schemas, "found_count": len(schemas)}
