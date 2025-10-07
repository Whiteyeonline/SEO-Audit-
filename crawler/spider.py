import scrapy
from scrapy_playwright.page import PageCoroutine
from urllib.parse import urlparse, urljoin
import logging


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
                    "playwright_page_coroutines": [
                        PageCoroutine("wait_for_selector", "body", timeout=15000)
                    ],
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

        page_data = {
            "url": url,
            "status_code": response.status,
            "is_crawlable": response.status == 200,
            "error_detail": None,
            "meta": {
                "title": response.css("title::text").get(default="").strip(),
                "description": response.css('meta[name="description"]::attr(content)').get(default="").strip(),
            },
            "headings": {
                "h1": len(response.css("h1")),
                "h2": len(response.css("h2")),
                "h3": len(response.css("h3")),
            },
            "links": {
                "internal": [],
                "external": [],
                "broken": [],  # Placeholder, to be filled after crawl if possible
            },
            "canonical": {
                "canonical_url": response.css('link[rel="canonical"]::attr(href)').get(default=""),
                "match": True,  # To be checked later with actual URL if needed
            },
            "images": {
                "total": len(response.css("img")),
                "missing_alt": len(response.xpath("//img[not(@alt)]")),
            },
            "content": {
                "word_count": len(response.xpath("//body//text()").getall()),
                "readability_score": "N/A (Calculated later)",
            },
            "mobile": {
                "mobile_friendly": True,  # Placeholder, requires separate check (Google API etc)
                "note": "",
                "issues": [],
            },
            "analytics": {
                "tracking_setup": {
                    "google_analytics_found": bool(response.xpath("//*[contains(@src, 'google-analytics.com')]")),
                    "google_tag_manager_found": bool(response.xpath("//*[contains(@src, 'googletagmanager.com')]")),
                }
            },
            "accessibility_issues": [],  # Placeholder, detailed accessibility checks later
            "keywords": {
                "density_check": {"result": "N/A", "message": ""},
                "placement_check": {"result": "N/A", "message": ""},
            },
        }

        # Extract internal and external links, filter and classify
        base_url = urljoin(url, '/')
        hrefs = response.css('a::attr(href)').getall()
        for href in hrefs:
            if not href:
                continue
            absolute_url = urljoin(url, href.strip())
            parsed_href = urlparse(absolute_url)

            if parsed_href.scheme not in ('http', 'https'):
                continue  # Skip non-http links
            if parsed_href.netloc == self.allowed_domains[0]:
                page_data['links']['internal'].append(absolute_url)
            else:
                page_data['links']['external'].append(absolute_url)

        yield page_data

        # Enqueue next internal links for crawling
        if self.pages_crawled < self.max_pages:
            for next_url in page_data['links']['internal']:
                if next_url not in self.visited:
                    yield scrapy.Request(
                        next_url,
                        meta={
                            "playwright": True,
                            "playwright_page_coroutines": [
                                PageCoroutine("wait_for_selector", "body", timeout=15000)
                            ],
                            "download_timeout": 60,
                        },
                        callback=self.parse,
                        errback=self.errback,
                    )

    async def errback(self, failure):
        self.logger.warning(f"Request failed: {failure.request.url} with exception {repr(failure.value)}")
    
