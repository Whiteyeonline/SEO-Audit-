# checks/meta_check.py
from bs4 import BeautifulSoup
import re

def run_audit(response, audit_level):
    """
    Checks for the presence and optimal length of the Title Tag and Meta Description.
    This check uses the fully rendered HTML provided by the Spider (Scrapy-Playwright).
    """
    try:
        # 💡 FIX: Use response.body for robust, encoding-safe parsing of the rendered HTML
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to parse content for meta check: {str(e)}"}


    # --- 1. Title Tag Check ---
    title = soup.find('title').get_text(strip=True) if soup.find('title') else ""
    title_length = len(title)
    
    title_fail = False
    title_check = "PASS"
    
    # Optimal length: 30-60 characters
    if title_length == 0:
        title_fail = True
        title_check = "MISSING"
    elif title_length < 30:
        title_fail = True
        title_check = "FAIL (Too Short)"
    elif title_length > 60:
        title_fail = True
        title_check = "FAIL (Too Long)"

    # --- 2. Meta Description Check ---
    # Find all meta tags named 'description' and prioritize the first one
    desc_tag = soup.find("meta", attrs={"name": "description"})
    
    # Use .get('content') defensively
    description = desc_tag.get("content").strip() if desc_tag and desc_tag.get("content") else ""
    desc_length = len(description)
    
    desc_fail = False
    desc_check = "PASS"
    
    # Optimal length: 120-158 characters (Modern SEO guidelines often allow up to 160)
    if desc_length == 0:
        desc_fail = True
        desc_check = "MISSING"
    elif desc_length < 120:
        desc_fail = True
        desc_check = "FAIL (Too Short)"
    elif desc_length > 158:
        desc_fail = True
        desc_check = "FAIL (Too Long)"

    return {
        "title_content": title,
        "title_length": title_length,
        "title_fail": title_fail,
        "title_check": title_check,
        
        "desc_content": description,
        "desc_length": desc_length,
        "desc_fail": desc_fail,
        "desc_check": desc_check
        }
        
