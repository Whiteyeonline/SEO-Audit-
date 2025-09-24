from urllib.parse import urlparse
def run(url, html_content=None):
    parsed = urlparse(url)
    return {"path": parsed.path, "is_clean": parsed.path.count('/') <= 2, "note": "Clean URLs are generally better for SEO."}
  
