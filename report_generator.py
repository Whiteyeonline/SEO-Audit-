def generate_report(data):
    # --- Calculate SEO Score ---
    score = 100

    # Deduct points for common issues
    score -= min(len(data['broken_links']) * 2, 20)  
    score -= min(data['image_missing_alt'] * 1, 15)  
    if not data['mobile_friendly']:
        score -= 15  
    if not data['title']:
        score -= 10
    if not data['description']:
        score -= 10

    # Clamp score between 0–100
    score = max(0, min(score, 100))

    # Status text
    if score >= 85:
        summary_status = "🟢 Excellent"
    elif score >= 70:
        summary_status = "🟡 Needs Improvement"
    else:
        summary_status = "🔴 Poor"

    # --- Build Report ---
    report = f"""
# 📊 SEO Audit Report for {data['url']}

## ⭐ SEO Score: {score}/100 — {summary_status}

---

## ✅ Strengths (What’s Working Well)
"""
    # Meta info strengths
    if data['title']:
        report += "- ✅ Title tag is present\n"
    if data['description']:
        report += "- ✅ Meta description is present\n"
    if data['mobile_friendly']:
        report += "- ✅ Website is mobile-friendly\n"
    if data['image_missing_alt'] == 0:
        report += "- ✅ All images have ALT text\n"
    if not data['broken_links']:
        report += "- ✅ No broken links detected\n"

    # Headings check
    for h, details in data['headings'].items():
        if details["count"] > 0:
            report += f"- ✅ {h.upper()} tags are present ({details['count']} found)\n"

    if report.strip().endswith("Strengths (What’s Working Well)"):
        report += "- ⚠️ No major strengths detected yet\n"

    report += "\n---\n\n## ❌ Issues (Need Attention)\n"

    # Meta info issues
    if not data['title']:
        report += "- ❌ Missing Title tag\n"
    if not data['description']:
        report += "- ❌ Missing Meta description\n"

    # Headings issues
    for h, details in data['headings'].items():
        if details["count"] == 0:
            report += f"- ❌ No {h.upper()} tags found\n"

    # Broken links
    if data['broken_links']:
        report += f"- ❌ {len(data['broken_links'])} broken link(s) detected. These should be fixed.\n"

    # Mobile friendliness
    if not data['mobile_friendly']:
        report += "- ❌ Website is not mobile-friendly (missing <meta viewport>)\n"

    # Image issues
    if data['image_missing_alt'] > 0:
        report += f"- ❌ {data['image_missing_alt']} image(s) missing ALT text. Add ALT descriptions.\n"

    if report.strip().endswith("Need Attention)"):
        report += "- ✅ No major issues found\n"

    report += "\n---\n"
    report += "\n*This audit was generated automatically. For a detailed professional SEO consultation, contact our team!*\n"

    return report
