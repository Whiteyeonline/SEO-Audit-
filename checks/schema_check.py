from bs4 import BeautifulSoup
import json
import re

# FIX: Changed function name and arguments to match the spider's requirement
def run_audit(response, audit_level):
    """
    Identifies all script tags that contain JSON-LD (Schema.org) markup
    and attempts to extract the primary type found.
    """
    # Use response.text to get the HTML content
    soup = BeautifulSoup(response.text, "lxml")
    
    # 1. Look for application/ld+json script tags
    schema_tags = soup.find_all("script", type="application/ld+json")
    
    found_types = []
    
    for tag in schema_tags:
        # Check if the tag content exists
        if tag.string:
            try:
                # Attempt to parse the JSON content
                data = json.loads(tag.string)
                
                # The primary type is usually found in the '@type' key
                if '@type' in data:
                    # Handle single type or array of types
                    schema_type = data['@type']
                    if isinstance(schema_type, list):
                        found_types.extend(schema_type)
                    else:
                        found_types.append(schema_type)
                
                # Check for multiple schemas in a single script (array of objects)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and '@type' in item:
                            found_types.append(item['@type'])
            except json.JSONDecodeError:
                # If JSON parsing fails, note that schema was present but invalid
                found_types.append("Invalid JSON-LD")
                
    # Use a set to get unique types
    unique_types = sorted(list(set(found_types)))

    # The audit_level argument is mandatory but not used in this specific check.
    return {
        "schema_types_found": unique_types, 
        "total_schemas_found": len(unique_types),
        "note": "Schema (Structured Data) helps search engines understand your content."
                    }
    
