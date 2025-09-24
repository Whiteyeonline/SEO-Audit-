# checks/backlinks_check.py
import re
from google import search # Corrected import statement

def run(url, html_content=None):
    try:
        domain = re.sub(r'https?://(?:www\.)?', '', url).split('/')[0]
        query = f'link:{domain}'
        backlinks = []
        for result in search(query, num=3, stop=3):
            backlinks.append(result)
        return {"found_backlinks": backlinks, "note": "This is a very basic check using a search operator."}
    except Exception as e:
        return {"error": str(e)}
        
