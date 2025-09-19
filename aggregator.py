import argparse
import json
from modules import onpage
from report_generator import generate_pdf

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Website URL to audit")
    parser.add_argument("--keywords", nargs="*", default=[], help="Optional list of target keywords")
    parser.add_argument("--max-links", type=int, default=100, help="Max number of links to check (to limit runtime)")
    args = parser.parse_args()

    data = onpage.run(args.url, keywords=args.keywords, max_links_check=args.max_links)
    with open("result.json", "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)

    generate_pdf(data)
    print("Done. Generated: result.json and report.pdf")
