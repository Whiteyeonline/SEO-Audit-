from urllib.parse import urlparse
def run(url, html_content=None):
    parsed = urlparse(url)
    is_clean = parsed.path.count("/") <= 2
    return {"path": parsed.path, "is_clean": is_clean}
