# SEO Audit with AI-Powered Reports

This project runs an SEO audit on any website and generates a **professional AI-enhanced report**.

## 🚀 Features
- Checks meta tags, headings, links, images, mobile friendliness
- Measures page speed & content length
- Keyword analysis (top keywords, density, placement)
- Detects broken links
- Generates **AI-powered professional report** (Markdown)

## 📂 Files
- `seo_audit.py` → Runs the audit, outputs `seo_data.json`
- `report_generator.py` → Uses Hugging Face AI to generate `seo_report.md`
- `.github/workflows/seo_audit.yml` → GitHub Actions automation

## 🔑 Setup
1. Get a free [Hugging Face API token](https://huggingface.co/settings/tokens)
2. In GitHub → Repo → Settings → Secrets → Actions  
   Add: `HF_API_TOKEN` = your token

## ▶️ Usage
Run locally:
```bash
python seo_audit.py https://example.com
python report_generator.pypython report_generator.py
