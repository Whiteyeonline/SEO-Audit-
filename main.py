# main.py (Finalized with Deep Competitor Analysis using Playwright)

import os
import json
import logging
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from collections import defaultdict
from twisted.internet import reactor # Required for running two spiders sequentially

# Relative imports from your project structure
from crawler.spider import SEOSpider
# NEW: Import the dedicated competitor spider
from crawler.competitor_spider import CompetitorSpider 
# MODIFIED: Import new report writer functions
from utils.report_writer import write_summary_report, get_check_aggregation, write_json_report, write_markdown_report
# REMOVE: We no longer need the simple utility check
# from checks.competitor_analysis_util import run_competitor_audit 


# --- Import all Check Modules (LOGIC REMAINS SAME) ---
# ... (ALL_CHECKS_MODULES list remains the same) ...
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

# --- EXPERT WEIGHTED PENALTY SYSTEM (LOGIC REMAINS SAME) ---
CRITICAL_ISSUE_WEIGHTS = {
    'title_fail_count': 10,
    'desc_fail_count': 5,
    'h1_fail_count': 10,
    'link_broken_total': 2,
    'mobile_unfriendly_count': 15,
    'robots_sitemap_fail_count': 5,
    'canonical_mismatch_count': 5,
    'ssl_check_fail_count': 20,
}
MAX_TOTAL_PENALTY = 70

# --- FINALIZED STABILITY SETTINGS FOR SCRAPY-PLAYWRIGHT (LOGIC REMAINS SAME) ---
CUSTOM_SETTINGS = {
    # ... (All existing settings remain the same) ...
    'USER_AGENT': 'ProfessionalSEOAgency (+https://github.com/your-repo)',
    'ROBOTSTXT_OBEY': False,
    'LOG_LEVEL': 'INFO',
    'CLOSESPIDER_PAGECOUNT': 250,
    'REQUEST_FINGERPRINTER_IMPLEMENTATION': '2.7', 
    'TELNET_ENABLED': False,
    'DOWNLOAD_TIMEOUT': 90, 
    'RETRY_TIMES': 0, 
    'DEPTH_LIMIT': 3,
    
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
        'wait_until': 'domcontentloaded', 
        'bypass_csp': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    },
    
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
    competitor_results = [] # NEW: Initialize competitor results
    crawl_file_path = settings.get('FEED_URI')
    error_message = None

    # --- 1. Load Main Crawl Results ---
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
        
    # --- 2. Load Competitor Crawl Results ---
    competitor_file_path = 'reports/competitor_results.json'
    if COMPETITOR_URL and os.path.exists(competitor_file_path) and os.path.getsize(competitor_file_path) > 0:
        try:
            with open(competitor_file_path, 'r', encoding='utf-8') as f:
                competitor_results = json.load(f)
            print(f"Competitor analysis results loaded for {COMPETITOR_URL}")
        except json.JSONDecodeError:
            print("WARNING: Failed to decode competitor results JSON.")
            competitor_results = []
    
    # 3. Separate Initial Checks from Crawled Pages
    initial_checks = next((item['checks'] for item in crawl_results if item.get('url') == 'INITIAL_CHECKS'), {})
    crawled_pages = [item for item in crawl_results if item.get('url') != 'INITIAL_CHECKS']
    total_pages_crawled = len(crawled_pages)
    
    
    if total_pages_crawled == 0:
        # If crawl failed completely (Pages Crawled: 0), default to a neutral score
        aggregation = {'total_pages_crawled': 0}
        final_score = 100 
    else:
        # 4. Get Aggregation from report_writer.py (UPDATED CALL)
        aggregation = get_check_aggregation(initial_checks, crawled_pages) 
        
        # 5. Calculate Robust Score using Centralized Weighted Penalties
        total_penalty = 0
        
        for agg_key, penalty_weight in CRITICAL_ISSUE_WEIGHTS.items():
            issue_count = aggregation.get(agg_key, 0)
            total_penalty += issue_count * penalty_weight

        final_penalty = min(total_penalty, MAX_TOTAL_PENALTY)
        final_score = max(100 - final_penalty, 30)
        
        aggregation['calculated_score'] = final_score


    # 6. Prepare Final Data Structure
    structured_report_data = {
        'audit_details': {
            'target_url': AUDIT_URL,
            'audit_level': AUDIT_LEVEL,
            'competitor_url': COMPETITOR_URL if COMPETITOR_URL else 'N/A',
            'audit_scope': AUDIT_SCOPE,
        },
        'final_score': final_score, 
        'crawled_pages': crawled_pages,
        'total_pages_crawled': total_pages_crawled,
        'aggregated_issues': aggregation,
        'basic_checks': initial_checks,
        'competitor_analysis': competitor_results[0] if competitor_results else None, # Store the full competitor audit results
        'crawl_error': error_message
    }

    # 7. Write all final report files
    structured_file_path = "reports/seo_audit_structured_report.json"
    with open(structured_file_path, 'w', encoding='utf-8') as f:
        json.dump(structured_report_data, f, indent=4)
    print(f"\nStructured report saved to: {structured_file_path}")

    # NEW: Write JSON and Markdown reports using updated functions
    write_json_report(structured_report_data, "reports/seo_audit_report.json")
    write_markdown_report(structured_report_data, "reports/seo_professional_report.md")

    write_summary_report(structured_report_data, "reports/seo_simple_summary.txt") 

    print(f"\nPages Crawled: {total_pages_crawled} | Final Score: {final_score}/100")

# --- Main Execution Flow (MODIFIED) ---
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
        settings.set('DEPTH_LIMIT', 5) 

    max_pages_count = settings.getint('CLOSESPIDER_PAGECOUNT')

    process = CrawlerProcess(settings)

    # --- NEW: Run Competitor Spider first if URL is provided ---
    if COMPETITOR_URL:
        print(f"Starting DEEP Competitor Audit for {COMPETITOR_URL} (Homepage only, full checks)...")
        # Run the Competitor Spider
        process.crawl(CompetitorSpider, start_url=COMPETITOR_URL, all_checks=ALL_CHECKS_MODULES)

    # --- Run Main Audit Spider ---
    print(f"\nStarting Main SEO Audit for {AUDIT_URL}...")
    print(f"Level: {AUDIT_LEVEL.capitalize()} | Scope: {AUDIT_SCOPE.replace('_', ' ')} (Max pages: {max_pages_count})\n")
    # Run the Main Spider
    process.crawl(SEOSpider, start_url=AUDIT_URL, max_pages_config=max_pages_count, all_checks=ALL_CHECKS_MODULES)

    # Start the process. If two crawls are scheduled, they run sequentially (Scrapy behavior)
    process.start() 
    
    load_and_generate_reports(settings, AUDIT_URL, AUDIT_LEVEL, COMPETITOR_URL, AUDIT_SCOPE)

if __name__ == "__main__":
    # Ensure the twisted reactor is stopped after all crawls are done
    try:
        main()
    except SystemExit:
        pass
    except Exception as e:
        print(f"An error occurred: {e}")
    
