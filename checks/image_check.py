from bs4 import BeautifulSoup

# FIX: Changed function name and arguments to match the spider's requirement
def run_audit(response, audit_level):
    """
    Checks all images for the presence of the alt attribute.
    
    The audit_level argument is mandatory but not used in this specific check.
    """
    # Use response.text to get the HTML content
    soup = BeautifulSoup(response.text, "lxml")
    
    imgs = soup.find_all("img")
    
    # Only count images that have a source attribute (i.e., real images)
    # Checks if 'alt' is missing or empty (img.get("alt") returns None or "")
    missing_alt = [
        img.get("src") 
        for img in imgs 
        if img.get("src") and not img.get("alt")
    ]
    
    return {
        "total_images": len(imgs), 
        "missing_alt_images_count": len(missing_alt), 
        "missing_alt_list": missing_alt,
        "note": "Alt text is crucial for accessibility and image search SEO."
    }
    
