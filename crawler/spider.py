import scrapy
from urllib.parse import urlparse, urljoin
import logging
from scrapy_playwright.page import PageMethod # CRITICAL IMPORT for defining wait conditions

class SEOSpider(scrapy.Spider):
    name = "seospider"
    
    # --- Spider Configuration and Initialization ---

    # NOTE: custom_settings is usually left empty here as settings are passed via main.py

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        # 1. Access the settings object from the crawler
        settings = crawler.settings
        
        # 2. Retrieve the required setting values
        audit_level = settings.get('AUDIT_LEVEL', 'standard')
        audit_scope = settings.get('AUDIT_SCOPE', 'only_onpage')
        
        # 3. Pass the retrieved values as keyword arguments to the __init__ method
        instance = super().from_crawler(crawler, *args, **kwargs, 
                                        audit_level=audit_level, 
                                        audit_scope=audit_scope)
        
        return instance

    def __init__(self, start_url=None, max_pages_config=25, all_checks=[], audit_level='standard', audit_scope='only_onpage', *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not start_url:
            # Note: This check is usually redundant as Scrapy requires start_urls, but remains good practice
            raise ValueError("A start URL is required.")
            
        self.start_urls = [start_url]
        self.allowed_domains = [urlparse(start_url).netloc]
        self.max_pages_config = max_pages_config
        self.pages_crawled = 0
        
        # Assign the values passed from from_crawler
        self.audit_level = audit_level 
        self.audit_scope = audit_scope 
        self.all_checks_modules = all_checks
        
        logging.info(f"Spider initialized with Audit Level: {self.audit_level} and Scope: {self.audit_scope}")

    def start_requests(self):
        """
        Initial request uses Playwright, with a crucial PageMethod to ensure
        the page is fully rendered before scraping.
        """
        for url in self.start_urls:
            # CRITICAL FIX: Add Playwright wait condition to ensure page rendering
            yield scrapy.Request(
                url, 
                callback=self.parse, 
                meta={
                    'playwright': True, 
                    'playwright_page_methods': [
                        # Wait for the body element to appear, a simple but effective readiness check
                        PageMethod('wait_for_selector', 'body') 
                        # Or, for better stability: PageMethod('wait_for_load_state', 'networkidle')
                    ]
                }, 
                dont_filter=True
            ) 

    def parse(self, response):
        self.pages_crawled += 1
        logging.info(f"Crawled page {self.pages_crawled}/{self.max_pages_config}: {response.url}")

        # Check if the response received is valid (e.g., status 200) before proceeding
        if response.status >= 400:
            logging.warning(f"Skipping checks due to bad status code {response.status} for {response.url}")
            # Yield a failed item so the report knows the page failed to load
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
            # Use only the final module name for the checks dictionary key
            check_key = module_name.split('.')[-1]
            try:
                # The name of the function MUST be 'run_audit'
                check_results = check_module.run_audit(response, self.audit_level) 
                page_audit_results['checks'][check_key] = check_results
            except AttributeError as e:
                # This will capture the 'module has no attribute run_audit' error and log it
                page_audit_results['checks'][check_key] = {
                    'error': f"MODULE ERROR: {e}. Check module '{check_key}' is likely missing the required **'run_audit(response, audit_level)'** function."
                }
            except Exception as e:
                page_audit_results['checks'][check_key] = {'error': f"Unhandled exception during check: {str(e)}"}

        yield page_audit_results 

        # Link following logic for deep crawl scopes
        if self.pages_crawled < self.max_pages_config and self.audit_scope != 'only_onpage':
            # Simplified link following
            for href in response.css('a::attr(href)').getall():
                url = urljoin(response.url, href)
                parsed_url = urlparse(url)
                
                # Check scheme and domain for internal links
                if parsed_url.netloc == self.allowed_domains[0] and parsed_url.scheme in ['http', 'https']:
                    # Re-use the Playwright configuration for subsequent requests
                    yield scrapy.Request(
                        url, 
                        callback=self.parse, 
                        meta={
                            'playwright': True, 
                            'playwright_page_methods': [PageMethod('wait_for_selector', 'body')]
                        }
                        )
                
