# checks/og_tags_check.py
from bs4 import BeautifulSoup
import re

def run_audit(response, audit_level):
    """
    Runs the Open Graph (OG) Tags and Twitter Card check.
    Ensures essential tags are present for robust social media sharing previews.
    
    This check uses the fully rendered HTML provided by the Spider (Scrapy-Playwright).
    """
    try:
        # 💡 FIX: Use response.body for robust, encoding-safe parsing of the rendered HTML
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to parse content for OG tags check: {str(e)}"}
    
    # 1. Open Graph (OG) Tags Check
    # Find all meta tags where the 'property' attribute starts with 'og:'
    og_tags = soup.find_all('meta', property=lambda value: value and value.startswith('og:'))
    
    existing_og_properties = {tag.get('property'): tag.get('content') 
                              for tag in og_tags if tag.get('property')}

    # The 4 essential tags for a good preview
    required_og_tags = ['og:title', 'og:type', 'og:image', 'og:url']
    missing_og_tags = [tag for tag in required_og_tags if not existing_og_properties.get(tag)]
    
    og_tags_missing = bool(missing_og_tags)

    # 2. Twitter Card Tags Check
    # Find all meta tags where the 'name' attribute starts with 'twitter:'
    twitter_tags = soup.find_all('meta', name=lambda value: value and value.startswith('twitter:'))
    
    existing_twitter_properties = {tag.get('name'): tag.get('content') 
                                   for tag in twitter_tags if tag.get('name')}

    # The 3 essential tags for a Twitter Summary Card with Large Image
    required_twitter_tags = ['twitter:card', 'twitter:title', 'twitter:image']
    missing_twitter_tags = [tag for tag in required_twitter_tags if not existing_twitter_properties.get(tag)]
    
    twitter_tags_missing = bool(missing_twitter_tags)

    # 3. Overall Status and Note
    missing_all = missing_og_tags + missing_twitter_tags
    
    if og_tags_missing:
        note = f"FAIL: Missing essential OG tags: {', '.join(missing_og_tags)}. Critical for Facebook/LinkedIn previews."
        if missing_twitter_tags:
            note += f" Also missing Twitter tags: {', '.join(missing_twitter_tags)}."
    elif twitter_tags_missing:
         note = f"WARNING: OG tags are present, but missing essential Twitter tags: {', '.join(missing_twitter_tags)}."
    else:
        note = "PASS: All essential Open Graph and Twitter Card tags are present for robust social sharing."
        
    return {
        "og_tags_missing": og_tags_missing,
        "missing_og_tags": missing_og_tags,
        "twitter_tags_missing": twitter_tags_missing,
        "missing_twitter_tags": missing_twitter_tags,
        "total_missing_tags": len(missing_all),
        "note": note
    }
    
