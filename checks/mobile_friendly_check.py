# checks/mobile_friendly_check.py
from bs4 import BeautifulSoup
import asyncio
import re

async def run(page):
    """
    Checks if a web page is mobile-friendly.
    Detects viewport tags, font scaling, and responsive elements.
    Works for both static and JS-rendered websites.

    Returns:
        {
            "mobile_friendly": bool,
            "issues": list,
            "note": str
        }
    """
    result = {
        "mobile_friendly": True,
        "issues": [],
        "note": ""
    }

    try:
        # Wait for JS-rendered elements to load
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(1.5)

        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')

        # --- 1️⃣ Check viewport meta tag ---
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        if not viewport or 'width=device-width' not in str(viewport) or 'initial-scale' not in str(viewport):
            result["mobile_friendly"] = False
            result["issues"].append("Missing or incorrect viewport meta tag.")
            result["note"] += "Viewport tag missing or incomplete. "

        # --- 2️⃣ Check for fixed-width layout (bad for mobile) ---
        fixed_width_elements = soup.find_all(style=re.compile(r'width:\s*\d{3,}px'))
        if len(fixed_width_elements) > 0:
            result["mobile_friendly"] = False
            result["issues"].append(f"Fixed-width elements detected ({len(fixed_width_elements)}).")
            result["note"] += "Fixed pixel widths found; may not scale on mobile. "

        # --- 3️⃣ Check for small font sizes ---
        small_fonts = soup.find_all(style=re.compile(r'font-size:\s*(\d{1,2})px'))
        too_small = [font for font in small_fonts if int(re.search(r'font-size:\s*(\d{1,2})px', font.get('style')).group(1)) < 12]
        if len(too_small) > 0:
            result["mobile_friendly"] = False
            result["issues"].append(f"Small font sizes detected ({len(too_small)}).")
            result["note"] += "Fonts below 12px detected; may be hard to read on small screens. "

        # --- 4️⃣ Check for horizontal scrolling ---
        # Looks for large tables, overflowing divs, etc.
        overflow_elements = soup.find_all(style=re.compile(r'overflow(-x)?:\s*(scroll|auto|visible)'))
        if len(overflow_elements) > 0:
            result["mobile_friendly"] = False
            result["issues"].append(f"Elements with horizontal scroll ({len(overflow_elements)}).")
            result["note"] += "Detected scrollable sections that may break mobile layout. "

        # --- 5️⃣ Final assessment ---
        if result["mobile_friendly"]:
            result["note"] = "Page appears mobile-friendly. No major layout or scaling issues detected."

        return result

    except Exception as e:
        result["mobile_friendly"] = False
        result["issues"].append("Error during mobile-friendly check.")
        result["note"] = f"Error: {str(e)}"
        return result
