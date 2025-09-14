import os
import requests
import json
from requests.exceptions import RequestException

# Use a more capable model from a different API
# This example uses OpenAI, but you can use any LLM with a similar API structure
API_URL = "https://api.openai.com/v1/chat/completions"
API_TOKEN = os.getenv("OPENAI_API_KEY")

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def query(payload):
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)  # Increased timeout
        response.raise_for_status()  # This will raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except RequestException as e:
        print(f"API request failed: {e}")
        # Log the response content for more details on the error
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        raise  # Re-raise the exception to stop execution

def generate_ai_summary(data):
    # Construct the prompt with the full data
    prompt_messages = [
        {
            "role": "system",
            "content": "You are an SEO expert. Generate a professional SEO audit report."
        },
        {
            "role": "user",
            "content": f"""
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
Write in Markdown.
"""
        }
    ]
    
    payload = {
        "model": "gpt-4o",  # or another powerful model
        "messages": prompt_messages,
        "temperature": 0.7
    }
    
    output = query(payload)
    
    # Extract the generated text from the OpenAI response
    if "choices" in output and output["choices"]:
        return output["choices"][0]["message"]["content"]
    
    # If there's an issue with the response structure, raise an error
    raise ValueError("Unexpected API response format.")

def main():
    try:
        # Assuming you have a file named seo_data.json
        with open("seo_data.json", encoding="utf-8") as f:
            data = json.load(f)
        
        summary = generate_ai_summary(data)
        
        # Ensure the file is written successfully
        with open("seo_report.md", "w", encoding="utf-8") as f:
            f.write(summary)
            
        print("✅ Professional AI SEO report saved to seo_report.md")

    except FileNotFoundError:
        print("Error: seo_data.json not found. Please ensure the file exists in the repository root.")
        exit(1) # Exit with a non-zero status code to indicate failure

    except RequestException as e:
        print(f"API request failed: {e}. The report could not be generated.")
        exit(1) # Exit with a non-zero status code to indicate failure

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1) # Exit with a non-zero status code to indicate failure

if __name__ == "__main__":
    main()
