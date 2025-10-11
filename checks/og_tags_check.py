# checks/og_tags_check.py

"""
Open Graph (OG) Tags Check Module
Checks for the presence of essential Open Graph meta tags.
"""

def run_check(response, page_data, report_data):
    """
    Runs the OG Tags check on the given response.
    """
    check_name = "og_tags_check"
    report_data[check_name] = {
        "status": "PASS",
        "description": "Checks for essential Open Graph meta tags (og:title, og:type, og:image, og:url).",
        "details": [],
        "score_impact": 0
    }

    # XPath to select Open Graph meta tags
    # property attribute is often used for OG tags
    og_tags = response.xpath('//meta[starts-with(@property, "og:")]')
    
    # Extract existing OG properties for easy lookup
    existing_og_properties = {tag.attrib.get('property'): tag.attrib.get('content') 
                              for tag in og_tags if tag.attrib.get('property')}

    required_tags = ['og:title', 'og:type', 'og:image', 'og:url']
    missing_tags = [tag for tag in required_tags if tag not in existing_og_properties]
    
    if missing_tags:
        report_data[check_name]['status'] = "FAIL"
        report_data[check_name]['score_impact'] = -15  # Negative impact for missing tags
        report_data[check_name]['details'].append(
            f"Missing essential Open Graph tags: {', '.join(missing_tags)}."
        )
        report_data[check_name]['description'] = "FAIL: Essential Open Graph tags are missing or incomplete."
    else:
        report_data[check_name]['details'].append(
            "All essential Open Graph tags (og:title, og:type, og:image, og:url) are present."
        )
        
    return report_data
  
