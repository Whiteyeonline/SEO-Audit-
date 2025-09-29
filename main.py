import os
import time
import json
import pandas as pd
import requests
from urllib.parse import urlparse, urljoin
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from crawler.spider import SEOSpider
from utils.report_writer import write_summary_report, calculate_seo_score_full
from checks import (
    ssl_check, robots_sitemap, performance_check 
)

# Load Scrapy settings from local file for granular control
CUSTOM_SETTINGS = {
    # CRITICAL CRAWL SETTINGS ADJUSTED FOR FREE GITHUB ACTIONS & ANTI-THROTTLING
    'USER_AGENT': 'ProfessionalSEOAgency (+https://github.com/your-repo)',
    'ROBOTSTXT_OBEY': False,
    'CONCURRENT_REQUESTS': 2,      # CRITICAL: Reduced for server stability
    'DOWNLOAD_DELAY': 3.0,         # CRITICAL: Increased to avoid blocking
    'LOG_LEVEL': 'INFO',
    'FEED_FORMAT': 'json',
    'FEED_URI': 'reports/crawl_results.json', # Temporary output for Scrapy
    'DOWNLOAD_TIMEOUT': 15,
    'CLOSESPIDER_PAGECOUNT': 250, # Max pages to crawl for full audit
    'TELNET_ENABLED': False,
    'RETRY_ENABLED': True,         
    'RETRY_TIMES': 5,
}

# --- New Function: Competitor On-Page Analysis ---
def competitor_analysis(url):
    """Performs a basic on-page analysis of the competitor's main URL."""
    if not url:
        return {"status": "skipped", "error": "No competitor URL provided."}
        
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        
        # NOTE: We use SEOSpider's static method to run checks without a full crawl
        temp_results = SEOSpider.run_single_page_checks(url, r.text)
        
        # Extract key metrics for comparison
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
    
    # 1. Prepare Crawling Parameters based on Scope
    settings = Settings()
    settings.setmodule(__import__('scrapy.settings'))
    settings.update(CUSTOM_SETTINGS)

    start_urls = [url]
    crawl_depth = None # None means full depth until page count limit
    
    if scope == 'only_onpage':
        # Only crawl the start URL
        settings.update({'CLOSESPIDER_PAGECOUNT': 1, 'MAX_DEPTH': 0})
        crawl_depth = 0
    elif scope == 'onpage_and_index_pages':
        # Crawl the start URL and immediate linked index pages
        settings.update({'CLOSESPIDER_PAGECOUNT': 10, 'MAX_DEPTH': 1})
        crawl_depth = 1
    # 'full_site_250_pages' uses the default CLOSESPIDER_PAGECOUNT: 250

    # 2. Run Domain-Level Checks and Competitor Check
    domain_checks = {
        "url": url,
        "ssl": ssl_check.run(url),
        "robots_sitemap": robots_sitemap.run(url),
        "performance": performance_check.run(url), 
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "audit_level": level, # Pass audit level for reporting
        "competitor_data": competitor_analysis(competitor_url)
    }
    
    # 3. Configure and Run the Crawler (Scrapy)
    try:
        process = CrawlerProcess(settings)
        process.crawl(SEOSpider, 
                      start_urls=start_urls, 
                      domain_checks=domain_checks,
                      audit_level=level, # Pass to spider to filter checks
                      crawl_depth=crawl_depth # Pass depth control
                     )
        process.start()
    except Exception as e:
         return {"error": f"Scrapy Crawl Failed: {str(e)}", "url": url, "status": "Failed"}
    
    # 4. Aggregate and Generate Final Report
    crawl_data_path = settings.get('FEED_URI')
    
    if not os.path.exists(crawl_data_path) or os.stat(crawl_data_path).st_size == 0:
        return {"error": "Crawl completed but produced no data. Check URL or robot.txt rules.", "url": url, "status": "Failed"}

    try:
        with open(crawl_data_path, 'r', encoding='utf-8') as f:
            all_page_results = [json.loads(line) for line in f if line.strip()] 
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return {"error": "Crawl output corrupted.", "url": url, "status": "Failed"}
    
    if not all_page_results:
         return {"error": "Crawl produced empty data set.", "url": url, "status": "Failed"}
    
    final_report_data = calculate_seo_score_full(all_page_results, domain_checks)
    
    final_report_data["audit_duration_s"] = round(time.time() - start_time, 2)
    
    os.makedirs("reports", exist_ok=True)
    
    # << CRITICAL UPDATE: Report file names include the audit level >>
    report_json_path = f"reports/full_site_report_{level}.json"
    report_md_path = f"reports/full_site_report_{level}.md"
    
    write_summary_report(final_report_data, report_json_path, report_md_path)

    return final_report_data

if __name__ == "__main__":
    # Retrieve all inputs from environment variables
    url = os.getenv("AUDIT_URL", "https://example.com")
    level = os.getenv("AUDIT_LEVEL", "standard")
    scope = os.getenv("AUDIT_SCOPE", "full_site_250_pages")
    competitor = os.getenv("COMPETITOR_URL", "")
    
    print(f"Starting {level.upper()} SEO audit for: {url}")
    
    try:
        import scrapy
        import pandas
    except ImportError:
        print("CRITICAL ERROR: Scrapy or Pandas not installed. Check requirements.txt.")
        exit(1)
        
    # NOTE: SEOSpider is imported, so its run_single_page_checks method is available for competitor_analysis
    
    audit_results = seo_audit(url, level, scope, competitor)
    
    if audit_results.get("error"):
        print(f"🛑 CRITICAL AUDIT FAILURE: {audit_results['error']}")
    else:
        pages = audit_results.get('summary_metrics', {}).get('total_pages_crawled', 'N/A')
        duration = audit_results.get('audit_duration_s', 'N/A')
        print(f"Audit complete in {duration} seconds. Total Pages: {pages}. Reports generated in /reports (files named with _{level})")
