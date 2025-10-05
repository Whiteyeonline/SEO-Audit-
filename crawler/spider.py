# crawler/spider.py (FINAL COMPLETE VERSION)
import scrapy
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from checks import (
    meta_check, heading_check, image_check, link_check,
    schema_check, keyword_analysis, 
    url_structure, internal_links, canonical_check,
    content_quality, accessibility_check, mobile_friendly_check,
    backlinks_check,
    local_seo_check, 
    analytics_check
)

class SEOSpider(scrapy.Spider):
    name = "seo_spider"
    
    # ... (init method remains unchanged) ...
    def __init__(self, start_urls=None, domain_checks=None, audit_level='standard', crawl_depth=None, *args, **kwargs):
        super(SEOSpider, self).__init__(*args, **kwargs)
        if start_urls is None:
            raise ValueError("start_urls must be provided.")
            
        self.start_urls = start_urls
        self.allowed_domains = [urlparse(u).netloc for u in start_urls]
        self.domain_checks = domain_checks if domain_checks else {}
        self.crawl_domain = self.allowed_domains[0]
        self.audit_level = audit_level
        self.max_depth = crawl_depth
        
        self.basic_checks = [
            'url_structure', 'canonical', 'meta', 'headings', 'content', 'images', 'mobile',
            'local_seo', 'analytics', 'accessibility'
        ]

    @staticmethod
    def run_single_page_checks(url, html_content):
        """Utility method to run all checks on a single page, used for Competitor analysis and full audit."""
        
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
            
            # Heavy/Standard-only checks:
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
        # Use response.body.decode('utf-8') for reliable content from Scrapy-Playwright
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
        
        # 1. Error Handling 
        if not page_results["is_crawlable"]:
            page_results["error_detail"] = f"Page returned HTTP error code {status}. Link structure analysis skipped."
            yield page_results
            return 
        
        # 2. Run Page Checks based on Audit Level
        page_checks = SEOSpider.run_single_page_checks(url, html_content)
        
        if self.audit_level == 'basic':
            filtered_results = {key: page_checks.get(key) for key in self.basic_checks if page_checks.get(key) is not None}
            page_results.update(filtered_results)
        else:
            page_results.update(page_checks)
            
        # 3. Follow Internal Links (Respecting Scope)
        if self.max_depth is None or depth < self.max_depth:
            for href in response.css('a::attr(href)').getall():
                absolute_url = urljoin(response.url, href)
                
                if urlparse(absolute_url).netloc == self.crawl_domain:
                    yield response.follow(absolute_url, callback=self.parse)
        
        # 4. Yield the completed page data
        yield page_results # Ensures that the data for the starting page is always saved.
            
