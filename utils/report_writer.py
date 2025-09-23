import json
import os
import requests
from huggingface_hub import InferenceClient

def get_ai_report(audit_data, hf_token):
    """
    Sends audit data to a Hugging Face model and gets a generated report.
    """
    # The Hugging Face API token is passed securely as a parameter.
    if not hf_token:
        print("Hugging Face API token not found.")
        return "AI report generation failed: Token missing."

    client = InferenceClient(token=hf_token)
    
    # Craft the prompt for the AI model
    prompt = f"""You are an expert SEO consultant. Your goal is to write a professional SEO audit report for a client based on the provided data. The report should be written in clear, non-technical language.

    Raw Audit Data (JSON format):
    {json.dumps(audit_data, indent=2)}

    The report must contain the following sections formatted in Markdown:

    1.  **Executive Summary:** A brief overview of the site's SEO health.
    2.  **On-Page SEO Analysis:** A breakdown of meta tags, headings, and image optimization.
    3.  **Technical SEO Analysis:** An analysis of links, SSL, and other technical factors.
    4.  **Performance:** A summary of the website's speed.
    5.  **Recommendations:** A prioritized list of the top 3-5 issues to fix, with a short explanation of why each fix is important.

    Be professional and concise.
    """
    
    try:
        response = client.text_generation(prompt, max_new_tokens=2000)
        return response
    except Exception as e:
        print(f"Error calling Hugging Face API: {e}")
        return f"AI report generation failed due to API error: {e}"

def write_report(data, json_path, md_path):
    # Save the raw JSON data
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w") as jf:
        json.dump(data, jf, indent=2)

    # **This is where the Hugging Face API token is used:**
    # The token is read from the environment variable set by GitHub Actions.
    hf_token = os.environ.get("HUGGING_FACE_TOKEN")

    # Generate and save the AI-powered Markdown report
    ai_generated_report = get_ai_report(data, hf_token)
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, "w") as mf:
        mf.write(ai_generated_report)
