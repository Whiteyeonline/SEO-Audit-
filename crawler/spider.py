# crawler/spider.py (FINAL COMPLETE VERSION - FIX: Added start_requests for Playwright)
import scrapy
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from checks import (
    meta_check, heading_check, image_check, link_check,
    schema_check, keyword_analysis, url_structure, internal_links, canonical_check,
    content_quality, accessibility_check, mobile_friendly_check, backlinks_check,
    local_seo_check, analytics_check
)

class SEOSpider(scrapy.Spider):
    name = "seo_spider"
    
    def __init__(self, start_urls=None, audit_level='standard', audit_scope='only_onpage', *args, **kwargs):
        super(SEOSpider, self).__init__(*args, **kwargs)
        if start_urls is None:
            raise ValueError("start_urls must be provided.")
        self.start_urls = start_urls
        self.crawl_domain = urlparse(start_urls[0]).netloc
        self.allowed_domains = [self.crawl_domain]
        self.audit_level = audit_level
        
        # Determine max_depth based on audit_scope for link following logic
        if audit_scope == 'only_onpage':
            self.max_depth = 0
        else:
            # Set a high depth for standard/advanced to be limited by CLOSESPIDER_PAGECOUNT in main.py
            self.max_depth = 100 
            
        self.basic_checks = [
            'url_structure', 'canonical', 'meta', 'headings', 'content', 'images', 'mobile',
            'local_seo', 'analytics', 'accessibility'
        ]

    # 🚨 CRITICAL FIX 1: Explicitly define start_requests to enable Playwright
    def start_requests(self):
        """Generates the initial requests with the 'playwright' meta key."""
        for url in self.start_urls:
            # MUST include meta={'playwright': True} for scrapy-playwright to handle the request
            yield scrapy.Request(
                url=url, 
                callback=self.parse, 
                meta={"playwright": True} 
            )

    @staticmethod
    def run_single_page_checks(url, html_content):
        # All 15 checks run on a single page
        results = {
            "url_structure": url_structure.run(url),
            "canonical": canonical_check.run(url, html_content),
            "meta": meta_check.run(url, html_content),
            "headings": heading_check.run(url, html_content),
            "content": content_quality.run(url, html_content),
            "images": image_check.run(url, html_content),
            "accessibility": accessibility_check.run(url, html_content),
            "mobile": mobile_friendly_check.run(url, html_content),
            "local_seo": local_seo_check.run(url, html_content), 
            "analytics": analytics_check.run(url, html_content),
            "schema": schema_check.run(url, html_content),
            "keywords": keyword_analysis.run(url, html_content),
            "links": link_check.run(url, html_content), 
            "internal_links": internal_links.run(url, html_content),
            "backlinks": backlinks_check.run(url, html_content),
        }
        return results

    def parse(self, response):
        """Processes each page crawled by Scrapy."""
        url = response.url
        html_content = response.body.decode('utf-8') 
        status = response.status
        depth = response.request.meta.get('depth', 0)
        
        page_results = {
            "url": url,
            "status_code": status,
            "is_crawlable": (status >= 200 and status < 400),
            "error_detail": None,
            "crawl_depth": depth
        }
        
        if not page_results["is_crawlable"]:
            page_results["error_detail"] = f"Page returned HTTP error code {status}. Analysis skipped."
            yield page_results
            return 
        
        page_checks = SEOSpider.run_single_page_checks(url, html_content)
        
        if self.audit_level == 'basic':
            # Filter results for basic level checks
            filtered_results = {key: page_checks.get(key) for key in self.basic_checks if page_checks.get(key) is not None}
            page_results.update(filtered_results)
        else:
            # Include all results for standard/advanced levels
            page_results.update(page_checks)
            
        # Follow Internal Links (Only for deep crawls)
        # Note: only_onpage sets self.max_depth=0, so this block is skipped for onpage audits.
        if depth < self.max_depth: 
            for href in response.css('a::attr(href)').getall():
                absolute_url = urljoin(response.url, href)
                
                # Ensure the link stays within the same domain
                if urlparse(absolute_url).netloc == self.crawl_domain:
                    # Subsequent requests *do not* need the 'playwright: True' meta unless you need JavaScript rendering for every link
                    # For performance, we assume only the start page needs Playwright unless specified otherwise.
                    yield response.follow(absolute_url, callback=self.parse)
        
        # Always yield the page results (this is the item that main.py collects)
        yield page_results
    
