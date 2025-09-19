# On-Page SEO Audit (single-page)

How to use:
1. Push this repo to GitHub.
2. Open GitHub -> Actions -> On-Page SEO Audit -> Run workflow.
3. Enter the URL you want audited.
4. Download `report.pdf` and `result.json` from workflow artifacts.

Notes:
- No paid API keys required.
- The script makes HTTP requests to the target site; scanning very large pages or sites with many links/images can take longer.
- If the target site blocks requests from GitHub IPs, some checks (link HEADs) may show as broken. Use on your client sites or use proxies if required.
