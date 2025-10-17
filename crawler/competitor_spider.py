# crawler/competitor_spider.py

import scrapy
from scrapy_playwright.page import PageMethod
import json
import logging
from collections import defaultdict

class CompetitorSpider(scrapy.Spider):
    name = 'competitor_spider'
    
    # Store all check modules passed from main.py
    check_modules = []
    
    def __init__(self, start_url=None, all_checks=None, *args, **kwargs):
        super(CompetitorSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.check_modules = all_checks
        self.max_pages_config = 1 # We only want the competitor's homepage
        self.pages_crawled = 0
        self.competitor_results = []
        
    def start_requests(self):
        # Initial request for the competitor's homepage
        yield scrapy.Request(
            url=self.start_urls[0],
            callback=self.parse,
            meta={
                'playwright': True,
                # Use the 'load' wait_until for a full JavaScript render 
                'playwright_page_methods': [
                    PageMethod('wait_for_selector', 'body')
                ],
                'page_type': 'competitor_homepage'
            }
        )

    def parse(self, response):
        """
        Runs all existing SEO checks on the competitor's single page.
        """
        if self.pages_crawled >= self.max_pages_config:
            return

        self.pages_crawled += 1
        page_checks = defaultdict(lambda: {'status': 'INFO', 'result': {}, 'error': None})

        # 1. Run all inherited checks
        for module in self.check_modules:
            try:
                # Assuming all check modules have a 'run_audit' method
                check_name = module.__name__.split('.')[-1]
                check_result = module.run_audit(response, audit_level='expert') # Run all checks at 'expert' level for best comparison
                
                # Check results should be a dictionary like {'status': 'FAIL', 'result': {...}}
                page_checks[check_name].update(check_result)
            except Exception as e:
                self.logger.error(f"Error running check {module.__name__} on competitor: {e}")
                page_checks[module.__name__.split('.')[-1]]['status'] = 'ERROR'
                page_checks[module.__name__.split('.')[-1]]['error'] = str(e)
        
        # 2. Store the single competitor page result
        self.competitor_results.append({
            'url': response.url,
            'http_status': response.status,
            'checks': dict(page_checks),
        })
        
        # NOTE: No follow-up requests, as we only crawl the homepage for comparison.
        
    def close(self, reason):
        """
        Called when the spider closes. Saves the results to a separate file.
        """
        if self.competitor_results:
            # Save the results to a temporary JSON file for main.py to load
            with open('reports/competitor_results.json', 'w', encoding='utf-8') as f:
                json.dump(self.competitor_results, f, indent=4)
        
        self.logger.info(f"Competitor audit finished. Status: {reason}")
      
