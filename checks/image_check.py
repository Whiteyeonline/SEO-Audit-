# checks/image_check.py
from bs4 import BeautifulSoup

def run_audit(response, audit_level):
    """
    Checks all visible <img> tags for the presence of the alt attribute.
    
    This check uses the fully rendered HTML provided by the Spider (Scrapy-Playwright).
    """
    try:
        # 💡 FIX: Use response.body for robust, encoding-safe parsing of the rendered HTML
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to parse content for image check: {str(e)}"}
    
    # Find all image tags
    imgs = soup.find_all("img")
    
    # 1. Filter out images that don't have a source (e.g., base64 or placeholder) and count the rest
    real_images = [
        img for img in imgs 
        if img.get("src") and img.get("src").strip() # Ensure src is present and not just whitespace
    ]
    
    # 2. Identify missing alt text: an image is flagged if 'alt' is missing or is an empty string
    missing_alt = [
        img.get("src") 
        for img in real_images 
        # alt is missing (None) OR alt is present but empty after stripping whitespace
        if not img.get("alt") or img.get("alt").strip() == "" 
    ]
    
    return {
        "total_images_count": len(real_images), 
        "missing_alt_images_count": len(missing_alt), 
        # Only return a sample of missing alt images for report brevity
        "sample_missing_alt_srcs": missing_alt[:5], 
        "note": "Alt text is crucial for accessibility and image search SEO. Empty alt (`alt=\"\"`) is acceptable for decorative images."
    }
    
