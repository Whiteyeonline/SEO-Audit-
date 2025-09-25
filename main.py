import json
import os
from utils.fetcher import fetch_html
from utils.report_writer import write_report
from checks import (
    meta_check, heading_check, image_check, link_check, ssl_check,
    robots_sitemap, canonical_check, schema_check, content_quality,
    keyword_analysis, performance_check, url_structure, internal_links,
    backlinks_check, accessibility_check, mobile_friendly_check
)

def score_check(check_name, data):
    """
    Assigns a score (0–10) for each check.
    """
    score = 5  # default

    if check_name == "Meta Tags":
        score = 10 if data.get("title") and data.get("description") else 3

    elif check_name == "Headings":
        score = 10 if data.get("h1", 0) == 1 else 5

    elif check_name == "Images":
        score = 10 if data.get("missing_alt", 0) == 0 else 5

    elif check_name == "Links":
        score = 10 if data.get("broken", 0) == 0 else 5

    elif check_name == "SSL":
        score = 10 if data.get("valid_ssl") else 0

    elif check_name == "Robots & Sitemap":
        score = 10 if data.get("robots.txt") == "found" and data.get("sitemap.xml") == "found" else 5

    elif check_name == "Canonical":
        score = 10 if data.get("match") else 5

    elif check_name == "Schema":
        score = 10 if data.get("found_count", 0) > 0 else 3

    elif check_name == "Content":
        score = 10 if data.get("word_count", 0) > 300 else 4

    elif check_name == "Keywords":
        score = 8 if data.get("top_keywords") else 4

    elif check_name == "Performance":
        score = 10 if "load_time_ms" in data and data["load_time_ms"] < 3000 else 5

    elif check_name == "URL Structure":
        score = 10 if data.get("is_clean") else 5

    elif check_name == "Internal Links":
        score = 10 if data.get("internal_link_count", 0) > 5 else 4

    elif check_name == "Backlinks":
        score = 8 if data.get("found_backlinks") else 2

    elif check_name == "Accessibility":
        score = 10 if not data.get("accessibility_issues") else 5

    elif check_name == "Mobile Friendliness":
        score = 10 if data.get("mobile_friendly") else 0

    return score


def seo_audit(url):
    """
    Orchestrates the full SEO audit by running all checks.
    """
    results = {"url": url, "checks": {}, "scores": {}, "overall_score": 0}

    # Fetch page
    fetched = fetch_html(url)
    html_content = fetched.get("html")
    status_code = fetched.get("status_code")
    results["status_code"] = status_code

    if not html_content:
        return {"error": "Unable to fetch page content."}

    # Run all checks
    checks = {
        "Meta Tags": meta_check.run,
        "Headings": heading_check.run,
        "Images": image_check.run,
        "Links": link_check.run,
        "SSL": ssl_check.run,
        "Robots & Sitemap": robots_sitemap.run,
        "Canonical": canonical_check.run,
        "Schema": schema_check.run,
        "Content": content_quality.run,
        "Keywords": keyword_analysis.run,
        "Performance": performance_check.run,
        "URL Structure": url_structure.run,
        "Internal Links": internal_links.run,
        "Backlinks": backlinks_check.run,
        "Accessibility": accessibility_check.run,
        "Mobile Friendliness": mobile_friendly_check.run
    }

    for name, func in checks.items():
        try:
            data = func(url, html_content)
        except Exception as e:
            data = {"error": str(e)}
        results["checks"][name] = data
        results["scores"][name] = score_check(name, data)

    # Calculate overall score
    results["overall_score"] = round(sum(results["scores"].values()) / len(results["scores"]), 2)

    # Save reports
    write_report(results, "reports/output.json", "reports/output.md")
    return results


if __name__ == "__main__":
    url = os.getenv("AUDIT_URL", "https://example.com")
    print(f"Starting SEO audit for: {url}")
    audit_results = seo_audit(url)
    print("Audit complete. Report generated.")
