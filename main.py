import json
import os
from utils.fetcher import fetch_html
from utils.report_writer import write_report
from checks import (
    meta_check, heading_check, image_check, link_check, ssl_check,
    robots_sitemap, canonical_check, schema_check, content_quality,
    keyword_analysis, performance_check, url_structure, internal_links,
    backlinks_check, accessibility_check
)

def seo_audit(url):
    """
    Orchestrates the full SEO audit by running all checks.
    """
    results = {"url": url, "checks": {}}
    html_content = fetch_html(url)
    
    if not html_content:
        return {"error": "Unable to fetch page content."}
    
    # Run all checks, passing the URL and HTML content for efficiency
    # (some checks might need to refetch, but we can pass it if possible)
    results["checks"]["meta"] = meta_check.run(url, html_content)
    results["checks"]["headings"] = heading_check.run(url, html_content)
    results["checks"]["images"] = image_check.run(url, html_content)
    results["checks"]["links"] = link_check.run(url, html_content)
    results["checks"]["ssl"] = ssl_check.run(url) # SSL check doesn't need HTML
    results["checks"]["robots_sitemap"] = robots_sitemap.run(url)
    results["checks"]["canonical"] = canonical_check.run(url, html_content)
    results["checks"]["schema"] = schema_check.run(url, html_content)
    results["checks"]["content"] = content_quality.run(url, html_content)
    results["checks"]["keywords"] = keyword_analysis.run(url, html_content)
    results["checks"]["performance"] = performance_check.run(url)
    results["checks"]["url_structure"] = url_structure.run(url)
    results["checks"]["internal_links"] = internal_links.run(url, html_content) # FIX: Added html_content
    results["checks"]["backlinks"] = backlinks_check.run(url)
    results["checks"]["accessibility"] = accessibility_check.run(url, html_content)

    # Write the report using the AI-powered report writer
    write_report(results, "reports/output.json", "reports/output.md")
    return results

if __name__ == "__main__":
    # Get the URL from GitHub Actions input
    url = os.getenv("AUDIT_URL", "https://example.com") 
    print(f"Starting SEO audit for: {url}")
    audit_results = seo_audit(url)
    print("Audit complete. Report generated.")
    
