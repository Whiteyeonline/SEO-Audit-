import json
import requests
import os

API_URL = "https://api-inference.huggingface.co/models/google/gemma-3-270m"
API_TOKEN = os.getenv("HF_API_TOKEN")  # set this in repo secrets

headers = {"Authorization": f"Bearer {API_TOKEN}"}

def query(payload):
    response = requests.post(HUGGINGFACE_API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()

def generate_ai_summary(data):
    prompt = f"""
You are an SEO expert. Generate a professional SEO audit report.

Data:
{json.dumps(data, indent=2)}

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
    output = query({"inputs": prompt})
    return output[0]["generated_text"] if isinstance(output, list) else output["generated_text"]

def main():
    with open("seo_data.json") as f:
        data = json.load(f)
    summary = generate_ai_summary(data)
    with open("seo_report.md", "w", encoding="utf-8") as f:
        f.write(summary)
    print("✅ Professional AI SEO report saved to seo_report.md")

if __name__ == "__main__":
    main()
