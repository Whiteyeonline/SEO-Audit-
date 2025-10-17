# main.py

import os
import json
import logging
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from scrapy.utils.reactor import install_reactor # <<< NEW IMPORT

# >>>>>>> CRITICAL FIX: FORCE ASYNCIO REACTOR START <<<<<<<<
# This line ensures Scrapy uses the twisted.internet.asyncioreactor.AsyncioSelectorReactor
# required by Scrapy-Playwright, resolving the "installed reactor does not match" error.
install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor') 
# >>>>>>> CRITICAL FIX: FORCE ASYNCIO REACTOR END <<<<<<<<

# Relative imports from your project structure
from crawler.spider import SEOSpider
# Assuming report_writer.py is available in utils directory
from utils.report_writer import write_summary_report, get_check_aggregation 

# --- Import all Check Modules ---
from checks import (
    ssl_check, robots_sitemap, performance_check, keyword_analysis,
    local_seo_check, meta_check, heading_check, image_check, link_check,
    schema_check, url_structure, internal_links, canonical_check,
    content_quality, accessibility_check, mobile_friendly_check,
    backlinks_check, analytics_check,
    og_tags_check, 
    redirect_check, 
    core_web_vitals_check 
)

ALL_CHECKS_MODULES = [
    ssl_check, robots_sitemap, performance_check, keyword_analysis,
    local_seo_check, meta_check, heading_check, image_check, link_check,
    schema_check, url_structure, internal_links, canonical_check,
    content_quality, accessibility_check, mobile_friendly_check,
    backlinks_check, analytics_check,
    og_tags_check, 
    redirect_check, 
    core_web_vitals_check
]

# --- EXPERT WEIGHTED PENALTY SYSTEM ---
# This dictionary defines what constitutes a "Critical" issue and its score impact.
# Format: { 'aggregation_key_from_report_writer': penalty_weight_per_instance }
CRITICAL_ISSUE_WEIGHTS = {
    'title_fail_count': 10,        # Missing or bad Title is a major SEO failure
    'desc_fail_count': 5,          # Missing meta description
    'h1_fail_count': 10,           # Missing or multiple H1
    'link_broken_total': 2,        # Moderate penalty per broken link
    'mobile_unfriendly_count': 15, # Very high penalty for being unusable on mobile
    'robots_sitemap_fail_count': 5, # Missing sitemap/robots
    'canonical_mismatch_count': 5, # Canonical issues
    'ssl_check_fail_count': 20,    # Critical: Missing/expired SSL
}
MAX_TOTAL_PENALTY = 70 # Ensures a minimum score of 30/100

# --- FINALIZED STABILITY SETTINGS FOR SCRAPY-PLAYWRIGHT ---
CUSTOM_SETTINGS = {
    'USER_AGENT': 'ProfessionalSEOAgency (+https://github.com/your-repo)',
    'ROBOTSTXT_OBEY': False,
    'LOG_LEVEL': 'INFO',
    'CLOSESPIDER_PAGECOUNT': 250,
    # Added for stability and consistency across runs
    'REQUEST_FINGERPRINTER_IMPLEMENTATION': '2.7', 
    'TELNET_ENABLED': False,
    'DOWNLOAD_TIMEOUT': 90, 
    'RETRY_TIMES': 0,
    'DEPTH_LIMIT': 3, # Prevent deep infinite loops by default
    
    # Keeping this setting for redundancy, although install_reactor is the primary fix
    'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor', 
    
    # Required for Scrapy-Playwright 
    'DOWNLOAD_HANDLERS': {
        'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
    },
    'PLAYWRIGHT_LAUNCH_OPTIONS': {
        'headless': True,
        'timeout': 60000, 
        'args': [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox', 
        ],
    },
    'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
    'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 90000, 
    'PLAYWRIGHT_CONTEXT_ARGS': {
        'viewport': {'width': 1280, 'height': 720},
        'wait_until': 'domcontentloaded', # More efficient than 'load' for checks
        'bypass_csp': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    },
    
    # Feed Export Settings for the crawl results
    'FEED_FORMAT': 'json',
    'FEED_URI': 'reports/crawl_results.json',
    'FEED_EXPORT_ENCODING': 'utf-8',
    'CONCURRENT_REQUESTS': 2,
    'DOWNLOAD_DELAY': 3.0,
    'LOG_ENABLED': False,
}

# --- Report Loading and Generation Logic (Synchronous) ---
def load_and_generate_reports(settings, AUDIT_URL, AUDIT_LEVEL, COMPETITOR_URL, AUDIT_SCOPE):
    """
    Loads crawl results, calculates the final score, and generates the reports.
    """
    crawl_results = []
    crawl_file_path = settings.get('FEED_URI')
    error_message = None
    
    if os.path.exists(crawl_file_path) and os.path.getsize(crawl_file_path) > 0:
        try:
            with open(crawl_file_path, 'r', encoding='utf-8') as f:
                crawl_results = json.load(f)
                        
            if not crawl_results:
                error_message = "CRAWL FAILED: Crawl finished, but the results file was an empty JSON list '[]'."
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding crawl results JSON: {e}")
            error_message = "FATAL ERROR: Failed to decode crawl results JSON. File format error."
    else:
        error_message = "CRAWL FAILED: The spider did not write a crawl results file. Check logs."

    if error_message:
        print(f"WARNING: {error_message}")
        
    # 1. Separate Initial Checks from Crawled Pages
    initial_checks = next((item['checks'] for item in crawl_results if item.get('url') == 'INITIAL_CHECKS'), {})
    crawled_pages = [item for item in crawl_results if item.get('url') != 'INITIAL_CHECKS']
    total_pages_crawled = len(crawled_pages)
    
    # Default score for failed/empty crawls
    final_score = 100
    aggregation = {'total_pages_crawled': 0}
    
    if total_pages_crawled > 0:
        # 2. Get Aggregation from report_writer.py
        aggregation = get_check_aggregation(initial_checks, crawled_pages)

        # 3. Calculate Robust Score using Centralized Weighted Penalties
        total_penalty = 0
                
        for agg_key, penalty_weight in CRITICAL_ISSUE_WEIGHTS.items():
            # Get the count from the aggregated issues dict, default to 0
            issue_count = aggregation.get(agg_key, 0)
     
            # Apply penalty: total_penalty += count * weight
            total_penalty += issue_count * penalty_weight
            
        # Cap the total penalty to prevent an impossibly low score
        final_penalty = min(total_penalty, MAX_TOTAL_PENALTY)
        final_score = max(100 - final_penalty, 30) # Score cannot drop below 30
          
        # Update aggregation with the final score and page count
        aggregation['calculated_score'] = final_score
        aggregation['total_pages_crawled'] = total_pages_crawled


    # 4. Prepare Final Data Structure
    structured_report_data = {
        'audit_details': {
            'target_url': AUDIT_URL,
            'audit_level': AUDIT_LEVEL,
            'competitor_url': COMPETITOR_URL,
            'audit_scope': AUDIT_SCOPE,
        },
        'final_score': final_score, 
        'crawled_pages': crawled_pages,
        'total_pages_crawled': aggregation.get('total_pages_crawled', 0), # Use the aggregated count
        'aggregated_issues': aggregation,
        'basic_checks': initial_checks,
        'crawl_error': error_message
    }
    
    # 5. Write both final report files
    structured_file_path = "reports/seo_audit_structured_report.json"
    with open(structured_file_path, 'w', encoding='utf-8') as f:
        json.dump(structured_report_data, f, indent=4)
        
    print(f"\nStructured report saved to: {structured_file_path}")
    
    markdown_file_path = "reports/seo_professional_report.md"
    # Assuming write_summary_report now calls write_markdown_report internally or is the full markdown function
    # NOTE: Based on previous steps, write_summary_report should be renamed to write_markdown_report for accuracy,
    # but since I don't have control over the entire codebase, I will stick to the function name provided in the snippet.
    from utils.report_writer import write_markdown_report as write_summary_report # Safe assumption for full report
    write_summary_report(structured_report_data, markdown_file_path)
    
    print(f"\nProfessional Report saved to: {markdown_file_path}")
    print(f"\nPages Crawled: {structured_report_data['total_pages_crawled']} | Final Score: {final_score}/100")

# --- Main Execution Flow ---
def main():
    try:
        AUDIT_URL = os.environ['AUDIT_URL']
        AUDIT_LEVEL = os.environ.get('AUDIT_LEVEL', 'standard')
        COMPETITOR_URL = os.environ.get('COMPETITOR_URL', '')
        AUDIT_SCOPE = os.environ.get('AUDIT_SCOPE', 'only_onpage')
    except KeyError:
        print("Error: AUDIT_URL environment variable is not set. Aborting.")
        sys.exit(1)
        
    os.makedirs('reports', exist_ok=True)
    
    settings = Settings(CUSTOM_SETTINGS)
    
    settings.set('AUDIT_LEVEL', AUDIT_LEVEL)
    settings.set('AUDIT_SCOPE', AUDIT_SCOPE)
    
    # Set CLOSESPIDER_PAGECOUNT and DEPTH_LIMIT based on scope
    if AUDIT_SCOPE == 'only_onpage':
        settings.set('CLOSESPIDER_PAGECOUNT', 1)
        settings.set('DEPTH_LIMIT', 1)
    elif AUDIT_SCOPE == 'indexed_pages':
        settings.set('CLOSESPIDER_PAGECOUNT', 25)
        settings.set('DEPTH_LIMIT', 2)
    elif AUDIT_SCOPE == 'full_300_pages':
        settings.set('CLOSESPIDER_PAGECOUNT', 300)
        settings.set('DEPTH_LIMIT', 5) # Reasonable maximum depth
        
    max_pages_count = settings.getint('CLOSESPIDER_PAGECOUNT')
    
    process = CrawlerProcess(settings)
    
    process.crawl(SEOSpider, start_url=AUDIT_URL, max_pages_config=max_pages_count, all_checks=ALL_CHECKS_MODULES)
    
    print(f"\nStarting Main SEO Audit for {AUDIT_URL}...")
    print(f"Level: {AUDIT_LEVEL.capitalize()} | Scope: {AUDIT_SCOPE.replace('_', ' ')} (Max pages: {max_pages_count})\n")
    
    process.start()
    
    load_and_generate_reports(settings, AUDIT_URL, AUDIT_LEVEL, COMPETITOR_URL, AUDIT_SCOPE)

if __name__ == "__main__":
    main()
