# main.py

import os
import json
import logging
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from crawler.spider import SEOSpider
from utils.report_writer import write_summary_report, get_check_aggregation
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

# ALL_CHECKS_MODULES is used by the SEOSpider to run every check on every crawled page.
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
    },
    
    # 1. Explicitly set browser type
    'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
    # 2. Increase the navigation timeout to 90s for complex pages
    'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 90000, 
    # 3. Match global download timeout
    'DOWNLOAD_TIMEOUT': 90, 
    # 4. Disable retries to prevent state confusion
    'RETRY_TIMES': 0, 
    
    # 5. CRITICAL FIX: Change 'networkidle' to 'load' for better stability on busy sites.
    'PLAYWRIGHT_CONTEXT_ARGS': {
        'viewport': {'width': 1280, 'height': 720},
        'wait_until': 'load' # Waits until the main resource and sub-resources are loaded.
    },
    # ===================================================
    
    # Feed Export Settings for the crawl results
    'FEED_FORMAT': 'json',
    'FEED_URI': 'reports/crawl_results.json',
    'FEED_EXPORT_ENCODING': 'utf-8',
    'CONCURRENT_REQUESTS': 2,
    'DOWNLOAD_DELAY': 3.0,
    
    # Keep LOG_ENABLED: False during crawl to ensure file write is finalized
    'LOG_ENABLED': False, 
}

# --- Report Loading and Generation Logic (Synchronous) ---

def load_and_generate_reports(settings, AUDIT_URL, AUDIT_LEVEL, COMPETITOR_URL, AUDIT_SCOPE):
    """
    Loads crawl results and generates the final reports.
    This is called *after* process.start() completes.
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
        aggregation = {'total_pages_crawled': 0}
        final_score = 100 
    else:
        aggregation = get_check_aggregation(crawled_pages) 
        
        critical_issues_count = (
            aggregation.get('title_fail_count', 0) +
            aggregation.get('desc_fail_count', 0) +
            aggregation.get('h1_fail_count', 0) +
            aggregation.get('link_broken_total', 0) +
            aggregation.get('mobile_unfriendly_count', 0)
        )
        final_score = max(100 - (critical_issues_count * 5), 50)


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

    # 1. Create directory early
    os.makedirs('reports', exist_ok=True)

    settings = Settings(CUSTOM_SETTINGS)
    
    settings.set('AUDIT_LEVEL', AUDIT_LEVEL)
    settings.set('AUDIT_SCOPE', AUDIT_SCOPE)

    # Configure the page limit based on the requested audit scope
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

    # Run the crawl process *synchronously*
    process.start() 
    
    # After process.start() returns, generate reports
    load_and_generate_reports(settings, AUDIT_URL, AUDIT_LEVEL, COMPETITOR_URL, AUDIT_SCOPE)

if __name__ == "__main__":
    main()
