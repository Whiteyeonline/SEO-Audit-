import json
from datetime import datetime

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

    avg_score = int(round(sum([p["seo_score"] for p in page_scores]) / len(page_scores))) if page_scores else 100

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

    # Use existing calculated scores (prevents redundant calculation)
    avg_score = summary.get('seo_score', 100)
    page_scores = data.get('page_scores', []) 

    # Write JSON report
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Write Markdown report
    with open(md_path, "w", encoding="utf-8") as f:
        # Title and summary
        f.write(f"# 👑 PROFESSIONAL {audit_level.upper()} SEO AUDIT REPORT for {domain_name}\n\n")
        f.write(f"**Audit Date:** {timestamp}\n\n")
        f.write("## 🎯 Executive Summary\n\n")
        f.write("| Metric | Value |\n")
        for k, v in summary.items():
            f.write(f"| {k.replace('_',' ').title()} | {v} |\n")
        f.write("\n---\n")

        # Domain-Level Technical Checks section (FIX: Includes SSL)
        f.write("## 🔒 Domain-Level Technical Checks\n\n")
        ssl_status = data['domain_info'].get('ssl', {}).get('valid_ssl', False)
        robots_status = data['domain_info'].get('robots_sitemap', {}).get('robots.txt', 'N/A')
        sitemap_status = data['domain_info'].get('robots_sitemap', {}).get('sitemap.xml', 'N/A')
        load_time = data['domain_info'].get('performance', {}).get('load_time_ms', 'N/A')
        
        f.write(f"- **SSL Certificate:** {'✅ Valid HTTPS' if ssl_status else '❌ Missing or Invalid'}\n")
        f.write(f"- **robots.txt:** {'✅ Found' if 'found' in robots_status else '❌ Not Found'}\n")
        f.write(f"- **sitemap.xml:** {'✅ Found' if 'found' in sitemap_status else '⚠️ Not Found'}\n")
        f.write(f"- **Initial Load Time:** {load_time}ms (Target: < 500ms)\n")
        f.write("\n---\n")


        # SEO Score section
        f.write(f"## ⭐ SEO Score Summary\n")
        f.write(f"- **Average SEO Score:** {avg_score}/100\n")
        for p in page_scores:
            url_display = p["url"] if p["url"] else "Homepage"
            f.write(f"    - {url_display}: {p['seo_score']}/100\n")
        f.write("\n---\n")

        # Top Actionable Priority
        homepage = data['detailed_page_data'][0] if data['detailed_page_data'] else {}
        issues = homepage.get('issues', [])
        solutions = homepage.get('solutions', [])
        homepage_score = data['page_scores'][0]['seo_score'] if data['page_scores'] else 100
        
        f.write("## 💡 Top Actionable Priority\n\n")
        f.write(f"**Homepage SEO Score:** {homepage_score}/100\n")
        if issues:
            for i, (issue, solution) in enumerate(zip(issues, solutions), 1):
                f.write(f"{i}. {issue} Solution: {solution}\n")
        else:
            f.write("1. ✅ STATUS: No critical issues found. Focus on medium priority items below.\n")
        f.write("\n---\n")

        # Per-page audit: summary, issues, solutions, SEO score
        f.write("# 📝 DETAILED ON-PAGE AUDIT CHECKLIST\n\n")
        for idx, page in enumerate(data['detailed_page_data']):
            url = page.get("url", "")
            issues = page.get('issues', [])
            solutions = page.get('solutions', [])
            score = data['page_scores'][idx]['seo_score'] if idx < len(data['page_scores']) else 100

            f.write(f"### Page {idx+1} ({domain_name}): [{url}]({url})\n")
            f.write(f"- **SEO Score:** {score}/100\n")
            f.write(f"- **Title:** {page.get('meta',{}).get('title','[MISSING]')}\n")
            f.write(f"- **Meta Description:** {page.get('meta',{}).get('description','[MISSING]')}\n")
            f.write(f"- **H1 Tags:** {page.get('headings',{}).get('h1',0)}\n")
            f.write(f"- **Word Count:** {page.get('content',{}).get('word_count',0)}\n")
            f.write(f"- **Mobile Friendly:** {'✅' if page.get('mobile',{}).get('mobile_friendly') else '❌'}\n")
            backlinks = page.get("backlinks", {})
            f.write("#### 🌐 Backlinks/External Links\n")
            f.write(f"- **Internal Link Count:** {backlinks.get('internal_link_count','N/A')}\n")
            f.write(f"- **External Link Count:** {backlinks.get('external_link_count','N/A')}\n")
            f.write(f"- **Sample External Domains:** {', '.join(backlinks.get('sample_external_domains',[]))}\n")
            f.write("- **Note:** This audit lists the external domains your site links to. To discover who links to your site (backlinks), use Google Search Console or paid tools.\n")
            f.write("\n#### Issues Found & Solutions\n")
            if issues:
                for i, (issue, solution) in enumerate(zip(issues, solutions), 1):
                    f.write(f"{i}. {issue} Solution: {solution}\n")
            else:
                f.write("✅ No major issues found on this page.\n")
            f.write("\n---\n")

        # Competitor Section
        f.write("## 📈 Competitor Analysis\n")
        if competitor.get("status") == "success":
            f.write(f"- **Competitor URL:** [{competitor.get('url')}]({competitor.get('url')})\n")
            f.write(f"- **Title Length:** {competitor.get('title_length','N/A')}\n")
            f.write(f"- **H1 Count:** {competitor.get('h1_count','N/A')}\n")
            f.write(f"- **Word Count:** {competitor.get('word_count','N/A')}\n")
        else:
            f.write(f"Competitor analysis skipped or failed: {competitor.get('error','No competitor URL provided.')}\n")
        f.write("\n---\n")

        # Disclaimer & Backlink Help
        f.write("## ℹ️ Audit Scope Disclaimer and Backlink Help\n")
        f.write("This audit covers on-page and technical SEO. It **does not** show who links to your site (backlinks).\n")
        f.write("To check your real backlinks for free:\n")
        f.write("- If you own the site, use [Google Search Console](https://search.google.com/search-console/about), go to 'Links' → 'External Links'.\n")
        f.write("- For a few free checks, try online tools like [ahrefs.com/backlink-checker](https://ahrefs.com/backlink-checker) (limited results).\n")
        f.write("- All issues above include a solution you can do yourself, without paid tools.\n")
        f.write("If you want more help fixing issues, contact us!\n")
        f.write(f"\n---\n**Audit ID:** `{timestamp}`\n")
        
