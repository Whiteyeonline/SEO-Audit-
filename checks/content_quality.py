from bs4 import BeautifulSoup
import textstat

def run(url, html_content):
    """Analyzes content length and basic readability."""
    soup = BeautifulSoup(html_content, "lxml")
    
    # Strip scripts, styles, and other noise
    for script_or_style in soup(["script", "style", "header", "footer", "nav"]):
        script_or_style.decompose()

    text = soup.get_text(separator=' ', strip=True)
    word_count = len(text.split())
    
    try:
        readability = textstat.flesch_reading_ease(text)
    except:
        readability = "N/A (Text too short for reliable score)"

    return {
        "word_count": word_count, 
        "readability_score": readability,
        "note": "Flesch Reading Ease: Higher score is easier to read."
    }
    
