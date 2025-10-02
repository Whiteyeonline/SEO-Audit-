import os
import time
import json
import pandas as pd
import requests
from urllib.parse import urlparse, urljoin
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from crawler.spider import SEOSpider
from utils.report_writer import write_summary_report, calculate_seo_score
from checks import (
    ssl_check, robots_sitemap, performance_check 
)

# Load Scrapy settings from local file for granular control
CUSTOM_SETTINGS = {
    'USER_AGENT': 'ProfessionalSEOAgency (+https://github.com/your-repo)',
    'ROBOTSTXT_OBEY': False,
    'CONCURRENT_REQUESTS': 2,
    'DOWNLOAD_DELAY': 3.0,
    'LOG_LEVEL': 'INFO',
    'FEED_FORMAT': 'json',
    'FEED_URI': 'reports/crawl_results.json',
    'DOWNLOAD_TIMEOUT': 15,
    'CLOSESPIDER_PAGECOUNT': 250,
    'TELNET_ENABLED': False,
    'RETRY_ENABLED': True,         
    'RETRY_TIMES': 5,
    'REDIRECT_ENABLED': True,
    'REDIRECT_MAX_TIMES': 5,
}

# --- New Function: Competitor On-Page Analysis ---
def competitor_analysis(url):
    """Performs a basic on-page analysis of the competitor's main URL."""
    if not url:
        return {"status": "skipped", "error": "No competitor URL provided."}
        
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        
        # Note: SEOSpider.run_single_page_checks must be accessible
        temp_results = SEOSpider.run_single_page_checks(url, r.text)
        
        return {
            "status": "success",
            "url": url,
            "title_length": len(temp_results.get("meta", {}).get("title", "")),
            "h1_count": temp_results.get("headings", {}).get("h1", 0),
            "word_count": temp_results.get("content", {}).get("word_count", 0),
            "ssl_valid": ssl_check.run(url).get("valid_ssl", False)
        }
    except Exception as e:
        return {"status": "failed", "error": f"Competitor check failed: {str(e)}"}
# --- End Competitor Analysis ---

def seo_audit(url, level, scope, competitor_url):
    start_time = time.time()
    
    print(f"Audit Scope: {scope}. Pages limit: {CUSTOM_SETTINGS.get('CLOSESPIDER_PAGECOUNT')}")
    
    settings = Settings()
    settings.setmodule(__import__('scrapy.settings'))
    settings.update(CUSTOM_SETTINGS)

    start_urls = [url]
    crawl_depth = None
    
    if scope == 'only_onpage':
        settings.update({'CLOSESPIDER_PAGECOUNT': 1, 'MAX_DEPTH': 0})
        crawl_depth = 0
    elif scope == 'onpage_and_index_pages':
        settings.update({'CLOSESPIDER_PAGECOUNT': 10, 'MAX_DEPTH': 1})
        crawl_depth = 1

    domain_checks = {
        "url": url,
        "ssl": ssl_check.run(url),
        "robots_sitemap": robots_sitemap.run(url),
        "performance": performance_check.run(url), 
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "audit_level": level,
        "competitor_data": competitor_analysis(competitor_url)
    }
    
    try:
        process = CrawlerProcess(settings)
        process.crawl(SEOSpider, 
                      start_urls=start_urls, 
                      domain_checks=domain_checks,
                      audit_level=level,
                      crawl_depth=crawl_depth
                     )
        process.start()
    except Exception as e:
         return {"error": f"Scrapy Crawl Failed: {str(e)}", "url": url, "status": "Failed"}
    
    crawl_data_path = settings.get('FEED_URI')
    all_page_results = []
    
    if os.path.exists(crawl_data_path) and os.stat(crawl_data_path).st_size > 0:
        try:
            # FIX: Correctly read a single JSON array from the file
            with open(crawl_data_path, 'r', encoding='utf-8') as f:
                all_page_results = json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            return {"error": "Crawl output corrupted.", "url": url, "status": "Failed"}
    else:
        print("⚠️ WARNING: Crawl produced an empty or non-existent file.")
    
     final_report_data = calculate_seo_score(all_page_results, domain_checks)
     final_report_data["audit_duration_s"] = round(time.time() - start_time, 2)
    os.makedirs("reports", exist_ok=True)
    
    report_json_path = f"reports/full_site_report_{level}.json"
    report_md_path = f"reports/full_site_report_{level}.md"
    
    write_summary_report(final_report_data, report_json_path, report_md_path)

    return final_report_data

if __name__ == "__main__":
    url = os.getenv("AUDIT_URL", "https://example.com")
    level = os.getenv("AUDIT_LEVEL", "standard")
    scope = os.getenv("AUDIT_SCOPE", "full_site_250_pages")
    competitor = os.getenv("COMPETITOR_URL", "")
    
    print(f"Starting {level.upper()} SEO audit for: {url}")
        
    audit_results = seo_audit(url, level, scope, competitor)
    
    if audit_results.get("error"):
        print(f"🛑 CRITICAL AUDIT FAILURE: {audit_results['error']}")
    else:
        pages = audit_results.get('summary_metrics', {}).get('total_pages_crawled', 'N/A')
        duration = audit_results.get('audit_duration_s', 'N/A')
        print(f"Audit complete in {duration} seconds. Total Pages: {pages}. Reports generated in /reports (files named with _{level})")
