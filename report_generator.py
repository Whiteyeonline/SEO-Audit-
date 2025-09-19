# report_generator.py
import json, html, os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import matplotlib.pyplot as plt

def _safe_text(x):
    if x is None:
        return ""
    if isinstance(x, (dict, list)):
        return html.escape(json.dumps(x, ensure_ascii=False, indent=0))
    return html.escape(str(x))

def _draw_headings_chart(headings_counts, out_path="/tmp/headings.png"):
    # headings_counts: dict h1..h6
    labels = []
    values = []
    for i in range(1,7):
        k = f"h{i}"
        labels.append(k.upper())
        values.append(headings_counts.get(k,0))
    plt.figure(figsize=(6,2.5))
    plt.bar(labels, values)  # no custom colors
    plt.title("Headings distribution (H1..H6)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path

def compute_grade(data):
    score = 0
    weight_total = 0
    def add(w, ok):
        nonlocal score, weight_total
        weight_total += w
        if ok:
            score += w
    add(10, data.get("title",{}).get("ok",False))
    add(10, data.get("meta_description",{}).get("ok",False))
    add(8, data.get("headings",{}).get("has_one_h1", False))
    add(15, data.get("content",{}).get("word_count",0) >= 300)
    add(10, data.get("images",{}).get("missing_alt_count",0) == 0)
    add(10, data.get("links",{}).get("broken_count",0) == 0)
    add(7, bool(data.get("canonical",{}).get("canonical")))
    add(4, data.get("robots_txt",{}).get("found", False))
    add(4, data.get("sitemap",{}).get("found", False))
    add(6, data.get("viewport",{}))
    add(6, data.get("https",{}).get("final_https", False))
    percent = int(round(100 * score / (weight_total or 1)))
    if percent >= 90:
        grade="A"
    elif percent >= 80:
        grade="B"
    elif percent >= 70:
        grade="C"
    elif percent >= 60:
        grade="D"
    else:
        grade="F"
    return {"score": percent, "grade": grade}

def generate_pdf(data, out="report.pdf"):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(out, pagesize=letter)
    elems = []

    title = data.get("final_url") or data.get("url")
    elems.append(Paragraph(_safe_text(f"On-Page SEO Audit — {title}"), styles['Title']))
    elems.append(Spacer(1,8))

    # Grade
    grade = compute_grade(data)
    elems.append(Paragraph(f"<b>Overall Grade:</b> {grade['grade']}  —  Score {grade['score']}%", styles['Heading2']))
    elems.append(Spacer(1,8))

    # Issues & actionable recommendations
    elems.append(Paragraph("<b>Issues & Recommendations</b>", styles['Heading3']))
    if data.get("issues"):
        for it in data["issues"]:
            elems.append(Paragraph("- " + _safe_text(it), styles['Normal']))
    else:
        elems.append(Paragraph("No high priority issues detected.", styles['Normal']))
    elems.append(Spacer(1,8))

    # Recommendations (concrete)
    rec = data.get("recommendations", {})
    elems.append(Paragraph("<b>Recommended Title (edit as needed)</b>", styles['Heading4']))
    elems.append(Paragraph(_safe_text(rec.get("suggested_title","")), styles['Normal']))
    elems.append(Spacer(1,6))
    elems.append(Paragraph("<b>Recommended Meta Description (edit as needed)</b>", styles['Heading4']))
    elems.append(Paragraph(_safe_text(rec.get("suggested_meta","")), styles['Normal']))
    elems.append(Spacer(1,12))

    # Details table
    elems.append(Paragraph("<b>On-Page Details</b>", styles['Heading3']))
    rows = [
        ["Item", "Summary / Value"],
        ["HTTP Status", _safe_text(data.get("http_status"))],
        ["Title", _safe_text(data.get("title",{}).get("value")) + f" ({data.get('title',{}).get('length')})"],
        ["Meta Description", _safe_text(data.get("meta_description",{}).get("value")) + f" ({data.get('meta_description',{}).get('length')})"],
        ["Headings (H1..H6)", _safe_text(data.get("headings",{}).get("counts"))],
        ["Word Count", _safe_text(data.get("content",{}).get("word_count"))],
        ["Readability (Flesch Reading Ease)", _safe_text(data.get("readability",{}).get("flesch_reading_ease"))],
        ["Images total / missing alt", f"{data.get('images',{}).get('total')} / {data.get('images',{}).get('missing_alt_count')}"],
        ["Links total / checked / broken", f"{data.get('links',{}).get('total')} / {data.get('links',{}).get('checked')} / {data.get('links',{}).get('broken_count')}"],
        ["Canonical", _safe_text(data.get("canonical",{}).get("canonical"))],
        ["Schema blocks", _safe_text(data.get("schema",{}).get("schema_blocks"))],
        ["Viewport", _safe_text(data.get("viewport"))],
        ["HTTPS final", _safe_text(data.get("https",{}).get("final_https"))],
        ["Robots.txt found", _safe_text(data.get("robots_txt",{}).get("found"))],
        ["Sitemap found", _safe_text(data.get("sitemap",{}).get("found"))]
    ]
    tbl = Table(rows, colWidths=[170, 350])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f0f0f0")),
        ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ]))
    elems.append(tbl)
    elems.append(Spacer(1,12))

    # Headings chart
    try:
        image_path = _draw_headings_chart(data.get("headings",{}).get("counts", {}))
        elems.append(Paragraph("<b>Headings distribution</b>", styles['Heading4']))
        elems.append(Image(image_path, width=420, height=150))
        elems.append(Spacer(1,12))
    except Exception:
        pass

    # Top keywords
    elems.append(Paragraph("<b>Top Keywords</b>", styles['Heading3']))
    kws = data.get("keywords",{}).get("top", [])
    if kws:
        for item in kws:
            elems.append(Paragraph(f"- {item['keyword']} (count: {item['count']})", styles['Normal']))
    else:
        elems.append(Paragraph("No keywords extracted.", styles['Normal']))
    elems.append(Spacer(1,12))

    # Broken links list (first 30)
    elems.append(Paragraph("<b>Broken Links (first 30)</b>", styles['Heading3']))
    bl = data.get("links",{}).get("broken_list", [])
    if bl:
        for b in bl[:30]:
            status = b.get("status") if b.get("status") else b.get("error","")
            elems.append(Paragraph(f"- {_safe_text(b.get('url'))}  (status: {_safe_text(status)})", styles['Normal']))
    else:
        elems.append(Paragraph("No broken links detected (in checked sample).", styles['Normal']))
    elems.append(Spacer(1,12))

    # Images examples
    elems.append(Paragraph("<b>Image examples (first 20)</b>", styles['Heading3']))
    imgs = data.get("images",{}).get("images", [])
    if imgs:
        for i in imgs[:20]:
            elems.append(Paragraph(f"- {i.get('src')} (alt: {html.escape(i.get('alt') or '')})", styles['Normal']))
    else:
        elems.append(Paragraph("No images detected.", styles['Normal']))
    elems.append(Spacer(1,12))

    # Schema sample
    elems.append(Paragraph("<b>Schema sample (truncated)</b>", styles['Heading3']))
    schema_samples = data.get("schema",{}).get("sample", [])
    if schema_samples:
        for s in schema_samples[:3]:
            elems.append(Paragraph("<pre>" + _safe_text(s[:1000]) + "</pre>", styles['Normal']))
    else:
        elems.append(Paragraph("No schema JSON-LD found.", styles['Normal']))
    elems.append(Spacer(1,12))

    doc.build(elems)
