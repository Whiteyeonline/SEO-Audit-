from bs4 import BeautifulSoup
import textstat

def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    text = soup.get_text(separator=' ', strip=True)
    word_count = len(text.split())
    readability = textstat.flesch_reading_ease(text)
    return {"word_count": word_count, "readability_score": readability}
