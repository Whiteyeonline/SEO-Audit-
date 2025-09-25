import os
from utils.fetcher import fetch_html
from utils.report_writer import write_report
from checks import (
    meta_check, headings_check, images_check,
    links_check, ssl_check, robots_sitemap, sitemap_check,
    schema_check, keyword_analysis, performance_check,
    url_structure, internal_links, backlinks_check,
    accessibility_check, mobile_check
)

def seo_audit(url):
    html_content, status = fetch_html(url)
    if not html_content:
        return {"error": f"Unable to fetch page content. Status: {status}"}

    results = {
        "url": url,
        "status_code": status,
        "meta": meta_check.run(html_content),
        "headings": headings_check.run(html_content),
        "images": images_check.run(html_content),
        "links": links_check.run(url, html_content),
        "ssl": ssl_check.run(url),
        "robots_sitemap": robots_sitemap.run(url),
        "sitemap": sitemap_check.run(url),
        "schema": schema_check.run(html_content),
        "keywords": keyword_analysis.run(html_content),
        "performance": performance_check.run(url),
        "url_structure": url_structure.run(url),
        "internal_links": internal_links.run(url, html_content),
        "backlinks": backlinks_check.run(url, html_content),
        "accessibility": accessibility_check.run(html_content),
        "mobile": mobile_check.run(url, html_content)
    }

    # Save reports
    os.makedirs("reports", exist_ok=True)
    write_report(results, "reports/output.json", "reports/output.md")

    return results

if __name__ == "__main__":
    url = os.getenv("AUDIT_URL", "https://example.com")
    print(f"Starting SEO audit for: {url}")
    audit_results = seo_audit(url)
    print("Audit complete. Reports generated in /reports")
