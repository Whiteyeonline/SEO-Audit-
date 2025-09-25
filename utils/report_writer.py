import json
import os
from datetime import datetime

def write_report(data, json_path, md_path):
    """
    Writes JSON + professional Markdown report.
    """
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w") as jf:
        json.dump(data, jf, indent=2)

    # Create professional Markdown report
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, "w") as mf:
        mf.write(f"# SEO Audit Report\n")
        mf.write(f"**Website:** {data.get('url')}\n\n")
        mf.write(f"**Audit Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        mf.write(f"**Overall SEO Score:** {data.get('overall_score')}/10\n\n")

        mf.write("## Scores by Section\n")
        for k, v in data.get("scores", {}).items():
            mf.write(f"- **{k}:** {v}/10\n")
        mf.write("\n")

        mf.write("## Detailed Checks\n")
        for k, v in data.get("checks", {}).items():
            mf.write(f"### {k}\n")
            mf.write("```\n")
            mf.write(json.dumps(v, indent=2))
            mf.write("\n```\n\n")

        # Recommendations (simple logic, can be expanded)
        mf.write("## Top Recommendations\n")
        recommendations = generate_recommendations(data)
        for rec in recommendations:
            mf.write(f"- {rec}\n")

def generate_recommendations(data):
    recs = []
    if data["scores"].get("Meta", 0) < 8:
        recs.append("Add or improve title and meta description.")
    if data["scores"].get("Headings",0) < 8:
        recs.append("Ensure exactly one H1 and proper heading hierarchy.")
    if data["scores"].get("Images",0) < 8:
        recs.append("Add alt text to images for accessibility and SEO.")
    if data["scores"].get("Links",0) < 8:
        recs.append("Fix broken links to improve UX and SEO.")
    if data["scores"].get("SSL",0) < 8:
        recs.append("Secure site with valid SSL certificate.")
    if data["scores"].get("Performance",0) < 8:
        recs.append("Improve page load speed and performance.")
    if data["scores"].get("Accessibility",0) < 8:
        recs.append("Fix accessibility issues (alt text, headings).")
    if data["scores"].get("Content Quality",0) < 8:
        recs.append("Increase content depth and keyword relevance.")
    return recs
