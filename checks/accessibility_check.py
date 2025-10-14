# checks/accessibility_check.py
from bs4 import BeautifulSoup

def run_audit(response, audit_level):
    """
    Performs foundational accessibility checks, primarily focusing on the 
    HTML language declaration.
    
    This check uses the fully rendered HTML provided by the Spider (Scrapy-Playwright).
    """
    try:
        # Use response.body for robust, encoding-safe parsing of the rendered HTML
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to parse content for accessibility check: {str(e)}"}
    
    issues = []
    
    # 1. HTML Lang Attribute Check (CRITICAL)
    html_tag = soup.find('html')
    lang_attribute = html_tag.get('lang') if html_tag else None
    
    lang_found = False
    
    if not html_tag:
        issues.append({"type": "error", "check": "Missing <html> Tag", "details": "The HTML document structure is invalid or missing."})
    elif not lang_attribute:
        issues.append({"type": "error", "check": "Missing or Empty `lang` Attribute", "details": "The `<html lang=\"...\">` attribute is required for accessibility and multilingual SEO."})
    elif lang_attribute:
        # Check if the attribute is present and not just an empty string
        lang_code = lang_attribute.strip()
        if not lang_code:
             issues.append({"type": "error", "check": "Empty `lang` Attribute", "details": "The `<html lang=\"...\">` attribute value is empty."})
        else:
            lang_found = True

    # 2. Basic ARIA Check (Presence of ARIA is an indicator of effort)
    # Check for presence of `role` attribute or other ARIA attributes
    aria_found = bool(soup.find(attrs={"role": True})) or bool(soup.find(attrs=lambda x: x and x.startswith('aria-')))
    
    
    # Final Summary Note
    if not issues:
        note = f"PASS: Found valid lang attribute: `{lang_attribute}`. ARIA usage: {'Yes' if aria_found else 'No'}"
    else:
        note = "FAIL: Critical accessibility issue(s) found. Check details."

    return {
        "html_lang_attribute": lang_attribute if lang_found else "MISSING",
        "aria_attributes_found": aria_found,
        "accessibility_issues_count": len(issues),
        "accessibility_issues_list": issues,
        "note": note
    }
    
