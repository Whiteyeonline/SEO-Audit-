# report_generator.py
import json
import sys
import argparse

def generate_report(data):
    """Generates a human-readable SEO report from raw JSON data."""
    if not data:
        return "Error: No data provided for report generation."

    report = f"# SEO Audit Report for {data.get('url', 'N/A')}\n\n"
    report += f"**Date of Audit:** {data.get('timestamp', 'N/A')}\n\n"
    
    # 📋 Summary
    report += "## 📋 Executive Summary\n"
    report += "This report provides a one-page SEO audit based on a recent crawl. It identifies key on-page SEO elements and potential issues.\n\n"

    # 🔗 Technical SEO
    report += "## 🔗 Technical SEO\n"
    report += f"- **Canonical URL:** {'✅' if 'canonical_url' in data and data['canonical_url'] != 'Missing' else '❌'} {data.get('canonical_url', 'N/A')}\n"
    report += f"- **robots.txt:** {'✅' if data.get('robots_txt_exists', False) else '❌'} `robots.txt` file found.\n"
    report += f"- **Mobile-Friendly:** {'✅' if data.get('mobile_friendly', False) else '❌'} Viewport meta tag detected.\n\n"
    
    # 📝 Content & Keywords
    report += "## 📝 Content & Keywords\n"
    report += f"- **Title Tag:** {data.get('title', 'N/A')}\n"
    report += f"- **Meta Description:** {data.get('description', 'N/A')}\n"
    report += f"- **Word Count:** {data.get('word_count', 'N/A')} words.\n"
    
    headings = data.get('headings', {})
    report += f"- **Headings:** H1 ({headings.get('h1', 0)}), H2 ({headings.get('h2', 0)}), H3 ({headings.get('h3', 0)}), etc.\n\n"
    
    report += "### Top Keywords\n"
    if data.get('keywords', {}).get('top_keywords'):
        for keyword in data['keywords']['top_keywords']:
            report += f" - {keyword}\n"
    else:
        report += " - No top keywords found.\n"
    report += "\n"

    # 🖼️ Images & Links
    report += "## 🖼️ Images & Links\n"
    report += f"- **Total Images:** {data.get('image_total', 0)}\n"
    report += f"- **Images Missing ALT:** {data.get('image_missing_alt', 0)}\n"
    report += f"- **Internal Links:** {data.get('internal_links', 0)}\n"
    report += f"- **External Links:** {data.get('external_links', 0)}\n"
    
    broken_links = data.get('broken_links', [])
    if broken_links:
        report += "- **Broken Links:** ❌ Found the following broken links:\n"
        for link in broken_links:
            report += f"  - {link}\n"
    else:
        report += "- **Broken Links:** ✅ No broken links found.\n"
    report += "\n"

    # 📄 Raw Data Appendix
    report += "## 📄 Raw Data Appendix\n"
    report += "```json\n"
    report += json.dumps(data, indent=2)
    report += "\n```\n"
    
    return report

def main():
    """Main function to run the report generation from a JSON file."""
    parser = argparse.ArgumentParser(description="📋 SEO Report Generator from JSON data")
    parser.add_argument("file_path", help="The path to the JSON data file (e.g., seo_data.json)")
    args = parser.parse_args()
    
    try:
        with open(args.file_path, 'r', encoding='utf-8') as f:
            seo_data = json.load(f)
        
        report_content = generate_report(seo_data)
        
        with open("seo_report.md", "w", encoding="utf-8") as f:
            f.write(report_content)
            
        print("✅ SEO report saved to seo_report.md")

    except FileNotFoundError:
        print(f"Error: The file {args.file_path} was not found.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
