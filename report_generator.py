import json

def generate_report():
    with open("seo_data.json", "r") as f:
        data = json.load(f)

    report = f"""
# SEO Audit Report for {data['url']}

## 📝 Meta Information
- **Title:** {data['title']}
- **Description:** {data['description']}
- **Canonical URL:** {data['canonical_url']}

## 🔍 SEO Checks
- Robots.txt Present: {"✅ Yes" if data['robots_txt_exists'] else "❌ No"}
- Mobile Friendly: {"✅ Yes" if data['mobile_friendly'] else "❌ No"}
- Word Count: {data['word_count']}
- Page Load Speed: {data['page_speed']}s

## 📊 Headings
"""
    for h, count in data["headings"].items():
        report += f"- {h.upper()}: {count}\n"

    report += f"""

## 🔗 Links
- Internal Links: {data['internal_links']}
- External Links: {data['external_links']}
- Broken Links: {len(data['broken_links'])}
"""
    if data["broken_links"]:
        report += "\n### Broken Links List:\n"
        for link in data["broken_links"]:
            report += f"- {link}\n"

    report += f"""

## 🖼️ Images
- Total Images: {data['image_total']}
- Missing ALT: {data['image_missing_alt']}

---
✅ Report generated successfully.
"""

    with open("seo_report.md", "w") as f:
        f.write(report)

    print("📄 Report saved as seo_report.md")

if __name__ == "__main__":
    generate_report()
