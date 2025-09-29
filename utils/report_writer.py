import json
import pandas as pd
import numpy as np
import datetime

# --- Score Calculation (Run AFTER the crawl finishes) ---

def calculate_seo_score_page(page_data):
    """Calculates a simple SEO score for a single page (out of 100)."""
    score = 100
    penalties = 0
    
    status = page_data.get("status_code", 0)
    
    # CRITICAL SERVER ERRORS
    if status >= 500: penalties += 50
    if status >= 400 and status != 404: penalties += 30 
    if status == 0 or status == 404: penalties += 10 # 404 penalty is lower
    
    # Skip complex content penalties if page is not crawlable
    if page_data.get("is_crawlable", False):
        # On-Page & Content Checks
        word_count = page_data.get("content", {}).get("word_count", 0)
        if page_data.get("meta", {}).get("title") in ["", None]: penalties += 10
        if page_data.get("meta", {}).get("description") in ["", None]: penalties += 10
        if page_data.get("headings", {}).get("h1", 0) != 1: penalties += 5 
        if word_count < 250: penalties += 10
        
        # Usability & Link Checks (Standard audit only checks will have data)
        if page_data.get("mobile", {}).get("mobile_friendly", False) == False: penalties += 5
        if page_data.get("links", {}).get("broken"): 
             penalties += min(10, len(page_data["links"]["broken"]) * 1) 
        if page_data.get("images", {}).get("missing_alt", 0) > 0: penalties += 5
             
        # Local SEO Penalty (only applies if site is local-focused - we assume yes for a basic audit)
        local_seo = page_data.get("local_seo", {}).get("nap_found", {})
        if not (local_seo.get("phone_format_found") and local_seo.get("address_keywords_found")):
             penalties += 5 # Minor penalty if NAP is not easily found
        
        # Analytics Penalty
        analytics = page_data.get("analytics", {}).get("tracking_setup", {})
        if not (analytics.get("google_analytics_found") or analytics.get("google_tag_manager_found")):
             penalties += 5 # Minor penalty if no common tracking is found

    final_score = max(0, score - penalties)
    return final_score

def calculate_seo_score_full(all_page_results, domain_checks):
    """Aggregates all page data, calculates overall scores, and returns full report dictionary."""
    
    df = pd.json_normalize(all_page_results)
    
    # 1. Calculate Per-Page Scores and Aggregate
    df['page_score'] = df.apply(calculate_seo_score_page, axis=1)
    
    # 2. Domain-Level Penalties (Higher weight)
    domain_penalty = 0
    if not domain_checks.get("ssl", {}).get("valid_ssl"): domain_penalty += 30
    if domain_checks.get("robots_sitemap", {}).get("robots.txt") != "found": domain_penalty += 10
    
    # 3. Overall Site Score (Weighted Average)
    critical_errors_count = df[df['status_code'] >= 500].shape[0]
    total_pages = df.shape[0]
    
    avg_page_score = df['page_score'].mean() if total_pages > 0 else 0
    critical_penalty = (critical_errors_count / total_pages) * 50 if total_pages > 0 else 0
    
    final_site_score = max(0, avg_page_score - domain_penalty - critical_penalty)

    # 4. Generate Key Metrics (Summary Section)
    summary_metrics = {
        "overall_score": round(final_site_score, 2),
        "total_pages_crawled": total_pages,
        "indexable_pages": df[df['status_code'] == 200].shape[0],
        "broken_pages_4xx": df[(df['status_code'] >= 400) & (df['status_code'] < 500)].shape[0],
        "server_errors_5xx": critical_errors_count,
        "no_h1_pages": df[df['headings.h1'] == 0].shape[0] + df[df['headings.h1'] > 1].shape[0],
        "thin_content_pages": df[df['content.word_count'] < 250].shape[0],
        "missing_title_pages": df['meta.title'].apply(lambda x: not x or x == 'N/A').sum(),
        "total_broken_links_found": df['links.broken'].apply(lambda x: len(x) if isinstance(x, list) else 0).sum(),
    }
    
    # Combine everything for the final JSON/Markdown report
    full_report_data = {
        "domain_info": domain_checks,
        "summary_metrics": summary_metrics,
        "detailed_page_data": df.to_dict(orient='records')
    }
    
    return full_report_data

# --- Report Generation (Run AFTER calculation) ---

def write_summary_report(data, json_path, md_path):
    """Writes the final comprehensive full-site JSON and Markdown report, adjusting content by audit_level."""
    
    # Add timestamp for the current run
    if 'timestamp' not in data['domain_info']:
         data['domain_info']['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save raw JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Prepare Markdown Report
    summary = data["summary_metrics"]
    domain = data["domain_info"]
    competitor = domain.get("competitor_data", {})
    audit_level = domain.get('audit_level', 'standard')
    
    # Find home page data for Local SEO/Analytics checks
    your_homepage_data = next((p for p in data['detailed_page_data'] if p.get('crawl_depth', -1) == 0), {})
    local_seo_data = your_homepage_data.get('local_seo', {}).get('nap_found', {})
    analytics_data = your_homepage_data.get('analytics', {}).get('tracking_setup', {})
    
    with open(md_path, "w", encoding="utf-8") as f:
        # --- TITLE ADJUSTMENT ---
        f.write(f"# 👑 PROFESSIONAL {audit_level.upper()} SEO AUDIT REPORT\n")
        f.write(f"## 🌐 Audited Domain: **{domain['url']}**\n")
        f.write(f"**Date:** {domain.get('timestamp', 'N/A')}\n")
        f.write(f"**Audit Level:** {audit_level.upper()}\n")
        f.write(f"**Total Pages Crawled:** {summary['total_pages_crawled']}\n")
        
        # --- AUDIT LEVEL EXPLANATION ---
        if audit_level == 'basic':
            f.write("\n### ⚠️ Basic Audit Note: Checks Skipped\n")
            f.write("This is a lightweight audit. Advanced checks like **Broken Link Validation**, **Schema Markup**, and **In-Depth Keyword Analysis** were **skipped** for faster results. Run the **Standard Audit** for full detail.\n")
        
        f.write("\n---\n")

        # --- 1. Executive Summary & Site Score ---
        f.write("## 1. Executive Summary & Site Score\n")
        f.write(f"### 1.1 Overall Site Quality Score: **{summary['overall_score']}/100**\n")
        
        status = 'EXCELLENT' if summary['overall_score'] > 90 else 'GOOD' if summary['overall_score'] > 70 else 'CRITICAL'
        f.write(f"**Overall Health Status:** **{status}**\n")
        
        f.write("\n---\n")
        
        # --- 2. Technical Health Metrics ---
        f.write("## 2. Technical Health Metrics\n")
        
        ssl_status = '✅ Valid HTTPS' if domain.get('ssl', {}).get('valid_ssl') else '❌ CRITICAL: No Valid SSL'
        f.write(f"- **SSL Security:** {ssl_status}\n")
        f.write(f"- **Robots.txt:** {domain.get('robots_sitemap', {}).get('robots.txt')}\n")
        f.write(f"- **Total Server Errors (5xx):** **{summary['server_errors_5xx']}**\n")
        f.write(f"- **Total Broken Pages (4xx):** **{summary['broken_pages_4xx']}**\n")
        
        # BROKEN LINKS ONLY SHOWN FOR STANDARD AUDIT
        if audit_level == 'standard':
             if 'total_broken_links_found' in summary:
                 f.write(f"- **Total Broken Outgoing Links:** **{summary['total_broken_links_found']}**\n")
        
        f.write("\n---\n")
        
        # --- 3. Local SEO Health (Main Page Check) ---
        f.write("## 3. Local SEO Health (Main Page Check)\n")
        
        nap_status = '✅ Found' if (local_seo_data.get('phone_format_found') and local_seo_data.get('address_keywords_found')) else '❌ Missing Key NAP Elements'
        gmb_status = '✅ Found Google Map/Embed' if local_seo_data.get('gmb_link_found') else '⚠️ GMB Proxy Link/Map Not Found'

        f.write(f"- **NAP Consistency Proxy:** **{nap_status}**\n")
        f.write(f"- **GMB/Map Integration:** **{gmb_status}**\n")
        f.write("\n---\n")

        # --- 4. Analytics & Tracking Check (Main Page) ---
        f.write("## 4. Analytics & Tracking Check (Main Page)\n")
        
        ga_status = '✅ GA/GTM Script Detected' if (analytics_data.get('google_analytics_found') or analytics_data.get('google_tag_manager_found')) else '❌ No GA/GTM Script Detected'
        other_status = '✅ Other Scripts Detected' if analytics_data.get('other_analytics_found') else '— None Detected'

        f.write(f"- **Google Tracking:** **{ga_status}**\n")
        f.write(f"- **Other Tracking Scripts:** **{other_status}**\n")
        f.write("    *NOTE: This is a static code check only. Event/Goal tracking cannot be verified.*\n")
        f.write("\n---\n")
        
        # --- 5. Competitor Analysis ---
        f.write("## 5. Competitor Analysis (Main Page)\n")
        if competitor.get("status") == "success":
            f.write(f"**Competitor URL:** {competitor.get('url')}\n\n")
            
            f.write("| Metric | Your Site (Home) | Competitor |\n")
            f.write("| :--- | :--- | :--- |\n")
            
            your_title_len = len(your_homepage_data.get('meta', {}).get('title', ''))
            your_h1 = your_homepage_data.get('headings', {}).get('h1', 0)
            your_words = your_homepage_data.get('content', {}).get('word_count', 0)
            
            comp_title_len = competitor.get('title_length', 'N/A')
            comp_h1 = competitor.get('h1_count', 'N/A')
            comp_words = competitor.get('word_count', 'N/A')
            
            f.write(f"| Title Length (Chars) | {your_title_len} | {comp_title_len} |\n")
            f.write(f"| H1 Count | {your_h1} | {comp_h1} |\n")
            f.write(f"| Word Count | {your_words} | {comp_words} |\n")
            f.write(f"| SSL Valid | {'✅' if domain.get('ssl', {}).get('valid_ssl') else '❌'} | {'✅' if competitor.get('ssl_valid') else '❌'} |\n")
        else:
             f.write(f"Competitor analysis skipped or failed: {competitor.get('error', 'N/A')}\n")

        f.write("\n---\n")
        
        # --- 6. Content & On-Page Issues ---
        f.write("## 6. Top On-Page Issues\n")
        f.write(f"This is a count of pages with the following issues:\n\n")

        f.write(f"- **Pages with Missing Title Tags:** **{summary['missing_title_pages']}**\n")
        f.write(f"- **Pages with Missing/Multiple H1:** **{summary['no_h1_pages']}**\n")
        f.write(f"- **Pages with Thin Content (<250 words):** **{summary['thin_content_pages']}**\n")
        f.write(f"- **Non-Indexable Pages (Redirects/Errors):** **{summary['total_pages_crawled'] - summary['indexable_pages']}**\n")
        
        f.write("\n---\n")
        
        # --- 7. Call to Action (Recommendations) ---
        f.write("## 7. Professional Recommendations\n")
        
        if summary['server_errors_5xx'] > 0 or not domain.get('ssl', {}).get('valid_ssl'):
            f.write("### 🔴 CRITICAL ACTION REQUIRED\n")
            f.write("- **Server Errors (5xx):** Immediately check server logs. These pages are blocked from search engines.\n")
            if not domain.get('ssl', {}).get('valid_ssl'):
                f.write("- **No SSL:** Must be fixed. Google flags non-HTTPS sites as insecure.\n")
        
        if summary['broken_pages_4xx'] > 0 or summary['thin_content_pages'] > 0:
            f.write("### ⚠️ HIGH PRIORITY FIXES\n")
            f.write(f"- **Fix {summary['broken_pages_4xx']} Broken Pages:** Implement 301 redirects or restore content.\n")
            f.write(f"- **Review {summary['thin_content_pages']} Thin Pages:** Expand content to be more authoritative.\n")
            f.write("- **Download the `full_site_report.json` artifact for the full, page-by-page data grid.**\n")
            
        f.write("\n*Disclaimer: This audit is based on open-source crawling and does not include external API data (Google Search Console, Backlink profiles, full plagiarism checks, or client-side event tracking).*")
