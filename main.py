# main.py (Final, Complete, and Error-Corrected Version)

import os
import json
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from crawler.spider import SEOSpider
from utils.report_writer import write_summary_report, calculate_seo_score

# --- IMPORT ALL 18 CHECK MODULES ---
# Ensures all 18 modules are available for the audit process
from checks import (
    ssl_check, robots_sitemap, performance_check, keyword_analysis, 
    local_seo_check, meta_check, heading_check, image_check, link_check,
    schema_check, url_structure, internal_links, canonical_check,
    content_quality, accessibility_check, mobile_friendly_check,
    backlinks_check, analytics_check
)
# -----------------------------------

# --- Scrapy/Playwright Settings for CI Stability ---
CUSTOM_SETTINGS = {
    'USER_AGENT': 'ProfessionalSEOAgency (+https://github.com/your-repo)',
    'ROBOTSTXT_OBEY': False,
    'CONCURRENT_REQUESTS': 2,
    'DOWNLOAD_DELAY': 3.0,
    'LOG_LEVEL': 'INFO',
    'FEED_FORMAT': 'json',
    'FEED_URI': 'reports/crawl_results.json',
    'DOWNLOAD_TIMEOUT': 30, 
    'CLOSESPIDER_PAGECOUNT': 250,
    'TELNET_ENABLED': False,
    'RETRY_ENABLED': True,         
    'RETRY_TIMES': 5,
    'REDIRECT_ENABLED': True,
    'REDIRECT_MAX_TIMES': 5,
    
    # --- CRITICAL PLAYWRIGHT INTEGRATION & STABILITY ---
    "DOWNLOAD_HANDLERS": {
        "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    },
    "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    "PLAYWRIGHT_LAUNCH_OPTIONS": {
        "headless": True, 
        "timeout": 30000 
    },
    "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60000, 
    "PLAYWRIGHT_BROWSER_TYPE": "chromium",
    "PLAYWRIGHT_RETRY_REQUESTS": True, # Retry failed Playwright requests
    "PLAYWRIGHT_RETRY_TIMES": 3, 
    "PLAYWRIGHT_MAX_PAGES_PER_PROCESS": 5, # Limit concurrent browser sessions
}

def competitor_analysis(url):
    # This remains a placeholder, as per your request not to use external, limited APIs
    return {"status": "skipped", "error": "Competitor analysis not fully implemented."}


def run_audit(target_url, audit_level, competitor_url, audit_scope):
    # 1. Initialize Report and Basic Checks
    report = {}
    report['audit_details'] = {
        'target_url': target_url, 
        'audit_level': audit_level, 
        'competitor_url': competitor_url,
        'audit_scope': audit_scope
    }

    # Run the three main.py checks
    report['basic_checks'] = {
        'ssl_check': ssl_check.run(target_url), 
        'robots_sitemap': robots_sitemap.run(target_url),
    }

    # 2. Run crawl (Scrapy with Playwright)
    settings = Settings(CUSTOM_SETTINGS)
    
    if audit_scope == 'only_onpage':
        settings.set('CLOSESPIDER_PAGECOUNT', 1)
        settings.set('DOWNLOAD_DELAY', 1.0) 
        settings.set('CONCURRENT_REQUESTS', 1) 
    elif audit_scope == 'onpage_and_index_pages':
        settings.set('CLOSESPIDER_PAGECOUNT', 25)
    elif audit_scope == 'full_site_250_pages':
        settings.set('CLOSESPIDER_PAGECOUNT', 250)

    process = CrawlerProcess(settings)
    process.crawl(SEOSpider, start_urls=[target_url], audit_level=audit_level, audit_scope=audit_scope)
    process.start() 
    
    # 3. Process crawl results and run post-crawl checks
    crawl_results_path = CUSTOM_SETTINGS['FEED_URI']
    
    # Robustly load the crawl results
    crawl_data = []
    if os.path.exists(crawl_results_path) and os.path.getsize(crawl_results_path) > 0:
        try:
            with open(crawl_results_path, 'r', encoding='utf-8') as f:
                crawl_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"CRITICAL WARNING: Could not fully decode crawl results JSON. Error: {e}")
    
    # Run internal performance check (FREE & UNLIMITED)
    # FIX: This function call is correct, matching the updated 'def run(url)' signature.
    report['performance_check'] = performance_check.run(target_url) 

    report['competitor_analysis'] = competitor_analysis(competitor_url)
    report['crawled_pages'] = crawl_data

    # 4. Calculate final score and write report
    report['final_score'] = calculate_seo_score(report)
    os.makedirs('reports', exist_ok=True)
    
    write_summary_report(
        report, 
        json_path='reports/seo_audit_report.json', 
        md_path='reports/seo_audit_report.md',
        audit_level=audit_level 
    )

    print(f"✅ SEO Audit Complete. Processed {len(crawl_data)} pages. Reports generated in the 'reports' directory.")


if __name__ == '__main__':
    audit_url = os.environ.get('AUDIT_URL')
    audit_level = os.environ.get('AUDIT_LEVEL', 'basic') 
    competitor_url = os.environ.get('COMPETITOR_URL')
    audit_scope = os.environ.get('AUDIT_SCOPE', 'full_site_250_pages') 
    
    if not audit_url:
        print("Error: AUDIT_URL environment variable is not set. Using fallback example.com.")
        audit_url = 'https://example.com' 
    
    run_audit(audit_url, audit_level, competitor_url, audit_scope)
    
