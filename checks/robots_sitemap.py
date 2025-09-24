import requests
def run(url, html_content=None):
    domain = url.split("//")[-1].split("/")[0]
    robots_url = f"https://{domain}/robots.txt"
    sitemap_url = f"https://{domain}/sitemap.xml"
    robots_status = "found" if requests.get(robots_url, timeout=5).status_code == 200 else "not found"
    sitemap_status = "found" if requests.get(sitemap_url, timeout=5).status_code == 200 else "not found"
    return {"robots.txt": robots_status, "sitemap.xml": sitemap_status}
  
