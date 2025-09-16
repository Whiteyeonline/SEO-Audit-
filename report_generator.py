# report_generator.py
import os
import requests
import json
import sys
import argparse
from requests.exceptions import RequestException, HTTPError
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# 🌟 API Configuration: Ensure your environment variable is set.
# Get your token from https://huggingface.co/settings/tokens
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
API_TOKEN = os.getenv("HF_API_TOKEN")

# Headers for the API request
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def query_llm(payload):
    """Communicates with the AI to conjure the report."""
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()
    except HTTPError as e:
        if e.response.status_code == 404:
            print(f"🚫 API Error: The model {API_URL} was not found.")
            print("This could mean the URL is wrong, or the model is not hosted on the free Inference API.")
        elif e.response.status_code == 401:
            print("🚫 API Error: Authentication failed. Is your HF_API_TOKEN correct?")
        else:
            print(f"🚫 API Error: {e.response.status_code} - {e.response.text}")
        raise
    except RequestException as e:
        print(f"🚫 API Request failed: {e}")
        raise

def generate_report(data):
    """Generates the report using the LLM."""
    if not data:
        return "Report could not be generated due to missing data."
    
    prompt = f"""
[INST]
You are a world-class SEO strategist. Generate a comprehensive and professional SEO audit report for a website based on the following raw data. The tone should be authoritative and insightful.

Data:
{json.dumps(data, indent=2)}

The report must contain the following sections, formatted in polished Markdown:
- 📈 **SEO Health Score:** A single number out of 100, followed by a brief justification.
- 🎯 **Executive Summary:** A concise, high-level overview of the site's SEO standing.
- ✅ **Key Findings & Recommendations:** A bulleted list using ✅ and ❌ emojis to highlight positive and negative points. For each ❌, provide a clear, actionable solution.
- 🔗 **Technical SEO Audit:** Specific notes on technical elements like title tags, meta descriptions, and status codes.
- 📊 **Visual Insights:** A suggestion for a simple chart or graph that would effectively represent a key finding.
- 📄 **Raw Data Appendix:** Include the raw input data at the end for reference.

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

def save_as_pdf(report_content, filename="seo_report.pdf"):
    """Saves the Markdown report to a beautiful PDF."""
    try:
        doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()
        story = []

        lines = report_content.split('\n')
        for line in lines:
            if line.strip().startswith('###'):
                style = styles['h2']
                story.append(Paragraph(line.strip('###').strip(), style))
            elif line.strip().startswith('##'):
                style = styles['h3']
                story.append(Paragraph(line.strip('##').strip(), style))
            elif line.strip().startswith('-'):
                story.append(Paragraph(line.strip('-').strip(), styles['Normal']))
            else:
                story.append(Paragraph(line.replace('\n', '<br/>'), styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))

        doc.build(story)
        print(f"📄 PDF report successfully saved to {filename}")
    except Exception as e:
        print(f"🚫 Failed to save PDF: {e}")

def main():
    """Main function to run the full process from a JSON file."""
    parser = argparse.ArgumentParser(description="🚀 Professional AI SEO Report Generator")
    parser.add_argument("file_path", help="The path to the JSON file to audit (e.g., seo_data.json)")
    args = parser.parse_args()
    
    print(f"🚀 Starting AI-powered SEO report generation from {args.file_path}...")

    # Check for the API token at the top for early exit
    if not API_TOKEN:
        print("🚨 Error: HF_API_TOKEN environment variable is not set. Please set it to your Hugging Face API key.")
        sys.exit(1)

    try:
        # Load the SEO data from the JSON file
        with open(args.file_path, 'r', encoding='utf-8') as f:
            seo_data = json.load(f)

        if seo_data:
            print("✨ Generating a professional AI report...")
            report_content = generate_report(seo_data)
            
            # Save as Markdown
            md_path = "seo_report.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            print(f"✅ AI SEO report saved to {md_path}")
            
            # Save as PDF
            save_as_pdf(report_content)
        else:
            print("❌ Audit failed. Report could not be generated.")
            sys.exit(1)
            
    except FileNotFoundError:
        print(f"🚨 Error: The file {args.file_path} was not found.")
        sys.exit(1)
    except (RequestException, ValueError) as e:
        print(f"🚨 An error occurred during report generation: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"🚨 An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
        
