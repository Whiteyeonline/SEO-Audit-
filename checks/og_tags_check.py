# utils/og_tags_check.py
from bs4 import BeautifulSoup
import asyncio

async def run(page):
    """
    Checks if essential Open Graph and Twitter Card tags exist and are correctly set.
    Works with dynamic JS-rendered pages.
    Returns:
        {
            "og_tags_missing": bool,
            "missing_tags_list": list,
            "og_title": str,
            "og_description": str,
            "og_image": str,
            "og_url": str,
            "note": str
        }
    """
    result = {
        "og_tags_missing": False,
        "missing_tags_list": [],
        "og_title": "",
        "og_description": "",
        "og_image": "",
        "og_url": "",
        "note": ""
    }

    try:
        # Wait until the full page is loaded (for JS-based sites)
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(1.5)  # Let scripts populate meta tags

        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')

        # --- Check essential OG tags ---
        essential_tags = {
            "og:title": None,
            "og:description": None,
            "og:image": None,
            "og:url": None
        }

        for tag in essential_tags:
            meta = soup.find('meta', attrs={'property': tag})
            if not meta or not meta.get('content') or not meta['content'].strip():
                result["missing_tags_list"].append(tag)
            else:
                result[tag.replace(':', '_')] = meta['content'].strip()

        # --- Check Twitter card tags too (extra professional touch) ---
        twitter_tags = ["twitter:title", "twitter:description", "twitter:image", "twitter:card"]
        for tag in twitter_tags:
            meta = soup.find('meta', attrs={'name': tag})
            if not meta or not meta.get('content') or not meta['content'].strip():
                if tag not in result["missing_tags_list"]:
                    result["missing_tags_list"].append(tag)

        # --- Determine status ---
        if len(result["missing_tags_list"]) > 0:
            result["og_tags_missing"] = True
            result["note"] = f"Missing or incomplete tags: {', '.join(result['missing_tags_list'])}"
        else:
            result["og_tags_missing"] = False
            result["note"] = "All essential OG and Twitter tags found."

        return result

    except Exception as e:
        result["og_tags_missing"] = True
        result["note"] = f"Error during OG tag check: {str(e)}"
        return result
