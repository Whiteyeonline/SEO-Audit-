import json
from playwright.sync_api import sync_playwright
def run(url, html_content=None):
    results = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url)
            metrics = page.evaluate("""() => {
                const navTiming = performance.getEntriesByType('navigation')[0];
                return {
                    fetchStart: navTiming.fetchStart,
                    responseEnd: navTiming.responseEnd,
                    domContentLoadedEventEnd: navTiming.domContentLoadedEventEnd,
                    loadEventEnd: navTiming.loadEventEnd
                };
            }""")
            dom_complete = metrics['loadEventEnd'] - metrics['fetchStart']
            dom_interactive = metrics['domContentLoadedEventEnd'] - metrics['fetchStart']
            results = {"load_time_ms": int(dom_complete), "dom_interactive_ms": int(dom_interactive)}
            browser.close()
            return results
    except Exception as e:
        return {"error": str(e)}
