from textblob import TextBlob
from collections import Counter
from bs4 import BeautifulSoup

def run(url, html_content):
    """
    Extracts top keywords using TextBlob.
    """
    soup = BeautifulSoup(html_content, "lxml")
    text = soup.get_text(separator=' ', strip=True)
    
    blob = TextBlob(text)
    
    # Get word counts and exclude common stop words
    word_counts = Counter(blob.words.lower())
    
    # Get the 10 most common words
    top_keywords = word_counts.most_common(10)

    return {"top_keywords": top_keywords, "note": "Keyword analysis performed using TextBlob."}
    
