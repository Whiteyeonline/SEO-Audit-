# SEO Audit Tool

This is a simple SEO audit tool written in Python.

## 🚀 Features
- Checks title, description, and canonical tags
- Verifies robots.txt
- Counts headings (H1–H6)
- Detects broken links (first 100 checked)
- Checks internal vs external links
- Detects missing image ALT attributes
- Measures word count
- Checks for mobile-friendliness
- Measures page speed

## 📂 Files
- `seo_audit.py` → Runs the audit and saves results into `seo_data.json`
- `report_generator.py` → Converts audit results into a human-readable Markdown report (`seo_report.md`)
- `.github/workflows/seo_audit.yml` → GitHub Actions workflow to run the audit

## ⚡ Usage

### Local
```bash
python seo_audit.py <URL>
python report_generator.py
