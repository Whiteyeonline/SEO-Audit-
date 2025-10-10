import scrapy
from urllib.parse import urlparse, urljoin
import logging

class SEOSpider(scrapy.Spider):
    name = "seospider"
    # Settings are handled by the main.py file's CrawlerProcess
    custom_settings = {
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000, 
    } 

    # --- CRITICAL FIX 1: Use from_crawler to access settings ---
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        # Create an instance of the class
        instance = super().from_crawler(crawler, *args, **kwargs)
        # Store settings for access in __init__
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

        # Run Checks using the 'run_audit' function
        for check_module in self.all_checks_modules:
            module_name = check_module.__name__
            try:
                check_results = check_module.run_audit(response, self.audit_level) 
                page_audit_results['checks'][module_name] = check_results
            except AttributeError:
                page_audit_results['checks'][module_name] = {
                    'error': f"MODULE ERROR: Check module '{module_name}' is missing the required 'run_audit(response, audit_level)' function. Please implement it."
                }
            except Exception as e:
                page_audit_results['checks'][module_name] = {'error': f"Unhandled exception during check: {str(e)}"}

        yield page_audit_results 

        # Link following logic for deep crawl scopes
        if self.pages_crawled < self.max_pages_config and self.audit_scope != 'only_onpage':
            for href in response.css('a::attr(href)').getall():
                url = urljoin(response.url, href)
                parsed_url = urlparse(url)
                
                if parsed_url.netloc == self.allowed_domains[0] and parsed_url.scheme in ['http', 'https']:
                    request_key = scrapy.Request(url, callback=self.parse, meta={'playwright': True}).url
                    if request_key not in response.request.cb_kwargs.get('visited_urls', {}):
                        yield scrapy.Request(url, callback=self.parse, meta={'playwright': True, 'visited_urls': response.request.cb_kwargs.get('visited_urls', {}).copy() | {request_key: True}})
                    
