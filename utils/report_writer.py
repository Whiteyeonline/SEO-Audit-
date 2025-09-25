def to_markdown(results, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# SEO Audit Report for {results['url']}\n\n")
        f.write(f"**Status Code:** {results['status_code']}\n\n")
        f.write(f"**SEO Score:** {results['seo_score']}/100\n\n")

        for section, data in results.items():
            if section in ["url", "status_code", "seo_score"]:
                continue
            f.write(f"## {section.title()}\n")
            if isinstance(data, dict):
                for k,v in data.items():
                    f.write(f"- **{k}:** {v}\n")
            else:
                f.write(f"- {data}\n")
            f.write("\n")
