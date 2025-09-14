import os
import requests
import json
from requests.exceptions import RequestException

# Use a text generation model with a large context window
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
API_TOKEN = os.getenv("HF_API_TOKEN")

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def query(payload):
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()  # This will raise an HTTPError for bad responses
        return response.json()
    except RequestException as e:
        print(f"API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        raise

def generate_ai_summary(data):
    # Construct the prompt as a single string for text generation models
    prompt = f"""
[INST]
You are an SEO expert. Generate a professional SEO audit report.

Data:
{json.dumps(data, indent=2)}

Based on the provided data, generate a comprehensive SEO audit report.

Report should include:
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
            "max_new_tokens": 2048,  # Specify a generous output length
            "return_full_text": False, # Only return the generated part
        }
    }
    
    output = query(payload)
    
    # Handle the response format, which might be a list or a dictionary
    if isinstance(output, list) and output:
        return output[0].get("generated_text", "Error: No generated text found.")
    elif isinstance(output, dict):
        return output.get("generated_text", "Error: No generated text found.")
    
    raise ValueError("Unexpected API response format.")

def main():
    try:
        with open("seo_data.json", encoding="utf-8") as f:
            data = json.load(f)
        
        summary = generate_ai_summary(data)
        
        with open("seo_report.md", "w", encoding="utf-8") as f:
            f.write(summary)
            
        print("✅ Professional AI SEO report saved to seo_report.md")

    except FileNotFoundError:
        print("Error: seo_data.json not found. Please ensure the file exists in the repository root.")
        exit(1)

    except RequestException as e:
        print(f"API request failed: {e}. The report could not be generated.")
        exit(1)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1)

if __name__ == "__main__":
    main()
    
