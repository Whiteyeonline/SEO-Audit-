import os
import json
from checks import (
    fetcher, meta_check, headings_check, images_check,
    links_check, ssl_check, robots_check, sitemap_check,
    schema_check, keyword_check, performance_check,
    url_structure_check, internal_links_check, backlinks_check,
    accessibility_check, mobile_check
)
import report_writer

def run_audit(url):
    html, status = fetcher.run(url)
    if not html:
        return {"error": f"Failed to fetch {url}, status: {status}"}

    results = {
        "url": url,
        "status_code": status,
        "meta": meta_check.run(html),
        "headings": headings_check.run(html),
        "images": images_check.run(html),
        "links": links_check.run(url, html),
        "ssl": ssl_check.run(url),
        "robots": robots_check.run(url),
        "sitemap": sitemap_check.run(url),
        "schema": schema_check.run(html),
        "keywords": keyword_check.run(html),
        "performance": performance_check.run(url),
        "url_structure": url_structure_check.run(url),
        "internal_links": internal_links_check.run(url, html),
        "backlinks": backlinks_check.run(url, html),
        "accessibility": accessibility_check.run(html),
        "mobile": mobile_check.run(url, html),
    }

    # calculate score
    passed = sum(1 for k,v in results.items() if isinstance(v, dict) and v.get("status") == "pass")
    total = sum(1 for k,v in results.items() if isinstance(v, dict) and "status" in v)
    score = int((passed / total) * 100) if total > 0 else 0
    results["seo_score"] = score

    return results

if __name__ == "__main__":
    url = os.getenv("AUDIT_URL", "https://example.com")
    results = run_audit(url)

    os.makedirs("reports", exist_ok=True)
    with open("reports/output.json", "w") as f:
        json.dump(results, f, indent=2)

    report_writer.to_markdown(results, "reports/output.md")
    print("✅ SEO audit finished. Reports saved in /reports")
