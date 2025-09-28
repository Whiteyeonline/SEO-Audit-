import os
import time
import json
import pandas as pd
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
    'CONCURRENT_REQUESTS': 2,      # ⬅️ CRITICAL: Reduced from 8 to 2 for server stability
    'DOWNLOAD_DELAY': 3.0,         # ⬅️ CRITICAL: Increased from 0.5s to 3.0s to avoid blocking
    'LOG_LEVEL': 'INFO',
    'FEED_FORMAT': 'json',
    'FEED_URI': 'reports/crawl_results.json',
    'DOWNLOAD_TIMEOUT': 15,
    'CLOSESPIDER_PAGECOUNT': 500, # Max pages to crawl
    'TELNET_ENABLED': False,
    'RETRY_ENABLED': True,         # Added: Better error handling
    'RETRY_TIMES': 5,
}

def seo_audit(url):
    start_time = time.time()
    
    # 1. Run Domain-Level Checks (SSL, Robots, and Performance)
    domain_checks = {
        "url": url,
        "ssl": ssl_check.run(url),
        "robots_sitemap": robots_sitemap.run(url),
        "performance": performance_check.run(url), # Performance Check Run Here (once)
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    }
    
    # 2. Configure and Run the Full Site Crawler (Scrapy)
    settings = Settings()
    settings.setmodule(__import__('scrapy.settings'))
    settings.update(CUSTOM_SETTINGS)

    start_urls = [url]
    
    try:
        process = CrawlerProcess(settings)
        process.crawl(SEOSpider, start_urls=start_urls, domain_checks=domain_checks)
        process.start()
    except Exception as e:
         return {"error": f"Scrapy Crawl Failed: {str(e)}", "url": url, "status": "Failed"}
    
    # 3. Aggregate and Generate Final Report
    
    crawl_data_path = settings.get('FEED_URI')
    if not os.path.exists(crawl_data_path) or os.stat(crawl_data_path).st_size == 0:
        return {"error": "Crawl completed but produced no data. Check URL or robot.txt rules.", "url": url, "status": "Failed"}

    try:
        with open(crawl_data_path, 'r', encoding='utf-8') as f:
            all_page_results = [json.loads(line) for line in f]
    except json.JSONDecodeError:
        return {"error": "Crawl output corrupted.", "url": url, "status": "Failed"}
    
    if not all_page_results:
         return {"error": "Crawl produced empty data set.", "url": url, "status": "Failed"}
    
    final_report_data = calculate_seo_score_full(all_page_results, domain_checks)
    
    final_report_data["audit_duration_s"] = round(time.time() - start_time, 2)
    
    os.makedirs("reports", exist_ok=True)
    write_summary_report(final_report_data, "reports/full_site_report.json", "reports/full_site_report.md")

    return final_report_data

if __name__ == "__main__":
    url = os.getenv("AUDIT_URL", "https://example.com")
    print(f"Starting FULL SITE SEO audit for: {url}")
    
    try:
        import scrapy
        import pandas
    except ImportError:
        print("CRITICAL ERROR: Scrapy or Pandas not installed. Check requirements.txt.")
        exit(1)
        
    audit_results = seo_audit(url)
    
    if audit_results.get("error"):
        print(f"🛑 CRITICAL AUDIT FAILURE: {audit_results['error']}")
    else:
        print(f"Audit complete in {audit_results.get('audit_duration_s', 'N/A')} seconds. Total Pages: {audit_results.get('summary_metrics', {}).get('total_pages_crawled', 'N/A')}. Reports generated in /reports")
        
