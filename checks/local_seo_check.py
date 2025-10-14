# checks/local_seo_check.py
from bs4 import BeautifulSoup
import json
import re

def run_audit(response, audit_level) -> dict:
    """
    Performs Local SEO checks on a single page, focusing on Schema.org,
    and presence of key local information (NAP: Name, Address, Phone).
    
    This check uses the fully rendered HTML provided by the Spider (Scrapy-Playwright).
    """
    results = {
        "check_name": "Local SEO & Business Info Check",
        "url": response.url,
        "status": "PASS", 
        "issues": [],
        "details": {},
        "nap_fail_count": 0
    }

    try:
        # Use response.body for robust, encoding-safe parsing of the rendered HTML
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
        
        # --- Check 1: Schema.org LocalBusiness Markup ---
        schema_status = "No Relevant Schema Found"
        
        # Look for application/ld+json script tags
        schema_tags = soup.find_all("script", type="application/ld+json")
        
        for tag in schema_tags:
            content = tag.string.strip() if tag.string else ""
            if not content:
                continue

            try:
                data = json.loads(content)
                
                # Normalize data check (handle single object or array of objects)
                items_to_check = data if isinstance(data, list) else [data]
                
                for item in items_to_check:
                    if isinstance(item, dict) and '@type' in item:
                        schema_type = item['@type']
                        
                        # Prioritize LocalBusiness, then Organization
                        if 'LocalBusiness' in schema_type:
                            schema_status = "LocalBusiness Schema Found (PASS)"
                            break
                        elif 'Organization' in schema_type:
                            schema_status = "Organization Schema Found (Warning: LocalBusiness preferred)"
                if "LocalBusiness" in schema_status:
                    break
                        
            except json.JSONDecodeError:
                continue
        
        results["details"]["schema_status"] = schema_status
        if "Organization" in schema_status and "LocalBusiness" not in schema_status:
            results["status"] = "WARNING"
            results["issues"].append({"type": "warning", "message": "LocalBusiness Schema preferred for local pages, only Organization found."})
        elif "No Relevant Schema Found" in schema_status:
            results["status"] = "WARNING"
            results["issues"].append({"type": "warning", "message": "Missing Schema.org markup (LocalBusiness or Organization) for local context."})


        # --- Check 2: NAP (Name, Address, Phone) Presence ---
        # Get the full *visible* text content (after stripping noise)
        for script_or_style in soup(["script", "style", "header", "footer", "nav", "noscript"]):
            script_or_style.decompose()
        full_text = soup.get_text(separator=' ', strip=True).lower()
        
        
        # Simple regex for finding key NAP components (high false positive rate, but good for flags)
        nap_found = {
            "address": bool(re.search(r'\b(street|road|avenue|av\b|st\b|rd\b|ln\b|p\.o\.|zip code|postal code)', full_text)),
            "phone": bool(re.search(r'\b(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b(tel|phone|call)\b)', full_text)),
            "email": bool(re.search(r'\b(\S+@\S+\.\S+)\b', full_text))
        }
        
        # Count critical NAP items found (Address, Phone)
        critical_nap_found = nap_found["address"] + nap_found["phone"]
        
        if critical_nap_found < 2:
            results["status"] = "FAIL" # Downgrade to FAIL if NAP is critically missing
            results["nap_fail_count"] = 1
            results["issues"].append({"type": "error", "message": "Critical NAP information (Address/Phone) is missing from the visible page content."})
            results["details"]["nap_status"] = f"NAP components found: Address ({nap_found['address']}), Phone ({nap_found['phone']}), Email ({nap_found['email']})."
        else:
            results["details"]["nap_status"] = "Address and Phone keywords are present on the page."

        if not results["issues"]:
            results["details"]["message"] = "Local Schema found or Organization Schema found, and key NAP elements are present."

    except Exception as e:
        results["status"] = "ERROR"
        results["issues"].append({"type": "error", "message": f"An error occurred during local SEO check: {e}"})

    return results
                
