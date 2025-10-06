import os
import re
from typing import Generator, Dict, Any, List

# --- Scrapy/Playwright Imports ---
import scrapy
from scrapy_playwright.page import PageMethod
from scrapy.selector import Selector
from urllib.parse import urljoin, urlparse

# --- Import All 18 Check Modules (CRITICAL: All must exist and have a 'run' function) ---
from checks import (
    ssl_check, robots_sitemap, performance_check, keyword_analysis, 
    local_seo_check, meta_check, heading_check, image_check, link_check,
    schema_check, url_structure, internal_links, canonical_check,
    content_quality, accessibility_check, mobile_friendly_check,
    backlinks_check, analytics_check
)
# -------------------------------------------------------------

class SEOSpider(scrapy.Spider):
    name = "SEOSpider"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.start_url = os.environ.get('AUDIT_URL')
        self.audit_scope = os.environ.get('AUDIT_SCOPE', 'only_onpage')
        self.allowed_domains = [urlparse(self.start_url).netloc]
        self.total_pages_crawled = 0
        
        # FIX 1: Use self.crawler.settings to access CLOSESPIDER_PAGECOUNT
        self.max_pages = self.crawler.settings.getint('CLOSESPIDER_PAGECOUNT', 250)
        
        self.crawled_results = []
        self.initial_basic_checks = {}

        if not self.start_url:
            raise ValueError("AUDIT_URL environment variable is not set.")

        # Run initial checks only once (these don't require the HTML content)
        self.initial_basic_checks['ssl_check'] = self._safe_run_check(ssl_check, 'run', self.start_url)
        self.initial_basic_checks['robots_sitemap'] = self._safe_run_check(robots_sitemap, 'run', self.start_url)
        
        # Store initial checks outside the main crawled list
        self.crawled_results.append({
            "url": "INITIAL_CHECKS",
            "checks": self.initial_basic_checks
        })
    
    # --- Helper function for safe check execution (rest of the file remains the same) ---
    def _safe_run_check(self, module, function_name, *args, **kwargs):
        """Safely executes a check function, returning an error structure on failure."""
        try:
            return getattr(module, function_name)(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error in {module.__name__}.{function_name} for {args[0]}: {e}")
            return {
                "check_name": f"{module.__name__} Check",
                "status": "Error",
                "issues": [{"type": "critical", "message": f"Check failed due to an internal execution error: {e}"}],
                "details": {}
            }

    # -----------------------------------------------------------------
    # 1. START REQUESTS: Defines the initial requests using Playwright
    # -----------------------------------------------------------------
    def start_requests(self) -> Generator[scrapy.Request, None, None]:
        self.crawler.stats.set_value('audit/start_url', self.start_url)
        
        yield scrapy.Request(
            url=self.start_url,
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", "body"),
                    PageMethod("wait_for_timeout", 3000), 
                ]
            },
            errback=self.errback
        )
    
    # -----------------------------------------------------------------
    # 2. PARSE: Handles the Playwright-rendered response
    # -----------------------------------------------------------------
    async def parse(self, response: scrapy.http.Response) -> Generator[Dict[str, Any], None, None]:
        self.total_pages_crawled += 1
        page = response.meta["playwright_page"]
        
        html_content = await page.content()
        current_url = response.url
        
        await page.close()

        self.logger.info(f"Processing page: {current_url} | Crawled: {self.total_pages_crawled}/{self.max_pages}")

        page_checks = self.run_single_page_checks(current_url, html_content)

        self.crawled_results.append({
            "url": current_url,
            "checks": page_checks
        })

        if self.audit_scope == 'full_site':
            for request in self.crawl_links(response):
                yield request

    # -----------------------------------------------------------------
    # 3. LINK CRAWLING: Logic for finding and queuing internal links
    # -----------------------------------------------------------------
    def crawl_links(self, response: scrapy.http.Response) -> Generator[scrapy.Request, None, None]:
        if self.total_pages_crawled >= self.max_pages:
            return

        links = response.css('a::attr(href)').getall()
        base_url = response.url
        
        for href in links:
            absolute_url = urljoin(base_url, href)
            
            if urlparse(absolute_url).netloc == self.allowed_domains[0] and not re.search(r'(\.pdf|\.zip|\#)', absolute_url):
                yield scrapy.Request(
                    url=absolute_url,
                    callback=self.parse,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_selector", "body"),
                            PageMethod("wait_for_timeout", 3000),
                        ]
                    },
                    errback=self.errback
                )
    
    # -----------------------------------------------------------------
    # 4. ERROR HANDLING & 5. CORE CHECK EXECUTION (As previously corrected)
    # -----------------------------------------------------------------
    async def errback(self, failure):
        request = failure.request
        self.logger.error(f"Request failed: {request.url} - {failure.value}")

        self.crawled_results.append({
            "url": request.url,
            "checks": {
                "fetch_error": {
                    "check_name": "Page Fetch Error",
                    "status": "Fail",
                    "issues": [{"type": "critical", "message": f"Request failed: {failure.value}"}],
                    "details": {"url": request.url}
                }
            }
        })
    
    def run_single_page_checks(self, url: str, html_content: str) -> dict:
        page_checks = {}
        
        checks_url_only = [
            (performance_check, 'run', url),
            (backlinks_check, 'run', url),
            (analytics_check, 'run', url),
        ]
        
        checks_url_html = [
            (meta_check, 'run', url, html_content),
            (heading_check, 'run', url, html_content),
            (image_check, 'run', url, html_content),
            (link_check, 'run', url, html_content),
            (schema_check, 'run', url, html_content),
            (local_seo_check, 'run', url, html_content), 
            (url_structure, 'run', url),
            (internal_links, 'run', url, html_content),
            (canonical_check, 'run', url, html_content),
            (content_quality, 'run', url, html_content),
            (mobile_friendly_check, 'run', url, html_content),
            (accessibility_check, 'run', url, html_content),
            (keyword_analysis, 'run', url, html_content),
        ]

        for module, func_name, *args in checks_url_only + checks_url_html:
            check_name = module.__name__.split('.')[-1]
            page_checks[check_name] = self._safe_run_check(module, func_name, *args)

        return page_checks

    # -----------------------------------------------------------------
    # 6. SPIDER CLOSED: Final aggregation before Scrapy shuts down
    # -----------------------------------------------------------------
    def closed(self, reason: str):
        self.crawler.stats.set_value('audit/final_results', self.crawled_results)
        self.crawler.stats.set_value('audit/total_pages_crawled', self.total_pages_crawled)
        self.logger.info(f"Spider closed. Reason: {reason}. Pages crawled: {self.total_pages_crawled}")
        
