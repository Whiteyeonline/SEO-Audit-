# report_generator.py
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import json
import html
import math

def _safe_text(s):
    if s is None:
        return ""
    if isinstance(s, (dict, list)):
        return html.escape(json.dumps(s, ensure_ascii=False, indent=0))
    return html.escape(str(s))

def compute_grade(data):
    # simple weighted scoring (0-100)
    score = 0
    weight_total = 0

    def add(w, ok):
        nonlocal score, weight_total
        weight_total += w
        score += w if ok else 0

    # title (10)
    add(10, data.get("title", {}).get("ok", False))
    # meta (10)
    add(10, data.get("meta_description", {}).get("ok", False))
    # h1 (8)
    add(8, data.get("headings", {}).get("has_one_h1", False))
    # content (15)
    add(15, data.get("content", {}).get("ok", False))
    # images alt (10)
    add(10, data.get("images", {}).get("missing_alt", 0) == 0)
    # links (10)
    add(10, data.get("links", {}).get("broken", 0) == 0)
    # canonical (7)
    add(7, bool(data.get("canonical", {}).get("canonical")))
    # robots & sitemap (8)
    add(4, data.get("robots_txt", {}).get("found", False))
    add(4, data.get("sitemap", {}).get("found", False))
    # viewport & https (12)
    add(6, data.get("viewport", False))
    add(6, data.get("https", {}).get("final_https", False))

    percent = int(round(100 * score / (weight_total or 1)))
    # map to A-F
    if percent >= 90:
        grade = "A"
    elif percent >= 80:
        grade = "B"
    elif percent >= 70:
        grade = "C"
    elif percent >= 60:
        grade = "D"
    else:
        grade = "F"
    return {"score": percent, "grade": grade}

def generate_pdf(data, out="report.pdf"):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(out, pagesize=letter)
    elems = []

    title_text = f"On-Page SEO Audit — {data.get('final_url') or data.get('url')}"
    elems.append(Paragraph(_safe_text(title_text), styles['Title']))
    elems.append(Spacer(1, 10))

    # grade
    grade = compute_grade(data)
    elems.append(Paragraph(f"<b>Overall Grade:</b> {grade['grade']}  —  Score {grade['score']}%", styles['Heading2']))
    elems.append(Spacer(1, 8))

    # Summary bullet points (issues)
    elems.append(Paragraph("<b>Issues / Recommendations</b>", styles['Heading3']))
    issues = data.get("issues", [])
    if issues:
        for it in issues:
            elems.append(Paragraph("- " + _safe_text(it), styles['Normal']))
    else:
        elems.append(Paragraph("No high priority issues detected in this scan.", styles['Normal']))
    elems.append(Spacer(1, 12))

    # On-Page details table
    elems.append(Paragraph("<b>On-Page Details</b>", styles['Heading3']))
    rows = []
    rows.append(["Item", "Value (summary)"])
    rows.append(["HTTP Status", _safe_text(data.get("http_status"))])
    rows.append(["Title", _safe_text(data.get("title", {}).get("value")) + f" ({data.get('title', {}).get('length')})"])
    rows.append(["Meta Description", _safe_text(data.get("meta_description", {}).get("value")) + f" ({data.get('meta_description', {}).get('length')})"])
    rows.append(["Headings (h1..h6)", _safe_text(data.get("headings", {}).get("counts"))])
    rows.append(["Word Count", _safe_text(data.get("content", {}).get("word_count"))])
    rows.append(["Images total / missing alt", f"{data.get('images',{}).get('total')} / {data.get('images',{}).get('missing_alt')}"])
    rows.append(["Links total / checked / broken", f"{data.get('links',{}).get('total')} / {data.get('links',{}).get('checked')} / {data.get('links',{}).get('broken')}"])
    rows.append(["Canonical", _safe_text(data.get("canonical", {}).get("canonical"))])
    rows.append(["Schema blocks", _safe_text(data.get("schema", {}).get("schema_blocks"))])
    rows.append(["Viewport meta", _safe_text(data.get("viewport"))])
    rows.append(["HTTPS final", _safe_text(data.get("https", {}).get("final_https"))])
    rows.append(["Robots.txt found", _safe_text(data.get("robots_txt", {}).get("found"))])
    rows.append(["Sitemap found", _safe_text(data.get("sitemap", {}).get("found"))])
    tbl = Table(rows, colWidths=[160, 340])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f0f0f0")),
        ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ]))
    elems.append(tbl)
    elems.append(Spacer(1,12))

    # Extra details: small lists
    elems.append(Paragraph("<b>Extra Details</b>", styles['Heading3']))
    elems.append(Paragraph("Sample schema / hreflang / missing image examples are included in result.json.", styles['Normal']))

    doc.build(elems)
