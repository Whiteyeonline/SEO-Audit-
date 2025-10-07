import scrapy
from urllib.parse import urlparse, urljoin
import logging

from checks import (
    ssl_check, robots_sitemap, performance_check, keyword_analysis,
    local_seo_check, meta_check, heading_check, image_check, link_check,
    schema_check, url_structure, internal_links, canonical_check,
    content_quality, accessibility_check, mobile_friendly_check,
    backlinks_check, analytics_check
)

ALL_CHECKS_MODULES = [
    ssl_check, robots_sitemap, performance_check, keyword_analysis,
    local_seo_check, meta_check, heading_check, image_check, link_check,
    schema_check, url_structure, internal_links, canonical_check,
    content_quality, accessibility_check, mobile_friendly_check,
    backlinks_check, analytics_check
]

class SEOSpider(scrapy.Spider):
    name = "seo_spider"

    custom_settings = {
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "CONCURRENT_REQUESTS": 2,
        "DOWNLOAD_DELAY": 3,
        "LOG_LEVEL": "INFO",
    }

    def __init__(self, start_url=None, max_pages_config=25, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not start_url:
            raise ValueError("start_url must be provided")
        self.start_urls = [start_url]
        self.allowed_domains = [urlparse(start_url).netloc]
        self.max_pages = max_pages_config
        self.pages_crawled = 0
        self.visited = set()

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"Starting crawl at {url}")
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "download_timeout": 60,
                },
                callback=self.parse,
                errback=self.errback,
            )

    async def parse(self, response):
        url = response.url

        if url in self.visited:
            self.logger.debug(f"Skipping visited URL: {url}")
            return
        if self.pages_crawled >= self.max_pages:
            self.logger.info(f"Reached max pages limit: {self.max_pages}")
            return

        self.visited.add(url)
        self.pages_crawled += 1
        self.logger.info(f"Crawling page {self.pages_crawled}: {url}")

        page = response.meta['playwright_page']
        await page.wait_for_selector('body', timeout=15000)
        html_content = await page.content()
        await page.close()

        # Run all 18 SEO checks
        check_results = {}
        for check_module in ALL_CHECKS_MODULES:
            try:
                # Assuming each module exposes an async run(url, html_content) function
                result = await check_module.run(url, html_content)
                check_results[check_module.__name__] = result
            except Exception as e:
                self.logger.error(f"Check {check_module.__name__} failed on {url}: {e}")
                check_results[check_module.__name__] = {"error": str(e)}

        page_data = {
            "url": url,
            "status_code": response.status,
            "checks": check_results,
            "is_crawlable": response.status == 200
        }

        yield page_data

        if self.pages_crawled >= self.max_pages:
            return

        base_url = f"{url.split('?')[0].rstrip('/')}"
        hrefs = response.css('a::attr(href)').getall()
        for href in hrefs:
            if not href:
                continue
            absolute_url = urljoin(base_url, href.strip())
            parsed_href = urlparse(absolute_url)
            if parsed_href.scheme not in ("http", "https"):
                continue
            if parsed_href.netloc != self.allowed_domains[0]:
                continue
            if absolute_url in self.visited:
                continue

            yield scrapy.Request(
                absolute_url,
                meta={
                    "playwright": True,
                    "download_timeout": 60,
                },
                callback=self.parse,
                errback=self.errback,
            )

    async def errback(self, failure):
        self.logger.warning(f"Request failed: {failure.request.url} with exception {repr(failure.value)}")
    
