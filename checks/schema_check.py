# checks/schema_check.py
from bs4 import BeautifulSoup
import json
import re

def run_audit(response, audit_level):
    """
    Identifies all script tags that contain JSON-LD (Schema.org) markup
    and attempts to extract the primary type found.
    
    This check uses the fully rendered HTML provided by the Spider (Scrapy-Playwright).
    """
    try:
        # 💡 FIX: Use response.body for robust, encoding-safe parsing of the rendered HTML
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to parse content for schema check: {str(e)}"}
    
    # 1. Look for application/ld+json script tags (most common format)
    schema_tags = soup.find_all("script", type="application/ld+json")
    
    found_types = []
    
    for tag in schema_tags:
        # Get the string content of the script tag
        tag_content = tag.string if tag.string else ""
        
        # Clean up common issues like newlines or leading/trailing whitespace
        clean_content = tag_content.strip()

        if clean_content:
            try:
                # Attempt to parse the JSON content
                data = json.loads(clean_content)
                
                # Check for array of schemas (multiple schemas in one script block)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and '@type' in item:
                            found_types.append(item['@type'])
                
                # Check for a single schema object
                elif isinstance(data, dict) and '@type' in data:
                    schema_type = data['@type']
                    # Handle single type or array of types (e.g., '@type': ['Article', 'NewsArticle'])
                    if isinstance(schema_type, list):
                        found_types.extend(schema_type)
                    else:
                        found_types.append(schema_type)
                
            except json.JSONDecodeError:
                # If JSON parsing fails, note that schema was present but invalid
                found_types.append("Invalid JSON-LD")
            except Exception as e:
                # Catch all other exceptions
                found_types.append(f"JSON-LD Error: {type(e).__name__}")
                
    # Use a set to get unique types and sort for clean reporting
    unique_types = sorted(list(set(found_types)))

    # Determine the status
    if len(unique_types) > 0:
        status_note = f"PASS: Schema found. Primary types detected: {', '.join(unique_types[:3])}"
    else:
        status_note = "INFO: No application/ld+json Schema found. Consider adding appropriate structured data."
        
    return {
        "schema_types_found": unique_types, 
        "total_schemas_found": len(unique_types),
        "note": status_note
    }
    
