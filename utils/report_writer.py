import json
from datetime import datetime
from urllib.parse import urlparse
import math # Import math for rounding/int conversion

def analyze_page_issues(page):
    issues = []
    solutions = []

    # Title tag - Logic is sound: Missing is CRITICAL (❌), Length is WARNING (⚠️)
    title = page.get('meta', {}).get('title', '')
    if not title:
        issues.append("❌ Title tag missing.")
        solutions.append("Add a unique, keyword-focused title tag (50-60 chars).")
    elif len(title) < 30 or len(title) > 60:
        issues.append(f"⚠️ Title length ({len(title)}) not optimal.")
        solutions.append("Rewrite title to 50-60 characters for best SEO.")

    # Meta description
    description = page.get('meta', {}).get('description', '')
    if not description:
        issues.append("❌ Meta description missing.")
        solutions.append("Add a compelling meta description (150-160 chars).")

    # H1
    h1_count = page.get('headings', {}).get('h1', 0)
    if h1_count != 1:
        issues.append(f"❌ Page has {h1_count} H1 tags (should be exactly 1).")
        solutions.append("Add one unique H1 tag summarizing page topic.")

    # Content/word count - Consistent advice
    word_count = page.get('content', {}).get('word_count', 0)
    if word_count < 250:
        issues.append(f"⚠️ Thin content (Word Count: {word_count}).")
        solutions.append("Expand content above 300 words for value and ranking.")

    # Mobile friendly
    mobile_friendly = page.get('mobile', {}).get('mobile_friendly', False)
    if not mobile_friendly:
        issues.append("❌ Not mobile friendly.")
        solutions.append("Add a `<meta name=\"viewport\" content=\"width=device-width\">` tag in the HTML.")

    # Alt tags for images
    missing_alt = page.get('images', {}).get('missing_alt', 0)
    if missing_alt > 0:
        issues.append(f"⚠️ {missing_alt} images missing ALT attributes.")
        solutions.append("Add descriptive alt text to all images.")

    # Analytics - FIXED: Correctly checks the nested structure and flags only if NOT found
    analytics_tracking = page.get('analytics', {}).get('tracking_setup', {})
    ga_found = analytics_tracking.get('google_analytics_found', False)
    gtm_found = analytics_tracking.get('google_tag_manager_found', False)
    
    if not (ga_found or gtm_found):
        issues.append("❌ No Google Analytics or Tag Manager detected.")
        solutions.append("Add Google Analytics or GTM script to your site.")

    # Canonical
    canonical = page.get('canonical', {}).get('canonical_url', '')
    if not canonical:
        issues.append("❌ Canonical tag missing.")
        solutions.append("Add a self-referencing canonical tag to every page.")

    # Schema markup (for standard audit)
    if "schema" in page:
        schema_count = page.get("schema", {}).get("found_count", 0)
        if schema_count == 0:
            issues.append("⚠️ No Schema markup found.")
            solutions.append("Add relevant Schema (Article, LocalBusiness, etc.) for rich results.")

    # Broken links (for standard audit)
    if "links" in page:
        broken_links = page.get("links", {}).get("broken", [])
        if broken_links:
            issues.append(f"❌ {len(broken_links)} broken external links found.")
            solutions.append("Replace or remove broken links (404 errors).")

    return issues, solutions

def calculate_seo_score(all_page_results, domain_checks):
    """
    Calculates SEO scores for all pages and aggregates summary metrics,
    incorporating domain-level checks.
    Returns a dictionary suitable for reporting.
    """
    # Detailed page scores and issues
    page_scores = []
    detailed_page_data = []
    for page in all_page_results:
        issues, solutions = analyze_page_issues(page)
        score = 100
        for issue in issues:
            if issue.startswith("❌"):
                score -= 15
            elif issue.startswith("⚠️"):
                score -= 7
        score = max(score, 0)
        page_scores.append({
            "url": page.get("url", ""),
            "seo_score": score,
            "issues": issues
        })
        page_copy = page.copy()
        page_copy["issues"] = issues
        page_copy["solutions"] = solutions
        detailed_page_data.append(page_copy)

    # Use math.ceil to ensure proper rounding for average score
    avg_score = int(math.ceil(sum([p["seo_score"] for p in page_scores]) / len(page_scores))) if page_scores else 100

    summary_metrics = {
        "total_pages_crawled": len(all_page_results),
        "seo_score": avg_score
    }

    # Structure expected by write_summary_report
    return {
        "domain_info": domain_checks,
        "summary_metrics": summary_metrics,
        "detailed_page_data": detailed_page_data,
        "page_scores": page_scores
    }

def write_summary_report(data, json_path, md_path):
    if 'timestamp' not in data['domain_info']:
        data['domain_info']['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    domain_name = data['domain_info'].get('url', 'N/A')
    audit_level = data['domain_info'].get('audit_level', 'standard')
    timestamp = data['domain_info'].get('timestamp', 'N/A')
    summary = data.get('summary_metrics', {})
    competitor = data['domain_info'].get('competitor_data', {})
    domain_info = data.get('domain_info', {})
    detailed_data = data.get('detailed_page_data', [])

    avg_score = summary.get('seo_score', 100)
    page_scores = data.get('page_scores', [])

    # --- AGGREGATE SITE-WIDE METRICS ---
    total_images = sum(p.get('images', {}).get('total', 0) for p in detailed_data)
    total_missing_alt = sum(p.get('images', {}).get('missing_alt', 0) for p in detailed_data)
    total_internal_links = sum(p.get('backlinks', {}).get('internal_link_count', 0) for p in detailed_data)
    total_external_links = sum(p.get('backlinks', {}).get('external_link_count', 0) for p in detailed_data)
    
    # Write JSON report
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Write Markdown report
    with open(md_path, "w", encoding="utf-8") as f:
        
        # === 1. REPORT HEADER AND TITLE ===
        f.write(f"# 👑 PROFESSIONAL {audit_level.upper()} SEO AUDIT REPORT\n\n")
        f.write(f"## 🌐 Audited Website: {domain_name}\n\n")
        f.write(f"**Audit Date:** {timestamp}\n")
        f.write(f"**Audit ID:** `{timestamp}`\n\n")
        f.write("--- \n\n") # Separator

        # === 2. EXECUTIVE SUMMARY ===
        f.write("## 🎯 Executive Summary\n\n")
        f.write("This summary provides a high-level overview of the entire audit. The average SEO score is derived from key checks across all crawled pages.\n\n")
        f.write("| Metric | Value |\n")
        f.write("| :--- | :--- |\n")
        f.write(f"| **Average SEO Score** | **{avg_score}/100** |\n")
        f.write(f"| Total Pages Audited | {summary.get('total_pages_crawled', 'N/A')} |\n")
        f.write(f"| Total Images Checked | {total_images} |\n")
        f.write(f"| Total Missing Alt Text | {total_missing_alt} |\n")
        f.write(f"| Site Load Time (Homepage) | {domain_info.get('performance', {}).get('load_time_ms', 'N/A')}ms |\n")
        f.write("\n--- \n\n") # Separator

        # === 3. SITE INDEX & CRAWL SCOPE (New Index Section) ===
        # Note: Since the exact max limit (N) is not in the JSON, we state the current pages audited.
        crawl_limit = "Up to 250 pages (Standard Audit Limit)" 
        f.write("## 🗺️ Site Index & Crawl Scope\n\n")
        f.write(f"The audit was performed with a limit of **{crawl_limit}**.\n\n")
        f.write(f"- **Total Pages Audited:** **{len(detailed_data)}**\n")
        f.write(f"- **Total Links Found (Internal):** {total_internal_links}\n")
        f.write(f"- **Total Links Found (External):** {total_external_links}\n")
        
        if domain_info.get('audit_level') == 'only_onpage':
             f.write("- **Audit Type:** **Basic** - Only the homepage was checked.\n\n")
        else:
            max_depth = max(p.get('crawl_depth', 0) for p in detailed_data if p) if detailed_data else 0
            f.write(f"- **Audit Type:** **Standard** - Full site crawl up to the set limit (Max Depth: {max_depth}).\n\n")
        f.write("--- \n\n") # Separator

        # === 4. DOMAIN-LEVEL TECHNICAL HEALTH ===
        f.write("## 🔒 Domain-Level Technical Health\n\n")
        
        # SSL Check (Extract Issuer from JSON)
        ssl_status = domain_info.get('ssl', {}).get('valid_ssl', False)
        issuer_data = domain_info.get('ssl', {}).get('issuer', [])
        # Search for the organizationName in the nested issuer list
        issuer_name = next((val[1] for item in issuer_data for val in item if isinstance(val, list) and val[0] == 'organizationName'), 'N/A')
        
        f.write("### Technical Checks\n\n")
        f.write(f"- **SSL Certificate:** {'✅ Valid HTTPS' if ssl_status else '❌ Missing or Invalid'}\n")
        f.write(f"  - *Provider:* {issuer_name}\n\n")

        # Robots & Sitemap
        robots_status = domain_info.get('robots_sitemap', {}).get('robots.txt', 'N/A')
        sitemap_status = domain_info.get('robots_sitemap', {}).get('sitemap.xml', 'N/A')
        f.write(f"- **robots.txt Status:** {'✅ Found' if 'found' in robots_status.lower() else '❌ Not Found'}\n")
        f.write(f"- **sitemap.xml Status:** {'✅ Found' if 'found' in sitemap_status.lower() else '⚠️ Not Found'}\n")
        
        # Performance
        load_time = domain_info.get('performance', {}).get('load_time_ms', 'N/A')
        f.write(f"- **Initial Load Time:** **{load_time}ms** (Target: < 500ms)\n")
        f.write("\n--- \n\n") # Separator

        # === 5. TOP ACTIONABLE PRIORITY (Homepage) ===
        homepage = detailed_data[0] if detailed_data else {}
        issues = homepage.get('issues', [])
        solutions = homepage.get('solutions', [])
        homepage_score = page_scores[0]['seo_score'] if page_scores else 100
        
        f.write("## 💡 Top Actionable Priority (Homepage)\n\n")
        f.write(f"The homepage is the most critical page for ranking. Its score is **{homepage_score}/100**.\n\n")
        
        if issues:
            f.write("### Critical and Priority Issues Found:\n\n")
            for i, (issue, solution) in enumerate(zip(issues, solutions), 1):
                f.write(f"- **{i}. {issue}**\n")
                f.write(f"  - *Solution:* {solution}\n\n")
        else:
            f.write("### ✅ STATUS: No critical issues found on the Homepage.\nFocus on medium priority items in the detailed report.\n\n")
        f.write("--- \n\n") # Separator

        # === 6. DETAILED ON-PAGE AUDIT CHECKLIST ===
        f.write(f"# 📚 DETAILED ON-PAGE AUDIT CHECKLIST (Total Pages: {len(detailed_data)})\n\n")
        
        for idx, page in enumerate(detailed_data):
            url = page.get("url", "N/A")
            issues = page.get('issues', [])
            solutions = page.get('solutions', [])
            score = page_scores[idx]['seo_score'] if idx < len(page_scores) else 100
            
            # Detailed page metrics
            meta = page.get('meta', {})
            headings = page.get('headings', {})
            content = page.get('content', {})
            images = page.get('images', {})
            backlinks = page.get("backlinks", {})


            f.write(f"## {idx+1}. Page Audit: [{url}]({url})\n\n")
            f.write(f"### Score & Core Metrics\n\n")
            f.write(f"- **SEO Score:** **{score}/100**\n")
            f.write(f"- **Status Code:** **{page.get('status_code', 'N/A')}**\n")
            f.write(f"- **Crawlable:** {'✅ Yes' if page.get('is_crawlable') else '❌ No'}\n\n")
            
            f.write("### On-Page Elements\n\n")
            f.write(f"- **Title Tag:** {meta.get('title','[MISSING]')}\n")
            f.write(f"- **Meta Description:** {meta.get('description','[MISSING]')}\n")
            f.write(f"- **Canonical URL:** {page.get('canonical', {}).get('canonical_url', '[MISSING]')}\n")
            f.write(f"- **H1 Tags Found:** {headings.get('h1',0)}\n")
            f.write(f"- **Word Count:** {content.get('word_count',0)}\n")
            f.write(f"- **Readability Score (Flesch):** {content.get('readability_score', 'N/A')}\n")
            f.write(f"- **Mobile Friendly:** {'✅' if page.get('mobile',{}).get('mobile_friendly') else '❌'}\n\n")
            
            f.write("### Image & Link Metrics\n\n")
            f.write(f"- **Total Images:** {images.get('total',0)}\n")
            f.write(f"- **Missing ALT Text:** **{images.get('missing_alt',0)}**\n")
            f.write(f"- **Internal Links:** {backlinks.get('internal_link_count','N/A')}\n")
            f.write(f"- **External Links:** {backlinks.get('external_link_count','N/A')}\n\n")
            
            f.write("### 🚧 Issues Found & Solutions\n\n")
            if issues:
                for i, (issue, solution) in enumerate(zip(issues, solutions), 1):
                    f.write(f"- **{i}. {issue}**\n")
                    f.write(f"  - *Solution:* {solution}\n")
            else:
                f.write("✅ No major issues found on this page.\n")
            f.write("\n--- \n\n") # Separator for pages

        # === 7. COMPETITOR & KEYWORD ANALYSIS (Updated Disclaimer) ===
        f.write("## 📈 Competitor & Keyword Analysis\n\n")
        f.write("This section requires integration with specialized (often paid) SEO tools. We currently provide basic data if a competitor URL was provided for comparison.\n\n")
        if competitor.get("status") == "success":
            f.write(f"- **Competitor URL:** [{competitor.get('url')}]({competitor.get('url')})\n")
            f.write(f"- **Title Length:** {competitor.get('title_length','N/A')}\n")
            f.write(f"- **H1 Count:** {competitor.get('h1_count','N/A')}\n")
            f.write(f"- **Word Count:** {competitor.get('word_count','N/A')}\n")
        else:
            f.write(f"- **Status:** Competitor analysis skipped or failed: *{competitor.get('error','No competitor URL provided.')}*\n")
        f.write("\n--- \n\n") # Separator

        # === 8. DISCLAIMER & BACKLINK HELP ===
        f.write("## ℹ️ Audit Scope & Disclaimer\n\n")
        f.write("This audit covers *technical* and *on-page* SEO using a proprietary, limited-depth crawler. Key external data is **not** included.\n\n")
        f.write("### Data NOT Included in This Report:\n\n")
        f.write("- **Backlinks (Inbound Links):** The audit does not show which sites link to your domain.\n")
        f.write("- **Keyword Rankings/Traffic:** This requires connection to Google Search Console or specialized API tools.\n")
        f.write("- **Live Broken Link Check:** The crawl prioritizes speed. A separate file (`external_links_to_check.txt`) is provided for asynchronous link validation.\n\n")
        f.write("### Actionable Solutions & Help:\n\n")
        f.write("- **External Data:** To check your real backlinks, use [Google Search Console](https://search.google.com/search-console/about) (if you own the site).\n")
        f.write("- **Solutions:** All issues above include a clear, step-by-step solution.\n")
        f.write("\n*If you want more help fixing issues or need full data integration, please contact us.*\n")
        f.write(f"\n--- \n\n")
        f.write(f"**Report Generated By:** Professional SEO Audit Tool\n")
        f.write(f"**Audit ID:** `{timestamp}`\n")


# --- NEW FUNCTION FOR TWO-STAGE LINK CHECKING (UNMODIFIED) ---
def write_external_link_list(data):
    """
    Extracts all unique external links and saves them to a text file for
    later asynchronous checking. This is the recommended way to handle broken links.
    """
    external_links = set()
    
    for page in data.get('detailed_page_data', []):
        # Links are extracted in the meta_check and stored here:
        all_links = page.get('meta', {}).get('links', [])
        
        # Determine the domain of the site being audited
        audit_url = data['domain_info'].get('url', '')
        if not audit_url: continue

        audit_netloc = urlparse(audit_url).netloc
        
        for link in all_links:
            parsed_link = urlparse(link)
            # Check if link has a network location (i.e., not a relative path)
            # AND if the network location is different from the audited domain
            if parsed_link.netloc and parsed_link.netloc != audit_netloc:
                # Reconstruct the URL without fragments/query params for cleaner checking
                clean_link = parsed_link.scheme + "://" + parsed_link.netloc + parsed_link.path
                external_links.add(clean_link)

    # Save the list to a file
    list_path = "reports/external_links_to_check.txt"
    with open(list_path, "w", encoding="utf-8") as f:
        f.write("# External links found during the SEO Audit (Check these asynchronously):\n")
        for link in sorted(list(external_links)):
            f.write(link + "\n")
            
    print(f"\n✅ Saved {len(external_links)} unique external links to {list_path}")

