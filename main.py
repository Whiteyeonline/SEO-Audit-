import os
import json
import logging
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from crawler.spider import SEOSpider
# Assuming these are correct imports from utils/report_writer.py
from utils.report_writer import write_summary_report, calculate_seo_score 

# --- IMPORT ALL 18 CHECK MODULES ---
from checks import (
    ssl_check, robots_sitemap, performance_check, keyword_analysis, 
    local_seo_check, meta_check, heading_check, image_check, link_check,
    schema_check, url_structure, internal_links, canonical_check,
    content_quality, accessibility_check, mobile_friendly_check,
    backlinks_check, analytics_check
)
ALL_CHECKS_MODULES = [
    ssl_check, robots_sitemap, performance_check, keyword_analysis, 
    local_seo_check, meta_check, heading_check, image_check, link_check,
    schema_check, url_structure, internal_links, canonical_check,
    content_quality, accessibility_check, mobile_friendly_check,
    backlinks_check, analytics_check
]
# -----------------------------------

# --- Scrapy/Playwright Settings for CI Stability ---
CUSTOM_SETTINGS = {
    'USER_AGENT': 'ProfessionalSEOAgency (+https://github.com/your-repo)',
    'ROBOTSTXT_OBEY': False,
    'LOG_LEVEL': 'INFO',
    'DOWNLOAD_TIMEOUT': 60, 
    'CLOSESPIDER_PAGECOUNT': 250,
    'TELNET_ENABLED': False,

    'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
    'DOWNLOAD_HANDLERS': {
        'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
    },
    'PLAYWRIGHT_LAUNCH_OPTIONS': {
        'headless': True,
        'timeout': 60000, 
    },
    
    'FEED_FORMAT': 'json',
    'FEED_URI': 'reports/crawl_results.json',
    'FEED_EXPORT_ENCODING': 'utf-8',

    'CONCURRENT_REQUESTS': 2,
    'DOWNLOAD_DELAY': 3.0,
}
# ---------------------------------------------------

def main():
    """Main execution function to run the Scrapy crawler and generate reports."""
    
    # 1. Setup Environment and Paths
    try:
        AUDIT_URL = os.environ['AUDIT_URL']
        AUDIT_LEVEL = os.environ.get('AUDIT_LEVEL', 'basic')
        COMPETITOR_URL = os.environ.get('COMPETITOR_URL', '')
        AUDIT_SCOPE = os.environ.get('AUDIT_SCOPE', 'only_onpage')
    except KeyError:
        print("Error: AUDIT_URL environment variable is not set.")
        return

    os.makedirs('reports', exist_ok=True)
    
    # 2. Configure and Run Crawler
    settings = Settings(CUSTOM_SETTINGS)
    
    if AUDIT_SCOPE == 'only_onpage':
        settings.set('CLOSESPIDER_PAGECOUNT', 1)
        
    process = CrawlerProcess(settings)
    
    # --- IMPORTANT FIX PREPARATION for spider.py ---
    # Pass the max_pages directly as a parameter to the spider
    max_pages_count = settings.getint('CLOSESPIDER_PAGECOUNT')

    process.crawl(SEOSpider, start_url=AUDIT_URL, max_pages_config=max_pages_count)
    # -----------------------------------------------
    
    print(f"\n🚀 Starting SEO Audit for {AUDIT_URL}...")
    print(f"   Scope: {AUDIT_SCOPE} (Max pages: {max_pages_count})\n")
    process.start()

    # 3. Retrieve and Aggregate Results
    crawl_results = []
    crawl_file_path = CUSTOM_SETTINGS['FEED_URI']
    if os.path.exists(crawl_file_path) and os.path.getsize(crawl_file_path) > 0:
        try:
            with open(crawl_file_path, 'r', encoding='utf-8') as f:
                crawl_results = json.load(f) 
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding crawl results JSON: {e}")
            print("🚨 FATAL ERROR: Failed to read crawl results file. Aborting report generation.")
            return
    else:
        print("⚠️ WARNING: Crawl results file is missing or empty. This indicates the spider may have failed to crawl any pages.")

    # 4. Process and Report Results
    initial_checks = next((item['checks'] for item in crawl_results if item.get('url') == 'INITIAL_CHECKS'), {})
    crawled_pages = [item for item in crawl_results if item.get('url') != 'INITIAL_CHECKS']
    
    total_pages_crawled = len(crawled_pages)
    if total_pages_crawled == 0 and not initial_checks:
        print(f"⚠️ Crawl finished, but no pages were successfully scraped beyond initial checks.")
        
    # --- FIX: Revert to dictionary passed positionally for calculate_seo_score ---
    audit_details_data = {
        'target_url': AUDIT_URL, 
        'audit_level': AUDIT_LEVEL, 
        'competitor_url': COMPETITOR_URL,
        'audit_scope': AUDIT_SCOPE
    }
        
    final_score, structured_report_data = calculate_seo_score(
        audit_details_data, # Pass dictionary positionally (this should resolve the TypeError)
        initial_checks=initial_checks,
        crawled_pages=crawled_pages,
        total_pages_crawled=total_pages_crawled,
        all_checks_modules=ALL_CHECKS_MODULES
    )

    # Save the structured report JSON
    structured_file_path = f"reports/seo_audit_structured_report.json"
    with open(structured_file_path, 'w', encoding='utf-8') as f:
        json.dump(structured_report_data, f, indent=4)
        
    print(f"✅ Structured report saved to: {structured_file_path}")

    # Generate the professional Markdown report
    markdown_file_path = f"reports/seo_professional_report.md"
    write_summary_report(structured_report_data, final_score, markdown_file_path)
    
    print(f"✅ Summary report saved to: {markdown_file_path}")
    print(f"\nFinal SEO Score: {final_score}/100 | Pages Crawled: {total_pages_crawled}")

if __name__ == "__main__":
    main()
    
