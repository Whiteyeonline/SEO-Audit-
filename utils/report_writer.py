import json
import datetime
from textblob import TextBlob
from nltk.tokenize import sent_tokenize
import re

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
        }
    }


def _calculate_readability(content):
    """Calculates Flesch-Kincaid Readability Score for a content block."""
    if not content or content.isspace():
        return {'flesch_kincaid_score': 0, 'grade_level': 'N/A', 'error': 'No content to analyze'}

    try:
        # Clean up text for better analysis
        text = re.sub(r'[\r\n\t]+', ' ', content).strip()
        text = re.sub(r'\s+', ' ', text)

        if not text:
            return {'flesch_kincaid_score': 0, 'grade_level': 'N/A', 'error': 'Content cleaned to empty string'}

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
    Aggregates issue counts across all crawled pages.
    """
    aggregation = {
        'total_pages_crawled': len(crawled_pages),
        # Initialize all known aggregation counts to 0
        'title_fail_count': 0, 'desc_fail_count': 0, 'h1_fail_count': 0,
        'thin_content_count': 0, 'missing_alt_total': 0, 'canonical_mismatch_count': 0,
        'link_broken_total': 0, 'analytics_missing_count': 0, 'mobile_unfriendly_count': 0,
        # Ensure all other keys used in the report are initialized here:
        'url_not_clean_count': 0, 'nap_fail_count': 0, 'accessibility_fail_count': 0, 
    }

    for page in crawled_pages:
        page_checks = page.get('checks', {})
        
        # --- Meta Checks ---
        meta_data = page_checks.get('checks.meta_check', {})
        if meta_data.get('title_fail') is True:
            aggregation['title_fail_count'] += 1
        if meta_data.get('desc_fail') is True:
            aggregation['desc_fail_count'] += 1

        # --- Heading Checks ---
        heading_data = page_checks.get('checks.heading_check', {})
        if heading_data.get('h1_fail') is True:
            aggregation['h1_fail_count'] += 1

        # --- Content Quality Checks ---
        content_data = page_checks.get('checks.content_quality', {})
        if content_data.get('thin_content') is True:
            aggregation['thin_content_count'] += 1

        # --- Image Checks ---
        image_data = page_checks.get('checks.image_check', {})
        aggregation['missing_alt_total'] += image_data.get('missing_alt_images_count', 0)

        # --- Link Checks ---
        link_data = page_checks.get('checks.link_check', {})
        aggregation['link_broken_total'] += link_data.get('broken_link_count', 0)

        # --- Canonical Checks ---
        canonical_data = page_checks.get('checks.canonical_check', {})
        if canonical_data.get('canonical_mismatch') is True:
            aggregation['canonical_mismatch_count'] += 1

        # --- Mobile Checks ---
        mobile_data = page_checks.get('checks.mobile_friendly_check', {})
        if mobile_data.get('not_mobile_friendly') is True:
            aggregation['mobile_unfriendly_count'] += 1

        # --- Analytics Checks ---
        analytics_data = page_checks.get('checks.analytics_check', {})
        if analytics_data.get('analytics_missing') is True:
            aggregation['analytics_missing_count'] += 1

    return aggregation


def write_summary_report(report, final_score, md_path):
    """
    Writes the final report data directly to a professional Markdown file.
    """
    audit_details = report['audit_details']
    crawled_pages = report['crawled_pages']
    aggregated_issues = report['aggregated_issues']
    basic_checks = report['basic_checks']
    
    # --- FIX implemented here (Line 186 in the original traceback) ---
    # Use .get() to safely access 'performance_check'. 
    # If the key is missing, it returns an empty dictionary {} instead of crashing.
    performance_check = report.get('performance_check', {})
    
    issue_map = _get_issue_description_map()
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # FIX: Use .get(key, 0) to ensure the script doesn't crash 
    # if the crawl failed and keys are missing from aggregated_issues.
    critical_issues_count = (
        aggregated_issues.get('title_fail_count', 0) + 
        aggregated_issues.get('desc_fail_count', 0) + 
        aggregated_issues.get('h1_fail_count', 0) +
        aggregated_issues.get('link_broken_total', 0)
    )
    # A simple scoring model (adjust as needed)
    score = max(100 - (critical_issues_count * 5), 50)
    
    
    content = []
    
    # -----------------------------------------------------
    # 1. Report Header
    # -----------------------------------------------------
    content.append("# 💎 PROFESSIONAL SEO AUDIT REPORT")
    content.append(f"**Date:** {current_time} | **URL:** {audit_details['target_url']}")
    content.append(f"**Audit Level:** {audit_details['audit_level'].capitalize()} | **Powered by:** Free, Open-Source Tools Only (No API Limits) 🚀")
    content.append("---")
    
    # -----------------------------------------------------
    # 2. Executive Summary
    # -----------------------------------------------------
    content.append("## 1. Executive Summary: At a Glance")
    content.append("| Metric | Value | Status |")
    content.append("| :--- | :--- | :--- |")
    content.append(f"| **Final SEO Score** | **{score}/100** | {'✅ GOOD' if score > 80 else '⚠️ NEEDS WORK' if score > 60 else '❌ CRITICAL'} |")
    content.append(f"| **Total Pages Crawled** | **{len(crawled_pages)}** | |")
    
    # CRITICAL UPDATE: Report scope logic updated for new names
    scope_display = audit_details['audit_scope'].replace('_', ' ').capitalize()
    scope_detail = f"The scan focused on {len(crawled_pages)} pages."
    if audit_details['audit_scope'] == 'only_onpage':
        scope_detail = "The scan was limited to the homepage only."
    elif audit_details['audit_scope'] == 'indexed_pages': 
        scope_detail = "The scan covered the homepage and core index pages (limit: 25)."
    elif audit_details['audit_scope'] == 'full_300_pages': 
        scope_detail = "The scan attempted a deep crawl of the site (limit: 300 pages)."
    
    content.append(f"| **Audit Scope** | **{scope_display}** | {scope_detail} |")
    content.append("---")
    
    # -----------------------------------------------------
    # 2a. Summary of Key Metrics (Aggregated Issues)
    # -----------------------------------------------------
    content.append("## 1a. Summary of Key Metrics")
    content.append("| Metric | Total Count |")
    content.append("| :--- | :--- |")
    # This key is guaranteed to exist
    content.append(f"| Total Pages Crawled | {aggregated_issues.get('total_pages_crawled', 0)} |")
    
    for key, count in aggregated_issues.items():
        if key.endswith('_count') and count > 0:
            human_name = issue_map.get(key, {}).get('name', key.replace('_', ' ').title())
            content.append(f"| {human_name} | {count} |")
        if key.endswith('_total') and count > 0:
            human_name = issue_map.get(key, {}).get('name', key.replace('_', ' ').title())
            content.append(f"| {human_name} | {count} |")
    content.append("---")

    # -----------------------------------------------------
    # 3. Critical Issues & Recommendations
    # -----------------------------------------------------
    content.append("## 3. Critical Issues & Recommendations")
    
    issue_counter = 0
    for key, count in aggregated_issues.items():
        if count > 0 and (key.endswith('_count') or key.endswith('_total')):
            issue_data = issue_map.get(key)
            if issue_data:
                issue_counter += 1
                content.append(f"### {issue_counter}. {issue_data['name']} ({count} Instances)")
                content.append(f"* **Description:** {issue_data['description']}")
                content.append(f"* **Priority:** **{issue_data['priority']}**")
                content.append(f"* **Solution:** {issue_data['solution']}")
    
    if issue_counter == 0:
        content.append("### 🎉 No Major Issues Detected!")
        content.append("* **Next Step:** Focus on advanced SEO strategies like deep content marketing and link building.")
    content.append("---")
    
    # -----------------------------------------------------
    # 4. Detailed Page-by-Page Audit
    # -----------------------------------------------------
    content.append(f"## 4. Detailed Page-by-Page Audit ({len(crawled_pages)} Pages)")
    content.append("This section provides granular data for each page crawled. Playwright is used to crawl JavaScript-rendered sites, ensuring all dynamic content is audited.")
    
    # Process each crawled page for its detailed report
    for idx, page in enumerate(crawled_pages):
        page_checks = page.get('checks', {})
        page_url = page.get('url', 'N/A')
        status = page.get('status_code', 'N/A')
        
        content.append(f"### 📄 Page {idx + 1}: `{page_url}` (Status: {status})")
        content.append("| Metric | Check Name | Status | Details |")
        content.append("| :--- | :--- | :--- | :--- |")

        # --- Extract and format check results ---
        
        # Meta Check (Example)
        meta_data = page_checks.get('checks.meta_check', {})
        if 'title_fail' in meta_data:
            title_status = '✅ OK'
            if meta_data.get('title_fail'): title_status = '❌ FAIL'
            if meta_data.get('title_check') == 'MISSING': title_status = '❌ MISSING'
            content.append(f"| **Meta** | Title Tag Length | {title_status} | **Title:** {meta_data.get('title_content', 'N/A')} (Length: {meta_data.get('title_length', 0)}) |")
            
        if 'desc_fail' in meta_data:
            desc_status = '✅ OK' if meta_data.get('desc_content') else '❌ MISSING'
            content.append(f"| **Meta** | Meta Description | {desc_status} | **Description:** {meta_data.get('desc_content', 'MISSING...')} |")
            
        # Heading Check (Example)
        heading_data = page_checks.get('checks.heading_check', {})
        if 'h1_fail' in heading_data:
            h1_status = '✅ OK' if not heading_data.get('h1_fail') else '❌ FAIL'
            content.append(f"| **Structure** | H1 Count | {h1_status} | Found **{heading_data.get('h1_count', 0)}** H1 tags. Must be exactly 1. |")

        # Content Quality Check (Example: Word Count)
        content_data = page_checks.get('checks.content_quality', {})
        if 'word_count' in content_data:
            word_status = '✅ OK'
            if content_data.get('word_count', 0) < 200: word_status = '❌ FAIL'
            content.append(f"| **Content** | Word Count | {word_status} | Found **{content_data.get('word_count', 0)}** words. Thin content warning below 200. |")
            
        # Canonical Check (Example)
        canonical_data = page_checks.get('checks.canonical_check', {})
        if 'canonical_url' in canonical_data:
            canonical_status = '✅ OK'
            if canonical_data.get('canonical_mismatch'): canonical_status = '⚠️ Check'
            if canonical_data.get('canonical_url') is None: canonical_status = '⚠️ Check'
            match_status = 'Yes' if canonical_data.get('canonical_mismatch') is False else 'No/Missing'
            content.append(f"| **Technical** | Canonical Tag | {canonical_status} | **Tag:** {canonical_data.get('canonical_url', 'N/A')}. **Matches Page URL:** {match_status}. |")

        # Link Check (Example: Broken Links)
        link_data = page_checks.get('checks.link_check', {})
        if 'broken_link_count' in link_data:
            link_status = '✅ OK' if link_data.get('broken_link_count', 0) == 0 else '❌ FAIL'
            content.append(f"| **Technical** | Broken Links | {link_status} | Found **{link_data.get('broken_link_count', 0)}** broken link(s). Sample broken: {link_data.get('sample_broken_link', 'N/A')} |")
            
        # Mobile Friendly Check (Example)
        mobile_data = page_checks.get('checks.mobile_friendly_check', {})
        if 'is_mobile_friendly' in mobile_data:
            mobile_status = '✅ OK' if mobile_data.get('is_mobile_friendly') else '❌ FAIL'
            content.append(f"| **Technical** | Mobile Friendly | {mobile_status} | **Status:** {'Friendly' if mobile_data.get('is_mobile_friendly') else 'Not Friendly'}. |")
            
        content.append("---\n") # Separator between pages

    # -----------------------------------------------------
    # 5. Appendix/Disclaimer
    # -----------------------------------------------------
    content.append("## 5. Disclaimer & Technology Used")
    content.append("* This report was generated using a custom automated SEO audit tool built entirely with **free, open-source Python libraries** and **GitHub Actions**.")
    content.append("* **Crawl:** Uses **Scrapy** and **Playwright** to crawl static and dynamic (JavaScript-rendered) pages.")
    content.append("* **Note:** The audit is a technical review and does not replace manual expert analysis.")
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    
    print(f"Professional Markdown Report written to {md_path}")
                
