# checks/competitor_analysis_util.py

import logging
from urllib.parse import urlparse
import requests 
from bs4 import BeautifulSoup 

# Simple fetcher function for external URL (competitor)
def fetch_html(url: str):
    """Fetches the HTML content of the target URL."""
    try:
        # Use a descriptive User-Agent
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; SEO Audit Bot/1.0; +https://your-github.com/repo)'}
        # Set a short timeout as this is a preliminary check
        response = requests.get(url, headers=headers, timeout=10) 
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return response.text, response.status_code
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {url}: {e}")
        return None, 0

def run_competitor_audit(competitor_url: str) -> dict:
    """
    Performs a basic, high-level audit on the competitor's URL.
    This runs as an 'INITIAL_CHECK' in main.py.
    """
    if not competitor_url:
        return {'competitor_analysis': {'status': 'INFO', 'details': 'No COMPETITOR_URL provided.', 'competitor_data': {}}}

    logging.info(f"Running competitor audit for: {competitor_url}")
    html_content, status_code = fetch_html(competitor_url)

    analysis_data = {'http_status': status_code, 'url': competitor_url}

    if status_code != 200 or not html_content:
        return {'competitor_analysis': {
            'status': 'FAIL', 
            'details': f'Competitor URL fetch failed (HTTP {status_code}).', 
            'competitor_data': analysis_data
        }}

    try:
        soup = BeautifulSoup(html_content, 'lxml')
        
        # 1. Title Check
        title_tag = soup.find('title')
        comp_title = title_tag.text.strip() if title_tag else "MISSING"
        
        # 2. H1 Check
        h1_tags = soup.find_all('h1')
        h1_count = len(h1_tags)
        
        # 3. Meta Description Check
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        comp_meta_desc_len = len(meta_desc['content'].strip()) if meta_desc and 'content' in meta_desc else 0
        
        # Output Results
        analysis_data.update({
            'title': comp_title,
            'h1_count': h1_count,
            'meta_description_length': comp_meta_desc_len,
            'parsed_domain': urlparse(competitor_url).netloc
        })
        
        return {'competitor_analysis': {
            'status': 'SUCCESS', 
            'details': f'Successfully parsed competitor (HTTP {status_code}).', 
            'competitor_data': analysis_data
        }}
        
    except Exception as e:
        logging.error(f"Competitor Parsing Error: {e}")
        return {'competitor_analysis': {
            'status': 'FAIL', 
            'details': f'Failed to parse competitor content: {e}.', 
            'competitor_data': analysis_data
        }}
      
