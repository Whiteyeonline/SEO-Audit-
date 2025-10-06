# utils/report_writer.py (REWRITTEN: Generates MD directly, no Jinja2)
import json
import datetime

def get_check_aggregation(crawled_pages):
    """Aggregates all 18 check results from crawled pages into site-wide counts."""
    # This is a critical function to summarize site health from page-level data.
    aggregation = {
        'total_pages_crawled': len(crawled_pages),
        'title_fail_count': 0, 
        'desc_fail_count': 0, 
        'h1_fail_count': 0, 
        'thin_content_count': 0, 
        'missing_alt_total': 0,
        'canonical_mismatch_count': 0,
        'link_broken_total': 0, # Total broken links across all pages
        'analytics_missing_count': 0, # Pages missing GTM/GA
        'mobile_unfriendly_count': 0,
        'url_not_clean_count': 0, # Clean URL structure
        'nap_fail_count': 0, # Local SEO NAP issue
        'accessibility_fail_count': 0, # Heading level skip
        'content_readability_warning': 0, # Readability warnings
        'keyword_density_warning': 0,
        'keyword_placement_warning': 0,
    }

    for page in crawled_pages:
        # Skip analysis if page was not crawlable (e.g., 404, 500)
        if not page.get('is_crawlable', False):
            continue

        # Meta Aggregations (from reports/template.md.j2 logic)
        title_len = page.get('meta', {}).get('title', '')
        if len(title_len) < 30 or len(title_len) > 65:
            aggregation['title_fail_count'] += 1
        if not page.get('meta', {}).get('description'):
            aggregation['desc_fail_count'] += 1
        
        # Structure Aggregations
        if page.get('headings', {}).get('h1', 0) != 1:
            aggregation['h1_fail_count'] += 1
        
        # Content Aggregations
        if page.get('content', {}).get('word_count', 0) < 200:
            aggregation['thin_content_count'] += 1
        if page.get('content', {}).get('readability_score') != "N/A (Text too short for reliable score)" and page.get('content', {}).get('readability_score', 100) < 60:
             aggregation['content_readability_warning'] += 1
        
        # Image Aggregations
        aggregation['missing_alt_total'] += page.get('images', {}).get('missing_alt', 0)
        
        # Canonical
        if not page.get('canonical', {}).get('match', True):
            aggregation['canonical_mismatch_count'] += 1
        
        # Broken Links
        aggregation['link_broken_total'] += len(page.get('links', {}).get('broken', []))

        # Analytics
        tracking = page.get('analytics', {}).get('tracking_setup', {})
        if not (tracking.get('google_analytics_found') or tracking.get('google_tag_manager_found')):
             aggregation['analytics_missing_count'] += 1

        # Mobile
        if not page.get('mobile', {}).get('mobile_friendly', True):
             aggregation['mobile_unfriendly_count'] += 1

        # URL Structure
        if not page.get('url_structure', {}).get('is_clean', True):
            aggregation['url_not_clean_count'] += 1

        # Local SEO
        if page.get('local_seo', {}).get('nap_consistency', {}).get('result') == 'Fail':
            aggregation['nap_fail_count'] += 1
            
        # Accessibility (Checking for heading level skips)
        if any('Skipped heading level' in i.get('check', '') for i in page.get('accessibility_issues', [])):
            aggregation['accessibility_fail_count'] += 1
            
        # Keywords
        if page.get('keywords', {}).get('density_check', {}).get('result') == 'Warning':
            aggregation['keyword_density_warning'] += 1
        if page.get('keywords', {}).get('placement_check', {}).get('result') == 'Warning':
            aggregation['keyword_placement_warning'] += 1
            
    return aggregation

def calculate_seo_score(report_data):
    """Calculates a final SEO score based on penalties applied to check results."""
    # (The score calculation logic remains the same for consistency)
    score = 100
    PENALTIES = {
        'ssl_fail': 20, 'robots_fail': 10, 'performance_fail': 15,  
        'meta_desc_fail_per_page': 1, 'h1_fail_per_page': 0.5,
    }
    
    # 1. Basic Checks
    ssl_status = report_data.get('basic_checks', {}).get('ssl_check', {}).get('valid_ssl')
    robots_status = report_data.get('basic_checks', {}).get('robots_sitemap', {}).get('robots.txt')
    sitemap_status = report_data.get('basic_checks', {}).get('robots_sitemap', {}).get('sitemap.xml')
        
    if not ssl_status:
        score -= PENALTIES['ssl_fail']
    if robots_status == 'not found' or sitemap_status == 'not found':
        score -= PENALTIES['robots_fail']

    # 2. Performance Check (Internal)
    performance_check = report_data.get('performance_check', {})
    desktop_result = performance_check.get('desktop_score', {}).get('result', 'Fail')
        
    if desktop_result == 'Fail':
        score -= PENALTIES['performance_fail']

    # 3. Crawled Page Penalties (Uses aggregation logic for pages that contribute to the score)
    crawled_pages = report_data.get('crawled_pages', [])
    for page in crawled_pages:
        # Penalize for missing Meta Description
        if not page.get('meta', {}).get('description'):
            score -= PENALTIES['meta_desc_fail_per_page']
            
        # Penalize for bad H1 count
        if page.get('headings', {}).get('h1') != 1:
            score -= PENALTIES['h1_fail_per_page']
            
    return max(0, score)

def _get_status_label(score):
    if score >= 85: return 'Excellent 🏆'
    if score >= 60: return 'Good 👍'
    return 'Needs Immediate Attention 🚨'

def _get_issue_description_map():
    # Maps issue keys to human-readable details, including solutions
    return {
        'title_fail_count': {'priority': 'High', 'description': 'Pages with missing, too short, or too long Title Tags (Optimal: 30-65 chars).', 'solution': 'Review and rewrite page titles to accurately reflect content, include primary keywords, and fit within length limits.'},
        'desc_fail_count': {'priority': 'High', 'description': 'Pages missing a Meta Description (Essential for click-through rate in SERPs).', 'solution': 'Add unique, compelling meta descriptions (120-158 characters) that encourage users to click.'},
        'h1_fail_count': {'priority': 'Medium', 'description': 'Pages with zero or more than one H1 heading (Should be exactly one H1 per page).', 'solution': 'Ensure every critical page has a single H1 tag containing the page\'s main topic keyword.'},
        'thin_content_count': {'priority': 'Medium', 'description': 'Pages with low word count (< 200 words), potentially seen as low-value or thin content.', 'solution': 'Expand the content on these pages to provide greater detail and better user value. The current average word count is too low.'},
        'missing_alt_total': {'priority': 'Low', 'description': 'Total images across all pages missing descriptive ALT text (A key accessibility and SEO factor).', 'solution': 'Add descriptive ALT text to all images to improve accessibility and help search engines understand image content.'},
        'canonical_mismatch_count': {'priority': 'High', 'description': 'Pages with a missing, incorrect, or self-referencing canonical tag that does not match the page URL.', 'solution': 'Ensure every page has a canonical tag pointing to the preferred version of the URL. This prevents duplicate content issues.'},
        'link_broken_total': {'priority': 'High', 'description': 'Total broken outbound or internal links found (HTTP 4xx/5xx errors).', 'solution': 'Identify and fix (redirect or update) all broken links to maintain link equity and improve user experience.'},
        'analytics_missing_count': {'priority': 'Medium', 'description': 'Pages where Google Analytics or Google Tag Manager tracking code was not detected.', 'solution': 'Verify that the correct GA/GTM snippet is implemented across all pages for accurate performance monitoring.'},
        'mobile_unfriendly_count': {'priority': 'High', 'description': 'Pages missing the critical Viewport meta tag or "width=device-width" for mobile rendering.', 'solution': 'Add or correct the viewport meta tag to ensure proper rendering on all mobile devices (a core Google ranking factor).'},
        'url_not_clean_count': {'priority': 'Low', 'description': 'Pages with complex or "unclean" URL structures (e.g., more than 2 sub-directories in the path).', 'solution': 'Aim for short, descriptive, keyword-rich URLs with minimal folder depth (e.g., /category/product-name).'},
        'nap_fail_count': {'priority': 'High', 'description': 'Pages completely missing a recognizable Name, Address, or Phone (NAP) marker (Crucial for Local SEO).', 'solution': 'Ensure complete and consistent NAP information is present on all relevant pages, ideally using a consistent format.'},
        'accessibility_fail_count': {'priority': 'Medium', 'description': 'Pages with improper heading structure (e.g., skipping from H1 to H3, poor screen reader experience).', 'solution': 'Correct the heading hierarchy to be logical (H1, H2, H3, etc.) to improve accessibility and content flow.'},
        'content_readability_warning': {'priority': 'Low', 'description': 'Pages with a Flesch Reading Ease score below 60 (considered difficult for a general audience).', 'solution': 'Simplify sentence structure and vocabulary to increase the reading ease score for a wider audience.'},
        'keyword_density_warning': {'priority': 'Warning', 'description': 'Pages with a primary keyword density either too high (>4%) or too low (<0.5%).', 'solution': 'Review the content to ensure primary keyword usage is natural, focusing on intent rather than stuffing.'},
        'keyword_placement_warning': {'priority': 'Warning', 'description': 'Pages where the primary keyword is missing from critical elements (Title, H1, Meta Description).', 'solution': 'Incorporate the main keyword into the Title Tag, Meta Description, and H1 tag of the page for optimal relevance.'},
    }

def write_summary_report(report, md_path, audit_level):
    """Writes the final report data directly to a professional Markdown file."""
    
    audit_details = report['audit_details']
    final_score = report['final_score']
    crawled_pages = report['crawled_pages']
    aggregated_issues = report['aggregated_issues']
    basic_checks = report['basic_checks']
    performance_check = report['performance_check']
    issue_map = _get_issue_description_map()
    
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    content = []
    
    # --- Report Header ---
    content.append("# 💎 PROFESSIONAL SEO AUDIT REPORT")
    content.append(f"**Date:** {current_time} | **URL:** {audit_details['target_url']}")
    content.append(f"**Audit Level:** {audit_details['audit_level'].capitalize()} | **Powered by:** Free, Open-Source Tools Only (No API Limits) 🚀")
    content.append("---")
    
    # --- 1. Executive Summary ---
    content.append("## 1. Executive Summary: At a Glance")
    content.append("| Metric | Value | Status |")
    content.append("| :--- | :--- | :--- |")
    content.append(f"| **Final SEO Score** | **{final_score}/100** | **{_get_status_label(final_score)}** |")
    content.append(f"| **Total Pages Crawled** | **{len(crawled_pages)}** | |")
    
    scope_display = audit_details['audit_scope'].replace('_', ' ').capitalize()
    scope_detail = f"The scan focused on {len(crawled_pages)} pages."
    if audit_details['audit_scope'] == 'only_onpage':
        scope_detail = "The scan was limited to the homepage only."
    elif audit_details['audit_scope'] == 'onpage_and_index_pages':
        scope_detail = "The scan covered the homepage and core index pages (limit: 25)."
    elif audit_details['audit_scope'] == 'full_site_300_pages':
         scope_detail = "The scan attempted a deep crawl of the site (limit: 300 pages)."

    content.append(f"| **Audit Scope** | **{scope_display}** | {scope_detail} |")
    content.append("---")
    
    # --- 2. Site-Wide Issue Aggregation (All 18 Checks) ---
    content.append("## 2. Site-Wide Issue Aggregation (All 18 Checks Summarized)")
    content.append("This section summarizes critical failures aggregated across all audited pages, providing a clear overview of the site's most pressing problems.")
    
    top_issues_found = []
    total_issues = 0
    
    # Iterate through the issue map to check against the aggregated counts
    for key, item_data in issue_map.items():
        count = aggregated_issues.get(key, 0)
        if count > 0:
            # Special handling for images missing ALT text, which is a total count, not a page count
            issue_title = item_data['description'].split('(')[0].strip()
            
            if key == 'missing_alt_total':
                 issue_title = f"Total Images Missing ALT Text"
                 
            top_issues_found.append({
                'title': issue_title,
                'count': count,
                'priority': item_data['priority'],
                'description': item_data['description'],
                'solution': item_data['solution']
            })
            total_issues += count

    content.append("### Top Site-Wide Issues Found")
    content.append("| Issue | Total Count | Priority |")
    content.append("| :--- | :--- | :--- |")
    
    for issue in sorted(top_issues_found, key=lambda x: x['priority'], reverse=True):
        content.append(f"| **{issue['title']}** | **{issue['count']}** | {issue['priority']} |")

    content.append(f"| **Total Aggregated Issue Instances** | **{total_issues}** | |")
    content.append("---")
    
    # --- 3. Core Technical Health Check (Basic Checks + Performance) ---
    content.append("## 3. Core Technical Health Check (Focus on Basic Infrastructure)")
    content.append("| Check | Status | Details |")
    content.append("| :--- | :--- | :--- |")
    
    # SSL Check
    ssl_result = basic_checks['ssl_check']
    ssl_status_display = '✅ Valid HTTPS' if ssl_result['valid_ssl'] else '❌ Missing or Invalid'
    ssl_detail = f"Issuer: {ssl_result.get('issuer', 'N/A')}. "
    if not ssl_result['valid_ssl']:
        ssl_detail = f"SSL is missing. HIGH PRIORITY FIX. Error: {ssl_result.get('error', 'Unknown')}"
    content.append(f"| **SSL/HTTPS** | **{ssl_status_display}** | {ssl_detail} |")
    
    # Robots/Sitemap Check
    robots_status = basic_checks['robots_sitemap']
    robots_status_display = '✅ OK' if robots_status['robots.txt'] == 'found' and robots_status['sitemap.xml'] == 'found' else '⚠️ Check Files'
    robots_detail = f"**robots.txt:** {robots_status['robots.txt'].capitalize()}; **sitemap.xml:** {robots_status['sitemap.xml'].capitalize()}. Ensure both are present and accessible."
    content.append(f"| **Robots/Sitemap** | **{robots_status_display}** | {robots_detail} |")

    # Server Response Time (Internal Performance Check)
    perf_result = performance_check['desktop_score']['result'].capitalize()
    perf_message = performance_check['desktop_score']['message']
    response_time = performance_check['response_time_ms']
    content.append(f"| **Server Response Time** | **{perf_result}** | Time: **{response_time}ms**. {perf_message} |")
    content.append("---")

    # --- 4. Actionable Solutions for Key Issues ---
    content.append("## 4. Actionable Solutions for Key Issues")
    content.append("This section provides clear, human-readable solutions for the most critical issues identified in Section 2.")
    
    for issue in sorted(top_issues_found, key=lambda x: x['priority'], reverse=True):
        content.append(f"### 💡 Issue: {issue['title']} ({issue['count']} Instances)")
        content.append(f"* **Description:** {issue['description']}")
        content.append(f"* **Priority:** **{issue['priority']}**")
        content.append(f"* **Solution:** {issue['solution']}")
        
    content.append("---")
    
    # --- 5. Detailed Page-by-Page Audit ---
    content.append(f"## 5. Detailed Page-by-Page Audit ({len(crawled_pages)} Pages)")
    content.append("This section provides granular data for each page crawled. Note that Playwright is used to crawl JavaScript-rendered sites, ensuring all dynamic content is audited.")
    
    # All 18 checks list for reference
    all_checks = [
        'url_structure', 'canonical', 'meta', 'headings', 'content', 'images', 'mobile', 'local_seo', 
        'analytics', 'accessibility', 'schema', 'keywords', 'links', 'internal_links', 'backlinks', 
        'ssl_check (Basic)', 'robots_sitemap (Basic)', 'performance_check (Basic)'
    ]
    
    for i, page in enumerate(crawled_pages):
        page_index = i + 1
        url = page.get('url', 'N/A')
        status_code = page.get('status_code', 'N/A')
        
        content.append(f"### 📄 Page {page_index}: `{url}` (Status: {status_code})")
        
        if not page.get('is_crawlable', True):
            content.append(f"**Crawl Status:** **❌ SKIPPED** - {page.get('error_detail', 'Page not crawlable/returned error code.')}")
            content.append("---")
            continue

        # --- Standard On-Page Checks (Always Run) ---
        content.append("| Metric | Check Name | Status | Details |")
        content.append("| :--- | :--- | :--- | :--- |")
        
        # Meta Title
        title = page.get('meta', {}).get('title', 'MISSING')
        title_len = len(title) if title != 'MISSING' else 0
        title_status = '✅ OK' if 30 <= title_len <= 65 else '❌ FAIL'
        content.append(f"| **Meta** | Title Tag Length | {title_status} | **Title:** {title[:50]}... (Length: {title_len}) |")
        
        # Meta Description
        description = page.get('meta', {}).get('description', 'MISSING')
        desc_status = '✅ OK' if description != 'MISSING' else '❌ MISSING'
        content.append(f"| **Meta** | Meta Description | {desc_status} | **Description:** {description[:50]}... |")
        
        # H1 Count
        h1_count = page.get('headings', {}).get('h1', 0)
        h1_status = '✅ OK' if h1_count == 1 else '❌ FAIL'
        content.append(f"| **Structure** | H1 Count | {h1_status} | Found **{h1_count}** H1 tags. Must be exactly 1. |")
        
        # Word Count
        word_count = page.get('content', {}).get('word_count', 0)
        word_status = '✅ OK' if word_count >= 200 else '❌ FAIL'
        content.append(f"| **Content** | Word Count | {word_status} | Found **{word_count}** words. Thin content warning below 200. |")
        
        # Canonical Tag
        canonical = page.get('canonical', {})
        canonical_status = '✅ Valid' if canonical.get('match', False) else '⚠️ Check'
        canonical_detail = f"**Tag:** {canonical.get('canonical_url', 'N/A')}. **Matches Page URL:** {'Yes' if canonical.get('match') else 'No/Missing'}."
        content.append(f"| **Technical** | Canonical Tag | {canonical_status} | {canonical_detail} |")
        
        # Broken Links
        broken_links = page.get('links', {}).get('broken', [])
        link_status = '✅ OK' if not broken_links else '❌ BROKEN'
        link_detail = f"Found **{len(broken_links)}** broken link(s). Sample broken: {broken_links[0] if broken_links else 'N/A'}"
        content.append(f"| **Technical** | Broken Links | {link_status} | {link_detail} |")

        # Mobile Friendliness
        mobile = page.get('mobile', {})
        mobile_status = '✅ OK' if mobile.get('mobile_friendly', True) else '❌ FAIL'
        mobile_detail = f"Note: {mobile.get('note', 'N/A')}. Issues: {', '.join(mobile.get('issues', [])) or 'None'}"
        content.append(f"| **Technical** | Mobile Friendly | {mobile_status} | {mobile_detail} |")

        # --- Advanced Checks (Conditional on Audit Level) ---
        if audit_level in ['standard', 'advanced']:
            content.append("#### Standard/Advanced Checks")
            
          # Local SEO NAP
            local_seo = page.get('local_seo', {}).get('nap_consistency', {})
            content.append(f"- **Local SEO (NAP):** ({local_seo.get('result', 'N/A')}) {local_seo.get('message', 'N/A')}")
            
            # Schema Markup
            schema = page.get('schema', {})
            schema_count = schema.get('found_count', 0)
            schema_status = '✅ OK' if schema_count > 0 else '⚠️ Check'
            content.append(f"- **Schema Markup:** ({schema_status}) Found **{schema_count}** JSON-LD tags ({', '.join(schema.get('schema_tags', [])[:3])}...)")

            # Keyword Density
            keywords = page.get('keywords', {})
            density = keywords.get('density_check', {})
            content.append(f"- **Keyword Density:** ({density.get('result', 'N/A')}) {density.get('message', 'N/A')}")

            # Analytics Check
            analytics = page.get('analytics', {})
            tracking = analytics.get('tracking_setup', {})
            analytics_status = '✅ OK' if tracking.get('google_analytics_found') or tracking.get('google_tag_manager_found') else '⚠️ Missing'
            content.append(f"- **Analytics Tracking:** ({analytics_status}) GA Found: {tracking.get('google_analytics_found')}, GTM Found: {tracking.get('google_tag_manager_found')}")
        
        content.append("---")

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    print(f"Professional Markdown Report written to {md_path}")
    
