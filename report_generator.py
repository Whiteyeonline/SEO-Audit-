import sys
import json
from markdown import markdown

def load_data(json_file):
    with open(json_file, "r") as f:
        return json.load(f)

def generate_markdown_report(data):
    report = f"# SEO Audit Report for {data['url']}\n\n"

    report += "## 📝 Meta Information\n"
    report += f"- **Title:** {data['title']}\n"
    report += f"- **Description:** {data['description']}\n"
    report += f"- **Canonical URL:** {data['canonical_url']}\n\n"

    report += "## 🔎 Headings Structure\n"
    for h, count in data['headings'].items():
        report += f"- {h.upper()}: {count}\n"
    report += "\n"

    report += "## 🔗 Links\n"
    report += f"- Internal Links: {data['internal_links']}\n"
    report += f"- External Links: {data['external_links']}\n"
    report += f"- Broken Links: {len(data['broken_links'])}\n\n"

    if data['broken_links']:
        for link in data['broken_links'][:10]:
            report += f"  - {link}\n"
        report += "\n"

    report += "## 📱 Mobile Friendly\n"
    report += "✅ Yes\n\n" if data['mobile_friendly'] else "❌ No\n\n"

    report += "## 🖼️ Images\n"
    report += f"- Total Images: {data['image_total']}\n"
    report += f"- Missing Alt Text: {data['image_missing_alt']}\n\n"

    report += "## 📊 Content\n"
    report += f"- Word Count: {data['word_count']}\n"
    report += f"- Page Speed: {data['page_speed']} seconds\n\n"

    # --- AI-like professional summary ---
    report += "## 💡 Professional Summary\n"
    issues = []
    if data['title'] == "Missing":
        issues.append("Missing title tag")
    if data['description'] == "Missing":
        issues.append("Missing meta description")
    if data['image_missing_alt'] > 0:
        issues.append(f"{data['image_missing_alt']} images missing alt text")
    if len(data['broken_links']) > 0:
        issues.append(f"{len(data['broken_links'])} broken links detected")
    if not data['mobile_friendly']:
        issues.append("Site not mobile-friendly")

    if issues:
        report += "### ❌ Issues Found\n"
        for i in issues:
            report += f"- {i}\n"
        report += "\n### ✅ Recommendations\n"
        if "Missing title tag" in issues:
            report += "- Add a descriptive `<title>` tag.\n"
        if "Missing meta description" in issues:
            report += "- Add a `<meta name='description'>` tag.\n"
        if "images missing alt text" in "".join(issues):
            report += "- Add meaningful `alt` text to all images.\n"
        if "broken links" in "".join(issues):
            report += "- Fix or remove broken links.\n"
        if "not mobile-friendly" in "".join(issues):
            report += "- Add a `<meta name='viewport'>` for responsiveness.\n"
    else:
        report += "✅ No major SEO issues detected.\n"

    return report

def save_reports(report_md):
    with open("seo_report.md", "w") as f:
        f.write(report_md)

    with open("seo_report.html", "w") as f:
        f.write(markdown(report_md))

def main():
    if len(sys.argv) < 2:
        print("Usage: python ai_report_generator.py seo_data.json")
        return
    data = load_data(sys.argv[1])
    report_md = generate_markdown_report(data)
    save_reports(report_md)
    print("AI Report generated: seo_report.md & seo_report.html")

if __name__ == "__main__":
    main()
