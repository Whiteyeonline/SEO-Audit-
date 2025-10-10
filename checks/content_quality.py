from bs4 import BeautifulSoup
import textstat

# FIX: Changed function name and arguments to match the spider's requirement
def run_audit(response, audit_level):
    """
    Analyzes content length and basic readability using the Scrapy response object.
    
    It also determines if the content is "thin" based on a word count threshold.
    """
    # Use response.text to get the HTML content
    soup = BeautifulSoup(response.text, "lxml")
    
    # Strip scripts, styles, and other noise
    for script_or_style in soup(["script", "style", "header", "footer", "nav"]):
        script_or_style.decompose()

    text = soup.get_text(separator=' ', strip=True)
    word_count = len(text.split())
    
    # Determine if content is thin (commonly defined as < 200 words)
    thin_content_flag = word_count < 200

    try:
        # Flesch Reading Ease: Higher score is easier to read (aim for 60-70)
        readability = textstat.flesch_reading_ease(text)
    except:
        readability = "N/A (Text too short for reliable score)"

    # The audit_level argument is mandatory but not used in this specific check.
    return {
        "word_count": word_count, 
        "readability_score": readability,
        "thin_content": thin_content_flag,
        "note": "Flesch Reading Ease: Higher score is easier to read."
    }
    
