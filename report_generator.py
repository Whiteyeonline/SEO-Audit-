# report_generator.py
import os
import requests
import json
import sys
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, HTTPError, Timeout

# Your Hugging Face API key
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
API_TOKEN = os.getenv("HF_API_TOKEN")

# Check if the API token is set
if not API_TOKEN:
    print("Error: HF_API_TOKEN environment variable not found.")
    print("Please set it with: export HF_API_TOKEN='your_api_token'")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def fetch_seo_data(url):
    """Fetches basic SEO data for a given URL."""
    print(f"Fetching data from {url}...")
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        
        # Check for non-HTML content
        if 'text/html' not in response.headers.get('Content-Type', ''):
            print("Skipping: URL does not contain HTML content.")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Collect data points
        title_tag = soup.title
        title = title_tag.string if title_tag and title_tag.string else 'No title found'
        
        meta_description_tag = soup.find('meta', attrs={'name': 'description'})
        description = meta_description_tag['content'] if meta_description_tag else 'No description found'
        
        # You can add more data points here, e.g., H1, canonical tags, etc.
        
        data = {
            "url": url,
            "title": title,
            "meta_description": description,
            "status_code": response.status_code,
        }
        print("Data fetched successfully.")
        return data
    except Timeout:
        print(f"Failed to fetch data from {url}: Request timed out.")
    except HTTPError as e:
        print(f"Failed to fetch data from {url}: HTTP error - {e.response.status_code}")
    except RequestException as e:
        print(f"Failed to fetch data from {url}: An error occurred during the request - {e}")
    return None

def query_llm(payload):
    """Sends the request to the Hugging Face Inference API."""
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()
    except HTTPError as e:
        print(f"API request failed with HTTP error: {e.response.status_code}")
        print(f"Error details: {e.response.text}")
        raise
    except RequestException as e:
        print(f"API request failed: {e}")
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

def main():
    """Main function to run the full process."""
    if len(sys.argv) < 2:
        print("Usage: python report_generator.py <url>")
        sys.exit(1)
        
    url = sys.argv[1]
    
    try:
        print(f"🚀 Starting SEO audit for {url}...")
        seo_data = fetch_seo_data(url)
        
        if seo_data:
            print("✨ Generating AI report...")
            report_content = generate_report(seo_data)
            
            output_file = "seo_report.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_content)
                
            print(f"✅ Professional AI SEO report saved to {output_file}")
        else:
            print("❌ Audit failed. Report could not be generated.")
            sys.exit(1)
            
    except (RequestException, ValueError) as e:
        print(f"An error occurred during report generation: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

