import os
import re
from typing import Generator, Dict, Any, List

# --- Scrapy/Playwright Imports ---
import scrapy
from scrapy_playwright.page import PageMethod
from scrapy.selector import Selector
from urllib.parse import urljoin, urlparse

# --- Import All 18 Check Modules (Required by main.py setup) ---
# Ensure all these files (e.g., checks/ssl_check.py) exist and each has a 'run' function.
from checks import (
    ssl_check, robots_sitemap, performance_check, keyword_analysis, 
    local_seo_check, meta_check, heading_check, image_check, link_check,
    schema_check, url_structure, internal_links, canonical_check,
    content_quality, accessibility_check, mobile_friendly_check,
    backlinks_check, analytics_check
)
# -------------------------------------------------------------

class SEOSpider(scrapy.Spider):
    """
    A comprehensive SEO audit spider using Scrapy and Playwright 
    to handle JavaScript-rendered websites.
    """
    name = "SEOSpider"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get parameters from environment variables (set in main.py)
        self.start_url = os.environ.get('AUDIT_URL')
        self.audit_scope = os.environ.get('AUDIT_SCOPE', 'only_onpage')
        self.allowed_domains = [urlparse(self.start_url).netloc]
        self.total_pages_crawled = 0
        self.max_pages = self.settings.getint('CLOSESPIDER_PAGECOUNT', 1)
        self.crawled_results = []
        self.initial_basic_checks = {}

        if not self.start_url:
            raise ValueError("AUDIT_URL environment variable is not set.")

        # Run initial, non-crawl-dependent checks once (e.g., SSL, Robots)
        self.initial_basic_checks['ssl_check'] = ssl_check.run(self.start_url)
        self.initial_basic_checks['robots_sitemap'] = robots_sitemap.run(self.start_url)
        
        # Store initial checks into results structure (will be aggregated in closed())
        self.crawled_results.append({
            "url": "INITIAL_CHECKS",
            "checks": self.initial_basic_checks
        })
    
    # -----------------------------------------------------------------
    # 1. START REQUESTS: Defines the initial requests using Playwright
    # -----------------------------------------------------------------
    def start_requests(self) -> Generator[scrapy.Request, None, None]:
        """
        The starting point of the spider, configured to use Playwright 
        for JavaScript rendering.
        """
        # Ensure we only start crawling the homepage once
        self.crawler.stats.set_value('audit/start_url', self.start_url)
        
        yield scrapy.Request(
            url=self.start_url,
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                # Simulate a standard user interaction to wait for page load
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", "body"),
                    PageMethod("wait_for_timeout", 3000), # Wait 3 seconds for hydration
                ]
            },
            errback=self.errback
        )
    
    # -----------------------------------------------------------------
    # 2. PARSE: Handles the Playwright-rendered response
    # -----------------------------------------------------------------
    async def parse(self, response: scrapy.http.Response) -> Generator[Dict[str, Any], None, None]:
        """
        Processes the rendered HTML response and initiates checks.
        """
        self.total_pages_crawled += 1
        page = response.meta["playwright_page"]
        
        # Get the final rendered HTML content
        html_content = await page.content()
        current_url = response.url
        
        await page.close() # Important: Close the page to free resources

        self.logger.info(f"Processing page: {current_url} | Crawled: {self.total_pages_crawled}/{self.max_pages}")

        # Run all individual SEO checks on the current page
        page_checks = self.run_single_page_checks(current_url, html_content)

        # Store results
        self.crawled_results.append({
            "url": current_url,
            "checks": page_checks
        })

        # Process next pages only if audit scope is full_site
        if self.audit_scope == 'full_site':
            yield from self.crawl_links(response)

    # -----------------------------------------------------------------
    # 3. LINK CRAWLING: Logic for finding and queuing internal links
    # -----------------------------------------------------------------
    def crawl_links(self, response: scrapy.http.Response) -> Generator[scrapy.Request, None, None]:
        """
        Extracts internal links and yields new requests if max pages is not reached.
        """
        if self.total_pages_crawled >= self.max_pages:
            return

        # Use Scrapy's selector on the response body for links
        links = response.css('a::attr(href)').getall()
        base_url = response.url
        
        for href in links:
            absolute_url = urljoin(base_url, href)
            
            # Check if link is on the same domain and is not a file/anchor
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
    # 4. ERROR HANDLING: For failed requests
    # -----------------------------------------------------------------
    async def errback(self, failure):
        """
        Handles failed requests, typically due to network errors or timeouts.
        """
        request = failure.request
        self.logger.error(f"Request failed: {request.url} - {failure.value}")

        # Log the failure as a check result
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


    # -----------------------------------------------------------------
    # 5. CORE CHECK EXECUTION (FIXED LOGIC)
    # -----------------------------------------------------------------
    @staticmethod
    def run_single_page_checks(url: str, html_content: str) -> dict:
        """
        Runs all individual SEO checks on the scraped page content.
        
        This method was the source of the previous AttributeError. 
        It is structured to call the 'run' method on all imported check modules.
        """
        page_checks = {}
        try:
            # All check modules must be imported at the top of this file
            page_checks = {
                "ssl": ssl_check.run(url),
                "robots_sitemap": robots_sitemap.run(url),
                "performance": performance_check.run(url),
                "meta_tags": meta_check.run(url, html_content),
                "heading_structure": heading_check.run(url, html_content),
                "image_optimization": image_check.run(url, html_content),
                "link_audit": link_check.run(url, html_content),
                "schema_markup": schema_check.run(url, html_content),
                "url_canonicalization": canonical_check.run(url, html_content),
                "url_structure": url_structure.run(url),
                "internal_links": internal_links.run(url, html_content),
                "content_quality": content_quality.run(url, html_content),
                "mobile_friendly": mobile_friendly_check.run(url, html_content),
                "accessibility": accessibility_check.run(url, html_content),
                
                # THIS IS THE PREVIOUSLY MISSING/FAILED CALL:
                "local_seo": local_seo_check.run(url, html_content), 
                
                # Standard checks that rely on external tools/data, often placeholders
                "keyword_analysis": keyword_analysis.run(url, html_content),
                "backlinks_check": backlinks_check.run(url),
                "analytics_check": analytics_check.run(url),
            }
        except Exception as e:
            # Catch errors in the check execution itself
            page_checks["internal_error"] = {
                "check_name": "Internal Spider Check Error",
                "status": "Fail",
                "issues": [{"type": "critical", "message": f"Internal check failed for {url}: {e}"}]
            }
            SEOSpider.logger.error(f"Error running checks for {url}: {e}")

        return page_checks

    # -----------------------------------------------------------------
    # 6. SPIDER CLOSED: Final aggregation before Scrapy shuts down
    # -----------------------------------------------------------------
    def closed(self, reason: str):
        """
        Called when the spider is closed for any reason (e.g., closespider_pagecount).
        """
        # Save the final results list to a shared variable/file 
        # (This is typically handled by main.py or a custom Scrapy Pipeline)
        self.crawler.stats.set_value('audit/final_results', self.crawled_results)
        self.crawler.stats.set_value('audit/total_pages_crawled', self.total_pages_crawled)
        
        self.logger.info(f"Spider closed. Reason: {reason}. Pages crawled: {self.total_pages_crawled}")

