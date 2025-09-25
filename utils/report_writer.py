import json

def write_report(data, json_path, md_path):
    # Save raw JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Save Markdown report
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# SEO Audit Report for {data['url']}\n\n")
        f.write(f"**Status Code:** {data.get('status_code', 'N/A')}\n")
        f.write(f"**SEO Score:** {data.get('seo_score', 'N/A')}/100\n\n")

        for section, content in data.items():
            if section in ["url", "status_code", "seo_score"]:
                continue
            f.write(f"## {section.title()}\n")
            if isinstance(content, dict):
                for k, v in content.items():
                    f.write(f"- **{k}:** {v}\n")
            else:
                f.write(f"- {content}\n")
            f.write("\n")
