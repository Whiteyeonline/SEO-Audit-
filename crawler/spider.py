import scrapy
from urllib.parse import urlparse, urljoin
import logging

class SEOSpider(scrapy.Spider):
    name = "seospider"
    # Settings are handled by the main.py file's CrawlerProcess
    custom_settings = {
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000, 
    } 

    # --- CRITICAL FIX: Use from_crawler to properly access settings ---
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        # Create an instance of the class and attach the crawler's settings
        instance = super().from_crawler(crawler, *args, **kwargs)
        instance.settings = crawler.settings
        return instance

    def __init__(self, start_url=None, max_pages_config=25, all_checks=[], *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not start_url:
            raise ValueError("A start URL is required.")
            
        self.start_urls = [start_url]
        self.allowed_domains = [urlparse(start_url).netloc]
        self.max_pages_config = max_pages_config
        self.pages_crawled = 0
        
        # Access settings via the stored attribute
        self.audit_level = self.settings.get('AUDIT_LEVEL', 'standard') 
        self.audit_scope = self.settings.get('AUDIT_SCOPE', 'only_onpage') 
        self.all_checks_modules = all_checks

    def start_requests(self):
        # Initial request uses Playwright for JavaScript rendering
        for url in self.start_urls:
            # Use 'dont_filter' to ensure the initial URL is always requested,
            # even if it was seen before (e.g., in sitemap checks)
            yield scrapy.Request(url, callback=self.parse, meta={'playwright': True}, dont_filter=True) 

    def parse(self, response):
        self.pages_crawled += 1
        logging.info(f"Crawled page {self.pages_crawled}/{self.max_pages_config}: {response.url}")

        page_audit_results = {
            'url': response.url,
            'status_code': response.status,
            'checks': {},
            'is_crawlable': True
        }

        # Run Checks using the 'run_audit' function
        # This assumes all your checks/*.py files have a function named run_audit(response, audit_level)
        for check_module in self.all_checks_modules:
            module_name = check_module.__name__
            try:
                # The name of the function MUST be 'run_audit'
                check_results = check_module.run_audit(response, self.audit_level) 
                page_audit_results['checks'][module_name] = check_results
            except AttributeError as e:
                # This will capture the 'module has no attribute run_url' error and log it
                page_audit_results['checks'][module_name] = {
                    'error': f"MODULE ERROR: {e}. Check module '{module_name}' is likely missing the required 'run_audit(response, audit_level)' function. Please update the function name in the checks/{module_name.split('.')[-1]}.py file."
                }
            except Exception as e:
                page_audit_results['checks'][module_name] = {'error': f"Unhandled exception during check: {str(e)}"}

        yield page_audit_results 

        # Link following logic for deep crawl scopes
        if self.pages_crawled < self.max_pages_config and self.audit_scope != 'only_onpage':
            # Simplified link following to avoid deep recursion issues
            for href in response.css('a::attr(href)').getall():
                url = urljoin(response.url, href)
                parsed_url = urlparse(url)
                
                if parsed_url.netloc == self.allowed_domains[0] and parsed_url.scheme in ['http', 'https']:
                    # Use a new request to crawl the next page
                    yield scrapy.Request(url, callback=self.parse, meta={'playwright': True})

