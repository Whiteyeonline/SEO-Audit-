# main.py (Final, Completed Version)
import os
import json
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from crawler.spider import SEOSpider
from utils.report_writer import write_summary_report, calculate_seo_score

# --- ALL 18 CHECK MODULES ARE IMPORTED HERE ---
from checks import (
    ssl_check, robots_sitemap, performance_check, keyword_analysis, 
    local_seo_check, meta_check, heading_check, image_check, link_check,
    schema_check, url_structure, internal_links, canonical_check,
    content_quality, accessibility_check, mobile_friendly_check,
    backlinks_check, analytics_check
)
# ---------------------------------------------

# --- Scrapy/Playwright Settings (Unchanged, stable) ---
CUSTOM_SETTINGS = {
    'USER_AGENT': 'ProfessionalSEOAgency (+https://github.com/your-repo)',
    'ROBOTSTXT_OBEY': False,
    # ... (rest of settings) ...
    "DOWNLOAD_HANDLERS": {
        "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    },
    # ... (rest of Playwright settings) ...
}

# ... (competitor_analysis placeholder) ...

def run_audit(target_url, audit_level, competitor_url, audit_scope):
    # 1. Initialize Report and Basic Checks
    # ... (runs ssl_check, robots_sitemap) ...

    # 2. Run crawl (Scrapy with Playwright)
    # ... (starts CrawlerProcess) ...
    
    # 3. Process crawl results and run post-crawl checks
    # CRITICAL: This now calls the internal, free performance check.
    report['performance_check'] = performance_check.run(target_url) 
    
    # ... (loads crawl_results.json into report['crawled_pages']) ...

    # 4. Calculate final score and write report
    report['final_score'] = calculate_seo_score(report)
    
    write_summary_report(
        report, 
        json_path='reports/seo_audit_report.json', 
        md_path='reports/seo_audit_report.md',
        audit_level=audit_level 
    )

# ... (if __name__ == '__main__': block) ...
