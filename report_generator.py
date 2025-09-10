def generate_report(data):
    report = f"""
# SEO Audit Report for {data['url']}

## 📝 Meta Information
- **Title:** {data['title']}
- **Description:** {data['description']}

## 🔎 Headings Structure
"""
    for h, count in data['headings'].items():
        report += f"- {h.upper()}: {count}\n"
    report += "\n"

    report += f"""## 🔗 Broken Links (First 20 checked)
- Total Broken: {len(data['broken_links'])}
"""
    for l in data['broken_links']:
        report += f"  - {l}\n"
    report += "\n"

    report += f"""## 📱 Mobile Friendliness
- Viewport Tag Present: {"✅ Yes" if data['mobile_friendly'] else "❌ No"}

## 🖼️ Images
- Total Images: {data['image_total']}
- Images Missing Alt Text: {data['image_missing_alt']}
"""

    report += "\n---\n"
    report += "\n*This audit was generated automatically. For a full professional review, contact us!*\n"

    return report
