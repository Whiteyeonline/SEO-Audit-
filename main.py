# main.py

import os
import json
import logging
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from crawler.spider import SEOSpider
# get_check_aggregation is still imported but the critical scoring logic will be more robust
from utils.report_writer import write_summary_report, get_check_aggregation 
# ... (all check imports remain the same) ...
from checks import (
    ssl_check, robots_sitemap, performance_check, keyword_analysis,
    local_seo_check, meta_check, heading_check, image_check, link_check,
    schema_check, url_structure, internal_links, canonical_check,
    content_quality, accessibility_check, mobile_friendly_check,
    backlinks_check, analytics_check,
    # === NEW CHECKS ADDED ===
    og_tags_check, 
    redirect_check, 
    core_web_vitals_check 
)

ALL_CHECKS_MODULES = [
    ssl_check, robots_sitemap, performance_check, keyword_analysis,
    local_seo_check, meta_check, heading_check, image_check, link_check,
    schema_check, url_structure, internal_links, canonical_check,
    content_quality, accessibility_check, mobile_friendly_check,
    backlinks_check, analytics_check,
    # === NEW CHECKS ADDED ===
    og_tags_check, 
    redirect_check, 
    core_web_vitals_check
]

# === FINALIZED STABILITY SETTINGS FOR SCRAPY-PLAYWRIGHT ===
# ... (CUSTOM_SETTINGS remain the same, they are correct) ...
CUSTOM_SETTINGS = {
    'USER_AGENT': 'ProfessionalSEOAgency (+https://github.com/your-repo)',
    'ROBOTSTXT_OBEY': False,
    'LOG_LEVEL': 'INFO',
    'CLOSESPIDER_PAGECOUNT': 250,
    'TELNET_ENABLED': False,
    
    # Required for Scrapy-Playwright
    'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
    # Enables Playwright for handling JavaScript/Dynamic Content
    'DOWNLOAD_HANDLERS': {
        'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
    },
    'PLAYWRIGHT_LAUNCH_OPTIONS': {
        'headless': True,
        'timeout': 60000, # Browser launch timeout (60s)
        'args': [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox', 
        ],
    },
    'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
    'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 90000, 
    'DOWNLOAD_TIMEOUT': 90, 
    'RETRY_TIMES': 0, 
    'PLAYWRIGHT_CONTEXT_ARGS': {
        'viewport': {'width': 1280, 'height': 720},
        'wait_until': 'load', 
        'bypass_csp': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    },
    
    # Feed Export Settings for the crawl results
    'FEED_FORMAT': 'json',
    'FEED_URI': 'reports/crawl_results.json',
    'FEED_EXPORT_ENCODING': 'utf-8',
    'CONCURRENT_REQUESTS': 2,
    'DOWNLOAD_DELAY': 3.0,
    
    'LOG_ENABLED': False, 
}

# --- Report Loading and Generation Logic (Synchronous) ---

def load_and_generate_reports(settings, AUDIT_URL, AUDIT_LEVEL, COMPETITOR_URL, AUDIT_SCOPE):
    """
    Loads crawl results and generates the final reports.
    """
    crawl_results = []
    crawl_file_path = settings.get('FEED_URI')
    error_message = None

    if os.path.exists(crawl_file_path) and os.path.getsize(crawl_file_path) > 0:
        try:
            with open(crawl_file_path, 'r', encoding='utf-8') as f:
                crawl_results = json.load(f)
            
            if not crawl_results:
                 error_message = "CRAWL FAILED: Crawl finished, but the results file was an empty JSON list '[]'."
        
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding crawl results JSON: {e}")
            error_message = "FATAL ERROR: Failed to decode crawl results JSON. File format error."
        
    else:
        error_message = "CRAWL FAILED: The spider did not write a crawl results file. Check logs."
    
    if error_message:
        print(f"WARNING: {error_message}")


    # 3. Prepare Data Structure
    initial_checks = next((item['checks'] for item in crawl_results if item.get('url') == 'INITIAL_CHECKS'), {})
    crawled_pages = [item for item in crawl_results if item.get('url') != 'INITIAL_CHECKS']
    total_pages_crawled = len(crawled_pages)

    if total_pages_crawled == 0:
        # If crawl failed completely (Pages Crawled: 0), default to a neutral score
        aggregation = {'total_pages_crawled': 0}
        final_score = 100 
    else:
        # Use report_writer for full aggregation, but calculate score robustly
        aggregation = get_check_aggregation(crawled_pages) 
        
        # ✅ FIX: Robust scoring logic by re-iterating and counting CRITICAL failures
        critical_issues_count = 0
        
        for page in crawled_pages:
            checks = page.get('checks', {})
            
            # --- CRITICAL FAILURE CHECKS (Using correct keys now) ---
            
            # 1. Meta Tags (Title/Description)
            meta = checks.get('meta_check', {})
            if meta.get('title_fail'): 
                critical_issues_count += 1
            if meta.get('desc_fail'): 
                critical_issues_count += 1
                
            # 2. Heading Structure (Missing or multiple H1)
            heading = checks.get('heading_check', {})
            if heading.get('h1_fail'): 
                critical_issues_count += 1
            
            # 3. Broken Links (If the page has ANY broken links, count as one critical issue for that page)
            links = checks.get('link_check', {})
            if links.get('broken_link_count', 0) > 0:
                critical_issues_count += 1 
                
            # 4. Mobile Friendliness
            mobile = checks.get('mobile_friendly_check', {})
            # Check if 'mobile_friendly' key exists and is False
            if mobile.get('mobile_friendly') is False:
                critical_issues_count += 1
        
        # Apply Scoring: 5 points penalty per critical issue, capped at 50 points
        penalty = min(critical_issues_count * 5, 50) 
        final_score = max(100 - penalty, 50) # Score cannot drop below 50


    structured_report_data = {
        'audit_details': {
            'target_url': AUDIT_URL,
            'audit_level': AUDIT_LEVEL,
            'competitor_url': COMPETITOR_URL,
            'audit_scope': AUDIT_SCOPE,
        },
        'final_score': final_score,
        'crawled_pages': crawled_pages,
        'total_pages_crawled': total_pages_crawled,
        'aggregated_issues': aggregation,
        'basic_checks': initial_checks,
        'crawl_error': error_message
    }

    # 4. Write both final report files
    structured_file_path = "reports/seo_audit_structured_report.json"
    with open(structured_file_path, 'w', encoding='utf-8') as f:
        json.dump(structured_report_data, f, indent=4)
    print(f"\nStructured report saved to: {structured_file_path}")

    markdown_file_path = "reports/seo_professional_report.md"
    write_summary_report(structured_report_data, final_score, markdown_file_path) 

    print(f"\nSummary report saved to: {markdown_file_path}")
    print(f"\nPages Crawled: {total_pages_crawled}")

# --- Main Execution Flow ---
def main():
    try:
        AUDIT_URL = os.environ['AUDIT_URL']
        AUDIT_LEVEL = os.environ.get('AUDIT_LEVEL', 'standard')
        COMPETITOR_URL = os.environ.get('COMPETITOR_URL', '')
        AUDIT_SCOPE = os.environ.get('AUDIT_SCOPE', 'only_onpage')
    except KeyError:
        print("Error: AUDIT_URL environment variable is not set. Aborting.")
        sys.exit(1)

    os.makedirs('reports', exist_ok=True)

    settings = Settings(CUSTOM_SETTINGS)
    
    settings.set('AUDIT_LEVEL', AUDIT_LEVEL)
    settings.set('AUDIT_SCOPE', AUDIT_SCOPE)

    if AUDIT_SCOPE == 'only_onpage':
        settings.set('CLOSESPIDER_PAGECOUNT', 1)
    elif AUDIT_SCOPE == 'indexed_pages':
        settings.set('CLOSESPIDER_PAGECOUNT', 25)
    elif AUDIT_SCOPE == 'full_300_pages':
        settings.set('CLOSESPIDER_PAGECOUNT', 300)
    
    max_pages_count = settings.getint('CLOSESPIDER_PAGECOUNT')

    process = CrawlerProcess(settings)
    process.crawl(SEOSpider, start_url=AUDIT_URL, max_pages_config=max_pages_count, all_checks=ALL_CHECKS_MODULES)

    print(f"\nStarting SEO Audit for {AUDIT_URL}...")
    print(f"Level: {AUDIT_LEVEL.capitalize()} | Scope: {AUDIT_SCOPE.replace('_', ' ')} (Max pages: {max_pages_count})\n")

    process.start() 
    
    load_and_generate_reports(settings, AUDIT_URL, AUDIT_LEVEL, COMPETITOR_URL, AUDIT_SCOPE)

if __name__ == "__main__":
    main()
