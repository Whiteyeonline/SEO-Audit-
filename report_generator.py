# report_generator.py
import os
import requests
import json
import sys
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

# Your Hugging Face API key
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
API_TOKEN = os.getenv("HF_API_TOKEN")

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def fetch_seo_data(url):
    """Fetches basic SEO data for a given URL."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Collect data points
        title = soup.title.string if soup.title else 'No title found'
        meta_description = soup.find('meta', attrs={'name': 'description'})
        description = meta_description['content'] if meta_description else 'No description found'
        
        # Add more data points as needed (e.g., H1, canonical, etc.)
        
        data = {
            "url": url,
            "title": title,
            "meta_description": description,
            "status_code": response.status_code,
            # Add other data points here
        }
        return data
    except RequestException as e:
        print(f"Failed to fetch data from {url}: {e}")
        return None

def query_llm(payload):
    """Sends the request to the Hugging Face Inference API."""
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        print(f"API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        raise

def generate_report(data):
    """Generates the report using the LLM."""
    if not data:
        return "Error: No data available for report generation."
        
    prompt = f"""
[INST]
You are an SEO expert. Generate a professional SEO audit report based on the following data.

Data:
{json.dumps(data, indent=2)}

The report should include:
- SEO Health Score (0-100)
- ✅❌ style checklist
- Issues found
- Keyword analysis
- Recommendations with solutions
- Simple chart/visual suggestions
- Final section with raw results
Write the report in Markdown.
[/INST]
"""
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 2048,
            "return_full_text": False,
        }
    }
    
    output = query_llm(payload)
    
    if isinstance(output, list) and output:
        return output[0].get("generated_text", "Error: No generated text found.")
    
    raise ValueError("Unexpected API response format.")

def main(url):
    """Main function to run the full process."""
    try:
        print(f"🚀 Starting SEO audit for {url}...")
        seo_data = fetch_seo_data(url)
        
        if seo_data:
            print("✨ Generating AI report...")
            report_content = generate_report(seo_data)
            
            with open("seo_report.md", "w", encoding="utf-8") as f:
                f.write(report_content)
                
            print("✅ Professional AI SEO report saved to seo_report.md")
        else:
            print("❌ Audit failed. Report could not be generated.")
            exit(1)
            
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("Usage: python report_generator.py <url>")
        exit(1)

