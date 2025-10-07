import os
import json
import logging
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from crawler.spider import SEOSpider
from utils.report_writer import write_summary_report, calculate_seo_score

# Import all check modules
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

def main():
    try:
        audit_url = os.environ['AUDIT_URL']
        audit_level = os.environ.get('AUDIT_LEVEL', 'basic')
        competitor_url = os.environ.get('COMPETITOR_URL', '')
        audit_scope = os.environ.get('AUDIT_SCOPE', 'only_onpage')
    except KeyError:
        print("Error: AUDIT_URL environment variable is not set.")
        return

    os.makedirs('reports', exist_ok=True)

    settings = Settings(CUSTOM_SETTINGS)

    if audit_scope == 'only_onpage':
        settings.set('CLOSESPIDER_PAGECOUNT', 1)

    process = CrawlerProcess(settings)
    max_pages = settings.getint('CLOSESPIDER_PAGECOUNT')

    process.crawl(SEOSpider, start_url=audit_url, max_pages_config=max_pages)

    print(f"\n🚀 Starting SEO Audit for {audit_url}...")
    print(f"   Scope: {audit_scope} (Max pages: {max_pages})\n")
    process.start()

    # Read crawl results
    crawl_file = CUSTOM_SETTINGS['FEED_URI']
    if os.path.exists(crawl_file) and os.path.getsize(crawl_file) > 0:
        with open(crawl_file, 'r', encoding='utf-8') as f:
            crawl_results = json.load(f)
    else:
        print("Warning: No crawl results found. Exiting.")
        return

    # Extract initial checks and pages
    initial_checks = next((item['checks'] for item in crawl_results if item.get('url') == 'INITIAL_CHECKS'), {})
    pages = [item for item in crawl_results if item.get('url') != 'INITIAL_CHECKS']
    total_pages = len(pages)

    # Prepare report data
    report_data = {
        'target_url': audit_url,
        'audit_level': audit_level,
        'competitor_url': competitor_url,
        'audit_scope': audit_scope,
        'crawled_pages': pages,
        'total_pages_crawled': total_pages,
        'basic_checks': initial_checks,
    }

    # Calculate score and get full report
    final_score, structured_data = calculate_seo_score(report_data)

    # Save structured JSON report
    structured_path = "reports/seo_audit_structured_report.json"
    with open(structured_path, 'w', encoding='utf-8') as f:
        json.dump(structured_data, f, indent=4)
    print(f"Structured report saved to {structured_path}")

    # Generate markdown report
    markdown_path = "reports/seo_professional_report.md"
    write_summary_report(structured_data, final_score, markdown_path)
    print(f"Report saved to {markdown_path}")
    print(f"\nFinal SEO Score: {final_score}/100 | Pages Crawled: {total_pages}")

if __name__ == "__main__":
    main()
    
