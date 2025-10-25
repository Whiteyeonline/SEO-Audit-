import re
from bs4 import BeautifulSoup
# CORRECTED LINE: Import the textstat module directly
import textstat

# Common English stop words (you can expand this list anytime)
STOP_WORDS = {
    "a","an","the","is","am","are","was","were","be","been","being",
    "has","have","had","do","does","did","of","on","in","to","for","by",
    "and","or","not","no","from","with","as","at","that","this","it",
    "its","but","if","then","so","because","than","too","very","there",
    "their","my","your","our","we","you","they","he","she","his","her",
    "them","these","those","what","which","who","whom","how","where",
    "when","why","can","will","shall","would","should","could"
}

def get_word_frequency_and_ngrams(text):
    """
    Extracts top keywords and two-word phrases (N-grams),
    excluding stop words and short meaningless terms.
    """
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    words = [w.lower() for w in text.split() if w.lower() not in STOP_WORDS and len(w) > 2]
    freq = {}

    for i in range(len(words)):
        # Single word
        single = words[i]
        freq[single] = freq.get(single, 0) + 1

        # Two-word phrase (skip if any part is stop word)
        if i + 1 < len(words):
            pair = f"{words[i]} {words[i+1]}"
            if all(w not in STOP_WORDS for w in [words[i], words[i+1]]):
                freq[pair] = freq.get(pair, 0) + 1

    return sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]


def run_checks(title, description, content, h1_tags, level):
    """
    Runs keyword frequency, density, placement, and readability checks.
    """
    results = {}

    clean_content = ' '.join(content.split())
    total_words = len(clean_content.split())

    # 1️⃣ Keyword frequency and filtering
    top_keywords = get_word_frequency_and_ngrams(clean_content)
    results['top_keywords'] = [{'keyword': w[0], 'count': w[1]} for w in top_keywords]

    if not top_keywords or total_words == 0:
        return {
            "primary_keyword": None,
            "primary_keyword_density": 0.0,
            "density_check": {"result": "Fail", "message": "No content found to analyze."},
            "placement_check": {"result": "Fail", "message": "Cannot run placement check without content."}
        }

    # 2️⃣ Primary keyword selection (skip too short ones)
    primary_keyword = None
    for kw, count in top_keywords:
        if len(kw) > 2 and kw not in STOP_WORDS:
            primary_keyword = kw
            break
    if not primary_keyword:
        primary_keyword = top_keywords[0][0]

    # 3️⃣ Keyword density (regex word-boundary match)
    text_to_search = clean_content.lower()
    keyword_count_in_text = len(re.findall(r'\b' + re.escape(primary_keyword.lower()) + r'\b', text_to_search))
    keyword_density = (keyword_count_in_text / total_words) * 100.0 if total_words > 0 else 0.0

    results["primary_keyword"] = primary_keyword
    results["primary_keyword_density"] = round(keyword_density, 2)

    # 4️⃣ Density interpretation
    if keyword_density > 3.0:
        density_result = "Warning"
        density_msg = f"Keyword '{primary_keyword}' density is {keyword_density:.2f}% — possible keyword stuffing."
    elif keyword_density < 0.5:
        density_result = "Warning"
        density_msg = f"Keyword '{primary_keyword}' density is {keyword_density:.2f}% — too low, weak focus."
    else:
        density_result = "Pass"
        density_msg = f"Keyword '{primary_keyword}' density is healthy ({keyword_density:.2f}%)."
    results["density_check"] = {"result": density_result, "message": density_msg}

    # 5️⃣ Placement check (title, desc, h1)
    placement_issues = []
    kw = primary_keyword.lower()
    if kw not in (title or '').lower():
        placement_issues.append("Missing in Title Tag.")
    if description and kw not in description.lower():
        placement_issues.append("Missing in Meta Description.")
    if not any(kw in h1.lower() for h1 in h1_tags):
        placement_issues.append("Missing in H1 Tag.")

    placement_msg = " ".join(placement_issues) if placement_issues else "Keyword appears in key elements."
    placement_result = "Pass" if not placement_issues else "Warning"
    results["placement_check"] = {"result": placement_result, "message": placement_msg}

    # 6️⃣ Readability check (only in advanced)
    if level == "advanced" and total_words > 100:
        try:
            # CORRECTED CALL: Call the method on the imported textstat module
            score = textstat.flesch_reading_ease(clean_content)
            results["readability_check"] = {
                "result": "Pass" if score >= 60 else "Warning",
                "flesch_score": round(score, 2),
                "message": f"Flesch Reading Ease Score: {score:.2f}"
            }
        except Exception:
            results["readability_check"] = {"result": "Fail", "message": "Error calculating readability."}

    return results


def run_audit(response, audit_level):
    """
    Extracts page data and runs keyword analysis.
    """
    try:
        soup = BeautifulSoup(response.body, "lxml", from_encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to parse HTML: {str(e)}"}

    title = soup.find("title").get_text(strip=True) if soup.find("title") else ""
    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = desc_tag.get("content", "") if desc_tag else ""

    for s in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        s.decompose()

    content = soup.get_text(separator=" ", strip=True)
    h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]

    return run_checks(title, description, content, h1_tags, audit_level)
        
