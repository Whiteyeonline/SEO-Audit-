import os
import requests
import json

# Use a more capable model from a different API
# This example uses OpenAI, but you can use any LLM with a similar API structure
API_URL = "https://api.openai.com/v1/chat/completions"
API_TOKEN = os.getenv("OPENAI_API_KEY")

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()

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
        "model": "gpt-4o",  # gpt-4o or another powerful model
        "messages": prompt_messages,
        "temperature": 0.7
    }
    
    output = query(payload)
    
    # Extract the generated text from the OpenAI response
    if "choices" in output and output["choices"]:
        return output["choices"][0]["message"]["content"]
    return "Error: Could not generate report."

def main():
    try:
        # Assuming you have a file named seo_data.json
        with open("seo_data.json", encoding="utf-8") as f:
            data = json.load(f)
        
        summary = generate_ai_summary(data)
        
        with open("seo_report.md", "w", encoding="utf-8") as f:
            f.write(summary)
            
        print("✅ Professional AI SEO report saved to seo_report.md")
    except FileNotFoundError:
        print("Error: seo_data.json not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
    
