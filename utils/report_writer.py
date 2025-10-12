# utils/report_writer.py
import json
import datetime
from textblob import TextBlob
from nltk.tokenize import sent_tokenize
import re
import textstat
from urllib.parse import urlparse

# NOTE: The existing _calculate_readability function is omitted for brevity but should remain unchanged.

def _get_issue_description_map():
    """Maps check keys to human-readable names, priorities, and solutions."""
    # NOTE: The keys here should generally match the aggregation keys in get_check_aggregation 
    # OR map directly to the specific failure condition.
    return {
        'title_fail': {
            'name': 'Missing or Poorly Formatted Title Tag',
            'priority': 'High',
            'description': 'Pages missing a Title Tag or having one that is too long/short (Optimal: 30-60 characters).',
            'solution': 'Add unique, compelling title tags (30-60 characters) that include the target keyword at the front.'
        },
        'desc_fail': {
            'name': 'Missing Meta Description',
            'priority': 'High',
            'description': 'Pages missing a Meta Description (Essential for click-through rate in SERPs).',
            'solution': 'Add unique, compelling meta descriptions (120-158 characters) that encourage users to click.'
        },
        'h1_fail': {
            'name': 'Multiple or Missing H1 Tag',
            'priority': 'High',
            'description': 'Pages having missing H1 tags or more than one H1 tag (SEO best practice is one H1 per page).',
            'solution': 'Ensure every page has exactly one descriptive H1 tag that outlines the primary topic.'
        },
        'thin_content': {
            'name': 'Thin Content Warning',
            'priority': 'Medium',
            'description': 'Pages with very little unique content (under 200 words).',
            'solution': 'Significantly increase the unique, high-quality, and useful content on these pages.'
        },
        'missing_alt_images': {
            'name': 'Images Missing Alt Text',
            'priority': 'Low',
            'description': 'Images without proper `alt` attributes, harming accessibility and image SEO.',
            'solution': 'Add descriptive `alt` text to all images to aid screen readers and search engines.'
        },
        'broken_link_count': {
            'name': 'Internal or External Broken Links (4XX/5XX)',
            'priority': 'High',
            'description': 'Links pointing to pages that return an error code (4xx or 5xx).',
            'solution': 'Update or remove all broken links to preserve link equity and user experience.'
        },
        'canonical_mismatch': {
            'name': 'Canonical Tag Issues',
            'priority': 'Medium',
            'description': 'Canonical tags pointing to an incorrect URL or missing entirely on pages that require one.',
            'solution': 'Review canonical tag implementation to ensure it points to the preferred version of the page, preventing duplicate content issues.'
        },
        'not_mobile_friendly': {
            'name': 'Mobile Unfriendly Pages',
            'priority': 'High',
            'description': 'Pages identified as not being fully responsive (critical for Mobile-First Indexing).',
            'solution': 'Use responsive design principles to ensure the layout adapts perfectly to all screen sizes.'
        },
        'analytics_missing': {
            'name': 'Missing Analytics/Tracking Code',
            'priority': 'Medium',
            'description': 'Pages where a Google Analytics or other specified tracking code could not be detected.',
            'solution': 'Ensure the appropriate tracking snippet is placed correctly in the `<head>` section of all pages.'
        },
        'og_tags_missing': {
            'name': 'Missing Essential Open Graph Tags',
            'priority': 'Medium',
            'description': 'Crucial Open Graph tags are missing, leading to poor social media sharing previews.',
            'solution': 'Implement all essential Open Graph meta tags in the `<head>` section to control how content appears when shared.'
        },
        'was_redirected': {
            'name': 'Unnecessary Page Redirect Detected',
            'priority': 'Low',
            'description': 'A redirect was detected, suggesting a redirect chain or an unnecessary hop.',
            'solution': 'For permanent changes, ensure a 301 Permanent Redirect is used. Aim for direct access to the final URL.'
        },
        'cwv_warn': {
            'name': 'Performance Warning (High Latency/TTFB)',
            'priority': 'High',
            'description': 'The page experienced high download latency, which acts as a proxy for slow server response time (TTFB), impacting Core Web Vitals.',
            'solution': 'Optimize server-side rendering, reduce initial server response time, and minimize resource load times.'
        },
        'robots_sitemap_fail': {
            'name': 'Robots/Sitemap Issues',
            'priority': 'Medium',
            'description': 'The `robots.txt` or `sitemap.xml` file was not found or contains errors, hindering crawl efficiency.',
            'solution': 'Verify the correct location and syntax of your `robots.txt`. Ensure a recent `sitemap.xml` file is linked from `robots.txt`.'
        },
        'unclean_url': {
            'name': 'Unclean URL Structure',
            'priority': 'Low',
            'description': 'URLs containing excessive parameters, stop words, or non-ASCII characters.',
            'solution': 'Keep URLs short, descriptive, and clean. Use hyphens to separate words and include target keywords.'
        },
        'nap_mismatch': {
            'name': 'Local SEO NAP Mismatch',
            'priority': 'Medium',
            'description': 'Mismatched Name, Address, or Phone (NAP) details, confusing local search engines.',
            'solution': 'Ensure NAP details are 100% consistent across all pages and external directory listings (Google Business Profile, Yelp, etc.).'
        },
        'accessibility_fail': {
            'name': 'Basic Accessibility Issues',
            'priority': 'Medium',
            'description': 'The page fails basic accessibility checks (e.g., color contrast, focus order), impacting all users.',
            'solution': 'Follow WCAG guidelines (e.g., use sufficient color contrast, keyboard-navigable elements, and aria attributes) for an inclusive experience.'
        },
        'missing_internal_links': {
            'name': 'Page Lacks Internal Links',
            'priority': 'Low',
            'description': 'The page has very few internal links pointing to it, reducing its visibility and passing link equity.',
            'solution': 'Contextually link to this page from other high-authority and relevant pages on your site.'
        },
        'server_response_slow': {
            'name': 'Slow Server Response Time',
            'priority': 'High',
            'description': 'Server response time (TTFB) is too slow, directly impacting page speed and user experience.',
            'solution': 'Optimize server configuration, use a CDN, and improve database query efficiency to reduce server response time below 200ms.'
        }
        # Backlinks check and Schema check are generally informational and handled inline.
    }


def get_check_aggregation(crawled_pages):
    """
    Aggregates issue counts across all crawled pages.
    (This function remains largely the same, but includes logic for all 21 checks.)
    """
    # Define a list of ALL check keys for aggregation initialization
    all_agg_keys = [
        'title_fail_count', 'desc_fail_count', 'h1_fail_count', 'thin_content_count', 
        'missing_alt_total', 'canonical_mismatch_count', 'link_broken_total', 
        'analytics_missing_count', 'mobile_unfriendly_count', 'url_not_clean_count', 
        'nap_fail_count', 'accessibility_fail_count', 'og_tags_fail_count', 
        'redirect_info_count', 'core_web_vitals_warn_count', 'robots_sitemap_fail_count',
        'server_response_fail_count' # Added for performance
    ]

    aggregation = {'total_pages_crawled': len(crawled_pages)}
    for key in all_agg_keys:
        aggregation[key] = 0

    for page in crawled_pages:
        page_checks = page.get('checks', {})

        # Meta & Heading Checks
        meta_data = page_checks.get('checks.meta_check', {})
        if meta_data.get('title_fail') is True: aggregation['title_fail_count'] += 1
        if meta_data.get('desc_fail') is True: aggregation['desc_fail_count'] += 1
        heading_data = page_checks.get('checks.heading_check', {})
        if heading_data.get('h1_fail') is True: aggregation['h1_fail_count'] += 1

        # Content & Image Checks
        content_data = page_checks.get('checks.content_quality', {})
        if content_data.get('thin_content') is True: aggregation['thin_content_count'] += 1
        image_data = page_checks.get('checks.image_check', {})
        aggregation['missing_alt_total'] += image_data.get('missing_alt_images_count', 0)

        # Link, Canonical & Redirect Checks
        link_data = page_checks.get('checks.link_check', {})
        aggregation['link_broken_total'] += link_data.get('broken_link_count', 0)
        canonical_data = page_checks.get('checks.canonical_check', {})
        if canonical_data.get('canonical_mismatch') is True: aggregation['canonical_mismatch_count'] += 1
        redirect_data = page_checks.get('checks.redirect_check', {})
        if redirect_data.get('was_redirected') is True: aggregation['redirect_info_count'] += 1

        # Technical & Structure Checks
        mobile_data = page_checks.get('checks.mobile_friendly_check', {})
        if mobile_data.get('not_mobile_friendly') is True: aggregation['mobile_unfriendly_count'] += 1
        analytics_data = page_checks.get('checks.analytics_check', {})
        if analytics_data.get('analytics_missing') is True: aggregation['analytics_missing_count'] += 1
        og_data = page_checks.get('checks.og_tags_check', {})
        if og_data.get('og_tags_missing') is True: aggregation['og_tags_fail_count'] += 1
        url_data = page_checks.get('checks.url_structure', {})
        if url_data.get('not_clean') is True: aggregation['url_not_clean_count'] += 1
        robots_data = page_checks.get('checks.robots_sitemap', {})
        if robots_data.get('robots_sitemap_fail_count', 0) > 0: aggregation['robots_sitemap_fail_count'] += 1
        
        # Performance & Accessibility
        cwv_data = page_checks.get('checks.core_web_vitals_check', {})
        if cwv_data.get('performance_status') == '⚠️ WARN': aggregation['core_web_vitals_warn_count'] += 1
        perf_data = page_checks.get('checks.performance_check', {})
        if perf_data.get('mobile_score', {}).get('result') != 'Pass': aggregation['server_response_fail_count'] += 1
        a11y_data = page_checks.get('checks.accessibility_check', {})
        if a11y_data.get('accessibility_fail') is True: aggregation['accessibility_fail_count'] += 1
        
        # Local SEO
        nap_data = page_checks.get('checks.local_seo_check', {})
        if nap_data.get('nap_fail') is True: aggregation['nap_fail_count'] += 1

    return aggregation


def write_summary_report(report, final_score, md_path):
    """
    Writes the final report data to a professional Markdown file, using the new 
    spacious 'word box' format for the detailed audit section, ensuring all 21 checks are included.
    """
    # NOTE: Header, Summary, and Recommendations sections are omitted for brevity but remain the same.
    audit_details = report['audit_details']
    crawled_pages = report['crawled_pages']
    aggregated_issues = report['aggregated_issues']
    
    # Recalculate Score (or use final_score from input)
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
    content.append(f"**Target URL:** `{audit_details.get('target_url', 'N/A')}`\n")
    content.append(f"**Audit Date:** {current_time}\n")
    content.append(f"**Total Pages Crawled:** {len(crawled_pages)}\n")
    content.append(f"**Overall Site Score:** **{score}/100**\n\n")
    content.append("---\n\n") # Separator

    # --- (Sections 2 and 3 omitted) ---
    content.append("## 3. Detailed Page-by-Page Audit\n\n")
    content.append("This section provides granular, check-by-check data for each page crawled, utilizing a clear block format for readability.\n\n")


    # Define ALL 21 Checks in their intended report order
    ALL_CHECK_KEYS = [
        'checks.ssl_check', 'checks.robots_sitemap', 'checks.redirect_check', 
        'checks.canonical_check', 'checks.url_structure', 'checks.meta_check', 
        'checks.heading_check', 'checks.content_quality', 'checks.image_check', 
        'checks.link_check', 'checks.internal_links', 'checks.schema_check', 
        'checks.mobile_friendly_check', 'checks.accessibility_check', 'checks.performance_check', 
        'checks.core_web_vitals_check', 'checks.analytics_check', 'checks.og_tags_check', 
        'checks.local_seo_check', 'checks.keyword_analysis', 'checks.backlinks_check'
    ]

    # Process each crawled page for its detailed report
    for idx, page in enumerate(crawled_pages):
        page_checks = page.get('checks', {})
        page_url = page.get('url', 'N/A')
        status = page.get('status_code', 'N/A')

        content.append(f"\n# 📍 PAGE AUDIT {idx + 1}: {page_url}\n")
        content.append(f"**HTTP Status Code:** `{status}`\n")
        content.append("---")
        
        
        # --- Helper Function for the New Formatting ---
        def _format_check_box(check_name, status, details, solution_key=None, note=None):
            box = []
            box.append(f"\n**{check_name.upper()}**")
            box.append("-----------------")
            box.append(f"**STATUS:** **{status}**")
            
            # Add general details/note if available
            if details:
                box.append(f"**DETAILS:** {details}")
            elif note:
                box.append(f"**NOTE:** {note}")

            # Add solution/recommendation if the status is not a PASS/OK
            if status.startswith('❌') or status.startswith('⚠️'):
                if solution_key and solution_key in issue_map:
                    issue = issue_map[solution_key]
                    box.append(f"\n**💡 RECOMMENDATION: {issue['name']}**")
                    box.append(f"**Priority:** {issue['priority']}")
                    box.append(f"**Solution:** {issue['solution']}")
            
            box.append("_______________________________")
            return '\n'.join(box)
        # --- End Helper Function ---


        # Process all 21 checks
        for key in ALL_CHECK_KEYS:
            data = page_checks.get(key, {})
            check_name = key.split('.')[-1].replace('_', ' ').title()
            
            # --- Specific Logic for Each Check (Crucial for the 21 Checks requirement) ---
            
            if data.get('error'):
                # Handle unhandled errors for any module
                formatted_box = _format_check_box(f"MODULE ERROR: {check_name}", "❌ FAIL", 
                                                f"Unhandled exception during check: {data.get('error')}", 
                                                'canonical_mismatch') # Using canonical as a general technical fix
                content.append(formatted_box)
                continue

            elif key == 'checks.ssl_check':
                if data.get('valid_ssl'):
                    status = '✅ PASS'
                    details = f"SSL is valid. Issuer: {data.get('issuer', 'N/A')}"
                else:
                    status = '❌ FAIL'
                    details = "SSL is invalid or missing."
                content.append(_format_check_box(check_name, status, details))

            elif key == 'checks.robots_sitemap':
                robots = data.get('robots.txt_status', 'not found')
                sitemap = data.get('sitemap.xml_status', 'not found')
                status = '✅ PASS'
                if robots != 'found' or sitemap != 'found':
                    status = '❌ FAIL'
                details = f"Robots.txt Status: **{robots.upper()}**. Sitemap.xml Status: **{sitemap.upper()}**."
                content.append(_format_check_box(check_name, status, details, 'robots_sitemap_fail', data.get('note')))
            
            elif key == 'checks.redirect_check':
                was_redirected = data.get('was_redirected', False)
                status = '✅ OK' if not was_redirected else '⚠️ INFO'
                details = f"Requested URL: `{data.get('initial_url', 'N/A')}` | Final URL: `{data.get('final_url', 'N/A')}`"
                content.append(_format_check_box(check_name, status, details, 'was_redirected', data.get('note')))
            
            
            elif key == 'checks.canonical_check':
                if data.get('error'):
                    # Handle the specific error returned by the robust check function
                    status = '❌ FAIL'
                    details = f"MODULE CRASHED: {data.get('error')}"
                else:
                    # Run the normal canonical logic
                    mismatch = data.get('canonical_mismatch', False)
                    canonical_url = data.get('canonical_url', None)
                    status = '✅ PASS'
                    if mismatch or canonical_url is None: status = '⚠️ CHECK'
                    if canonical_url is None: status = '❌ MISSING'
                    details = f"Canonical URL: `{canonical_url if canonical_url else 'NONE DETECTED'}`. Is on-page URL correct? {data.get('note', 'N/A')}"
                    
                content.append(_format_check_box(check_name, status, details, 'canonical_mismatch', data.get('note')))
                
    

            elif key == 'checks.url_structure':
                if data.get('not_clean'):
                    status = '⚠️ WARN'
                    details = f"URL contains parameters or stop words (e.g., `{urlparse(page_url).path}`)."
                else:
                    status = '✅ PASS'
                    details = f"URL is clean and uses best practices: `{urlparse(page_url).path}`"
                content.append(_format_check_box(check_name, status, details, 'unclean_url'))

            elif key == 'checks.meta_check':
                # Split Title and Description for better readability in the new format
                title_fail = data.get('title_fail')
                desc_fail = data.get('desc_fail')

                # Title Tag Block
                t_status = '❌ FAIL' if title_fail else '✅ PASS'
                t_details = f"Title: `{data.get('title_content', 'N/A')}` (Length: {data.get('title_length', 0)})"
                content.append(_format_check_box("Title Tag Check", t_status, t_details, 'title_fail'))

                # Meta Description Block
                d_status = '❌ FAIL' if desc_fail or not data.get('desc_content') else '✅ PASS'
                d_details = f"Description: `{data.get('desc_content', 'MISSING...')[:100]}...` (Length: {data.get('desc_length', 0)})"
                content.append(_format_check_box("Meta Description Check", d_status, d_details, 'desc_fail'))
            
            elif key == 'checks.heading_check':
                h1_fail = data.get('h1_fail')
                status = '❌ FAIL' if h1_fail else '✅ PASS'
                details = f"Found **{data.get('h1_count', 0)}** H1 tags. (Optimal: exactly 1)"
                content.append(_format_check_box(check_name, status, details, 'h1_fail'))

            elif key == 'checks.content_quality':
                word_count = data.get('word_count', 0)
                status = '✅ PASS'
                if word_count < 200: status = '❌ FAIL'
                details = f"Found **{word_count}** words. (Warning for thin content below 200 words)"
                content.append(_format_check_box(check_name, status, details, 'thin_content', data.get('readability_note')))
            
            elif key == 'checks.image_check':
                missing_alt = data.get('missing_alt_images_count', 0)
                status = '❌ FAIL' if missing_alt > 0 else '✅ PASS'
                details = f"**{missing_alt}** image(s) missing alt text. (Total images: {data.get('total_images_count', 0)})"
                content.append(_format_check_box(check_name, status, details, 'missing_alt_images'))

            elif key == 'checks.link_check':
                broken_count = data.get('broken_link_count', 0)
                status = '❌ FAIL' if broken_count > 0 else '✅ PASS'
                details = f"Found **{broken_count}** broken link(s). Sample: `{data.get('sample_broken_link', 'N/A')}`"
                content.append(_format_check_box(check_name, status, details, 'broken_link_count'))

            elif key == 'checks.internal_links':
                internal_links = data.get('internal_links_count', 0)
                status = '✅ PASS'
                if internal_links == 0: status = '⚠️ WARN' # Pages should have internal links
                details = f"Page links to **{internal_links}** internal pages and {data.get('external_links_count', 0)} external pages."
                content.append(_format_check_box(check_name, status, details, 'missing_internal_links'))

            elif key == 'checks.schema_check':
                schema_found = data.get('schema_found')
                status = '✅ PASS' if schema_found else '⚠️ INFO'
                details = f"Schema Markup Found: {schema_found}. Types detected: {', '.join(data.get('schema_types', ['None']))}"
                content.append(_format_check_box(check_name, status, details)) # No specific solution, informational check

            elif key == 'checks.mobile_friendly_check':
                is_mobile = data.get('is_mobile_friendly')
                status = '❌ FAIL' if not is_mobile else '✅ PASS'
                details = f"Mobile-Friendly Status: {'Friendly' if is_mobile else 'NOT FRIENDLY'}. Viewport Tag: {data.get('viewport_found', False)}"
                content.append(_format_check_box(check_name, status, details, 'not_mobile_friendly'))

            elif key == 'checks.accessibility_check':
                if data.get('accessibility_fail'):
                    status = '❌ FAIL'
                else:
                    status = '✅ PASS'
                details = f"Basic A11y Issues: **{data.get('a11y_issue_count', 0)}** detected. (e.g., contrast, tab order, etc.)"
                content.append(_format_check_box(check_name, status, details, 'accessibility_fail'))

            elif key == 'checks.performance_check':
                desktop = data.get('desktop_score', {})
                mobile = data.get('mobile_score', {})
                status = '✅ PASS'
                if desktop.get('result') != 'Pass' or mobile.get('result') != 'Pass':
                    status = '❌ FAIL'
                details = f"Server Response (TTFB) - Mobile: {mobile.get('message', 'N/A')}. Desktop: {desktop.get('message', 'N/A')}"
                content.append(_format_check_box(check_name, status, details, 'server_response_slow'))


            
            elif key == 'checks.core_web_vitals_check':
                cwv_status = data.get('performance_status', 'INFO')
                status = cwv_status
                
                # --- FIX START: Handle float formatting ---
                latency = data.get('download_latency', 'N/A')
                
                # Check if 'latency' is a number and format it to 3 decimal places.
                if isinstance(latency, (float, int)):
                    # Use f-string formatting to control decimal precision (e.g., 0.930)
                    latency_str = f"{latency:.3f}"
                else:
                    # If it's the fallback 'N/A', keep it as a string
                    latency_str = latency
                
                details = f"Download Latency (Proxy for LCP/TTFB): **{latency_str}s**. Review full note."
                # --- FIX END ---
                
                content.append(_format_check_box(check_name, status, details, 'cwv_warn', data.get('note')))


            
            elif key == 'checks.analytics_check':
                status = '❌ MISSING' if data.get('analytics_missing') else '✅ PASS'
                details = f"GA/GTM Found: **{status}**. Note: {data.get('note', 'N/A')}"
                content.append(_format_check_box(check_name, status, details, 'analytics_missing'))

            elif key == 'checks.og_tags_check':
                status = '❌ FAIL' if data.get('og_tags_missing') else '✅ PASS'
                details = f"Missing Tags: **{len(data.get('missing_tags_list', []))}** ({', '.join(data.get('missing_tags_list', ['None']))})"
                content.append(_format_check_box(check_name, status, details, 'og_tags_missing'))
            
            elif key == 'checks.local_seo_check':
                status = '❌ FAIL' if data.get('nap_fail') else '✅ PASS'
                details = f"NAP Consistency Check: **{data.get('consistency_status', 'N/A')}**. Review manual audit for external citations."
                content.append(_format_check_box(check_name, status, details, 'nap_mismatch'))

            elif key == 'checks.keyword_analysis':
                density = data.get('primary_keyword_density', 0)
                status = '✅ PASS'
                if density > 5: status = '⚠️ WARN' # Assuming >5% is keyword stuffing
                details = f"Primary Keyword: `{data.get('primary_keyword', 'N/A')}`. Density: **{density:.2f}%**. (Target: 1-3%)"
                content.append(_format_check_box(check_name, status, details)) # Informational check

            elif key == 'checks.backlinks_check':
                status = '⚠️ INFO'
                details = f"Top Referring Domains: **{data.get('referring_domains_count', 0)}** detected. Sample: {', '.join(data.get('sample_domains', ['N/A']))}"
                content.append(_format_check_box(check_name, status, details, note=data.get('note'))) # Informational check
            
        content.append("\n\n---\n") # Final separator for the page audit


    # -----------------------------------------------------
    # 4. Appendix/Disclaimer
    # -----------------------------------------------------
    content.append("## 4. Disclaimer & Technology Used\n\n")
    content.append("This is a static, on-page analysis. True Core Web Vitals, link quality, and ranking difficulty require integration with third-party APIs (e.g., Google PageSpeed Insights, Ahrefs, SEMrush).\n")


    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    print(f"Professional Markdown Report written to {md_path}")

    
         
