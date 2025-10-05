# main.py
import os
import json
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from crawler.spider import SEOSpider
from utils.report_writer import write_summary_report, calculate_seo_score
from checks import (
    ssl_check, 
    robots_sitemap, 
    performance_check,
    keyword_analysis,  # NEW: For advanced keyword checks
    local_seo_check,   # CORRECTED: Must match local_seo_check.py file name
)

# --- NEW: Playwright Settings for JS/CSS Rendering ---
CUSTOM_SETTINGS = {
    'USER_AGENT': 'ProfessionalSEOAgency (+https://github.com/your-repo)',
    'ROBOTSTXT_OBEY': False,
    'CONCURRENT_REQUESTS': 2,
    'DOWNLOAD_DELAY': 3.0,
    'LOG_LEVEL': 'INFO',
    'FEED_FORMAT': 'json',
    'FEED_URI': 'reports/crawl_results.json',
    'DOWNLOAD_TIMEOUT': 30, # Increased for Playwright/JS rendering
    'CLOSESPIDER_PAGECOUNT': 250,
    'TELNET_ENABLED': False,
    'RETRY_ENABLED': True,         
    'RETRY_TIMES': 5,
    'REDIRECT_ENABLED': True,
    'REDIRECT_MAX_TIMES': 5,
    
    # --- PLAYWRIGHT INTEGRATION for modern sites ---
    "DOWNLOAD_HANDLERS": {
        "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    },
    "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    "PLAYWRIGHT_LAUNCH_OPTIONS": {
        "headless": True, # Runs the browser without a visible GUI
    },
    "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000, # 30 seconds
    "PLAYWRIGHT_BROWSER_TYPE": "chromium",
    # -----------------------------------------------
}

def competitor_analysis(url):
    # This remains a placeholder/skipped analysis
    return {"status": "skipped", "error": "Competitor analysis not fully implemented for JS rendering in main.py."}


def run_audit(target_url, audit_level, competitor_url, audit_scope):
    # 1. Initialize Report and Basic Checks
    report = {}
    report['audit_details'] = {
        'target_url': target_url, 
        'audit_level': audit_level, 
        'competitor_url': competitor_url,
        'audit_scope': audit_scope
    }

    report['basic_checks'] = {
        'ssl_check': ssl_check.run(target_url), # Corrected: uses .run()
        'robots_sitemap': robots_sitemap.run(target_url), # Corrected: uses .run()
    }

    # 2. Run crawl (Scrapy with Playwright)
    settings = Settings(CUSTOM_SETTINGS)
    
    # Update CLOSESPIDER_PAGECOUNT based on audit_scope
    if audit_scope == 'only_onpage':
        settings.set('CLOSESPIDER_PAGECOUNT', 1)
    elif audit_scope == 'onpage_and_index_pages':
        settings.set('CLOSESPIDER_PAGECOUNT', 25)
    elif audit_scope == 'full_site_250_pages':
        settings.set('CLOSESPIDER_PAGECOUNT', 250)

    process = CrawlerProcess(settings)
    
    # Pass audit_level and scope to the spider so it knows which checks to run
    process.crawl(SEOSpider, start_urls=[target_url], audit_level=audit_level, audit_scope=audit_scope)
    process.start() 
    
    # 3. Process crawl results and run post-crawl checks
    crawl_results_path = CUSTOM_SETTINGS['FEED_URI']
    if not os.path.exists(crawl_results_path):
        print(f"Error: Crawl results file not found at {crawl_results_path}. Exiting.")
        return

    with open(crawl_results_path, 'r', encoding='utf-8') as f:
        crawl_data = json.load(f)

    # Run performance check (free Google PageSpeed Insights API)
    report['performance_check'] = performance_check.run_pagespeed_check(target_url)

    # Run competitor analysis (Currently skipped for full JS compatibility)
    report['competitor_analysis'] = competitor_analysis(competitor_url)
    
    # Merge crawl results into the main report structure
    report['crawled_pages'] = crawl_data

    # 4. Calculate final score and write report
    report['final_score'] = calculate_seo_score(report)
    
    os.makedirs('reports', exist_ok=True)
    
    write_summary_report(
        report, 
        json_path='reports/seo_audit_report.json', 
        md_path='reports/seo_audit_report.md',
        audit_level=audit_level # Pass level for conditional reporting in MD
    )

    print("✅ SEO Audit Complete. Reports generated in the 'reports' directory.")


if __name__ == '__main__':
    # Get environment variables (e.g., from GitHub Actions)
    audit_url = os.environ.get('AUDIT_URL')
    audit_level = os.environ.get('AUDIT_LEVEL', 'basic') # basic, standard, advanced
    competitor_url = os.environ.get('COMPETITOR_URL')
    audit_scope = os.environ.get('AUDIT_SCOPE', 'full_site_250_pages') # only_onpage, onpage_and_index_pages, full_site_250_pages
    
    if not audit_url:
        print("Error: AUDIT_URL environment variable is not set.")
    else:
        run_audit(audit_url, audit_level, competitor_url, audit_scope)
