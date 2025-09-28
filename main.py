import os
import time
import json
import pandas as pd
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from crawler.spider import SEOSpider
from utils.report_writer import write_summary_report, calculate_seo_score_full
from checks import (
    ssl_check, robots_sitemap # Only run these once per domain
)

# Load Scrapy settings from local file for granular control
# You would need a scrapy.cfg file in a real project, but we'll use a dict here
CUSTOM_SETTINGS = {
    'USER_AGENT': 'ProfessionalSEOAgency (+https://github.com/your-repo)',
    'ROBOTSTXT_OBEY': False, # Important for forcing an audit crawl
    'CONCURRENT_REQUESTS': 8,
    'DOWNLOAD_DELAY': 0.5, # Respectful delay
    'LOG_LEVEL': 'INFO',
    'FEED_FORMAT': 'json',
    'FEED_URI': 'reports/crawl_results.json', # Output file for all page data
    'DOWNLOAD_TIMEOUT': 15,
    'CLOSESPIDER_PAGECOUNT': 100, # FREE LIMIT: Set a hard limit on pages for GitHub's free tier
    'TELNET_ENABLED': False,
}

def seo_audit(url):
    start_time = time.time()
    
    # 1. Run Domain-Level Checks (SSL, Robots)
    domain_checks = {
        "url": url,
        "ssl": ssl_check.run(url),
        "robots_sitemap": robots_sitemap.run(url),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    }
    
    # 2. Configure and Run the Full Site Crawler (Scrapy)
    settings = Settings()
    settings.setmodule(__import__('scrapy.settings'))
    settings.update(CUSTOM_SETTINGS)

    # Scrapy requires a list of URLs to start
    start_urls = [url]
    
    # The Scrapy process collects all per-page data into reports/crawl_results.json
    try:
        process = CrawlerProcess(settings)
        process.crawl(SEOSpider, start_urls=start_urls, domain_checks=domain_checks)
        process.start() # The script blocks here until the crawling finishes
    except Exception as e:
         return {"error": f"Scrapy Crawl Failed: {str(e)}", "url": url, "status": "Failed"}
    
    # 3. Aggregate and Generate Final Report
    
    # Check if the crawl generated any data
    crawl_data_path = settings.get('FEED_URI')
    if not os.path.exists(crawl_data_path) or os.stat(crawl_data_path).st_size == 0:
        return {"error": "Crawl completed but produced no data. Check URL or robot.txt rules.", "url": url, "status": "Failed"}

    try:
        with open(crawl_data_path, 'r', encoding='utf-8') as f:
            # Scrapy output is line-delimited JSON
            all_page_results = [json.loads(line) for line in f]
    except json.JSONDecodeError:
        return {"error": "Crawl output corrupted.", "url": url, "status": "Failed"}
    
    if not all_page_results:
         return {"error": "Crawl produced empty data set.", "url": url, "status": "Failed"}
    
    # Calculate scores and write the final report
    final_report_data = calculate_seo_score_full(all_page_results, domain_checks)
    
    final_report_data["audit_duration_s"] = round(time.time() - start_time, 2)
    
    os.makedirs("reports", exist_ok=True)
    write_summary_report(final_report_data, "reports/full_site_report.json", "reports/full_site_report.md")

    return final_report_data

if __name__ == "__main__":
    url = os.getenv("AUDIT_URL", "https://example.com")
    print(f"Starting FULL SITE SEO audit for: {url}")
    
    # Ensure all Scrapy dependencies are installed before running
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
        print(f"Audit complete in {audit_results.get('audit_duration_s', 'N/A')} seconds. Total Pages: {audit_results.get('total_pages_crawled', 'N/A')}. Reports generated in /reports")
        
