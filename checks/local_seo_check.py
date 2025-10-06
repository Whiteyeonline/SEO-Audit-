import json
from lxml import html
import re

def run(url: str, html_content: str) -> dict:
    """
    Performs Local SEO checks on a single page, focusing on Schema.org,
    and presence of key local information.
    
    :param url: The URL of the page being audited.
    :param html_content: The HTML content of the page.
    :return: A dictionary containing the local SEO audit results.
    """
    results = {
        "check_name": "Local SEO & Business Info Check",
        "url": url,
        "status": "Pass", 
        "issues": [],
        "details": {}
    }

    try:
        tree = html.fromstring(html_content)
        
        # --- Check 1: Schema.org LocalBusiness Markup ---
        # Look for script tags with application/ld+json containing "LocalBusiness"
        local_schema = tree.xpath('//script[@type="application/ld+json" and contains(., "LocalBusiness")]')
        
        if not local_schema:
            # Check for alternative types if LocalBusiness is not found, e.g., Organization
            org_schema = tree.xpath('//script[@type="application/ld+json" and contains(., "Organization")]')
            
            if org_schema:
                results["status"] = "Warning"
                results["issues"].append({"type": "warning", "message": "Missing LocalBusiness Schema.org markup. Organization Schema found, but LocalBusiness is preferred for local pages."})
                results["details"]["schema_status"] = "Organization Schema Found"
            else:
                results["status"] = "Warning"
                results["issues"].append({"type": "warning", "message": "Missing Schema.org markup (LocalBusiness or Organization) for local context."})
                results["details"]["schema_status"] = "No Relevant Schema Found"
        else:
            results["details"]["schema_status"] = "LocalBusiness Schema Found"

        # --- Check 2: NAP (Name, Address, Phone) Presence ---
        # This is a complex check, providing a simple keyword check placeholder
        
        # Simple keywords to check for contact details
        contact_keywords = ["address", "phone", "contact", "location"]
        found_keywords = [kw for kw in contact_keywords if re.search(r'\b' + kw + r'\b', html_content, re.IGNORECASE)]

        if len(found_keywords) < 2:
            results["details"]["nap_status"] = "Potential NAP information is sparse."
            # Only downgrade status if schema is also missing
            if results["status"] != "Warning":
                 results["status"] = "Info" 
            
        else:
            results["details"]["nap_status"] = f"Common contact keywords found: {', '.join(found_keywords)}"
        
        if not results["issues"]:
            results["details"]["message"] = "No critical Local SEO issues detected (Placeholder logic)."

    except Exception as e:
        results["status"] = "Error"
        results["issues"].append({"type": "error", "message": f"An error occurred during local SEO check: {e}"})

    return results
    
