import json
import pandas as pd
import numpy as np
import datetime

# --- Utility Functions (Score Calculation - Same as previous, correct version) ---

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
    # ... (score aggregation logic is correct and omitted for brevity)
    df = pd.json_normalize(all_page_results)
    df['page_score'] = df.apply(calculate_seo_score_page, axis=1)
    
    domain_penalty = 0
    if not domain_checks.get("ssl", {}).get("valid_ssl"): domain_penalty += 30
    if domain_checks.get("robots_sitemap", {}).get("robots.txt") != "found": domain_penalty += 10
    
    critical_errors_count = df[df['status_code'] >= 500].shape[0]
    total_pages = df.shape[0]
    
    avg_page_score = df['page_score'].mean() if total_pages > 0 else 0
    critical_penalty = (critical_errors_count / total_pages) * 50 if total_pages > 0 else 0
    
    final_site_score = max(0, avg_page_score - domain_penalty - critical_penalty)

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
    
    full_report_data = {
        "domain_info": domain_checks,
        "summary_metrics": summary_metrics,
        "detailed_page_data": df.to_dict(orient='records')
    }
    
    return full_report_data


# --- Professional Report Generation (with line break fixes) ---

def write_summary_report(data, json_path, md_path):
    """Writes the final comprehensive full-site JSON and PROFESSIONAL Markdown report."""
    
    if 'timestamp' not in data['domain_info']:
         data['domain_info']['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    summary = data["summary_metrics"]
    domain = data["domain_info"]
    competitor = domain.get("competitor_data", {})
    audit_level = domain.get('audit_level', 'standard')
    
    your_homepage_data = next((p for p in data['detailed_page_data'] if p.get('crawl_depth', -1) == 0), {})
    local_seo_data = your_homepage_data.get('local_seo', {}).get('nap_found', {})
    analytics_data = your_homepage_data.get('analytics', {}).get('tracking_setup', {})
    
    with open(md_path, "w", encoding="utf-8") as f:
        
        # ----------------------------------------------------------------------
        # SECTION 1: EXECUTIVE SUMMARY & SCORE
        # ----------------------------------------------------------------------
        f.write(f"# 👑 PROFESSIONAL {audit_level.upper()} SEO AUDIT REPORT\n\n")
        f.write(f"## 🎯 Executive Summary for **{domain['url']}**\n\n")
        f.write(f"**Date:** {domain.get('timestamp', 'N/A')} | **Audit Level:** {audit_level.upper()} | **Pages Crawled:** {summary['total_pages_crawled']}\n\n")

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

        # ----------------------------------------------------------------------
        # SECTION 2: IMMEDIATE, ACTIONABLE RECOMMENDATIONS (Prioritized)
        # ----------------------------------------------------------------------
        f.write("## 💡 Top 3 Actionable Recommendations\n\n")
        
        recs = []
        if not domain.get('ssl', {}).get('valid_ssl'):
            recs.append("🔴 **CRITICAL: Install Valid SSL Certificate.** Your site is currently flagged as insecure by browsers and search engines.")
        if summary['server_errors_5xx'] > 0:
            recs.append(f"🔴 **CRITICAL: Fix {summary['server_errors_5xx']} Server Errors (5xx).** These pages are completely blocked from search and must be addressed immediately.")
        if summary['broken_pages_4xx'] > 0:
            recs.append(f"🟠 **HIGH: Resolve {summary['broken_pages_4xx']} Broken Pages (4xx).** Implement 301 redirects to recover link equity and improve user experience.")
        if summary['missing_title_pages'] > 0:
            recs.append(f"🟡 **MEDIUM: Add Unique Title Tags** to the {summary['missing_title_pages']} pages currently missing them, as this is a key ranking factor.")
        if not (analytics_data.get('google_analytics_found') or analytics_data.get('google_tag_manager_found')):
             recs.append("🟡 **MEDIUM: Verify Analytics Setup.** No Google Analytics/GTM script found on the homepage. Tracking is likely disabled or misconfigured.")
        
        for i, rec in enumerate(recs[:3]):
            f.write(f"{i+1}. {rec}\n")
        if not recs:
            f.write("1. Site health is generally **Good**. Review the detailed metrics below for minor optimizations and competitive positioning.\n")

        f.write("\n--- \n")

        # ----------------------------------------------------------------------
        # SECTION 3: TECHNICAL & DOMAIN HEALTH CHECKLIST
        # ----------------------------------------------------------------------
        f.write("## ⚙️ Technical Health Checklist\n\n")
        
        f.write("| Technical Metric | Status | Pages Affected |\n")
        f.write("| :--- | :--- | :--- |\n")
        
        ssl_status = '✅ Valid' if domain.get('ssl', {}).get('valid_ssl') else '❌ FAILED'
        robots_status = '✅ Found' if domain.get('robots_sitemap', {}).get('robots.txt') == "found" else '❌ Missing'
        
        f.write(f"| **HTTPS/SSL** | {ssl_status} | Domain-wide |\n")
        f.write(f"| **Robots.txt** | {robots_status} | Domain-wide |\n")
        f.write(f"| **Server Errors (5xx)** | {'✅ 0' if summary['server_errors_5xx'] == 0 else '🛑 ' + str(summary['server_errors_5xx'])} | {summary['server_errors_5xx']} Pages |\n")
        f.write(f"| **Broken Pages (4xx)** | {'✅ 0' if summary['broken_pages_4xx'] == 0 else '❌ ' + str(summary['broken_pages_4xx'])} | {summary['broken_pages_4xx']} Pages |\n")
        
        if audit_level == 'standard':
             broken_links = summary['total_broken_links_found']
             f.write(f"| **Broken Outgoing Links** | {'✅ 0' if broken_links == 0 else '⚠️ ' + str(broken_links)} | Crawl-wide total |\n")

        f.write("\n--- \n")

        # ----------------------------------------------------------------------
        # SECTION 4: ON-PAGE & CONTENT ISSUES
        # ----------------------------------------------------------------------
        f.write("## 📝 On-Page & Content Issues\n\n")

        f.write("| Issue Type | Pages Affected | Priority |\n")
        f.write("| :--- | :--- | :--- |\n")
        f.write(f"| Missing/Empty Title Tags | {summary['missing_title_pages']} | High |\n")
        f.write(f"| Missing/Multiple H1s | {summary['no_h1_pages']} | Medium |\n")
        f.write(f"| Thin Content (<250 words) | {summary['thin_content_pages']} | Medium |\n")
        f.write(f"| Missing Mobile Viewport Tag | {summary['total_pages_crawled'] - your_homepage_data.get('mobile', {}).get('mobile_friendly', True)} | High |\n")
        
        if audit_level == 'standard':
            schema_count = sum(1 for p in data['detailed_page_data'] if p.get('schema', {}).get('schema_count', 0) > 0)
            f.write(f"| Pages with Schema Markup | {schema_count} | N/A (Opportunity) |\n")


        f.write("\n--- \n")
        
        # ----------------------------------------------------------------------
        # SECTION 5: HOMEPAGE DEEP DIVE (Local SEO & Analytics)
        # ----------------------------------------------------------------------
        f.write("## 🏠 Homepage Deep Dive\n\n")
        
        f.write("### 5.1 Local SEO & NAP Check\n")
        nap_status = '✅ Found' if (local_seo_data.get('phone_format_found') and local_seo_data.get('address_keywords_found')) else '❌ Missing Key NAP Elements (High Priority for local businesses)'
        gmb_status = '✅ Found Google Map/Embed' if local_seo_data.get('gmb_link_found') else '⚠️ GMB Proxy Link/Map Not Found (Verify local listing integration)'
        f.write(f"- **NAP Consistency Proxy:** {nap_status}\n")
        f.write(f"- **GMB/Map Integration:** {gmb_status}\n\n")
        
        f.write("### 5.2 Analytics & Tracking\n")
        ga_status = '✅ Detected' if (analytics_data.get('google_analytics_found') or analytics_data.get('google_tag_manager_found')) else '❌ NOT Detected (Tracking is likely broken)'
        f.write(f"- **Google Tracking (GA/GTM):** {ga_status}\n")
        f.write("    *NOTE: This is a static check. Event/Goal tracking cannot be verified; consult your analytics provider.*\n")

        f.write("\n--- \n")

        # ----------------------------------------------------------------------
        # SECTION 6: COMPETITOR ANALYSIS
        # ----------------------------------------------------------------------
        f.write("## 📈 Competitor Analysis (vs. Homepage)\n\n")
        if competitor.get("status") == "success":
            
            your_title_len = len(your_homepage_data.get('meta', {}).get('title', ''))
            your_h1 = your_homepage_data.get('headings', {}).get('h1', 0)
            your_words = your_homepage_data.get('content', {}).get('word_count', 0)
            
            comp_title_len = competitor.get('title_length', 'N/A')
            comp_h1 = competitor.get('h1_count', 'N/A')
            comp_words = competitor.get('content', {}).get('word_count', 'N/A')
            
            f.write(f"**Competitor URL:** [{competitor.get('url')}]({competitor.get('url')})\n\n")

            f.write("| Metric | Your Site | Competitor |\n")
            f.write("| :--- | :--- | :--- |\n")
            f.write(f"| Title Length (Chars) | {your_title_len} | {comp_title_len} |\n")
            f.write(f"| H1 Count | {your_h1} | {comp_h1} |\n")
            f.write(f"| Word Count | {your_words} | {comp_words} |\n")
            f.write(f"| SSL Valid | {'✅' if domain.get('ssl', {}).get('valid_ssl') else '❌'} | {'✅' if competitor.get('ssl_valid') else '❌'} |\n")
        else:
             f.write(f"Competitor analysis skipped or failed: {competitor.get('error', 'No competitor URL provided.')}\n")

        f.write("\n--- \n")
        
        # ----------------------------------------------------------------------
        # SECTION 7: DISCLAIMER
        # ----------------------------------------------------------------------
        if audit_level == 'basic':
            f.write("## ℹ️ Audit Scope Disclaimer\n")
            f.write("This **Basic Audit** intentionally skipped resource-intensive checks (Schema, Broken Link Validation, Keyword Analysis) to provide quick feedback.\n")
            f.write("For a complete analysis, run the **Standard Audit**.\n\n")
        
        f.write("### Data Source Note\n")
        f.write("*Note: This audit is based on open-source crawling only. It does not include external API data (Google Search Console, Backlink profiles, etc.) or client-side event tracking.*\n")
        
