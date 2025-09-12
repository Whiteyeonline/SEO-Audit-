def generate_report(data):
    # --- SEO Score Calculation ---
    score = 100
    deductions = 0

    if data['title'] == "Missing":
        score -= 10; deductions += 1
    if data['description'] == "Missing":
        score -= 10; deductions += 1
    if data['headings']['h1'] == 0:
        score -= 10; deductions += 1
    if len(data['broken_links']) > 0:
        score -= min(15, len(data['broken_links']) * 2); deductions += 1
    if not data['mobile_friendly']:
        score -= 15; deductions += 1
    if data['image_missing_alt'] > 0:
        score -= min(10, data['image_missing_alt']); deductions += 1
    if isinstance(data['page_speed'], (int, float)) and data['page_speed'] >= 4:
        score -= 10; deductions += 1

    if score < 0:
        score = 0

    # Rating
    if score >= 85:
        rating = "🟢 Good"
    elif score >= 60:
        rating = "⚠️ Medium"
    else:
        rating = "🔴 Bad"

    # --- Report ---
    report = f"""
# SEO Audit Report for {data['url']}

## 📊 SEO Score
- **Score:** {score}/100
- **Rating:** {rating}

## 📝 Meta Information
- **Title:** {data['title']}
- **Description:** {data['description']}

## 🔎 Headings Structure
"""
    for h, count in data['headings'].items():
        report += f"- {h.upper()}: {count}\n"
    report += "\n"

    report += f"""## 🔗 Broken Links (First 100 checked)
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

## ⚡ Quick Facts
- SEO Score: {score}/100
- Status: {rating}
- Total Headings: {sum(data['headings'].values())}
- Total Images: {data['image_total']}
- Broken Links: {len(data['broken_links'])}
- Mobile Friendly: {"Yes" if data['mobile_friendly'] else "No"}
- Page Speed: {data['page_speed']} seconds
"""

    # --- Issues Section ---
    issues = []
    if data['title'] == "Missing":
        issues.append("❌ Missing Title tag – add a clear, descriptive title.")
    if data['description'] == "Missing":
        issues.append("❌ Missing Meta Description – add a relevant description.")
    if data['headings']['h1'] == 0:
        issues.append("⚠️ No H1 tag found – add at least one main heading.")
    if len(data['broken_links']) > 0:
        issues.append("❌ Broken links detected – please fix or remove them.")
    if not data['mobile_friendly']:
        issues.append("❌ Website is not mobile friendly – add a viewport meta tag.")
    if data['image_missing_alt'] > 0:
        issues.append("⚠️ Some images are missing alt text – add descriptive alt text to all images.")
    if isinstance(data['page_speed'], (int, float)) and data['page_speed'] >= 4:
        issues.append(f"⚠️ Page load time is slow ({data['page_speed']}s) – optimize images, scripts, or hosting.")

    report += "\n## ❗ Issues Found\n"
    if issues:
        for idx, i in enumerate(issues, 1):
            report += f"{idx}. {i}\n"
    else:
        report += "✅ No major issues found. Great job!\n"

    report += "\n---\n"
    report += "\n*This audit was generated automatically. For a full professional review, contact us!*\n"

    return report
