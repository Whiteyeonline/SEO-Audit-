# crawler/spider.py

import scrapy
from urllib.parse import urlparse, urljoin
import logging
from scrapy_playwright.page import PageMethod 

class SEOSpider(scrapy.Spider):
    name = "seospider"
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        settings = crawler.settings
        audit_level = settings.get('AUDIT_LEVEL', 'standard')
        audit_scope = settings.get('AUDIT_SCOPE', 'only_onpage')
        
        instance = super().from_crawler(crawler, *args, **kwargs, 
                                        audit_level=audit_level, 
                                        audit_scope=audit_scope)
        return instance

    def __init__(self, start_url=None, max_pages_config=25, all_checks=[], audit_level='standard', audit_scope='only_onpage', *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not start_url:
            raise ValueError("A start URL is required.")
            
        self.start_urls = [start_url]
        # Use a list for allowed_domains for consistency
        self.allowed_domains = [urlparse(start_url).netloc]
        self.max_pages_config = max_pages_config
        self.pages_crawled = 0
        self.audit_level = audit_level 
        self.audit_scope = audit_scope 
        self.all_checks_modules = all_checks
        
        logging.info(f"Spider initialized with Audit Level: {self.audit_level} and Scope: {self.audit_scope}")

    def start_requests(self):
        """
        Initial request uses Playwright, with a crucial PageMethod to ensure
        the page is fully rendered before scraping, as the initial URL's type is unknown.
        """
        for url in self.start_urls:
            yield scrapy.Request(
                url, 
                callback=self.parse, 
                # CRITICAL: Added errback for robust error handling
                errback=self.handle_error,
                meta={
                    # Force Playwright rendering
                    'playwright': True, 
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', 'body') 
                    ]
                }, 
                dont_filter=True
            ) 

    def parse(self, response):
        self.pages_crawled += 1
        logging.info(f"Crawled page {self.pages_crawled}/{self.max_pages_config}: {response.url}")

        if response.status >= 400:
            logging.warning(f"Skipping checks due to bad status code {response.status} for {response.url}")
            # This logic is also handled by handle_error, but kept here for clarity on good responses.
            # We skip link following on bad status pages anyway.
            yield {
                'url': response.url,
                'status_code': response.status,
                'checks': {'load_status': {'error': f"Page failed to load with HTTP status {response.status}"}},
                'is_crawlable': False
            }
            return

        page_audit_results = {
            'url': response.url,
            'status_code': response.status,
            'checks': {},
            'is_crawlable': True
        }

        # Run Checks using the 'run_audit' function
        for check_module in self.all_checks_modules:
            module_name = check_module.__name__
            check_key = module_name.split('.')[-1]
            try:
                # Passes the Playwright-rendered response
                check_results = check_module.run_audit(response, self.audit_level) 
                page_audit_results['checks'][check_key] = check_results
            except AttributeError as e:
                # Error: Function missing
                page_audit_results['checks'][check_key] = {
                    'error': f"MODULE ERROR: {e}. Check module '{check_key}' is likely missing the required **'run_audit(response, audit_level)'** function."
                }
            except Exception as e:
                # Error: Unhandled exception during check execution
                page_audit_results['checks'][check_key] = {'error': f"Unhandled exception during check: {str(e)}"}

        yield page_audit_results 

        # Link following logic for deep crawl scopes
        if self.pages_crawled < self.max_pages_config and self.audit_scope != 'only_onpage':
            # Use response.css('a::attr(href)').getall() for robust link extraction
            for href in response.css('a::attr(href)').getall():
                url = urljoin(response.url, href)
                parsed_url = urlparse(url)
                
                # Check if link is internal and a standard web link
                if parsed_url.netloc == self.allowed_domains[0] and parsed_url.scheme in ['http', 'https']:
                    # Use response.follow for cleaner link creation
                    yield response.follow(
                        url, 
                        callback=self.parse, 
                        errback=self.handle_error, # Critical: Add error handling
                        meta={
                            # CRITICAL: Force Playwright rendering for every link as requested
                            'playwright': True, 
                            'playwright_page_methods': [PageMethod('wait_for_selector', 'body')]
                        }
                    )

    def handle_error(self, failure):
        """
        Handles any request failures (DNS, connection, Playwright timeout, etc.).
        """
        url = failure.request.url
        logging.error(f"Request failed for {url}: {failure.getErrorMessage()}")

        # Yield a result item with failure status instead of crashing
        yield {
            'url': url,
            'status_code': 'CRAWL_ERROR',
            'checks': {
                'load_status': {'error': f"Crawl failed due to connection error or Playwright timeout: {failure.getErrorMessage()}"}
            },
            'is_crawlable': False
            }
            
