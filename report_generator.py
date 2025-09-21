# report_generator.py
import json
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors


# ---------- Pie chart helpers ----------
def make_pie_chart(data_dict, title, out_path):
    if not data_dict or not isinstance(data_dict, dict):
        return None
    labels = list(data_dict.keys())
    values = list(data_dict.values())

    plt.figure(figsize=(4, 4))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


# ---------- PDF generator ----------
def generate_pdf(data, out_pdf="SEO_Report.pdf"):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(out_pdf, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elems = []

    url = data.get("final_url") or data.get("url", "Unknown")
    score = data.get("score", "N/A")
    grade = "A" if isinstance(score, int) and score >= 90 else \
            "B" if isinstance(score, int) and score >= 80 else \
            "C" if isinstance(score, int) and score >= 70 else \
            "D" if isinstance(score, int) and score >= 60 else "F"

    # Title
    elems.append(Paragraph(f"<b>SEO Audit Summary</b>", styles["Title"]))
    elems.append(Spacer(1, 0.2 * inch))

    # Executive Summary
    summary = f"""
    This audit for <b>{url}</b> achieved a score of <b>{score}/100 (Grade {grade})</b>.
    The page has good content length and basic optimizations, but also shows issues
    that should be addressed to improve SEO performance.
    """
    elems.append(Paragraph(summary, styles["Normal"]))
    elems.append(Spacer(1, 0.3 * inch))

    # Key Findings
    elems.append(Paragraph("<b>Key Findings</b>", styles["Heading2"]))
    findings = data.get("issues", [])
    if findings:
        for issue in findings[:5]:  # show first 5 only
            elems.append(Paragraph(f"• {issue}", styles["Normal"]))
    else:
        elems.append(Paragraph("✅ No major issues found.", styles["Normal"]))
    elems.append(Spacer(1, 0.3 * inch))

    # Details Table
    elems.append(Paragraph("<b>Audit Details</b>", styles["Heading2"]))
    rows = [
        ["Title", f"{data.get('title',{}).get('value','')} ({data.get('title',{}).get('length','N/A')} chars)"],
        ["Meta Description", f"{data.get('meta_description',{}).get('value','')} ({data.get('meta_description',{}).get('length','N/A')} chars)"],
        ["Word Count", str(data.get('content',{}).get('word_count','N/A'))],
        ["Headings", str(data.get('headings',{}).get('counts',''))],
        ["Images (total/missing alt)", f"{data.get('images',{}).get('total','N/A')} / {data.get('images',{}).get('missing_alt','N/A')}"],
        ["Links (total/internal/external/broken)", f"{data.get('links',{}).get('total','N/A')} / {data.get('links',{}).get('internal','N/A')} / {data.get('links',{}).get('external','N/A')} / {data.get('links',{}).get('broken','N/A')}"],
        ["Canonical", str(data.get('canonical',{}).get('canonical','N/A'))],
        ["Robots.txt Found", str(data.get('robots_txt',{}).get('found','N/A'))],
        ["Sitemap Found", str(data.get('sitemap',{}).get('found','N/A'))],
        ["HTTPS", str(data.get('https',{}).get('final_https','N/A'))],
        ["Viewport", str(data.get('viewport','N/A'))],
    ]

    table = Table(rows, colWidths=[180, 330])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f0f0f0")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ]))
    elems.append(table)
    elems.append(Spacer(1, 0.3 * inch))

    # Charts
    # Pie chart for headings
    headings_counts = data.get("headings", {}).get("counts", {})
    hpath = make_pie_chart(headings_counts, "Headings Distribution", "headings_pie.png")
    if hpath:
        elems.append(Paragraph("<b>Headings Distribution</b>", styles["Heading2"]))
        elems.append(Image(hpath, width=300, height=300))
        elems.append(Spacer(1, 0.3 * inch))

    # Pie chart for links
    links = data.get("links", {})
    link_data = {
        "Internal": links.get("internal", 0),
        "External": links.get("external", 0),
        "Broken": links.get("broken", 0),
    }
    lpath = make_pie_chart(link_data, "Links Breakdown", "links_pie.png")
    if lpath:
        elems.append(Paragraph("<b>Links Breakdown</b>", styles["Heading2"]))
        elems.append(Image(lpath, width=300, height=300))
        elems.append(Spacer(1, 0.3 * inch))

    doc.build(elems)
    return out_pdf


if __name__ == "__main__":
    with open("seo_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    generate_pdf(data)
