from bs4 import BeautifulSoup
def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    schemas = [script.get("type") for script in soup.find_all("script") if script.get("type") and "json" in script.get("type")]
    return {"schema_tags": schemas, "found_count": len(schemas)}
  
