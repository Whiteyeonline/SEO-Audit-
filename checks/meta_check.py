from bs4 import BeautifulSoup
import re

# FIX: Changed function name and arguments to match the spider's requirement
def run_audit(response, audit_level):
    """
    Checks for the presence and optimal length of the Title Tag and Meta Description.
    """
    # Use response.text to get the HTML content
    soup = BeautifulSoup(response.text, "lxml")

    # --- 1. Title Tag Check ---
    title = soup.find('title').get_text(strip=True) if soup.find('title') else ""
    title_length = len(title)
    
    title_fail = False
    title_check = "PASS"
    
    # Optimal length: 30-60 characters
    if title_length == 0:
        title_fail = True
        title_check = "MISSING"
    elif title_length < 30 or title_length > 60:
        title_fail = True
        title_check = "FAIL (Length Issue)"

    # --- 2. Meta Description Check ---
    desc_tag = soup.find("meta", attrs={"name": "description"})
    # Use .get('content') defensively to handle tags with no content attribute
    description = desc_tag.get("content").strip() if desc_tag and desc_tag.get("content") else ""
    desc_length = len(description)
    
    desc_fail = False
    desc_check = "PASS"
    
    # Optimal length: 120-158 characters
    if desc_length == 0:
        desc_fail = True
        desc_check = "MISSING"
    elif desc_length < 120 or desc_length > 158:
        desc_fail = True
        desc_check = "FAIL (Length Issue)"

    # The audit_level argument is mandatory but not used in this specific check.
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
    
