import scrapy
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from checks import (
    meta_check, heading_check, image_check, link_check,
    schema_check, keyword_analysis, performance_check,
    url_structure, internal_links, canonical_check,
    content_quality, accessibility_check, mobile_friendly_check,
    backlinks_check # Note: backlinks check here is limited to page-level external links
)

class SEOSpider(scrapy.Spider):
    name = "seo_spider"
    
    def __init__(self, start_urls=None, domain_checks=None, *args, **kwargs):
        super(SEOSpider, self).__init__(*args, **kwargs)
        if start_urls is None:
            raise ValueError("start_urls must be provided.")
        self.start_urls = start_urls
        self.allowed_domains = [urlparse(u).netloc for u in start_urls]
        self.domain_checks = domain_checks if domain_checks else {}
        self.crawl_domain = self.allowed_domains[0]

    def parse(self, response):
        """Processes each page crawled by Scrapy."""
        url = response.url
        html_content = response.text
        status = response.status
        
        # --- 1. Initial Data and Error Handling (Addresses '40 score' issue) ---
        page_results = {
            "url": url,
            "status_code": status,
            "is_crawlable": (status >= 200 and status < 400),
            "error_detail": None,
            "crawl_depth": response.request.meta.get('depth', 0)
        }
        
        # If the page failed to load (4xx/5xx), we stop processing and only record status
        if not page_results["is_crawlable"]:
            page_results["error_detail"] = f"Page returned HTTP error code {status}. Link structure analysis skipped."
            # Yield the minimal result and stop further processing for this URL
            yield page_results
            return 
        
        # --- 2. Run All Professional Page Checks ---
        # Note: We skip performance_check here to avoid rate-limiting and duplicate work. 
        # A separate tool like Lighthouse (or the basic performance check) is run once in main.py.
        
        page_results.update({
            "url_structure": url_structure.run(url),
            "canonical": canonical_check.run(url, html_content),
            "schema": schema_check.run(url, html_content),

            "meta": meta_check.run(url, html_content),
            "headings": heading_check.run(url, html_content),
            "content": content_quality.run(url, html_content),
            "keywords": keyword_analysis.run(url, html_content),
            "images": image_check.run(url, html_content),

            "links": link_check.run(url, html_content),
            "internal_links": internal_links.run(url, html_content),
            "accessibility": accessibility_check.run(url, html_content),
            "mobile": mobile_friendly_check.run(url, html_content),
            "backlinks": backlinks_check.run(url, html_content),
        })

        # --- 3. Follow Internal Links for Full Crawl ---
        for href in response.css('a::attr(href)').getall():
            absolute_url = urljoin(response.url, href)
            
            # Check if the link is within the allowed domains
            if urlparse(absolute_url).netloc == self.crawl_domain:
                yield response.follow(absolute_url, callback=self.parse)
        
        # --- 4. Yield the completed page data ---
        yield page_results
          
