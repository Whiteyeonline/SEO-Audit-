import os, json, logging
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from crawler.spider import SEOSpider
from utils.reportwriter import writesummaryreport, getcheckaggregation
from checks import *
ALL_CHECKS_MODULES = [
    sslcheck, robotssitemap, performancecheck, keywordanalysis,
    localseocheck, metacheck, headingcheck, imagecheck, linkcheck,
    schemacheck, urlstructure, internallinks, canonicalcheck,
    contentquality, accessibilitycheck, mobilefriendlycheck,
    backlinkscheck, analyticscheck
]

CUSTOM_SETTINGS = {
    "USER_AGENT": "ProfessionalSEOAgency",
    "ROBOTSTXT_OBEY": False,
    "LOG_LEVEL": "INFO",
    "DOWNLOAD_TIMEOUT": 60,
    "CLOSESPIDER_PAGECOUNT": 250,
    "TELNETCONSOLE_ENABLED": False,
    "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    "DOWNLOAD_HANDLERS": {
        "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler"
    },
    "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True, "timeout": 60000},
    "FEED_FORMAT": "json",
    "FEED_URI": "reports/crawlresults.json",
    "FEED_EXPORT_ENCODING": "utf-8",
    "CONCURRENT_REQUESTS": 2,
    "DOWNLOAD_DELAY": 3.0,
}

def main():
    try:
        AUDIT_URL = os.environ['AUDITURL']
        AUDIT_LEVEL = os.environ.get('AUDITLEVEL', 'basic')
        COMPETITOR_URL = os.environ.get('COMPETITORURL')
        AUDIT_SCOPE = os.environ.get('AUDITSCOPE', 'onlyonpage')
    except KeyError:
        print("Error: AUDITURL environment variable is not set.")
        return

    os.makedirs("reports", exist_ok=True)
    settings = Settings(CUSTOM_SETTINGS)
    if AUDIT_SCOPE == "onlyonpage":
        settings.set("CLOSESPIDER_PAGECOUNT", 1)
    process = CrawlerProcess(settings)
    maxpagescount = settings.getint("CLOSESPIDER_PAGECOUNT")
    process.crawl(SEOSpider, starturl=AUDIT_URL, maxpagesconfig=maxpagescount)
    print(f"Starting SEO Audit for {AUDIT_URL}...")
    print(f"Scope: {AUDIT_SCOPE} Max pages: {maxpagescount}")
    process.start()

    crawlfilepath = CUSTOM_SETTINGS["FEED_URI"]
    if os.path.exists(crawlfilepath) and os.path.getsize(crawlfilepath) > 0:
        try:
            with open(crawlfilepath, "r", encoding="utf-8") as f:
                crawlresults = json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding crawlresults JSON: {e}")
            print("FATAL ERROR: Failed to read crawlresults file. Aborting report generation.")
            return
    else:
        print("WARNING: Crawlresults file is missing or empty. This indicates the spider may have failed to crawl any pages.")
        return

    initialchecks = [item for item in crawlresults if item.get("url") and item.get("iscrawlable", True)]
    crawledpages = [item for item in crawlresults if item.get("url") and not item.get("initialcheck")]
    totalpagescrawled = len(crawledpages)
    if totalpagescrawled == 0 and not initialchecks:
        print("Crawl finished, but no pages were successfully scraped beyond initial checks.")
        return

    aggregation = getcheckaggregation(crawledpages)
    structuredreportdata = {
        "auditdetails": {
            "targeturl": AUDIT_URL, "auditlevel": AUDIT_LEVEL,
            "competitorurl": COMPETITOR_URL, "auditscope": AUDIT_SCOPE,
        },
        "finalscore": None,
        "crawledpages": crawledpages,
        "totalpagescrawled": totalpagescrawled,
        "aggregatedissues": aggregation,
        "basicchecks": initialchecks,
        "performancecheck": {}, # Optionally insert performance checks here
    }
    structuredfilepath = "reports/seoaudit_structured_report.json"
    with open(structuredfilepath, "w", encoding="utf-8") as f:
        json.dump(structuredreportdata, f, indent=4)
    print(f"Structured report saved to {structuredfilepath}")

    markdownfilepath = "reports/seoprofessional_report.md"
    writesummaryreport(structuredreportdata, None, markdownfilepath)
    print(f"Summary report saved to {markdownfilepath}")
    print(f"Total pages crawled: {totalpagescrawled}")

if __name__ == "__main__":
    main()
    
