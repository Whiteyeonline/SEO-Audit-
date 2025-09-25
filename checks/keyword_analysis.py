from textblob import TextBlob
from collections import Counter
from bs4 import BeautifulSoup

def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    text = soup.get_text(separator=' ', strip=True)
    blob = TextBlob(text)
    counts = Counter(blob.words.lower())
    top = counts.most_common(10)
    return {"top_keywords": top}
