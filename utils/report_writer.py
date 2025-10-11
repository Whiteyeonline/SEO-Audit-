# utils/report_writer.py
import json
import datetime
from textblob import TextBlob
from nltk.tokenize import sent_tokenize
import re
import textstat
from urllib.parse import urlparse

# NOTE: The existing _calculate_readability function relies on the external 
# textstat library which is included in your requirements.txt.

def _get_issue_description_map():
    """Maps check keys to human-readable names, priorities, and solutions."""
    return {
        'title_fail_count': {
            'name': 'Missing or Poorly Formatted Title Tag',
            'priority': 'High',
            'description': 'Pages missing a Title Tag or having one that is too long/short (Optimal: 30-60 characters).',
            'solution': 'Add unique, compelling title tags (30-60 characters) that include the target keyword at the front.'
        },
        'desc_fail_count': {
            'name': 'Missing Meta Description',
            'priority': 'High',
            'description': 'Pages missing a Meta Description (Essential for click-through rate in SERPs).',
            'solution': 'Add unique, compelling meta descriptions (120-158 characters) that encourage users to click.'
        },
        'h1_fail_count': {
            'name': 'Multiple or Missing H1 Tag',
            'priority': 'High',
            'description': 'Pages having missing H1 tags or more than one H1 tag (SEO best practice is one H1 per page).',
            'solution': 'Ensure every page has exactly one descriptive H1 tag that outlines the primary topic.'
        },
        'thin_content_count': {
            'name': 'Thin Content Warning',
            'priority': 'Medium',
            'description': 'Pages with very little unique content (under 200 words).',
            'solution': 'Significantly increase the unique, high-quality, and useful content on these pages.'
        },
        'missing_alt_total': {
            'name': 'Images Missing Alt Text',
            'priority': 'Low',
            'description': 'Images without proper `alt` attributes, harming accessibility and image SEO.',
            'solution': 'Add descriptive `alt` text to all images to aid screen readers and search engines.'
        },
        'link_broken_total': {
            'name': 'Internal or External Broken Links (4XX/5XX)',
            'priority': 'High',
            'description': 'Links pointing to pages that return an error code (4xx or 5xx).',
            'solution': 'Update or remove all broken links to preserve link equity and user experience.'
        },
        'canonical_mismatch_count': {
            'name': 'Canonical Tag Issues',
            'priority': 'Medium',
            'description': 'Canonical tags pointing to an incorrect URL or missing entirely on pages that require one (e.g., product filters).',
            'solution': 'Review canonical tag implementation to ensure it points to the preferred version of the page, preventing duplicate content issues.'
        },
        'mobile_unfriendly_count': {
            'name': 'Mobile Unfriendly Pages',
            'priority': 'High',
            'description': 'Pages identified as not being fully responsive or mobile-friendly (critical for Google’s Mobile-First Indexing).',
            'solution': 'Use responsive design principles (CSS media queries) to ensure the layout adapts perfectly to all screen sizes.'
        },
        'analytics_missing_count': {
            'name': 'Missing Analytics/Tracking Code',
            'priority': 'Medium',
            'description': 'Pages where a Google Analytics or other specified tracking code could not be detected.',
            'solution': 'Ensure the appropriate tracking snippet is placed correctly in the `<head>` section of all pages.'
        },
        # === NEW CHECKS ===
        'og_tags_fail_count': {
            'name': 'Missing Essential Open Graph Tags',
            'priority': 'Medium',
            'description': 'Crucial Open Graph tags (e.g., og:title, og:image) are missing, leading to poor social media sharing previews (e.g., Facebook, X/Twitter).',
            'solution': 'Implement all essential Open Graph meta tags in the `<head>` section to control how content appears when shared.'
        },
        'redirect_info_count': {
            'name': 'Page Redirect Detected',
            'priority': 'Low',
            'description': 'A redirect was detected, meaning the requested URL is not the final URL. This suggests a redirect chain or an unnecessary hop.',
            'solution': 'For permanent changes, ensure a 301 Permanent Redirect is used. Avoid long redirect chains, aiming for direct access to the final URL.'
        },
        'core_web_vitals_warn_count': {
            'name': 'Performance Warning (High Latency)',
            'priority': 'High',
            'description': 'The page experienced high download latency, which acts as a proxy for slow server response time (TTFB), impacting Core Web Vitals (LCP).',
            'solution': 'Optimize server-side rendering, reduce initial server response time, and minimize resource load times.'
        }
    }

# (The _calculate_readability function is omitted here for brevity but should remain the same as the last version you received)

def get_check_aggregation(crawled_pages):
    """
    Aggregates issue counts across all crawled pages.
    """
    aggregation = {
        'total_pages_crawled': len(crawled_pages),
        # Initialize all known aggregation counts to 0
        'title_fail_count': 0, 'desc_fail_count': 0, 'h1_fail_count': 0,
        'thin_content_count': 0, 'missing_alt_total': 0, 'canonical_mismatch_count': 0,
        'link_broken_total': 0, 'analytics_missing_count': 0, 'mobile_unfriendly_count': 0,
        'url_not_clean_count': 0, 'nap_fail_count': 0,
        'accessibility_fail_count': 0,
        # === NEW CHECKS ADDED HERE ===
        'og_tags_fail_count': 0,
        'redirect_info_count': 0,
        'core_web_vitals_warn_count': 0,
        # =============================
    }
    for page in crawled_pages:
        page_checks = page.get('checks', {})

        # --- Aggregation Logic (Unchanged from last version) ---
        meta_data = page_checks.get('checks.meta_check', {})
        if meta_data.get('title_fail') is True:
            aggregation['title_fail_count'] += 1
        if meta_data.get('desc_fail') is True:
            aggregation['desc_fail_count'] += 1

        heading_data = page_checks.get('checks.heading_check', {})
        if heading_data.get('h1_fail') is True:
            aggregation['h1_fail_count'] += 1

        content_data = page_checks.get('checks.content_quality', {})
        if content_data.get('thin_content') is True:
            aggregation['thin_content_count'] += 1

        image_data = page_checks.get('checks.image_check', {})
        aggregation['missing_alt_total'] += image_data.get('missing_alt_images_count', 0)

        link_data = page_checks.get('checks.link_check', {})
        aggregation['link_broken_total'] += link_data.get('broken_link_count', 0)

        canonical_data = page_checks.get('checks.canonical_check', {})
        if canonical_data.get('canonical_mismatch') is True:
            aggregation['canonical_mismatch_count'] += 1

        mobile_data = page_checks.get('checks.mobile_friendly_check', {})
        if mobile_data.get('not_mobile_friendly') is True:
            aggregation['mobile_unfriendly_count'] += 1

        analytics_data = page_checks.get('checks.analytics_check', {})
        if analytics_data.get('analytics_missing') is True:
            aggregation['analytics_missing_count'] += 1

        # === NEW CHECK AGGREGATIONS ===
        og_data = page_checks.get('checks.og_tags_check', {})
        if og_data.get('og_tags_missing') is True:
            aggregation['og_tags_fail_count'] += 1

        redirect_data = page_checks.get('checks.redirect_check', {})
        if redirect_data.get('was_redirected') is True:
            aggregation['redirect_info_count'] += 1

        cwv_data = page_checks.get('checks.core_web_vitals_check', {})
        if cwv_data.get('performance_status') == '⚠️ WARN':
            aggregation['core_web_vitals_warn_count'] += 1
        # ==============================

    return aggregation

def write_summary_report(report, final_score, md_path):
    """
    Writes the final report data directly to a professional, spacious Markdown file.
    (This function is expanded to display ALL checks in the detail section)
    """
    audit_details = report['audit_details']
    crawled_pages = report['crawled_pages']
    aggregated_issues = report['aggregated_issues']
    
    # Calculate Score
    critical_issues_count = (
        aggregated_issues.get('title_fail_count', 0) +
        aggregated_issues.get('desc_fail_count', 0) +
        aggregated_issues.get('h1_fail_count', 0) +
        aggregated_issues.get('link_broken_total', 0) +
        aggregated_issues.get('mobile_unfriendly_count', 0)
    )
    score = max(100 - (critical_issues_count * 5), 50)

    issue_map = _get_issue_description_map()
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    content = []
    
    # --- 1. Report Header ---
    content.append("# 💎 PROFESSIONAL SEO AUDIT REPORT\n\n")
    # ... (Header details are omitted for brevity but remain the same)
    
    # --- 2. Executive Summary ---
    # ... (Summary section is omitted for brevity but remains the same)

    # --- 3. Critical Issues & Recommendations ---
    # ... (Recommendation section is omitted for brevity but remains the same)
    
    # --- 4. Detailed Page-by-Page Audit ---
    content.append(f"## 3. Detailed Page-by-Page Audit ({len(crawled_pages)} Pages)\n\n")
    content.append("This section provides granular data for each page crawled. The output is structured to allow comfortable reading for detailed analysis.\n\n")

    # Process each crawled page for its detailed report
    for idx, page in enumerate(crawled_pages):
        page_checks = page.get('checks', {})
        page_url = page.get('url', 'N/A')
        status = page.get('status_code', 'N/A')

        content.append(f"\n--- 📄 **PAGE AUDIT: {idx + 1}** ---\n")
        content.append(f"### 📍 URL: `{page_url}`\n")
        content.append(f"**HTTP Status Code:** `{status}`\n\n")
        
        check_details = []

        # Helper function to create a detail line
        def add_detail(category, check, status, description):
            check_details.append(f"| {category} | {check} | **{status}** | {description} |")

        # Handle Module Errors
        has_error = False
        for key, data in page_checks.items():
            if data.get('error'):
                error_name = key.split('.')[-1].replace('_', ' ').title()
                add_detail('ERROR', error_name, '❌ FAIL', data.get('error'))
                has_error = True

        # --- Technical Checks (Expanded) ---
        
        # SSL CHECK
        ssl_data = page_checks.get('checks.ssl_check', {})
        if 'valid_ssl' in ssl_data:
            ssl_status = '✅ PASS' if ssl_data.get('valid_ssl') else '❌ FAIL'
            add_detail('Technical', 'SSL/HTTPS', ssl_status, ssl_data.get('note', 'N/A'))
        
        # ROBOTS & SITEMAP CHECK
        robots_data = page_checks.get('checks.robots_sitemap', {})
        if 'robots.txt_status' in robots_data:
            robots_status = '✅ PASS' if robots_data.get('robots.txt_status') == 'found' else '⚠️ WARN'
            add_detail('Technical', 'Robots.txt', robots_status, f"Status: {robots_data.get('robots.txt_status').capitalize()}.")
            
        # CANONICAL CHECK (Crucial for AMP pages)
        canonical_data = page_checks.get('checks.canonical_check', {})
        if 'canonical_url' in canonical_data:
            canonical_status = '✅ PASS'
            if canonical_data.get('canonical_mismatch'): canonical_status = '⚠️ CHECK'
            if canonical_data.get('canonical_url') is None: canonical_status = '⚠️ MISSING'
            add_detail('Technical', 'Canonical Tag', canonical_status, canonical_data.get('note', 'N/A'))
            
        # REDIRECT CHECK (NEW)
        redirect_data = page_checks.get('checks.redirect_check', {})
        if 'was_redirected' in redirect_data:
            redirect_status = '✅ OK' if not redirect_data.get('was_redirected') else '⚠️ INFO'
            add_detail('Technical', 'Redirect Check', redirect_status, redirect_data.get('note', 'N/A'))

        # MOBILE FRIENDLY CHECK
        mobile_data = page_checks.get('checks.mobile_friendly_check', {})
        if 'is_mobile_friendly' in mobile_data:
            mobile_status = '✅ PASS' if mobile_data.get('is_mobile_friendly') else '❌ FAIL'
            add_detail('Technical', 'Mobile Friendly', mobile_status, f"Status: {'Friendly' if mobile_data.get('is_mobile_friendly') else 'Not Friendly'}.")
            
        # LINK CHECK (Broken Links)
        link_data = page_checks.get('checks.link_check', {})
        if 'broken_link_count' in link_data:
            link_status = '✅ PASS' if link_data.get('broken_link_count', 0) == 0 else '❌ FAIL'
            add_detail('Technical', 'Broken Links', link_status, f"Found **{link_data.get('broken_link_count', 0)}** broken link(s). Sample: {link_data.get('sample_broken_link', 'N/A')}")
        
        # ANALYTICS CHECK
        analytics_data = page_checks.get('checks.analytics_check', {})
        if 'analytics_missing' in analytics_data:
            analytics_status = '✅ PASS' if not analytics_data.get('analytics_missing') else '⚠️ MISSING'
            add_detail('Technical', 'Analytics', analytics_status, f"GA/GTM Found: {analytics_status}. Note: {analytics_data.get('note', 'N/A')}")


        # --- Content/Structure Checks (Expanded) ---

        # META CHECK (Title/Description)
        meta_data = page_checks.get('checks.meta_check', {})
        if 'title_fail' in meta_data:
            title_status = '✅ PASS'
            if meta_data.get('title_fail'): title_status = '❌ FAIL'
            if meta_data.get('title_check') == 'MISSING': title_status = '❌ MISSING'
            add_detail('Meta', 'Title Tag', title_status, f"Title: `{meta_data.get('title_content', 'N/A')}` (Length: {meta_data.get('title_length', 0)})")
        
        if 'desc_fail' in meta_data:
            desc_status = '✅ PASS' if meta_data.get('desc_content') else '❌ MISSING'
            add_detail('Meta', 'Meta Description', desc_status, f"Description: `{meta_data.get('desc_content', 'MISSING...')[:100]}...`")

        # HEADING CHECK (H1)
        heading_data = page_checks.get('checks.heading_check', {})
        if 'h1_fail' in heading_data:
            h1_status = '✅ PASS' if not heading_data.get('h1_fail') else '❌ FAIL'
            add_detail('Structure', 'H1 Count', h1_status, f"Found **{heading_data.get('h1_count', 0)}** H1 tags. Must be exactly 1.")

        # CONTENT QUALITY (Word Count)
        content_data = page_checks.get('checks.content_quality', {})
        if 'word_count' in content_data:
            word_status = '✅ PASS'
            if content_data.get('word_count', 0) < 200: word_status = '❌ FAIL'
            add_detail('Content', 'Word Count', word_status, f"Found **{content_data.get('word_count', 0)}** words. Thin content warning below 200.")
        
        # OG TAGS CHECK (NEW)
        og_data = page_checks.get('checks.og_tags_check', {})
        if 'og_tags_missing' in og_data:
            og_status = '✅ PASS' if not og_data.get('og_tags_missing') else '❌ FAIL'
            add_detail('Social', 'Open Graph Tags', og_status, og_data.get('note', 'N/A'))

        # CWV PROXY CHECK (NEW)
        cwv_data = page_checks.get('checks.core_web_vitals_check', {})
        if 'performance_status' in cwv_data:
            cwv_status = cwv_data.get('performance_status')
            add_detail('Performance', 'CWV Proxy (TTFB)', cwv_status, cwv_data.get('note', 'N/A'))


        # --- Output the table ---
        if check_details:
            # Sort errors to the top
            sorted_details = sorted(check_details, key=lambda x: 0 if '❌ FAIL' in x else (1 if '⚠️ WARN' in x else 2))

            content.append("| Category | Check Name | Status | Details |\n")
            content.append("| :--- | :--- | :--- | :--- |\n")
            content.extend(sorted_details)
        else:
            content.append("* No check results available for this page.*\n")
        
        content.append("\n\n---\n") # Final separator for the page audit


    # -----------------------------------------------------
    # 5. Appendix/Disclaimer
    # -----------------------------------------------------
    content.append("## 4. Disclaimer & Technology Used\n\n")
    # ... (Disclaimer section is omitted for brevity but remains the same)


    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    print(f"Professional Markdown Report written to {md_path}")
    
