# checks/keyword_analysis.py
from textblob import TextBlob
from textstat.textstat import textstatistics
from bs4 import BeautifulSoup

STOP_WORDS = set(['the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'of', 'in', 'to', 'for', 'with', 'on', 'at', 'i', 'you', 'your', 'we', 'our', 'it'])

def get_word_frequency(text, top_n=10):
    """Calculates word frequency, excluding common stop words."""
    if not text:
        return []
    
    words = TextBlob(text.lower()).words
    words = [word for word in words if word.isalpha() and word not in STOP_WORDS]
    
    word_counts = {}
    for word in words:
        word_counts[word] = word_counts.get(word, 0) + 1

    sorted_counts = sorted(word_counts.items(), key=lambda item: item[1], reverse=True)
    return sorted_counts[:top_n]


def run_checks(title, description, content, h1_tags, level):
    """Runs all keyword reinforcement checks (The original logic)."""
    
    results = {}
    total_words = len(content.split())
    
    # 1. Word Frequency Check 
    top_keywords = get_word_frequency(content)
    results['top_keywords'] = [{'word': w[0], 'count': w[1]} for w in top_keywords]
    
    if not top_keywords or total_words == 0:
        results['density_check'] = {'result': 'Fail', 'message': 'No content found to analyze.'}
        return results

    primary_keyword = top_keywords[0][0]
    keyword_count = top_keywords[0][1]
    keyword_density = (keyword_count / total_words) * 100
    
    # 2. Density Check (Target: 1-3%)
    density_result = 'Pass'
    message = f"Density of primary keyword '{primary_keyword}' is {keyword_density:.2f}%."
    if keyword_density > 4.0:
        density_result = 'Warning'
        message += " Risk of keyword stuffing (over 4.0%)."
    elif keyword_density < 0.5:
        density_result = 'Warning'
        message += " Low keyword focus (below 0.5%)."
    
    results['density_check'] = {'result': density_result, 'message': message}
    
    # 3. Placement Check (Reinforce)
    placement_result = 'Pass'
    placement_message = []
    
    if primary_keyword.lower() not in (title or '').lower():
        placement_result = 'Warning'
        placement_message.append("Keyword missing from Title Tag.")
    
    if primary_keyword.lower() not in (description or '').lower():
        placement_result = 'Warning'
        placement_message.append("Keyword missing from Meta Description.")
        
    if not any(primary_keyword.lower() in h1.lower() for h1 in h1_tags):
        placement_result = 'Warning'
        placement_message.append("Keyword missing from H1 Tag.")

    if not placement_message:
        placement_message = ["Primary keyword is well-placed in critical SEO elements."]

    results['placement_check'] = {'result': placement_result, 'message': ' '.join(placement_message)}

    # 4. Readability Score (Advanced Level Only)
    if level == 'advanced' and total_words > 100:
        flesch_score = textstatistics().flesch_reading_ease(content)
        results['readability_check'] = {
            'result': 'Pass' if flesch_score >= 60 else 'Warning',
            'flesch_score': f"{flesch_score:.2f}",
            'message': f"Flesch Reading Ease Score is {flesch_score:.2f}. Scores below 60 are often considered difficult for general audiences."
        }
    
    return results

# FIX: The mandatory function signature is implemented here
def run_audit(response, audit_level):
    """
    Wrapper function to extract data from the Scrapy response and run keyword analysis checks.
    """
    soup = BeautifulSoup(response.text, "lxml")
    
    # 1. Extract Title
    title = soup.find('title').get_text(strip=True) if soup.find('title') else ""

    # 2. Extract Meta Description
    desc_tag = soup.find('meta', attrs={'name': 'description'})
    description = desc_tag.get('content', '') if desc_tag else ""

    # 3. Extract Content (Text after removing noise)
    # Strip scripts, styles, and other noise
    content_soup = BeautifulSoup(response.text, "lxml")
    for script_or_style in content_soup(["script", "style", "header", "footer", "nav"]):
        script_or_style.decompose()
    content = content_soup.get_text(separator=' ', strip=True)

    # 4. Extract H1 Tags
    h1_tags = [h.get_text(strip=True) for h in soup.find_all('h1')]
    
    # Run the core logic with the extracted data
    return run_checks(title, description, content, h1_tags, audit_level)
    
