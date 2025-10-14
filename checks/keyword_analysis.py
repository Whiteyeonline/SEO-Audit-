# checks/keyword_analysis.py
from textstat.textstat import textstatistics
from bs4 import BeautifulSoup
from collections import Counter
import re

# FIX: Expanded STOP_WORDS list to include critical missing ones like 'by', 'from', 'as', etc.
STOP_WORDS = set([
    'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'of', 'in', 'to', 'for', 'with', 'on', 'at', 
    'i', 'you', 'your', 'we', 'our', 'it', 'by', 'from', 'as', 'that', 'this', 'have', 'has', 'had', 'will', 
    'would', 'can', 'could', 'may', 'might', 'do', 'does', 'did', 'be', 'been', 'being', 'about', 'just', 'more',
    'which', 'who', 'what', 'where', 'when', 'why', 'how', 'its', 'them', 'their', 'they', 'than', 'up', 'down',
    'out', 'into', 'over', 'under', 'through', 'after', 'before'
])

def get_word_frequency_and_ngrams(text, top_n=10):
    """Calculates frequency for single words and N-grams (2, 3 words), excluding common stop words."""
    if not text:
        return []

    # Tokenize and clean text using regex to get full words only
    words = [word.lower() for word in re.findall(r'\b\w+\b', text) if word.isalpha()]
    
    # Filter out stop words from the main list
    clean_words = [word for word in words if word not in STOP_WORDS]
    
    # 1. Single Word Frequency
    word_counts = Counter(clean_words)
    
    # 2. N-Gram (2-word and 3-word phrase) Frequency
    final_counts = word_counts.copy()
    
    # 2-grams
    ngrams_2 = [' '.join(clean_words[i:i+2]) for i in range(len(clean_words) - 1)]
    final_counts.update(Counter(ngrams_2))
    
    # 3-grams
    ngrams_3 = [' '.join(clean_words[i:i+3]) for i in range(len(clean_words) - 2)]
    final_counts.update(Counter(ngrams_3))

    # Sort by count (highest first)
    sorted_counts = sorted(final_counts.items(), key=lambda item: item[1], reverse=True)
    
    # Filter out any final keywords that are single, very short, and not the start of a phrase
    # E.g., removes single letters or very common short words that were missed by stop-word filter
    sorted_counts = [(k, v) for k, v in sorted_counts if len(k) > 2 or ' ' in k]

    return sorted_counts[:top_n]


def run_checks(title, description, content, h1_tags, level):
    """Runs all keyword reinforcement checks (Improved logic using N-grams)."""
    
    results = {}
    
    # Clean up excessive whitespace in content
    clean_content = ' '.join(content.split())
    total_words = len(clean_content.split())
    
    # 1. Word/N-gram Frequency Check 
    top_keywords = get_word_frequency_and_ngrams(clean_content)
    results['top_keywords'] = [{'keyword': w[0], 'count': w[1]} for w in top_keywords]
    
    if not top_keywords or total_words == 0:
        results['density_check'] = {'result': 'Fail', 'message': 'No content found to analyze.'}
        results['placement_check'] = {'result': 'Fail', 'message': 'Cannot run placement check without content.'}
        return results

    # The primary keyword is now the highest frequency word or N-gram
    primary_keyword = top_keywords[0][0]
    
    # Calculate density for the primary keyword/N-gram
    text_to_search = clean_content.lower()
    # Count appearances of the *full phrase*
    keyword_count_in_text = text_to_search.count(primary_keyword.lower())
    keyword_density = (keyword_count_in_text / total_words) * 100
    
    # 2. Density Check (Target: 0.5-3.0%)
    density_result = 'Pass'
    message = f"Density of primary keyword/N-gram '{primary_keyword}' is {keyword_density:.2f}% (Total Words: {total_words})."
    if keyword_density > 3.0:
        density_result = 'Warning'
        message += " Risk of keyword stuffing (over 3.0%)."
    elif keyword_density < 0.5:
        density_result = 'Warning'
        message += " Low keyword focus (below 0.5%)."
    
    results['density_check'] = {'result': density_result, 'message': message}
    
    # 3. Placement Check (Reinforce) - Checks for phrase presence in critical elements
    placement_result = 'Pass'
    placement_message = []
    
    keyword_check = primary_keyword.lower()
    
    if keyword_check not in (title or '').lower():
        placement_result = 'Warning'
        placement_message.append("Keyword missing from Title Tag.")
    
    if description and keyword_check not in description.lower():
        placement_result = 'Warning'
        placement_message.append("Keyword missing from Meta Description.")
        
    if not any(keyword_check in h1.lower() for h1 in h1_tags):
        placement_result = 'Warning'
        placement_message.append("Keyword missing from H1 Tag.")

    if not placement_message:
        placement_message = ["Primary keyword is well-placed in critical SEO elements."]

    results['placement_check'] = {'result': placement_result, 'message': ' '.join(placement_message)}

    # 4. Readability Score (Advanced Level Only - already covered by content_quality.py, but kept for redundancy)
    if level == 'advanced' and total_words > 100:
        try:
            flesch_score = textstatistics().flesch_reading_ease(clean_content)
            results['readability_check'] = {
                'result': 'Pass' if flesch_score >= 60 else 'Warning',
                'flesch_score': f"{flesch_score:.2f}",
                'message': f"Flesch Reading Ease Score is {flesch_score:.2f}. Scores below 60 are often considered difficult for general audiences."
            }
        except Exception:
             results['readability_check'] = {'result': 'Fail', 'message': 'Could not calculate Flesch Score due to content parsing error.'}

    
    return results

def run_audit(response, audit_level):
    """
    Wrapper function to extract data from the Scrapy response and run keyword analysis checks.
    """
    try:
        # Use response.body for robust parsing of the rendered HTML
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
        content_soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to parse content for keyword analysis: {str(e)}"}
    
    # 1. Extract Title
    title = soup.find('title').get_text(strip=True) if soup.find('title') else ""

    # 2. Extract Meta Description
    desc_tag = soup.find('meta', attrs={'name': 'description'})
    description = desc_tag.get('content', '') if desc_tag else ""

    # 3. Extract Content (Text after removing noise)
    # Strip scripts, styles, and other noise
    for script_or_style in content_soup(["script", "style", "header", "footer", "nav", "aside", "noscript"]):
        script_or_style.decompose()
    content = content_soup.get_text(separator=' ', strip=True)

    # 4. Extract H1 Tags
    h1_tags = [h.get_text(strip=True) for h in soup.find_all('h1')]
    
    # Run the core logic with the extracted data
    return run_checks(title, description, content, h1_tags, audit_level)
