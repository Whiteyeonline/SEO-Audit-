import json
import pandas as pd
import numpy as np
import datetime

def calculate_seo_score_page(page_data):
    """Calculates a simple SEO score for a single page (out of 100)."""
    score = 100
    penalties = 0
    status = page_data.get("status_code", 0)
    
    if status >= 500: penalties += 50
    if status >= 400 and status != 404: penalties += 30 
    if status == 0 or status == 404: penalties += 10
    
    if page_data.get("is_crawlable", False):
        word_count = page_data.get("content", {}).get("word_count", 0)
        if page_data.get("meta", {}).get("title") in ["", None]: penalties += 10
        if page_data.get("meta", {}).get("description") in ["", None]: penalties += 10
        if page_data.get("headings", {}).get("h1", 0) != 1: penalties += 5 
        if word_count < 250: penalties += 10
        
        if page_data.get("mobile", {}).get("mobile_friendly", False) == False: penalties += 5
        
        # Check for broken links only if the key exists (i.e., if it was a Standard Audit)
        if page_data.get("links", {}).get("broken"): 
             penalties += min(10, len(page_data["links"]["broken"]) * 1) 
        
        if page_data.get("images", {}).get("missing_alt", 0) > 0: penalties += 5
             
        local_seo = page_data.get("local_seo", {}).get("nap_found", {})
        if not (local_seo.get("phone_format_found") and local_seo.get("address_keywords_found")):
             penalties += 5
        
        analytics = page_data.get("analytics", {}).get("tracking_setup", {})
        if not (analytics.get("google_analytics_found") or analytics.get("google_tag_manager_found")):
             penalties += 5

    final_score = max(0, score - penalties)
    return final_score

def calculate_seo_score_full(all_page_results, domain_checks):
    """Aggregates all page data, calculates overall scores, and returns full report dictionary."""
    df = pd.json_normalize(all_page_results)
    
    if df.empty:
        return {
            "domain_info": domain_checks,
            "summary_metrics": {
                "overall_score": 0,
                "total_pages_crawled": 0,
                "indexable_pages": 0,
                "broken_pages_4xx": 0,
                "server_errors_5xx": 0,
                "no_h1_pages": 0,
                "thin_content_pages": 0,
                "missing_title_pages": 0,
                "total_broken_links_found": 0
            },
            "detailed_page_data": []
        }
        
    df['page_score'] = df.apply(calculate_seo_score_page, axis=1)
    
    domain_penalty = 0
    if not domain_checks.get("ssl", {}).get("valid_ssl"): domain_penalty += 30
    if domain_checks.get("robots_sitemap", {}).get("robots.txt") != "found": domain_penalty += 10
    
    critical_errors_count = df[df['status_code'] >= 500].shape[0]
    total_pages = df.shape[0]
    
    avg_page_score = df['page_score'].mean() if total_pages > 0 else 0
    critical_penalty = (critical_errors_count / total_pages) * 50 if total_pages > 0 else 0
    
    final_site_score = max(0, avg_page_score - domain_penalty - critical_penalty)

    broken_links_count = 0
    if 'links.broken' in df.columns:
        broken_links_count = df['links.broken'].apply(lambda x: len(x) if isinstance(x, list) else 0).sum()

    # FIX: Convert numpy data types to standard Python data types for JSON serialization
    summary_metrics = {
        "overall_score": float(round(final_site_score, 2)),
        "total_pages_crawled": int(total_pages),
        "indexable_pages": int(df[df['status_code'] == 200].shape[0]),
        "broken_pages_4xx": int(df[(df['status_code'] >= 400) & (df['status_code'] < 500)].shape[0]),
        "server_errors_5xx": int(critical_errors_count),
        "no_h1_pages": int(df[df['headings.h1'] == 0].shape[0] + df[df['headings.h1'] > 1].shape[0]),
        "thin_content_pages": int(df[df['content.word_count'] < 250].shape[0]),
        "missing_title_pages": int(df['meta.title'].apply(lambda x: not x or x == 'N/A').sum()),
        "total_broken_links_found": int(broken_links_count),
    }
    
    # We must also ensure detailed page data is serializable.
    detailed_page_data = []
    for record in df.to_dict(orient='records'):
        for k, v in record.items():
            if isinstance(v, (np.integer, np.int64)):
                record[k] = int(v)
            elif isinstance(v, (np.floating, np.float64)):
                record[k] = float(v)
        detailed_page_data.append(record)
        
    full_report_data = {
        "domain_info": domain_checks,
        "summary_metrics": summary_metrics,
        "detailed_page_data": detailed_page_data
    }
    
    return full_report_data


# --- Helper Functions for Detailed Checklist ---

def _write_meta_section(f, data):
    title = data.get("meta", {}).get("title", "")
    description = data.get("meta", {}).get("description", "")
    url = data.get("url")
    
    f.write("## 📝 Search Result Summary & Meta Tags\n\n")
    
    # SERP Snippet Simulation
    f.write("### Search Engine Snippet Simulation\n\n")
    f.write(f"```\n")
    f.write(f"TITLE: {title or '[MISSING TITLE]'}\n")
    f.write(f"URL: {url}\n")
    f.write(f"DESCRIPTION: {description or '[MISSING DESCRIPTION]'}\n")
    f.write(f"```\n\n")
    
    f.write("### Findings\n")
    f.write(f"* **Title Tag:** {'✅ Found' if title else '❌ Missing'}. Length: {len(title)} characters.\n")
    f.write(f"* **Meta Description:** {'✅ Found' if description else '❌ Missing'}. Length: {len(description)} characters.\n\n")
    
    f.write("### Issues & Solutions\n")
    issues = False
    
    if not title:
        f.write("* ❌ **ISSUE:** Title tag is missing or empty.\n")
        f.write("  * **SOLUTION:** Add a unique, keyword-focused title tag (optimal length: 50-60 chars) for every page.\n")
        issues = True
    elif len(title) < 30 or len(title) > 60:
        f.write(f"* ⚠️ **ISSUE:** Title length ({len(title)} chars) is outside the optimal range.\n")
        f.write("  * **SOLUTION:** Aim for 50-60 characters to maximize click-through rate (CTR) and visibility.\n")
        issues = True
        
    if not description:
        f.write("* ❌ **ISSUE:** Meta description is missing or empty.\n")
        f.write("  * **SOLUTION:** Write a compelling description (optimal length: 150-160 chars) to entice clicks, even though it's not a ranking factor.\n")
        issues = True
    
    if not issues:
        f.write("* ✅ **STATUS:** Title and Description tags are present. Further action is likely only needed for optimization (e.g., keyword focus).\n")
    
    f.write("\n---\n")

def _write_url_canonical_section(f, data):
    url_data = data.get("url_structure", {})
    canonical_data = data.get("canonical", {})
    
    f.write("## 🔗 URL Structure and Canonicalization\n\n")
    
    f.write("### Findings\n")
    f.write(f"* **URL Path:** `{url_data.get('path', 'N/A')}`\n")
    f.write(f"* **Clean URL:** {'✅ Yes' if url_data.get('is_clean') else '❌ No (Contains parameters)'}\n")
    f.write(f"* **Canonical Tag Found:** {'✅ Yes' if canonical_data.get('canonical_url') else '❌ No'}\n")
    f.write(f"* **Canonical URL:** `{canonical_data.get('canonical_url', 'N/A')}`\n\n")
    
    f.write("### Issues & Solutions\n")
    issues = False
    
    if not url_data.get('is_clean'):
        f.write("* ⚠️ **ISSUE:** URL contains non-essential parameters (e.g., `?sa=t`, `&amp;`).\n")
        f.write("  * **SOLUTION:** Configure the site to use short, descriptive, and keyword-rich URLs without tracking parameters where possible.\n")
        issues = True

    if not canonical_data.get('canonical_url'):
        f.write("* ❌ **ISSUE:** Canonical tag is missing. This risks duplicate content issues.\n")
        f.write("  * **SOLUTION:** Add a self-referencing canonical tag to every page to explicitly signal the preferred version to search engines.\n")
        issues = True
    
    if not issues:
        f.write("* ✅ **STATUS:** URL is clean, or Canonical tag is correctly managing the page version.\n")
    
    f.write("\n---\n")

def _write_content_headings_section(f, data):
    heading_data = data.get("headings", {})
    content_data = data.get("content", {})
    
    f.write("## 📄 Content and Heading Structure\n\n")
    
    f.write("### Findings\n")
    f.write(f"* **Total Word Count:** **{content_data.get('word_count', 0)}** words.\n")
    # This value is pulled from the crawled data, which is where the error was previously.
    f.write(f"* **Readability Score (Flesch):** **{round(content_data.get('readability_score', 0.0), 2)}** (Target > 60).\n")
    f.write(f"* **H1 Tags Found:** **{heading_data.get('h1', 0)}**\n")
    f.write(f"* **H2 Tags Found:** **{heading_data.get('h2', 0)}**\n\n")

    f.write("### Issues & Solutions\n")
    issues = False
    
    h1_count = heading_data.get('h1', 0)
    if h1_count != 1:
        f.write(f"* ❌ **ISSUE:** Page has **{h1_count}** H1 tags (should be exactly 1).\n")
        f.write("  * **SOLUTION:** Ensure every page has one unique H1 tag that summarizes the content and includes the main target keyword.\n")
        issues = True
        
    word_count = content_data.get('word_count', 0)
    if word_count < 250:
        f.write(f"* ⚠️ **ISSUE:** Content is considered **thin** (Word Count: {word_count}).\n")
        f.write("  * **SOLUTION:** Expand the content to provide more value, context, and semantic keywords, aiming for > 500 words for informational pages.\n")
        issues = True
        
    if content_data.get('readability_score', 0.0) < 50 and word_count > 100:
        f.write(f"* ⚠️ **ISSUE:** Readability score is low ({round(content_data.get('readability_score', 0.0), 2)}). Content may be too complex.\n")
        f.write("  * **SOLUTION:** Use shorter sentences, simpler language, and break up large paragraphs to improve engagement.\n")
        issues = True
        
    if not issues:
        f.write("* ✅ **STATUS:** Content and heading structure meets basic SEO best practices.\n")
    
    f.write("\n---\n")

def _write_technical_ux_section(f, data):
    image_data = data.get("images", {})
    mobile_data = data.get("mobile", {})
    local_data = data.get("local_seo", {}).get("nap_found", {})
    analytics_data = data.get("analytics", {}).get("tracking_setup", {})
    
    f.write("## 💻 Technical & User Experience Checklist\n\n")

    f.write("### Findings\n")
    f.write(f"* **Mobile Friendly (Viewport):** {'✅ Yes' if mobile_data.get('mobile_friendly') else '❌ No'}\n")
    f.write(f"* **Images Missing ALT Tag:** **{image_data.get('missing_alt', 0)}** of {image_data.get('total', 0)} images.\n")
    f.write(f"* **Analytics Setup (GA/GTM):** {'✅ Detected' if (analytics_data.get('google_analytics_found') or analytics_data.get('google_tag_manager_found')) else '❌ Not Detected'}\n")
    
    f.write(f"* **Local NAP Proxy:** {'✅ Found Key Elements' if (local_data.get('phone_format_found') and local_data.get('address_keywords_found')) else '⚠️ Missing'}\n\n")

    f.write("### Issues & Solutions\n")
    issues = False
    
    if not mobile_data.get('mobile_friendly'):
        f.write("* ❌ **ISSUE:** Mobile viewport meta tag is missing.\n")
        f.write("  * **SOLUTION:** Add `<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">` to the `<head>` section. This is critical for mobile rankings.\n")
        issues = True
        
    if image_data.get('missing_alt', 0) > 0:
        f.write(f"* ⚠️ **ISSUE:** **{image_data.get('missing_alt')}** images are missing `alt` attributes.\n")
        f.write("  * **SOLUTION:** Add descriptive, keyword-optimized alt text to all informational images to improve accessibility and image search ranking.\n")
        issues = True
        
    if not (analytics_data.get('google_analytics_found') or analytics_data.get('google_tag_manager_found')):
        f.write("* ❌ **ISSUE:** No Google Analytics or GTM script was found.\n")
        f.write("  * **SOLUTION:** Verify that your site's tracking code is correctly implemented to avoid data loss.\n")
        issues = True
        
    if not issues:
        f.write("* ✅ **STATUS:** Technical on-page elements meet key requirements.\n")
    
    f.write("\n---\n")

def _write_advanced_standard_section(f, data):
    schema_data = data.get("schema", {})
    keywords_data = data.get("keywords", {})
    links_data = data.get("links", {})
    
    f.write("## ✨ Advanced Checks (Standard Audit Only)\n\n")
    
    f.write("### Findings\n")
    f.write(f"* **Schema Markup Tags:** **{schema_data.get('found_count', 0)}** found (e.g., Article, Breadcrumb, FAQ).\n")
    f.write(f"* **Top Keywords:** {', '.join(keywords_data.get('top_keywords', [])) or 'N/A'}\n")
    f.write(f"* **Broken Outgoing Links:** **{len(links_data.get('broken', []))}** broken external links found.\n\n")

    f.write("### Issues & Solutions\n")
    issues = False
    
    if schema_data.get('found_count', 0) == 0:
        f.write("* ⚠️ **OPPORTUNITY:** No Structured Data (Schema) found.\n")
        f.write("  * **SOLUTION:** Implement relevant Schema markup (e.g., Article, Review, LocalBusiness) to qualify for rich snippets in search results.\n")
        issues = True
        
    if len(links_data.get('broken', [])) > 0:
        f.write(f"* ❌ **ISSUE:** **{len(links_data.get('broken', []))}** broken external links were identified. (Sample: {', '.join(links_data.get('broken', [])[:3])}...)\n")
        f.write("  * **SOLUTION:** Replace or remove broken links. Too many 404 links damage trust and user experience.\n")
        issues = True
        
    if not keywords_data.get('top_keywords', []):
        f.write("* ⚠️ **OPPORTUNITY:** Keyword density analysis failed or page has no text.\n")
        f.write("  * **SOLUTION:** Ensure content is present (check Word Count) and focused on a clear primary topic.\n")
        issues = True
        
    if not issues:
        f.write("* ✅ **STATUS:** Advanced on-page features are implemented, or no critical issues found.\n")

    f.write("\n---\n")


# --- Main Report Writer Function ---

def write_summary_report(data, json_path, md_path):
    """Writes the final comprehensive full-site JSON and PROFESSIONAL Markdown report."""
    
    if 'timestamp' not in data['domain_info']:
         data['domain_info']['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save raw JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    if not data['detailed_page_data']:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# 👑 PROFESSIONAL SEO AUDIT REPORT\n\n")
            f.write(f"## ❌ CRITICAL CRAWL FAILURE\n\n")
            f.write(f"The audit failed to extract any content from the starting URL **{data['domain_info']['url']}**.\n\n")
            f.write("### Potential Causes and Solutions:\n")
            f.write("* **Check 1: Redirects:** The URL may be a complex redirect or Google wrapper (e.g., `google.com/url?...`). **Solution:** Use the final, clean destination URL.\n")
            f.write("* **Check 2: JavaScript:** The page content may require JavaScript rendering. **Solution:** This tool is a static crawler; use an alternative tool for JS-heavy sites.\n")
            f.write("* **Check 3: Blocking:** The site's `robots.txt` or server is actively blocking the crawler's user agent.\n")
        return

    summary = data["summary_metrics"]
    domain = data["domain_info"]
    competitor = domain.get("competitor_data", {})
    audit_level = domain.get('audit_level', 'standard')
    
    your_homepage_data = data['detailed_page_data'][0]
    
    with open(md_path, "w", encoding="utf-8") as f:
        
        f.write(f"# 👑 PROFESSIONAL {audit_level.upper()} SEO AUDIT REPORT\n\n")
        f.write(f"## 🎯 Executive Summary for **{domain['url']}**\n\n")
        f.write(f"**Date:** {domain.get('timestamp', 'N/A')} | **Audit Level:** {audit_level.upper()} | **Crawl Type:** On-Page Only\n\n")

        status_text, emoji = "", ""
        if summary['overall_score'] > 90: status_text, emoji = "Excellent (Maintain Strategy)", "✅"
        elif summary['overall_score'] > 75: status_text, emoji = "Good (Minor Improvements Needed)", "🟢"
        elif summary['overall_score'] > 50: status_text, emoji = "Fair (High-Priority Fixes Needed)", "🟡"
        else: status_text, emoji = "Poor (CRITICAL Intervention Required)", "🛑"

        f.write("--- \n")
        f.write("| Metric | Result | Status |\n")
        f.write("| :--- | :--- | :--- |\n")
        f.write(f"| **Overall Site Health Score** | **{summary['overall_score']}/100** | **{emoji} {status_text}** |\n")
        f.write("--- \n\n")

        f.write("## 💡 Top Actionable Priority\n\n")
        if not domain.get('ssl', {}).get('valid_ssl'):
            f.write("1. 🔴 **CRITICAL: Install Valid SSL Certificate.** Your site is flagged as insecure.\n")
        elif your_homepage_data.get("status_code") >= 400:
            f.write(f"1. 🔴 **CRITICAL: Fix Status Code {your_homepage_data['status_code']}.** This page is not indexable and must be fixed with 301/200 codes.\n")
        elif not your_homepage_data.get("meta", {}).get("title"):
             f.write("1. 🔴 **CRITICAL: Add Title Tag.** The page is missing its most important ranking factor.\n")
        elif your_homepage_data.get("headings", {}).get("h1", 0) != 1:
             f.write(f"1. 🟠 **HIGH: Fix H1 Count.** Page has {your_homepage_data.get('headings', {}).get('h1', 0)} H1 tags (should be exactly 1).\n")
        else:
             f.write("1. ✅ **STATUS:** No critical issues found. Focus on the medium priority items below.\n")
        
        f.write("\n---\n")
        
        f.write("# 📝 DETAILED ON-PAGE AUDIT CHECKLIST\n\n")

        _write_meta_section(f, your_homepage_data)
        _write_url_canonical_section(f, your_homepage_data)
        _write_content_headings_section(f, your_homepage_data)
        _write_technical_ux_section(f, your_homepage_data)
        
        if audit_level == 'standard':
            _write_advanced_standard_section(f, your_homepage_data)
            
        f.write("## 🌎 Domain Health Summary\n\n")
        f.write(f"* **SSL Status:** {'✅ Valid HTTPS' if domain.get('ssl', {}).get('valid_ssl') else '❌ FAILED (Requires Immediate Action)'}\n")
        f.write(f"* **Robots.txt:** {'✅ Found' if domain.get('robots_sitemap', {}).get('robots.txt') == 'found' else '❌ Missing'}\n")
        f.write(f"* **Sitemap.xml:** {'✅ Found' if domain.get('robots_sitemap', {}).get('sitemap') == 'found' else '⚠️ Not Found'}\n")

        f.write("\n---\n")
        
        f.write("## 📈 Competitor Analysis (vs. Your Homepage)\n\n")
        if competitor.get("status") == "success":
            your_title_len = len(your_homepage_data.get('meta', {}).get('title', ''))
            your_h1 = your_homepage_data.get('headings', {}).get('h1', 0)
            your_words = your_homepage_data.get('content', {}).get('word_count', 0)
            
            comp_title_len = competitor.get('title_length', 'N/A')
            comp_h1 = competitor.get('h1_count', 'N/A')
            comp_words = competitor.get('word_count', 'N/A')
            
            f.write(f"**Competitor URL:** [{competitor.get('url')}]({competitor.get('url')})\n\n")

            f.write("| Metric | Your Site | Competitor |\n")
            f.write("| :--- | :--- | :--- |\n")
            f.write(f"| Title Length (Chars) | {your_title_len} | {comp_title_len} |\n")
            f.write(f"| H1 Count | {your_h1} | {comp_h1} |\n")
            f.write(f"| Word Count | {your_words} | {comp_words} |\n")
        else:
             f.write(f"Competitor analysis skipped or failed: {competitor.get('error', 'No competitor URL provided.')}\n")

        f.write("\n---\n")
        
        if audit_level == 'basic':
            f.write("## ℹ️ Audit Scope Disclaimer\n")
            f.write("This **Basic Audit** intentionally skipped advanced, time-consuming checks (Schema, Broken Link Validation, Keyword Analysis) to provide quick feedback.\n")
            f.write("For a complete analysis, run the **Standard Audit**.\n\n")
