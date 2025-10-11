# checks/og_tags_check.py
from bs4 import BeautifulSoup

def run_audit(response, audit_level):
    """
    Runs the Open Graph (OG) Tags check.
    Checks for the presence of essential OG meta tags (og:title, og:type, og:image, og:url).
    """
    soup = BeautifulSoup(response.text, "lxml")
    
    og_tags = soup.find_all('meta', property=lambda value: value and value.startswith('og:'))
    
    existing_og_properties = {tag.get('property'): tag.get('content') 
                              for tag in og_tags if tag.get('property')}

    required_tags = ['og:title', 'og:type', 'og:image', 'og:url']
    missing_tags = [tag for tag in required_tags if tag not in existing_og_properties]
    
    og_tags_missing = bool(missing_tags)

    if og_tags_missing:
        note = f"FAIL: Missing essential Open Graph tags: {', '.join(missing_tags)}. This negatively impacts social sharing previews."
    else:
        note = "PASS: All essential Open Graph tags (og:title, og:type, og:image, og:url) are present."
        
    return {
        "og_tags_missing": og_tags_missing,
        "missing_tags_list": missing_tags,
        "note": note
    }
    
