import os
from openai import OpenAI

# Connect to Hugging Face OpenAI-compatible endpoint
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_API_TOKEN"),
)


def generate_ai_report(prompt: str) -> str:
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b:cerebras",  # Hugging Face router model
        messages=[
            {"role": "system", "content": "You are an SEO expert. Write a professional, structured SEO report."},
            {"role": "user", "content": prompt},
        ],
    )
    # Return only the AI’s text
    return completion.choices[0].message["content"]

if __name__ == "__main__":
    # Load SEO results from seo_audit.py (example file name)
    with open("seo_results.txt", "r") as f:
        seo_data = f.read()

    # Generate AI-based report
    report = generate_ai_report(seo_data)

    # Save to markdown file
    with open("seo_report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print("✅ SEO report generated successfully: seo_report.md")
