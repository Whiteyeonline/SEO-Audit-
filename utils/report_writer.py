import json
import pandas as pd
import numpy as np
from datetime import datetime

# ... [all your helper functions stay as is, unless you want visual improvements] ...

def write_summary_report(data, json_path, md_path):
    """Writes the final comprehensive full-site JSON and PROFESSIONAL Markdown report, ensuring both match in all details."""
    # Add timestamp if missing
    if 'timestamp' not in data['domain_info']:
        data['domain_info']['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Write JSON report (unchanged)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Write Markdown report
    with open(md_path, "w", encoding="utf-8") as f:
        domain = data["domain_info"]
        summary = data["summary_metrics"]
        competitor = domain.get("competitor_data", {})
        audit_level = domain.get('audit_level', 'standard')
        timestamp = domain.get('timestamp', 'N/A')

        f.write(f"# 👑 PROFESSIONAL {audit_level.upper()} SEO AUDIT REPORT\n\n")
        f.write(f"## 🎯 Executive Summary for **{domain['url']}**\n\n")
        f.write(f"**Audit Date:** {timestamp}\n\n")

        # Summary Table
        status_text, emoji = "", ""
        if summary['overall_score'] > 90: status_text, emoji = "Excellent (Maintain Strategy)", "✅"
        elif summary['overall_score'] > 75: status_text, emoji = "Good (Minor Improvements Needed)", "🟢"
        elif summary['overall_score'] > 50: status_text, emoji = "Fair (High-Priority Fixes Needed)", "🟡"
        else: status_text, emoji = "Poor (CRITICAL Intervention Required)", "🛑"
        f.write("--- \n")
        f.write("| Metric | Value | \n")
        for k, v in summary.items():
            f.write(f"| {k.replace('_',' ').title()} | {v} |\n")
        f.write(f"\n| **Overall Site Health Score** | **{summary['overall_score']}/100** | **{emoji} {status_text}** |\n")
        f.write("--- \n\n")

        # Actionable Priority
        f.write("## 💡 Top Actionable Priority\n\n")
        homepage = data['detailed_page_data'][0] if data['detailed_page_data'] else {}
        if not domain.get('ssl', {}).get('valid_ssl'):
            f.write("1. 🔴 **CRITICAL: Install Valid SSL Certificate.** Your site is flagged as insecure.\n")
        elif homepage.get("status_code", 200) >= 400:
            f.write(f"1. 🔴 **CRITICAL: Fix Status Code {homepage.get('status_code')}.** This page is not indexable and must be fixed with 301/200 codes.\n")
        elif not homepage.get("meta", {}).get("title"):
            f.write("1. 🔴 **CRITICAL: Add Title Tag.** The page is missing its most important ranking factor.\n")
        elif homepage.get("headings", {}).get("h1", 0) != 1:
            f.write(f"1. 🟠 **HIGH: Fix H1 Count.** Page has {homepage.get('headings', {}).get('h1', 0)} H1 tags (should be exactly 1).\n")
        else:
            f.write("1. ✅ **STATUS:** No critical issues found. Focus on the medium priority items below.\n")
        f.write("\n---\n")

        # Detailed audit for ALL pages - MATCHES JSON!
        f.write("# 📝 DETAILED ON-PAGE AUDIT CHECKLIST\n\n")
        for idx, page in enumerate(data['detailed_page_data']):
            url = page.get("url", "")
            f.write(f"### Page {idx+1}: [{url}]({url})\n")
            _write_meta_section(f, page)
            _write_url_canonical_section(f, page)
            _write_content_headings_section(f, page)
            _write_technical_ux_section(f, page)
            if audit_level == 'standard':
                _write_advanced_standard_section(f, page)

            # Backlinks Section (always shown)
            backlinks = page.get("backlinks", {})
            f.write("#### 🌐 Backlinks/External Links\n")
            f.write(f"- **Internal Link Count:** {backlinks.get('internal_link_count','N/A')}\n")
            f.write(f"- **External Link Count:** {backlinks.get('external_link_count','N/A')}\n")
            f.write(f"- **Sample External Domains:** {', '.join(backlinks.get('sample_external_domains',[]))}\n")
            f.write(f"- **Note:** {backlinks.get('note','[No backlink data available]')}\n")
            f.write("\n---\n")

        # Domain Health (matches JSON summary)
        f.write("## 🌎 Domain Health Summary\n\n")
        f.write(f"* **SSL Status:** {'✅ Valid HTTPS' if domain.get('ssl', {}).get('valid_ssl') else '❌ FAILED (Requires Immediate Action)'}\n")
        f.write(f"* **Robots.txt:** {'✅ Found' if domain.get('robots_sitemap', {}).get('robots.txt') == 'found' else '❌ Missing'}\n")
        f.write(f"* **Sitemap.xml:** {'✅ Found' if domain.get('robots_sitemap', {}).get('sitemap') == 'found' else '⚠️ Not Found'}\n")
        f.write("\n---\n")

        # Competitor (matches JSON)
        f.write("## 📈 Competitor Analysis\n")
        if competitor.get("status") == "success":
            f.write(f"- **Competitor URL:** [{competitor.get('url')}]({competitor.get('url')})\n")
            f.write(f"- **Title Length:** {competitor.get('title_length','N/A')}\n")
            f.write(f"- **H1 Count:** {competitor.get('h1_count','N/A')}\n")
            f.write(f"- **Word Count:** {competitor.get('word_count','N/A')}\n")
        else:
            f.write(f"Competitor analysis skipped or failed: {competitor.get('error','No competitor URL provided.')}\n")
        f.write("\n---\n")

        # Disclaimer (always matches JSON)
        if audit_level == 'basic':
            f.write("## ℹ️ Audit Scope Disclaimer\n")
            f.write("This **Basic Audit** intentionally skipped advanced, time-consuming checks (Schema, Broken Link Validation, Keyword Analysis) to provide quick feedback.\n")
            f.write("For a complete analysis, run the **Standard Audit**.\n\n")

        # Traceability
        f.write(f"\n---\n**Audit ID:** `{timestamp}`. This report matches summary and detailed data from the JSON output.\n")
        
