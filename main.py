# main.py

import os
import json
import logging
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
    # 5. CRITICAL: Force Playwright to wait until network activity is idle (fully rendered)
    'PLAYWRIGHT_CONTEXT_ARGS': {
        'viewport': {'width': 1280, 'height': 720},
        'wait_until': 'networkidle' # Waits for 500ms without new network requests
    },
    # ===================================================
    
    # Feed Export Settings for the crawl results
    'FEED_FORMAT': 'json',
    'FEED_URI': 'reports/crawl_results.json',
    'FEED_EXPORT_ENCODING': 'utf-8',
    'CONCURRENT_REQUESTS': 2,
    'DOWNLOAD_DELAY': 3.0,
}

def main():
    try:
        AUDIT_URL = os.environ['AUDIT_URL']
        AUDIT_LEVEL = os.environ.get('AUDIT_LEVEL', 'standard')
        COMPETITOR_URL = os.environ.get('COMPETITOR_URL', '')
        AUDIT_SCOPE = os.environ.get('AUDIT_SCOPE', 'only_onpage')
    except KeyError:
        print("Error: AUDIT_URL environment variable is not set. Aborting.")
        return

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

    process.start()

    # --- REPORT GENERATION LOGIC ---
    crawl_results = []
    crawl_file_path = settings.get('FEED_URI')
    error_message = None

    # 2. Attempt to load crawl results
    if os.path.exists(crawl_file_path) and os.path.getsize(crawl_file_path) > 0:
        try:
            with open(crawl_file_path, 'r', encoding='utf-8') as f:
                crawl_results = json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding crawl results JSON: {e}")
            error_message = "FATAL ERROR: Failed to decode crawl results JSON. Data corrupted during crawl."
    else:
        # This is where your 'Total Pages Crawled: 0' error originates
        error_message = "CRAWL FAILED: The spider did not successfully write any crawl data. Check logs for network or script errors."
        print(f"WARNING: {error_message}")

    # 3. Prepare Data Structure
    initial_checks = next((item['checks'] for item in crawl_results if item.get('url') == 'INITIAL_CHECKS'), {})
    crawled_pages = [item for item in crawl_results if item.get('url') != 'INITIAL_CHECKS']
    total_pages_crawled = len(crawled_pages)

    if total_pages_crawled == 0 and not initial_checks and error_message:
        aggregation = {'total_pages_crawled': 0}
    else:
        aggregation = get_check_aggregation(crawled_pages) 
        
    structured_report_data = {
        'audit_details': {
            'target_url': AUDIT_URL,
            'audit_level': AUDIT_LEVEL,
            'competitor_url': COMPETITOR_URL,
            'audit_scope': AUDIT_SCOPE,
        },
        'final_score': None,
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
    write_summary_report(structured_report_data, None, markdown_file_path) 

    print(f"\nSummary report saved to: {markdown_file_path}")
    print(f"\nPages Crawled: {total_pages_crawled}")

if __name__ == "__main__":
    main()
