from bs4 import BeautifulSoup
import nltk
from collections import Counter
def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    text = soup.get_text(separator=' ', strip=True)
    words = nltk.word_tokenize(text.lower())
    freq = Counter(words).most_common(10)
    return {"top_keywords": freq, "note": "This is a basic keyword frequency check."}
  
