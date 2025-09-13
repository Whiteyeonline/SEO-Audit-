import json
from transformers import pipeline
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def generate_ai_report():
    # Load SEO data
    with open("seo_data.json", "r") as f:
        data = json.load(f)

    # AI Prompt
    prompt = f"""
You are an SEO consultant. Write a professional SEO audit report with:
1. Executive Summary (rating, findings, key issues, solutions).
2. Detailed Explanations (on-page, technical SEO, links, images, content).
Make it client-friendly, clear, and professional.

Website data:
{json.dumps(data, indent=2)}
"""

    generator = pipeline("text-generation", model="tiiuae/falcon-7b-instruct")
    ai_text = generator(prompt, max_length=1000, do_sample=True, temperature=0.7)[0]['generated_text']

    # Build markdown report
    final_report = "# SEO Audit Report\n\n"
    final_report += "## 📌 Professional SEO Analysis (AI Generated)\n\n"
    final_report += ai_text.strip() + "\n\n"
    final_report += "## 📊 Raw SEO Data (Technical Results)\n\n"
    for k, v in data.items():
        final_report += f"- **{k}:** {v}\n"

    # Save Markdown
    with open("seo_report_full.md", "w") as f:
        f.write(final_report)

    # Save PDF
    doc = SimpleDocTemplate("seo_report_full.pdf")
    styles = getSampleStyleSheet()
    story = [Paragraph("SEO Audit Report", styles["Title"]), Spacer(1, 12)]
    for line in final_report.split("\n"):
        if line.strip():
            story.append(Paragraph(line, styles["Normal"]))
            story.append(Spacer(1, 6))
    doc.build(story)

    print("✅ Full SEO report saved as seo_report_full.md and seo_report_full.pdf")

if __name__ == "__main__":
    generate_ai_report()
