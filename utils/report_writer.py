# utils/report_writer.py
import json
import datetime
from textblob import TextBlob
from nltk.tokenize import sent_tokenize
import re
import textstat

# NOTE: The existing _calculate_readability function relies on the external 
# [span_0](start_span)textstat library which is included in your requirements.txt[span_0](end_span).

def _get_issue_description_map():
    """Maps check keys to human-readable names, priorities, and solutions."""
    return {
        'title_fail_count': {
            'name': 'Missing or Poorly Formatted Title Tag',
            'priority': 'High',
            [span_1](start_span)'description': 'Pages missing a Title Tag or having one that is too long/short (Optimal: 30-60 characters)[span_1](end_span).',
            [span_2](start_span)'solution': 'Add unique, compelling title tags (30-60 characters) that include the target keyword at the front[span_2](end_span).'
        },
        'desc_fail_count': {
            'name': 'Missing Meta Description',
            'priority': 'High',
            [span_3](start_span)'description': 'Pages missing a Meta Description (Essential for click-through rate in SERPs)[span_3](end_span).',
            [span_4](start_span)'solution': 'Add unique, compelling meta descriptions (120-158 characters) that encourage users to click[span_4](end_span).'
        },
        'h1_fail_count': {
            'name': 'Multiple or Missing H1 Tag',
            'priority': 'High',
            [span_5](start_span)'description': 'Pages having missing H1 tags or more than one H1 tag (SEO best practice is one H1 per page)[span_5](end_span).',
            [span_6](start_span)'solution': 'Ensure every page has exactly one descriptive H1 tag that outlines the primary topic[span_6](end_span).'
        },
        'thin_content_count': {
            'name': 'Thin Content Warning',
            'priority': 'Medium',
            [span_7](start_span)'description': 'Pages with very little unique content (under 200 words)[span_7](end_span).',
            [span_8](start_span)'solution': 'Significantly increase the unique, high-quality, and useful content on these pages[span_8](end_span).'
        },
        'missing_alt_total': {
            'name': 'Images Missing Alt Text',
            'priority': 'Low',
            [span_9](start_span)'description': 'Images without proper `alt` attributes, harming accessibility and image SEO[span_9](end_span).',
            [span_10](start_span)'solution': 'Add descriptive `alt` text to all images to aid screen readers and search engines[span_10](end_span).'
        },
        'link_broken_total': {
            'name': 'Internal or External Broken Links (4XX/5XX)',
            'priority': 'High',
            [span_11](start_span)'description': 'Links pointing to pages that return an error code (4xx or 5xx)[span_11](end_span).',
            [span_12](start_span)'solution': 'Update or remove all broken links to preserve link equity and user experience[span_12](end_span).'
        },
        'canonical_mismatch_count': {
            'name': 'Canonical Tag Issues',
            'priority': 'Medium',
            [span_13](start_span)'description': 'Canonical tags pointing to an incorrect URL or missing entirely on pages that require one (e.g., product filters)[span_13](end_span).',
            [span_14](start_span)'solution': 'Review canonical tag implementation to ensure it points to the preferred version of the page, preventing duplicate content issues[span_14](end_span).'
        },
        'mobile_unfriendly_count': {
            'name': 'Mobile Unfriendly Pages',
            'priority': 'High',
            [span_15](start_span)'description': 'Pages identified as not being fully responsive or mobile-friendly (critical for Google’s Mobile-First Indexing)[span_15](end_span).',
            [span_16](start_span)'solution': 'Use responsive design principles (CSS media queries) to ensure the layout adapts perfectly to all screen sizes[span_16](end_span).'
        },
        'analytics_missing_count': {
            'name': 'Missing Analytics/Tracking Code',
            'priority': 'Medium',
            [span_17](start_span)'description': 'Pages where a Google Analytics or other specified tracking code could not be detected[span_17](end_span).',
            [span_18](start_span)'solution': 'Ensure the appropriate tracking snippet is placed correctly in the `<head>` section of all pages[span_18](end_span).'
        },
        # === NEW CHECKS ADDED HERE ===
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
        # =============================
    }

def _calculate_readability(content):
    [span_19](start_span)"""Calculates Flesch-Kincaid Readability Score for a content block[span_19](end_span)."""
    if not content or content.isspace():
        return {'flesch_kincaid_score': 0, 'grade_level': 'N/A', 'error': 'No content to analyze'}
    try:
        # Clean up text for better analysis
        text = re.sub(r'[\r\n\t]+', ' ', content).strip()
        text = re.sub(r'\s+', ' ', text)
        if not text:
            return {'flesch_kincaid_score': 0, 'grade_level': 'N/A', 'error': 'Content cleaned to empty string'}
        
        # [span_20](start_span)This section requires TextBlob and NLTK, which are in your requirements.txt[span_20](end_span)
        blob = TextBlob(text)
        sentences = sent_tokenize(text)
        total_words = len(blob.words)
        total_sentences = len(sentences)

        # Approximate syllables per word using textblob's simple syllable count
        total_syllables = sum(len(w.syllables) for w in blob.words)

        if total_words == 0 or total_sentences == 0:
            return {'flesch_kincaid_score': 0, 'grade_level': 'N/A', 'error': 'Insufficient words/sentences'}
        
        # Flesch-Kincaid formula
        score = 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words)

        # Estimate U.S. Grade Level for the score
        if score >= 90:
            grade = '5th Grade'
        elif score >= 80:
            grade = '6th Grade'
        elif score >= 70:
            grade = '7th Grade'
        elif score >= 60:
            grade = '8th Grade'
        elif score >= 50:
            grade = '9th Grade - High School'
        elif score >= 30:
            grade = 'College Level'
        else:
            grade = 'Graduate/Difficult'
        return {
            'flesch_kincaid_score': round(score, 2),
            'grade_level': grade
        }
    except Exception as e:
        return {'flesch_kincaid_score': 0, 'grade_level': 'N/A', 'error': f'Readability calculation failed: {str(e)}'}

def get_check_aggregation(crawled_pages):
    """
    [span_21](start_span)Aggregates issue counts across all crawled pages[span_21](end_span).
    """
    aggregation = {
        'total_pages_crawled': len(crawled_pages),
        # Initialize all known aggregation counts to 0
        'title_fail_count': 0, 'desc_fail_count': 0, 'h1_fail_count': 0,
        'thin_content_count': 0, 'missing_alt_total': 0, 'canonical_mismatch_count': 0,
        'link_broken_total': 0, 'analytics_missing_count': 0, 'mobile_unfriendly_count': 0,
        # Ensure all other keys used in the report are initialized here:
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

        # --- Existing Check Aggregations (from source 22, 23) ---
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
    """
    audit_details = report['audit_details']
    crawled_pages = report['crawled_pages']
    aggregated_issues = report['aggregated_issues']
    basic_checks = report['basic_checks']

    performance_check = report.get('performance_check', {})

    issue_map = _get_issue_description_map()
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Calculate Score: Adjusted to include the new checks in the critical count
    critical_issues_count = (
        aggregated_issues.get('title_fail_count', 0) +
        aggregated_issues.get('desc_fail_count', 0) +
        aggregated_issues.get('h1_fail_count', 0) +
        aggregated_issues.get('link_broken_total', 0) +
        aggregated_issues.get('mobile_unfriendly_count', 0)
    )
    # A simple scoring model (from source 25)
    score = max(100 - (critical_issues_count * 5), 50)

    content = []
    
    # --- 1. Report Header (More space added) ---
    content.append("# 💎 PROFESSIONAL SEO AUDIT REPORT\n\n")
    content.append(f"**Date:** {current_time}\n")
    content.append(f"**Target URL:** {audit_details['target_url']}\n")
    content.append(f"**Audit Level:** {audit_details['audit_level'].capitalize()}\n")
    content.append(f"**Powered by:** Free, Open-Source Tools Only (No API Limits) 🚀\n\n")
    content.append("---\n\n")


    # --- 2. Executive Summary --- (Spacious tables for comfortable reading)
    content.append("## 1. Executive Summary: At a Glance\n\n")
    content.append("This section summarizes the overall health and scope of the audit.\n\n")
    
    # Calculate Status and Scope Details
    score_status = '✅ GOOD' if score > 80 else '⚠️ NEEDS WORK' if score > 60 else '❌ CRITICAL'
    scope_display = audit_details['audit_scope'].replace('_', ' ').capitalize()
    
    scope_detail = f"The scan focused on **{len(crawled_pages)}** pages."
    if audit_details['audit_scope'] == 'only_onpage':
        scope_detail = "The scan was limited to the **homepage only**."
    elif audit_details['audit_scope'] == 'indexed_pages':
        scope_detail = f"The scan covered the homepage and core index pages (limit: 25)."
    elif audit_details['audit_scope'] == 'full_300_pages':
        scope_detail = f"The scan attempted a deep crawl of the site (limit: 300 pages)."

    content.append("| Metric | Value | Detail |\n")
    content.append("| :--- | :--- | :--- |\n")
    content.append(f"| **Final SEO Score** | **{score}/100** | {score_status} |\n")
    content.append(f"| **Total Pages Crawled** | **{len(crawled_pages)}** | (Max: {report.get('total_pages_crawled', 0)}) |\n")
    content.append(f"| **Audit Scope** | **{scope_display}** | {scope_detail} |\n\n")

    content.append("---\n\n")


    # --- 3. Critical Issues & Recommendations --- (Grouped by priority and highly spacious)
    content.append("## 2. Critical Issues & Recommendations\n\n")
    content.append("The following issues represent areas with the greatest negative impact on SEO and user experience. **Fixing these first is highly recommended.**\n\n")

    issue_counter = 0
    # Group issues by priority for better focus
    issues_by_priority = {'High': [], 'Medium': [], 'Low': []}
    
    for key, count in aggregated_issues.items():
        if count > 0 and (key.endswith('_count') or key.endswith('_total')):
            issue_data = issue_map.get(key)
            if issue_data:
                issues_by_priority[issue_data['priority']].append((count, issue_data))

    
    for priority in ['High', 'Medium', 'Low']:
        if issues_by_priority[priority]:
            content.append(f"### ➡️ Priority: {priority} ({len(issues_by_priority[priority])} Issues)\n\n")
            
            for count, issue_data in issues_by_priority[priority]:
                issue_counter += 1
                content.append(f"#### {issue_counter}. {issue_data['name']} ({count} Instances)\n")
                content.append(f"- **Description:** {issue_data['description']}\n")
                content.append(f"- **Solution:** **{issue_data['solution']}**\n\n")
            
            # Use a triple dash with extra space for visual separation between priority groups
            content.append("\n---\n\n") 


    if issue_counter == 0:
        content.append("### 🎉 No Major Issues Detected!\n\n")
        content.append("* **Next Step:** Focus on advanced SEO strategies like deep content marketing and link building.\n\n")
        content.append("\n---\n\n")
    

    # --- 4. Detailed Page-by-Page Audit --- (Structured and Spacious)
    content.append(f"## 3. Detailed Page-by-Page Audit ({len(crawled_pages)} Pages)\n\n")
    content.append("This section provides granular data for each page crawled. The output is structured to allow comfortable reading for detailed analysis.\n\n")

    # Process each crawled page for its detailed report
    for idx, page in enumerate(crawled_pages):
        page_checks = page.get('checks', {})
        page_url = page.get('url', 'N/A')
        status = page.get('status_code', 'N/A')

        # Use a large visual separator for each page
        content.append(f"\n--- 📄 **PAGE AUDIT: {idx + 1}** ---\n")
        content.append(f"### 📍 URL: `{page_url}`\n")
        content.append(f"**HTTP Status Code:** `{status}`\n\n")
        
        check_details = []

        # Helper function to create a detail line
        def add_detail(category, check, status, description):
            check_details.append(f"| {category} | {check} | **{status}** | {description} |")

        # --- Extract and format check results ---

        # [span_22](start_span)META CHECK (Title/Description)[span_22](end_span)
        meta_data = page_checks.get('checks.meta_check', {})
        if 'title_fail' in meta_data:
            title_status = '✅ PASS'
            if meta_data.get('title_fail'): title_status = '❌ FAIL'
            if meta_data.get('title_check') == 'MISSING': title_status = '❌ MISSING'
            add_detail('Meta', 'Title Tag', title_status, f"Title: `{meta_data.get('title_content', 'N/A')}` (Length: {meta_data.get('title_length', 0)})")
        
        if 'desc_fail' in meta_data:
            desc_status = '✅ PASS' if meta_data.get('desc_content') else '❌ MISSING'
            add_detail('Meta', 'Meta Description', desc_status, f"Description: `{meta_data.get('desc_content', 'MISSING...')[:100]}...`")

        # [span_23](start_span)HEADING CHECK (H1)[span_23](end_span)
        heading_data = page_checks.get('checks.heading_check', {})
        if 'h1_fail' in heading_data:
            h1_status = '✅ PASS' if not heading_data.get('h1_fail') else '❌ FAIL'
            add_detail('Structure', 'H1 Count', h1_status, f"Found **{heading_data.get('h1_count', 0)}** H1 tags. Must be exactly 1.")

        # [span_24](start_span)CONTENT QUALITY (Word Count)[span_24](end_span)
        content_data = page_checks.get('checks.content_quality', {})
        if 'word_count' in content_data:
            word_status = '✅ PASS'
            if content_data.get('word_count', 0) < 200: word_status = '❌ FAIL'
            add_detail('Content', 'Word Count', word_status, f"Found **{content_data.get('word_count', 0)}** words. Thin content warning below 200.")
        
        # [span_25](start_span)CANONICAL CHECK[span_25](end_span)
        canonical_data = page_checks.get('checks.canonical_check', {})
        if 'canonical_url' in canonical_data:
            canonical_status = '✅ PASS'
            if canonical_data.get('canonical_mismatch'): canonical_status = '⚠️ CHECK'
            if canonical_data.get('canonical_url') is None: canonical_status = '⚠️ MISSING'
            match_status = 'Yes' if canonical_data.get('canonical_mismatch') is False else 'No/Missing'
            add_detail('Technical', 'Canonical Tag', canonical_status, f"Tag: `{canonical_data.get('canonical_url', 'N/A')}`. Matches Page URL: {match_status}.")

        # [span_26](start_span)LINK CHECK (Broken Links)[span_26](end_span)
        link_data = page_checks.get('checks.link_check', {})
        if 'broken_link_count' in link_data:
            link_status = '✅ PASS' if link_data.get('broken_link_count', 0) == 0 else '❌ FAIL'
            add_detail('Technical', 'Broken Links', link_status, f"Found **{link_data.get('broken_link_count', 0)}** broken link(s). Sample: {link_data.get('sample_broken_link', 'N/A')}")
        
        # [span_27](start_span)MOBILE FRIENDLY CHECK[span_27](end_span)
        mobile_data = page_checks.get('checks.mobile_friendly_check', {})
        if 'is_mobile_friendly' in mobile_data:
            mobile_status = '✅ PASS' if mobile_data.get('is_mobile_friendly') else '❌ FAIL'
            add_detail('Technical', 'Mobile Friendly', mobile_status, f"Status: {'Friendly' if mobile_data.get('is_mobile_friendly') else 'Not Friendly'}.")

        

        # ANALYTICS CHECK
        analytics_data = page_checks.get('checks.analytics_check', {})
        if 'analytics_missing' in analytics_data:
            analytics_status = '✅ PASS' if not analytics_data.get('analytics_missing') else '⚠️ MISSING'
            add_detail('Technical', 'Analytics', analytics_status, f"GA/GTM Found: {analytics_status}. Note: {analytics_data.get('note', 'N/A')}")
            
        # --- NEW CHECKS ---
        og_data = page_checks.get('checks.og_tags_check', {})
        if 'og_tags_missing' in og_data:
            og_status = '✅ PASS' if not og_data.get('og_tags_missing') else '❌ FAIL'
            add_detail('Social', 'Open Graph Tags', og_status, og_data.get('note', 'N/A'))

        redirect_data = page_checks.get('checks.redirect_check', {})
        if 'was_redirected' in redirect_data:
            redirect_status = '✅ OK' if not redirect_data.get('was_redirected') else '⚠️ INFO'
            add_detail('Technical', 'Redirect Check', redirect_status, redirect_data.get('note', 'N/A'))
        
        cwv_data = page_checks.get('checks.core_web_vitals_check', {})
        if 'performance_status' in cwv_data:
            cwv_status = cwv_data.get('performance_status')
            add_detail('Performance', 'CWV Proxy (TTFB)', cwv_status, cwv_data.get('note', 'N/A'))

        # --- Output the table ---
        if check_details:
            content.append("| Category | Check Name | Status | Details |\n")
            content.append("| :--- | :--- | :--- | :--- |\n")
            content.extend(check_details)
        else:
            content.append("* No check results available for this page.*\n")
        
        content.append("\n\n---\n") # Final separator for the page audit


    # -----------------------------------------------------
    # 5. [span_28](start_span)Appendix/Disclaimer[span_28](end_span)
    # -----------------------------------------------------
    content.append("## 4. Disclaimer & Technology Used\n\n")
    content.append("* This report was generated using a custom automated SEO audit tool built entirely with **free, open-source Python libraries** and **GitHub Actions**.\n")
    content.append("* **Crawl:** Uses **Scrapy** and **Playwright** to crawl static and dynamic (JavaScript-rendered) pages.\n")
    content.append("* **Note:** The audit is a technical review and does not replace manual expert analysis.\n")


    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    print(f"Professional Markdown Report written to {md_path}")
            
