import scrapy
from urllib.parse import urlparse, urljoin
import logging
# All check modules are now passed to the spider via arguments
# from main.py, so we remove the large block of imports and definition here

class SEOSpider(scrapy.Spider):
    name = "seospider"
    # Settings are handled by the main.py file's CrawlerProcess
    custom_settings = {
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000, 
    } 

    def __init__(self, start_url=None, max_pages_config=25, all_checks=[], *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not start_url:
            raise ValueError("A start URL is required.")
            
        self.start_urls = [start_url]
        self.allowed_domains = [urlparse(start_url).netloc]
        self.max_pages_config = max_pages_config
        self.pages_crawled = 0
        
        # Get settings from Scrapy settings set in main.py
        self.audit_level = self.settings.get('AUDIT_LEVEL', 'standard') 
        self.audit_scope = self.settings.get('AUDIT_SCOPE', 'only_onpage') 
        self.all_checks_modules = all_checks # The list of check modules passed from main.py

    def start_requests(self):
        # Initial request uses Playwright for JavaScript rendering
        for url in self.start_urls:
            # We are using the Playwright handler to ensure dynamic content is available
            yield scrapy.Request(url, callback=self.parse, meta={'playwright': True}) 

    def parse(self, response):
        self.pages_crawled += 1
        logging.info(f"Crawled page {self.pages_crawled}/{self.max_pages_config}: {response.url}")

        page_audit_results = {
            'url': response.url,
            'status_code': response.status,
            'checks': {},
            'is_crawlable': True
        }

        # --- CRITICAL FIX: Run Checks using the new 'run_audit' function ---
        for check_module in self.all_checks_modules:
            module_name = check_module.__name__
            try:
                # The fix is to assume a proper function name and structure that accepts response
                # YOU MUST IMPLEMENT run_audit(response, audit_level) in every checks module
                check_results = check_module.run_audit(response, self.audit_level) 
                page_audit_results['checks'][module_name] = check_results
            except AttributeError:
                # Provides a helpful error if the user forgets to implement the function
                page_audit_results['checks'][module_name] = {
                    'error': f"MODULE ERROR: Check module '{module_name}' is missing the required 'run_audit(response, audit_level)' function. Please implement it."
                }
            except Exception as e:
                # Catches any other exceptions during the check process
                page_audit_results['checks'][module_name] = {'error': f"Unhandled exception during check: {str(e)}"}
        # --- End CRITICAL FIX ---

        yield page_audit_results # Export the results

        # Link following logic for deep crawl scopes
        if self.pages_crawled < self.max_pages_config and self.audit_scope != 'only_onpage':
            # Follow all internal links found on the page
            for href in response.css('a::attr(href)').getall():
                url = urljoin(response.url, href)
                parsed_url = urlparse(url)
                
                # Only follow links that are on the same domain and have not been crawled/queued
                if parsed_url.netloc == self.allowed_domains[0] and parsed_url.scheme in ['http', 'https']:
                    # Use a unique key to prevent re-queuing the same URL multiple times
                    request_key = scrapy.Request(url, callback=self.parse, meta={'playwright': True}).url
                    if request_key not in response.request.cb_kwargs.get('visited_urls', {}):
                        # Use Playwright for all subsequent requests to handle JS pages
                        yield scrapy.Request(url, callback=self.parse, meta={'playwright': True, 'visited_urls': response.request.cb_kwargs.get('visited_urls', {}).copy() | {request_key: True}})
