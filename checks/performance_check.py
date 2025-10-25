# utils/performance_check.py
import asyncio
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse

async def run(page):
    """
    Analyzes page performance metrics such as:
    - TTFB (Time to First Byte)
    - Total load time
    - Page size (approx)
    - Render performance (basic score)
    Works entirely offline — no paid APIs.
    """

    result = {
        "desktop_score": {"result": "Pass", "message": ""},
        "mobile_score": {"result": "Pass", "message": ""},
        "page_size_kb": 0,
        "load_time": 0,
        "note": ""
    }

    try:
        # Start timing
        start_time = time.time()

        # Measure network response time (TTFB)
        req_start = time.time()
        await page.goto(page.url, wait_until='domcontentloaded')
        req_end = time.time()
        ttfb = req_end - req_start

        # Wait for full load and get content
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(1.5)
        html = await page.content()

        end_time = time.time()
        total_load = end_time - start_time

        # --- Estimate page size ---
        size_kb = len(html.encode('utf-8')) / 1024

        # --- Quick DOM complexity check ---
        soup = BeautifulSoup(html, 'html.parser')
        tag_count = len(soup.find_all())
        image_count = len(soup.find_all('img'))

        # --- Simple scoring logic ---
        if ttfb > 2.0 or total_load > 6.0 or size_kb > 2000:
            desktop_result = "Fail"
        elif ttfb > 1.5 or total_load > 4.0 or size_kb > 1500:
            desktop_result = "Warn"
        else:
            desktop_result = "Pass"

        # Mobile is more sensitive
        if ttfb > 1.5 or total_load > 4.5 or size_kb > 1500:
            mobile_result = "Fail"
        else:
            mobile_result = desktop_result

        result["desktop_score"]["result"] = desktop_result
        result["mobile_score"]["result"] = mobile_result
        result["desktop_score"]["message"] = f"TTFB: {ttfb:.2f}s, Load: {total_load:.2f}s, Size: {size_kb:.1f}KB"
        result["mobile_score"]["message"] = f"TTFB: {ttfb:.2f}s, Load: {total_load:.2f}s, Size: {size_kb:.1f}KB"

        result["page_size_kb"] = round(size_kb, 1)
        result["load_time"] = round(total_load, 2)
        result["note"] = (
            f"TTFB: {ttfb:.2f}s | Load: {total_load:.2f}s | "
            f"Elements: {tag_count} | Images: {image_count} | Size: {size_kb:.1f}KB"
        )

        return result

    except Exception as e:
        result["desktop_score"]["result"] = "Fail"
        result["mobile_score"]["result"] = "Fail"
        result["note"] = f"Error during performance test: {str(e)}"
        return result
