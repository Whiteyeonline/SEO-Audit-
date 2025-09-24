import json
import asyncio
from playwright.sync_api import sync_playwright

def run(url, html_content=None):
    """
    Measures page performance using Playwright to get key timing metrics.
    """
    results = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Use page.evaluate to get performance metrics from the browser
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
            
            # Calculate key metrics
            dom_complete = metrics['loadEventEnd'] - metrics['fetchStart']
            dom_interactive = metrics['domContentLoadedEventEnd'] - metrics['fetchStart']
            
            results = {
                "load_time_ms": int(dom_complete),
                "dom_interactive_ms": int(dom_interactive),
                "note": "This is a basic performance check. For full Core Web Vitals, a dedicated tool is needed. This provides foundational speed metrics."
            }

            browser.close()
            return results
    except Exception as e:
        print(f"Performance check failed: {e}")
        return {"error": str(e)}

if __name__ == '__main__':
    # This block is for local testing of the script
    test_url = "https://example.com"
    performance_data = run(test_url)
    print(json.dumps(performance_data, indent=2))
          
