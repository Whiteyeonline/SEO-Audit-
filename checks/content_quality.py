# checks/content_quality.py
from bs4 import BeautifulSoup
import textstat
# NOTE: textstat requires the nltk and textblob dependencies to be installed
# (as confirmed in the main.py file imports and GitHub Actions file)

def run_audit(response, audit_level):
    """
    Analyzes content length and basic readability using the Scrapy response object.
    
    It also determines if the content is "thin" based on a word count threshold.
    This check uses the fully rendered HTML provided by the Spider (Scrapy-Playwright).
    """
    try:
        # 💡 FIX: Use response.body for robust, encoding-safe parsing of the rendered HTML
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to parse content for quality check: {str(e)}"}
    
    # Strip scripts, styles, and other noise to get clean, visible text
    for script_or_style in soup(["script", "style", "header", "footer", "nav", "noscript"]):
        script_or_style.decompose()

    text = soup.get_text(separator=' ', strip=True)
    
    # Clean up excessive whitespace created by decomposition
    clean_text = ' '.join(text.split())
    word_count = len(clean_text.split())
    
    # Determine if content is thin (commonly defined as < 200 words)
    thin_content_flag = word_count < 200

    readability = "N/A"
    readability_note = "Readability score N/A: Content too short or non-English."

    try:
        if word_count > 100: # Score is often unreliable for very short texts
            # Flesch Reading Ease: Higher score is easier to read (aim for 60-70)
            readability_score = textstat.flesch_reading_ease(clean_text)
            readability = f"{readability_score:.2f}"
            readability_note = f"Flesch Reading Ease: {readability}. Aim for 60-70 (College/High School level)."
        else:
            readability_note = "Flesch Reading Ease: Score skipped due to low word count (<100)."
    except Exception:
        # Catches exceptions like ZeroDivisionError or non-Latin alphabet issues
        readability = "N/A"
        
    final_note = f"Word Count: {word_count}. Below 200 words triggers a thin content warning."
    if thin_content_flag:
        final_note = f"WARNING: Thin content detected! Word count: {word_count}. Aim for over 300 words."
        
    return {
        "word_count": word_count, 
        "readability_score": readability,
        "thin_content": thin_content_flag,
        "readability_note": readability_note,
        "note": final_note
                                 }
    
