# checks/local_seo.py
import re
import json

def extract_schema(response):
    """Extracts JSON-LD schema from the response."""
    schemas = []
    for script in response.css('script[type="application/ld+json"]::text').getall():
        try:
            schemas.append(json.loads(script))
        except json.JSONDecodeError:
            pass
    return schemas

def extract_nap(content):
    """Basic extraction of NAP indicators."""
    # Simple regex for phone number detection (common US/International format)
    phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', content)
    # Simple check for common address indicators
    address_match = re.search(r'\d+ .*?(street|avenue|road|st|ave|rd|blvd|suite|unit)', content, re.IGNORECASE)
    
    return {
        'address_found': bool(address_match),
        'phone_found': bool(phone_match),
    }

def run_checks(response, content, level):
    """Runs local SEO checks."""
    
    results = {}
    
    # 1. NAP Consistency Check (Standard/Advanced)
    if level in ['standard', 'advanced']:
        nap_data = extract_nap(content)
        
        nap_result = 'Pass'
        nap_message = "Basic NAP markers (Address and Phone) appear to be present on the page."
        if not nap_data['address_found'] and not nap_data['phone_found']:
            nap_result = 'Fail'
            nap_message = "❌ Critical: No clear Address or Phone number found on the page."
        elif not nap_data['address_found'] or not nap_data['phone_found']:
            nap_result = 'Warning'
            nap_message = "Partial NAP: Either Address or Phone number is missing. Ensure NAP is consistent."
            
        results['nap_consistency'] = {'result': nap_result, 'message': nap_message}
        
    # 2. Local Schema Markup Check (Advanced Level)
    if level == 'advanced':
        schemas = extract_schema(response)
        local_schema_found = False
        
        for schema in schemas:
            types = [s.get('@type') for s in (schema if isinstance(schema, list) else [schema])]
                
            if any(t in ['LocalBusiness', 'Organization', 'Restaurant', 'Service'] for t in types):
                local_schema_found = True
                break
                
        schema_result = 'Pass'
        schema_message = "LocalBusiness, Organization, or relevant local schema markup found."
        if not local_schema_found:
            schema_result = 'Warning'
            schema_message = "No relevant Local/Organization Schema Markup (JSON-LD) found. Recommended for Local SEO visibility."
            
        results['local_schema'] = {'result': schema_result, 'message': schema_message}
        
    return results
        
