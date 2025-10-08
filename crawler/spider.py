import scrapy
from urllib.parse import urlparse, urljoin
import logging
from checks import *

ALL_CHECKS_MODULES = [
    sslcheck, robotssitemap, performancecheck, keywordanalysis,
    localseocheck, metacheck, headingcheck, imagecheck, linkcheck,
    schemacheck, urlstructure, internallinks, canonicalcheck,
    contentquality, accessibilitycheck, mobilefriendlycheck,
    backlinkscheck, analyticscheck
]

class SEOSpider(scrapy.Spider):
    name = "seospider"
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
        "LOG_LEVEL": "INFO"
    }

    def __init__(self, starturl=None, maxpagesconfig=25, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not starturl:
            raise ValueError("starturl must be provided")
        self.starturls = [starturl]
        self.allowed_domains = [urlparse(starturl).netloc]
        self.maxpages = maxpagesconfig
        self.pagescrawled = 0
        self.visited = set()

    def start_requests(self):
        for url in self.starturls:
            self.logger.info(f"Starting crawl at url: {url}")
            yield scrapy.Request(
                url,
                meta={"playwright": True, "download_timeout": 60},
                callback=self.parse,
                errback=self.errback,
            )

    async def parse(self, response):
        url = response.url
        if url in self.visited:
            self.logger.debug(f"Skipping visited URL {url}")
            return
        if self.pagescrawled >= self.maxpages:
            self.logger.info(f"Reached max pages limit {self.maxpages}")
            return
        self.visited.add(url)
        self.pagescrawled += 1
        self.logger.info(f"Crawling page {self.pagescrawled}: {url}")

        page = response.meta.get("playwright_page")
        if page:
            await page.wait_for_selector("body", timeout=15000)
            html_content = await page.content()
            await page.close()
        else:
            html_content = response.text

        checkresults = {}
        # Run all checks async where possible, otherwise fallback to sync
        for checkmodule in ALL_CHECKS_MODULES:
            try:
                result = await checkmodule.run_url(url, html_content) if hasattr(checkmodule, "async_run_url") else checkmodule.run_url(url, html_content)
                checkresults[checkmodule.__name__] = result
            except Exception as e:
                self.logger.error(f"Check {checkmodule.__name__} failed on URL {url}: {str(e)}")
                checkresults[checkmodule.__name__] = {"error": str(e)}

        pagedata = {
            "url": url,
            "statuscode": response.status,
            "checks": checkresults,
            "iscrawlable": response.status == 200
        }
        yield pagedata

        # Enqueue more URLs (limit to domain and not previously visited)
        baseurl = url.split("?")[0].rstrip("/")
        hrefs = response.css("a::attr(href)").getall()
        for href in hrefs:
            if not href:
                continue
            absolute_url = urljoin(baseurl, href.strip())
            parsed_href = urlparse(absolute_url)
            if parsed_href.scheme not in ("http", "https") or parsed_href.netloc != self.allowed_domains[0]:
                continue
            if absolute_url in self.visited:
                continue
            yield scrapy.Request(absolute_url, meta={"playwright": True, "download_timeout": 60}, callback=self.parse, errback=self.errback)

    async def errback(self, failure):
        self.logger.warning(f"Request failed for {failure.request.url} with exception: {repr(failure.value)}")
        
