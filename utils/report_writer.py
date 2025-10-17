# utils/report_writer.py

import json
import datetime
import re
from urllib.parse import urlparse
from collections import defaultdict
import logging

# Assuming ALL checks (like ssl_check, etc.) are available when this is run by main.py
# and the CRITICAL_ISSUE_WEIGHTS structure is implicitly known from main.py's logic
# for the aggregation keys.

# --- Helper Functions ---

def _get_issue_description_map():
    """
    Defines common issues, their priority, description, and an expert solution.
    (Retained from your original file)
    """
    return {
        'title_fail': {'name': 'Missing or Poorly Formatted Title Tag', 'priority': 'High', 'description': 'Pages missing a Title Tag or having one that is too long/short (Optimal: 30-60 characters).', 'solution': 'For any page, **view the source code** (Ctrl+U or Cmd+Option+U) and locate the `<title>` tag. Ensure its length is 30-60 characters and it is unique across your site.'},
        'desc_fail': {'name': 'Missing Meta Description', 'priority': 'High', 'description': 'Pages missing a Meta Description (Essential for click-through rate in SERPs).', 'solution': 'In the page\'s source code, check the `<meta name="description">` tag. The optimal length is **120-158 characters** to maximize click-through rate in search results.'},
        'h1_fail': {'name': 'Multiple or Missing H1 Tag', 'priority': 'High', 'description': 'Pages having missing H1 tags or more than one H1 tag (SEO best practice is one H1 per page).', 'solution': 'Use your browser\'s **Inspect Element** tool to verify that exactly **one** descriptive `<h1>` tag is present and visible on the page. It should summarize the primary topic.'},
        'thin_content': {'name': 'Thin Content Warning', 'priority': 'Medium', 'description': 'Pages with very little unique content (under 200 words).', 'solution': 'Significantly increase the unique, high-quality, and useful content on these pages. Aim for **over 300 words** of valuable text for informational pages.'},
        'missing_alt_images': {'name': 'Images Missing Alt Text', 'priority': 'Low', 'description': 'Images without proper `alt` attributes, harming accessibility and image SEO.', 'solution': 'Use the **Inspect Element** tool on every image to check for the `alt` attribute. Add descriptive, keyword-rich `alt` text to all images to aid screen readers and search engines.'},
        'broken_link_count': {'name': 'Internal or External Broken Links (4XX/5XX)', 'priority': 'High', 'description': 'Links pointing to pages that return an error code (4xx or 5xx).', 'solution': 'Use a reliable link checker tool or a crawl report to identify the source of these broken links and **update or remove** them immediately.'},
        'canonical_mismatch': {'name': 'Canonical Tag Issues', 'priority': 'Medium', 'description': 'Canonical tags pointing to an incorrect URL or missing entirely on pages that require one.', 'solution': 'Verify the `<link rel="canonical">` tag in the page\'s HTML source code. It **must point to the absolute, preferred version of the page** (the final destination URL after any redirects).'},
        'not_mobile_friendly': {'name': 'Mobile Unfriendly Pages', 'priority': 'High', 'description': 'Pages identified as not being fully responsive (critical for Mobile-First Indexing).', 'solution': 'Ensure the required viewport tag: `<meta name="viewport" content="width=device-width, initial-scale=1">` is present in the `<head>` of the page. Test your site using the **Google Mobile-Friendly Test tool**.'},
        'analytics_missing': {'name': 'Missing Analytics/Tracking Code', 'priority': 'Medium', 'description': 'Pages where a Google Analytics or other specified tracking code could not be detected.', 'solution': 'Verify that the correct Google Analytics (GA4) or Google Tag Manager (GTM) snippet is placed correctly and unedited in the **`<head>` section** of all pages.'},
        'og_tags_missing': {'name': 'Missing Essential Open Graph Tags', 'priority': 'Medium', 'description': 'Crucial Open Graph tags are missing, leading to poor social media sharing previews.', 'solution': 'Manually share the page link on Facebook or Twitter and check the resulting preview card. Ensure all essential tags (`og:title`, `og:image`, `og:url`) are present in the source code.'},
        'was_redirected': {'name': 'Unnecessary Page Redirect Detected', 'priority': 'Low', 'description': 'A redirect was detected, suggesting a redirect chain or an unnecessary hop.', 'solution': 'Use a **free HTTP header checker tool** to trace the redirect path. If the redirect is permanent, ensure it uses a **301 status code** and links directly to the final destination.'},
        'cwv_warn': {'name': 'Performance Warning (High Latency/TTFB)', 'priority': 'High', 'description': 'The page experienced high download latency, which acts as a proxy for slow server response time (TTFB), impacting Core Web Vitals.', 'solution': 'For precise Core Web Vitals (LCP, FID, CLS), **site owners should check their Google Search Console Core Web Vitals Report** or use the free **PageSpeed Insights** tool.'},
        'robots_sitemap_fail': {'name': 'Robots/Sitemap Issues', 'priority': 'Medium', 'description': 'The `robots.txt` or `sitemap.xml` file was not found or contains errors, hindering crawl efficiency.', 'solution': 'Verify that your `robots.txt` is accessible at `yourdomain.com/robots.txt` and is not blocking essential files. Ensure your `sitemap.xml` is linked from `robots.txt`.'},
        'unclean_url': {'name': 'Unclean URL Structure', 'priority': 'Low', 'description': 'URLs containing excessive parameters, stop words, or non-ASCII characters.', 'solution': 'Keep URLs short, descriptive, and clean. Use **hyphens (`-`)** to separate words and include target keywords. Avoid using underscores (`_`) or excessive parameters.'},
        'nap_mismatch': {'name': 'Local SEO NAP Mismatch', 'priority': 'Medium', 'description': 'Mismatched Name, Address, or Phone (NAP) details, confusing local search engines.', 'solution': 'Ensure your Name, Address, and Phone (NAP) details are **100% consistent** across all pages of your site and all external listings (e.g., Google Business Profile).'},
        'accessibility_fail': {'name': 'Basic Accessibility Issues', 'priority': 'Medium', 'description': 'The page fails basic accessibility checks (e.g., color contrast, focus order), impacting all users.', 'solution': 'Use a browser extension (like Lighthouse or a Contrast Checker) to quickly identify and fix issues like low color contrast or missing label attributes on forms.'},
        'missing_internal_links': {'name': 'Page Lacks Internal Links', 'priority': 'Low', 'description': 'The page has very few internal links pointing to it, reducing its visibility and passing link equity.', 'solution': 'Contextually link to this page from **other high-authority and relevant pages** on your site. Aim for at least one or two descriptive anchor text links.'},
        'server_response_slow': {'name': 'Slow Server Response Time', 'priority': 'High', 'description': 'Server response time (TTFB) is too slow, directly impacting page speed and user experience.', 'solution': 'Optimize server configuration, use a CDN, and improve database query efficiency to reduce server response time **below 200ms**.'},
        'backlinks_info': {'name': 'Backlinks Information (Basic Check)', 'priority': 'Informational', 'description': 'This check provides a basic list of domains linked from the page. A detailed analysis requires paid tools.', 'solution': 'To get a full backlink profile (required for SEO), **site owners should check the Links Report in Google Search Console** or use limited free versions of paid tools like Ahrefs/SEMrush.'}
    }

def _get_status_or_value(data_dict, check_name, key=None):
    """Helper to safely retrieve status or a specific key value for comparison."""
    check = data_dict.get(check_name, {})
    if key:
        value = check.get('result', {}).get(key, 'N/A')
        # Format CWV values
        if 'value' in key and isinstance(value, (float, int)):
            return f"{value:.3f}s"
        return value
    return check.get('status', 'N/A')

def _format_status_for_md(status):
    """Converts check status strings to formatted Markdown strings with emojis."""
    if isinstance(status, str):
        return status.replace('SUCCESS', '✅ PASS').replace('FAIL', '❌ FAIL').replace('WARNING', '⚠️ WARN').replace('INFO', '💡 INFO')
    return status

def _format_check_box(check_name, status, details, solution_key=None, note=None):
    """Helper function to format individual check results for the markdown report."""
    issue_map = _get_issue_description_map()
    box = []
    box.append(f"\n**{check_name.upper()}**")
    box.append("-----------------")
    box.append(f"**STATUS:** **{status}**")
    
    if details:
        box.append(f"**DETAILS:** {details}")
    if note:
        box.append(f"**NOTE:** {note}")

    if status.startswith('❌') or status.startswith('⚠️'):
        # Determine the best solution key to display
        if solution_key in issue_map:
            use_key = solution_key
        elif 'backlink' in check_name.lower():
            use_key = 'backlinks_info'
        elif 'vitals' in check_name.lower() or 'performance' in check_name.lower():
            use_key = 'cwv_warn'
        else:
            use_key = None # No specific fix available

        if use_key and use_key in issue_map:
            issue = issue_map[use_key]
            box.append(f"\n**💡 RECOMMENDATION: {issue['name']}**")
            box.append(f"**Priority:** {issue['priority']}")
            box.append(f"**Solution:** {issue['solution']}")
    
    box.append("_______________________________")
    return '\n'.join(box)


# --- Core Logic Functions (UPDATED) ---

def get_check_aggregation(initial_checks: dict, crawled_pages: list) -> dict:
    """
    FIXED: Aggregates issue counts across both initial checks and crawled pages.
    The aggregation keys must align with CRITICAL_ISSUE_WEIGHTS in main.py.
    """
    
    # These keys must match the ones in CRITICAL_ISSUE_WEIGHTS in main.py
    aggregated_counts = defaultdict(int, {
        'title_fail_count': 0, 'desc_fail_count': 0, 'h1_fail_count': 0,
        'link_broken_total': 0, 'mobile_unfriendly_count': 0, 'robots_sitemap_fail_count': 0,
        'canonical_mismatch_count': 0, 'ssl_check_fail_count': 0,
        'total_pages_crawled': 0
    }) 

    # 1. Process GLOBAL Initial Checks
    if initial_checks:
        ssl_data = initial_checks.get('ssl_check', {})
        if not ssl_data.get('valid_ssl', True): 
            aggregated_counts['ssl_check_fail_count'] += 1 # Only one check for the whole site
        
        robots_data = initial_checks.get('robots_sitemap', {})
        if robots_data.get('robots.txt_status') != 'found' or robots_data.get('sitemap.xml_status') != 'found':
             aggregated_counts['robots_sitemap_fail_count'] += 1 # Only one check for the whole site
             
    # 2. Process Page-Specific Crawled Issues
    for page in crawled_pages:
        page_checks = page.get('checks', {})

        # --- High Priority Issues (Scored in main.py) ---
        if page_checks.get('meta_check', {}).get('title_fail') is True: aggregated_counts['title_fail_count'] += 1
        if page_checks.get('meta_check', {}).get('desc_fail') is True: aggregated_counts['desc_fail_count'] += 1
        if page_checks.get('heading_check', {}).get('h1_fail') is True: aggregated_counts['h1_fail_count'] += 1
        
        # NOTE: link_broken_total is typically a total count across the site, not per page failure.
        # We sum all broken links found on a single page check.
        aggregated_counts['link_broken_total'] += page_checks.get('link_check', {}).get('broken_link_count', 0)
        
        if page_checks.get('mobile_friendly_check', {}).get('mobile_friendly') is False: aggregated_counts['mobile_unfriendly_count'] += 1
        if page_checks.get('canonical_check', {}).get('canonical_mismatch') is True: aggregated_counts['canonical_mismatch_count'] += 1

    aggregated_counts['total_pages_crawled'] = len(crawled_pages)
    
    return dict(aggregated_counts)

def write_json_report(structured_report_data: dict, file_path: str):
    """NEW: Writes the full structured data to a JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(structured_report_data, f, indent=4)
        logging.info(f"JSON Report written successfully to: {file_path}")
    except Exception as e:
        logging.error(f"Failed to write JSON report: {e}")

def write_summary_report(structured_report_data: dict, file_path: str):
    """
    NEW: Generates a simple text summary (for console/log purposes).
    (Kept for compatibility with main.py's multiple report writers)
    """
    final_score = structured_report_data['final_score']
    total_pages = structured_report_data['total_pages_crawled']
    
    summary_content = f"--- SEO AUDIT SUMMARY ---\n"
    summary_content += f"Target URL: {structured_report_data['audit_details']['target_url']}\n"
    summary_content += f"Final Score: {final_score}/100\n"
    summary_content += f"Pages Audited: {total_pages}\n"
    summary_content += f"Competitor Audited: {structured_report_data['audit_details'].get('competitor_url', 'N/A')}\n"
    summary_content += f"-------------------------\n"
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        logging.info(f"Simple Summary Report written successfully to: {file_path}")
    except Exception as e:
        logging.error(f"Failed to write simple summary report: {e}")


def write_markdown_report(report, md_path):
    """
    RENAMED/UPDATED: Writes the final professional Markdown report, including
    the new Deep Competitor Analysis section.
    """
    audit_details = report['audit_details']
    crawled_pages = report['crawled_pages']
    score = report['final_score'] 
    aggregated_issues = report['aggregated_issues']
    
    issue_map = _get_issue_description_map()
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    content = []

    # --- 1. Report Header ---
    content.append("# 💎 PROFESSIONAL SEO AUDIT REPORT\n\n")
    content.append(f"**Target URL:** `{audit_details.get('target_url', 'N/A')}`\n")
    content.append(f"**Audit Date:** {current_time}\n")
    content.append(f"**Total Pages Crawled:** {len(crawled_pages)}\n")
    content.append(f"**Overall Site Score:** **{score}/100**\n\n") 
    content.append("---\n\n") 

    # --- 2. Executive Summary ---
    content.append("## 2. Executive Summary\n\n")
    content.append("This score is based on a weighted penalty model focusing on critical, crawl-impacting issues. See the Structured JSON file for a breakdown of penalties.\n\n")
    content.append(f"The site received a score of **{score}/100** based on the on-page analysis of {len(crawled_pages)} pages.\n\n")
    content.append("### Key Issues\n\n")
    # List top 5 issues from aggregated_issues (using logic from main.py's weights for priority)
    top_issues = {k: v for k, v in aggregated_issues.items() if '_count' in k and v > 0}
    sorted_issues = sorted(top_issues.items(), key=lambda item: item[1], reverse=True)[:5]
    
    if sorted_issues:
        for key, count in sorted_issues:
            issue_name = key.replace('_count', '').replace('_', ' ').title()
            content.append(f"* **{issue_name}:** Found **{count}** instance(s) across the site.\n")
    else:
        content.append("* No critical issues detected on the crawled pages.\n")
        
    content.append("\n---\n\n")

    # --- 3. Deep Competitor Analysis (NEW INTEGRATION) ---
    comp_audit = report.get('competitor_analysis')
    your_url = audit_details.get('target_url')
    
    content.append(f"## 3. Deep Competitor Audit: {audit_details.get('competitor_url', 'N/A')}\n\n")

    if comp_audit and crawled_pages:
        comp_url_key = comp_audit['url']
        your_homepage_checks = crawled_pages[0]['checks'] 
        comp_checks = comp_audit['checks']
        
        # --- Create Comparison Table Data ---
        comparison_data = [
            {
                'name': 'Title Tag Status',
                'yours': _format_status_for_md(_get_status_or_value(your_homepage_checks, 'meta_check')),
                'competitor': _format_status_for_md(_get_status_or_value(comp_checks, 'meta_check')),
            },
            {
                'name': 'H1 Status',
                'yours': _format_status_for_md(_get_status_or_value(your_homepage_checks, 'heading_check')),
                'competitor': _format_status_for_md(_get_status_or_value(comp_checks, 'heading_check')),
            },
            {
                'name': 'Mobile Friendly',
                'yours': _format_status_for_md(_get_status_or_value(your_homepage_checks, 'mobile_friendly_check')),
                'competitor': _format_status_for_md(_get_status_or_value(comp_checks, 'mobile_friendly_check')),
            },
            {
                'name': 'LCP (Core Web Vitals)',
                'yours': _get_status_or_value(your_homepage_checks, 'core_web_vitals_check', 'lcp_value'),
                'competitor': _get_status_or_value(comp_checks, 'core_web_vitals_check', 'lcp_value'),
            },
            {
                'name': 'Server Response (TTFB Proxy)',
                'yours': _format_status_for_md(_get_status_or_value(your_homepage_checks, 'performance_check')),
                'competitor': _format_status_for_md(_get_status_or_value(comp_checks, 'performance_check')),
            },
            {
                'name': 'Schema Markup',
                'yours': _format_status_for_md(_get_status_or_value(your_homepage_checks, 'schema_check', 'schema_found')),
                'competitor': _format_status_for_md(_get_status_or_value(comp_checks, 'schema_check', 'schema_found')),
            }
        ]

        # --- Write Comparison Table ---
        content.append("### On-Page Technical Comparison (Homepage Only)\n")
        content.append(f"| Metric | **Your Site ({urlparse(your_url).netloc})** | **Competitor ({urlparse(comp_url_key).netloc})** |\n")
        content.append("| :--- | :--- | :--- |\n")
        
        for metric in comparison_data:
            content.append(f"| **{metric['name']}** | {metric['yours']} | {metric['competitor']} |\n")
        content.append("\n")
        
        content.append(f"**NOTE:** This comparison uses your full suite of checks for both sites, including Playwright-based Core Web Vitals checks. Full details of the competitor's raw audit are in the `seo_audit_structured_report.json` file.\n\n")

    else:
        content.append(f"**Competitor Check Status:** No deep competitor analysis was performed or results failed to load. Ensure the `COMPETITOR_URL` environment variable is set.\n\n")

    content.append("---\n\n") 
    
    # --- 4. Detailed Page-by-Page Audit ---
    content.append("## 4. Detailed Page-by-Page Audit\n\n")
    content.append("This section provides granular, check-by-check data for each page crawled, utilizing a clear block format for readability.\n\n")

    ALL_CHECK_KEYS = [
        'ssl_check', 'robots_sitemap', 'redirect_check', 
        'canonical_check', 'url_structure', 'meta_check', 
        'heading_check', 'content_quality', 'image_check', 
        'link_check', 'internal_links', 'schema_check', 
        'mobile_friendly_check', 'accessibility_check', 'performance_check', 
        'core_web_vitals_check', 'analytics_check', 'og_tags_check', 
        'local_seo_check', 'keyword_analysis', 'backlinks_check'
    ]

    # Process each crawled page for its detailed report
    for idx, page in enumerate(crawled_pages):
        page_checks = page.get('checks', {})
        page_url = page.get('url', 'N/A')
        status_code = page.get('http_status', 'N/A')

        content.append(f"\n# 📍 PAGE AUDIT {idx + 1}: {page_url}\n")
        content.append(f"**HTTP Status Code:** `{status_code}`\n")
        content.append("---")
        
        # --- Process all 21 checks ---
        for key in ALL_CHECK_KEYS:
            data = page_checks.get(key, {}) 
            check_name = key.replace('_', ' ').title()
            
            # Use a generic approach for the detailed checks to make the code shorter
            status = data.get('status', 'N/A')
            details = data.get('details', 'N/A')
            solution_key = data.get('solution_key') # Assuming simple checks set this on failure

            if key == 'meta_check':
                # Special handling for Title/Desc as separate boxes
                t_status = '❌ FAIL' if data.get('title_fail') else '✅ PASS'
                t_details = f"Title: `{data.get('title_content', 'N/A')}` (Length: {data.get('title_length', 0)})"
                content.append(_format_check_box("Title Tag Check", t_status, t_details, 'title_fail'))

                d_status = '❌ FAIL' if data.get('desc_fail') or not data.get('desc_content') else '✅ PASS'
                d_details = f"Description: `{data.get('desc_content', 'MISSING...')[:100]}...` (Length: {data.get('desc_length', 0)})"
                content.append(_format_check_box("Meta Description Check", d_status, d_details, 'desc_fail'))
                continue
            
            elif key == 'robots_sitemap':
                robots = data.get('robots.txt_status', 'not found')
                sitemap = data.get('sitemap.xml_status', 'not found')
                status = '✅ PASS'
                if robots != 'found' or sitemap != 'found': status = '❌ FAIL'
                details = f"Robots.txt Status: **{robots.upper()}**. Sitemap.xml Status: **{sitemap.upper()}**."
                solution_key = 'robots_sitemap_fail'
            
            elif key == 'mobile_friendly_check':
                 is_mobile_friendly = data.get('mobile_friendly')
                 status = '❌ FAIL' if is_mobile_friendly is False else '✅ PASS'
                 details = f"Status: {'Friendly' if is_mobile_friendly else 'NOT FRIENDLY'}. Issues: {', '.join(data.get('issues', [])) if data.get('issues') else 'None'}"
                 solution_key = 'not_mobile_friendly'

            # Default check box for all other checks
            content.append(_format_check_box(check_name, _format_status_for_md(status), details, solution_key, data.get('note')))
            
        content.append("\n\n---\n") # Final separator for the page audit


    # -----------------------------------------------------
    # 5. Appendix/Disclaimer
    # -----------------------------------------------------
    content.append("## 5. Disclaimer & Technology Used\n\n")
    content.append("This audit uses free, open-source tools (Scrapy, Playwright, NLTK) and provides a static, on-page analysis. True Core Web Vitals, link quality, and comprehensive ranking difficulty require dedicated access (often paid) to first-party data (Google Search Console) or premium third-party APIs (e.g., Ahrefs, SEMrush).\n")


    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    print(f"Professional Markdown Report written to {md_path}")


   
