import os
from utils.fetcher import fetch_html
from utils.report_writer import write_report
from checks import (
    meta_check, heading_check, image_check, # Renamed to standard
    link_check, ssl_check, robots_sitemap, # sitemap_check is now integrated into robots_sitemap
    schema_check, keyword_analysis, performance_check,
    url_structure, internal_links, backlinks_check,
    accessibility_check, mobile_friendly_check, # Renamed
    canonical_check, content_quality # Added missing checks
)

def calculate_seo_score(results):
    """Calculates a simple SEO score (out of 100) based on key passes/fails."""
    score = 100
    penalties = 0

    if not results.get("ssl", {}).get("valid_ssl"): penalties += 15
    if results.get("robots_sitemap", {}).get("robots.txt") != "found": penalties += 5
    if results.get("robots_sitemap", {}).get("sitemap.xml") != "found": penalties += 5
    if not results.get("mobile", {}).get("mobile_friendly"): penalties += 10
    if not results.get("canonical", {}).get("match"): penalties += 5
    if not results.get("meta", {}).get("title"): penalties += 10
    if not results.get("meta", {}).get("description"): penalties += 10
    if results.get("links", {}).get("broken"): penalties += min(15, len(results["links"]["broken"]) * 1) # Max 15 points
    if results.get("images", {}).get("missing_alt", 0) > 0: penalties += 10

    final_score = max(0, score - penalties)
    return final_score

def seo_audit(url):
    html_content, status = fetch_html(url)
    if not html_content:
        return {"error": f"Unable to fetch page content. Status: {status}"}

    results = {
        "url": url,
        "status_code": status,
        # Technical Checks
        "ssl": ssl_check.run(url),
        "robots_sitemap": robots_sitemap.run(url),
        "url_structure": url_structure.run(url),
        "canonical": canonical_check.run(url, html_content), # New
        "schema": schema_check.run(url, html_content),

        # On-Page Checks
        "meta": meta_check.run(url, html_content),
        "headings": heading_check.run(url, html_content),
        "content": content_quality.run(url, html_content), # New
        "keywords": keyword_analysis.run(url, html_content),
        "images": image_check.run(url, html_content),

        # Link/Performance/Usability Checks
        "links": link_check.run(url, html_content),
        "internal_links": internal_links.run(url, html_content),
        "performance": performance_check.run(url),
        "accessibility": accessibility_check.run(url, html_content),
        "mobile": mobile_friendly_check.run(url, html_content),
        "backlinks": backlinks_check.run(url, html_content), # Simple external link check
    }

    # Calculate Score
    results["seo_score"] = calculate_seo_score(results)

    # Save reports
    os.makedirs("reports", exist_ok=True)
    write_report(results, "reports/output.json", "reports/output.md")

    return results

if __name__ == "__main__":
    # Removed the use of os.getenv for simplicity in this context.
    url = "https://example.com" # Placeholder. Use an actual URL for real audit.
    print(f"Starting SEO audit for: {url}")
    audit_results = seo_audit(url)
    print("Audit complete. Reports generated in /reports")
    
