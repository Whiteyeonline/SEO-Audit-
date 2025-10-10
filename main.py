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
    backlinks_check, analytics_check
)

# ALL_CHECKS_MODULES is used by the SEOSpider to run every check on every crawled page.
ALL_CHECKS_MODULES = [
    ssl_check, robots_sitemap, performance_check, keyword_analysis,
    local_seo_check, meta_check, heading_check, image_check, link_check,
    schema_check, url_structure, internal_links, canonical_check,
    content_quality, accessibility_check, mobile_friendly_check,
    backlinks_check, analytics_check
]

CUSTOM_SETTINGS = {
    'USER_AGENT': 'ProfessionalSEOAgency (+https://github.com/your-repo)',
    'ROBOTSTXT_OBEY': False,
    'LOG_LEVEL': 'INFO',
    'DOWNLOAD_TIMEOUT': 60,
    'CLOSESPIDER_PAGECOUNT': 250,
    'TELNET_ENABLED': False,
    # This reactor is required for Scrapy-Playwright to work properly
    'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
    # Enables Playwright for handling JavaScript/Dynamic Content
    'DOWNLOAD_HANDLERS': {
        'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
    },
    'PLAYWRIGHT_LAUNCH_OPTIONS': {
        'headless': True,
        'timeout': 60000,
    },
    # Feed Export Settings for the crawl results
    'FEED_FORMAT': 'json',
    'FEED_URI': 'reports/crawl_results.json', # Scrapy will attempt to write this
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

    # --- REPORT GENERATION LOGIC (FIXED TO GUARANTEE FILE CREATION) ---
    crawl_results = []
    crawl_file_path = settings.get('FEED_URI')
    error_message = None # Initialize error flag

    # 2. Attempt to load crawl results
    if os.path.exists(crawl_file_path) and os.path.getsize(crawl_file_path) > 0:
        try:
            with open(crawl_file_path, 'r', encoding='utf-8') as f:
                crawl_results = json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding crawl results JSON: {e}")
            error_message = "FATAL ERROR: Failed to decode crawl results file. Data corrupted during crawl."
    else:
        error_message = "CRAWL FAILED: The spider did not successfully write any crawl data. Check logs for network or script errors."
        print(f"WARNING: {error_message}")


    # 3. Prepare Data Structure
    initial_checks = next((item['checks'] for item in crawl_results if item.get('url') == 'INITIAL_CHECKS'), {})
    crawled_pages = [item for item in crawl_results if item.get('url') != 'INITIAL_CHECKS']
    total_pages_crawled = len(crawled_pages)
    
    # Determine aggregation based on available data
    if total_pages_crawled == 0 and not initial_checks and error_message:
        # If absolutely nothing worked, use a minimal error aggregation
        aggregation = {'total_pages_crawled': 0}
    else:
        # Otherwise, aggregate whatever partial results we have
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
        'performance_check': {}, 
        'crawl_error': error_message # Include error in report for summary writer
    }
    
    # 4. Write both final report files (GUARANTEED TO RUN)
    # This ensures the 'reports/' directory contains files for the artifact upload.
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
        
