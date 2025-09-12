def generate_report(data):
    """
    Robust SEO report generator.
    Accepts headings as either:
      - {"h1": 1, "h2": 0}
      - {"h1": {"count": 1, "pages": ["index.html"]}, ...}
    and safely handles missing keys or unexpected types.
    """

    # --- Normalize inputs with safe defaults ---
    url = data.get("url", "(no url provided)")
    title = data.get("title") or ""
    description = data.get("description") or ""
    headings = data.get("headings") or {}
    broken_links = data.get("broken_links") or []
    # ensure broken_links is a list
    if not isinstance(broken_links, (list, tuple)):
        broken_links = []
    mobile_friendly = bool(data.get("mobile_friendly", False))
    image_total = int(data.get("image_total", 0) or 0)
    image_missing_alt = int(data.get("image_missing_alt", 0) or 0)

    images_without_alt = data.get("images_without_alt") or []
    if not isinstance(images_without_alt, (list, tuple)):
        images_without_alt = []

    # --- Calculate SEO Score (same logic as before, but safe) ---
    score = 100
    score -= min(len(broken_links) * 2, 20)
    score -= min(image_missing_alt * 1, 15)
    if not mobile_friendly:
        score -= 15
    if not title:
        score -= 10
    if not description:
        score -= 10
    score = max(0, min(100, int(score)))

    if score >= 85:
        summary_status = "🟢 Excellent"
    elif score >= 70:
        summary_status = "🟡 Needs Improvement"
    else:
        summary_status = "🔴 Poor"

    # --- Prepare Strengths & Issues lists (clean output) ---
    strengths = []
    issues = []

    # Meta strengths / issues
    if title:
        strengths.append("- ✅ Title tag is present")
    else:
        issues.append("- ❌ Missing Title tag")

    if description:
        strengths.append("- ✅ Meta description is present")
    else:
        issues.append("- ❌ Missing Meta description")

    if mobile_friendly:
        strengths.append("- ✅ Website is mobile-friendly")
    else:
        issues.append("- ❌ Website is not mobile-friendly (missing <meta viewport>)")

    if image_missing_alt == 0:
        strengths.append("- ✅ All images include ALT text")
    else:
        issues.append(f"- ❌ {image_missing_alt} image(s) missing ALT text")

    if not broken_links:
        strengths.append("- ✅ No broken links detected")
    else:
        issues.append(f"- ❌ {len(broken_links)} broken link(s) detected")

    # Headings: handle both int and dict formats
    heading_details_lines = []
    for h_tag, details in (headings.items() if isinstance(headings, dict) else []):
        # Normalize count & pages
        if isinstance(details, dict):
            count = int(details.get("count", 0) or 0)
            pages = details.get("pages") or []
            if not isinstance(pages, (list, tuple)):
                pages = []
        else:
            # details likely an int (or something else)
            try:
                count = int(details)
            except Exception:
                count = 0
            pages = []

        if count > 0:
            strengths.append(f"- ✅ {h_tag.upper()} tags are present ({count} found)")
        else:
            issues.append(f"- ❌ No {h_tag.upper()} tags found")

        # Prepare a short neat line for heading details (no long lists)
        if pages:
            # Show only a small hint that pages contain these headings (no long dumps)
            heading_details_lines.append(f"- {h_tag.upper()}: present on {min(len(pages), 5)} page(s) (sample shown in logs)")

    # If headings is empty (not provided), note it
    if not headings:
        issues.append("- ❌ No heading information provided")

    # --- Build the final report string (neat & professional) ---
    report_lines = []
    report_lines.append(f"# 📊 SEO Audit Report for {url}\n")
    report_lines.append(f"## ⭐ SEO Score: {score}/100 — {summary_status}\n")
    report_lines.append("---\n")
    report_lines.append("## ✅ Strengths (What’s Working Well)")
    if strengths:
        report_lines.extend(strengths)
    else:
        report_lines.append("- ⚠️ No major strengths detected yet")
    # compact heading hints (if any)
    if heading_details_lines:
        report_lines.append("")  # blank line
        report_lines.append("### 🔎 Headings Summary")
        report_lines.extend(heading_details_lines)

    report_lines.append("\n---\n")
    report_lines.append("## ❌ Issues (Need Attention)")
    if issues:
        report_lines.extend(issues)
    else:
        report_lines.append("- ✅ No major issues found")

    # Final short sections (counts only, professional tone)
    report_lines.append("\n---\n")
    report_lines.append("## 📌 Quick Facts")
    report_lines.append(f"- Title: {'Present' if title else 'Missing'}")
    report_lines.append(f"- Description: {'Present' if description else 'Missing'}")
    report_lines.append(f"- Broken links: {len(broken_links)}")
    report_lines.append(f"- Mobile friendly: {'Yes' if mobile_friendly else 'No'}")
    report_lines.append(f"- Total images: {image_total}")
    report_lines.append(f"- Images missing ALT: {image_missing_alt}")

    report_lines.append("\n---\n")
    report_lines.append("*This audit was generated automatically. For a detailed professional SEO consultation, contact our team!*\n")

    # Join lines with newlines
    report = "\n".join(report_lines)
    return report
