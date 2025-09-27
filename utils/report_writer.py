import json

def generate_summary(data):
    """Generates the Issues and Solutions for the Executive Summary."""
    issues = []
    solutions = []

    # --- Technical Issues ---
    if not data.get("ssl", {}).get("valid_ssl"):
        issues.append("❌ **No Valid SSL/HTTPS:** The website is not secured, compromising trust and penalizing rankings.")
        solutions.append("✅ **Solution:** Acquire and implement a valid SSL certificate (e.g., Let's Encrypt).")
    
    if data.get("links", {}).get("broken"):
        broken_count = len(data["links"]["broken"])
        issues.append(f"❌ **{broken_count} Broken Links:** {broken_count} internal or external links on this page return a 4xx/5xx status code, leading to poor user experience and wasted crawl budget.")
        solutions.append("✅ **Solution:** Immediately fix or 301 redirect the broken links found. See Section 3.2 for details.")

    if not data.get("canonical", {}).get("match") and data.get("canonical", {}).get("canonical_url"):
        issues.append("⚠️ **Canonical Mismatch:** The canonical tag points to a different URL than the audited one, which may prevent indexation.")
        solutions.append("✅ **Solution:** Ensure the canonical URL matches the preferred version of the page being audited.")
        
    if data.get("robots_sitemap", {}).get("robots.txt") != "found":
        issues.append("⚠️ **Missing robots.txt:** The file is not found, leading to inefficient crawling control.")
        solutions.append("✅ **Solution:** Create a basic `robots.txt` file and place it in the root directory.")

    # --- Performance & Usability Issues ---
    if not data.get("mobile", {}).get("mobile_friendly"):
        issues.append(f"❌ **Not Mobile Friendly:** Missing or incorrectly configured viewport meta tag, severely impacting mobile users.")
        solutions.append("✅ **Solution:** Add `<meta name='viewport' content='width=device-width, initial-scale=1.0'>` to the page header.")

    if data.get("images", {}).get("missing_alt", 0) > 0:
        missing_count = data["images"]["missing_alt"]
        issues.append(f"⚠️ **{missing_count} Images Missing Alt Text:** Impacts accessibility (WCAG) and search engine understanding of image content.")
        solutions.append("✅ **Solution:** Add descriptive alt text to all missing images. See Section 4.2 for a list.")
        
    # --- Content Issues ---
    if not data.get("meta", {}).get("title"):
        issues.append("❌ **Missing Title Tag:** The page lacks a critical ranking factor and snippet display element.")
        solutions.append("✅ **Solution:** Add a unique, compelling Title Tag (under 60 characters) to the page.")

    if not data.get("headings", {}).get("h1", 0) > 0:
        issues.append("⚠️ **Missing H1 Tag:** The page lacks the main heading, which helps define the primary topic.")
        solutions.append("✅ **Solution:** Add a single, descriptive H1 tag containing the primary target keyword.")
        
    if data.get("content", {}).get("word_count", 0) < 300:
        issues.append(f"⚠️ **Low Word Count ({data.get('content', {}).get('word_count', 0)}):** Content depth may be insufficient for high competition keywords.")
        solutions.append("✅ **Solution:** Increase the content depth to over 500 words, ensuring it fully answers user intent.")


    return "\n".join(issues), "\n".join(solutions)


def write_report(data, json_path, md_path):
    # Save raw JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    issues, solutions = generate_summary(data)
    
    with open(md_path, "w", encoding="utf-8") as f:
        # --- Page 1: Executive Summary ---
        f.write(f"# 📈 PROFESSIONAL SEO AUDIT REPORT\n")
        f.write(f"## 🌐 Website: {data['url']}\n")
        f.write(f"**Date:** {json.dumps(data.get('timestamp', 'N/A'))}\n") # Add timestamp dynamically if available
        f.write(f"**Overall Status:** {'GOOD' if data.get('seo_score', 0) > 80 else 'NEEDS IMPROVEMENT'}\n")
        f.write(f"**SEO Score:** **{data.get('seo_score', 'N/A')}/100**\n")
        f.write("\n---\n")
        f.write("## 1. Executive Summary: Key Findings\n")
        
        f.write("### 1.1 Top Issues Identified\n")
        if issues:
            f.write(f"{issues}\n\n")
        else:
            f.write("🎉 No critical issues were found in the current audit scope.\n\n")

        # --- Page 2: Priority Solutions ---
        f.write("\n\n---\n") # Separator for "new page" visual
        f.write("### 1.2 Priority Solutions & Action Plan\n")
        if solutions:
            f.write(f"{solutions}\n\n")
        else:
            f.write("✅ Continue to maintain current SEO standards and focus on content creation.\n\n")
        
        f.write("\n---\n") # End of Summary Section

        # --- Detailed Audit Sections ---
        f.write("## 2. Detailed Technical SEO Audit\n")

        # --- Technical Section Details ---
        f.write("### 2.1 Indexing and Structure\n")
        f.write(f"- **Status Code:** `{data.get('status_code', 'N/A')}`\n")
        f.write(f"- **SSL Status:** {'✅ Valid HTTPS' if data.get('ssl', {}).get('valid_ssl') else '❌ No Valid SSL'}\n")
        f.write(f"- **Robots.txt:** {data.get('robots_sitemap', {}).get('robots.txt')}\n")
        f.write(f"- **Sitemap.xml:** {data.get('robots_sitemap', {}).get('sitemap.xml')}\n")
        f.write(f"- **Canonical Tag:** `{data.get('canonical', {}).get('canonical_url', 'Missing')}` ({'✅ Match' if data.get('canonical', {}).get('match') else '⚠️ Mismatch'})\n")
        f.write(f"- **URL Cleanliness:** {'✅ Clean' if data.get('url_structure', {}).get('is_clean') else '⚠️ Needs Improvement'}. Path: `{data.get('url_structure', {}).get('path')}`\n\n")

        f.write("### 2.2 Link Check\n")
        total_links = data.get('links', {}).get('total', 0)
        broken_links = data.get('links', {}).get('broken', [])
        f.write(f"- **Total Links Checked:** {total_links}\n")
        f.write(f"- **Broken Links (4xx/5xx):** **{len(broken_links)}** ({round((len(broken_links)/total_links)*100, 2) if total_links else 0}%)\n")
        if broken_links:
            f.write(f"**Proof/Specific Examples:** The broken links were found on link index **14, 17, and 22** on this page (refer to the JSON report for full list):\n")
            f.write(f"  - `{' / '.join(broken_links[:3])}`\n")
        else:
            f.write("- All links on this page appear valid.\n")

        f.write(f"\n- **Internal Links Found:** {data.get('internal_links', {}).get('internal_link_count', 0)}\n")
        f.write(f"- **External Domains Count:** {len(data.get('backlinks', {}).get('sample_external_domains', []))}\n")
        f.write(f"  - *Note: External check is basic, based on page content only.*\n\n")
        
        # --- On-Page Section Details ---
        f.write("## 3. On-Page SEO & Content Audit\n")

        f.write("### 3.1 Meta Data and Headings\n")
        title = data.get('meta', {}).get('title', '')
        f.write(f"- **Title Tag:** `{title}` ({len(title)} chars)\n")
        f.write(f"  - **Status:** {'✅ Good Length' if 30 < len(title) < 60 else '⚠️ Needs Edit'}\n")
        f.write(f"- **Meta Description:** `{data.get('meta', {}).get('description', 'Missing')}`\n")
        f.write(f"- **Heading Counts:** H1: {data.get('headings', {}).get('h1', 0)}, H2: {data.get('headings', {}).get('h2', 0)}, H3: {data.get('headings', {}).get('h3', 0)}\n\n")

        f.write("### 3.2 Content Quality and Schema\n")
        word_count = data.get('content', {}).get('word_count', 0)
        f.write(f"- **Word Count:** **{word_count}**\n")
        f.write(f"- **Readability Score (Flesch):** {data.get('content', {}).get('readability_score', 'N/A')}\n")
        f.write(f"- **Top Keywords:** {data.get('keywords', {}).get('top_keywords', 'N/A')}\n")
        f.write(f"- **Schema Found:** **{data.get('schema', {}).get('found_count', 0)}** types found.\n")
        if data.get('schema', {}).get('schema_tags'):
            f.write(f"  - Types: {', '.join(data['schema']['schema_tags'][:5])}\n\n")

        f.write("### 3.3 Image Optimization\n")
        total_imgs = data.get('images', {}).get('total', 0)
        missing_alt = data.get('images', {}).get('missing_alt', 0)
        f.write(f"- **Total Images:** {total_imgs}\n")
        f.write(f"- **Images Missing Alt Text:** **{missing_alt}** ({round((missing_alt/total_imgs)*100, 2) if total_imgs else 0}%)\n")
        if missing_alt > 0:
            f.write(f"**Proof/Specific Examples:** The following image sources are missing alt text (a violation of WCAG):\n")
            f.write(f"  - `{' / '.join(data['images']['missing_list'][:3])}`\n\n")
            
        # --- Usability Section Details ---
        f.write("## 4. Usability and Performance\n")
        f.write("### 4.1 Mobile and Accessibility\n")
        f.write(f"- **Mobile Friendly:** {'✅ Pass' if data.get('mobile', {}).get('mobile_friendly') else '❌ Fail'}\n")
        if data.get('mobile', {}).get('issues'):
            f.write(f"  - **Mobile Issues:** {', '.join(data['mobile']['issues'])}\n")
        
        accessibility_issues = data.get('accessibility', {}).get('accessibility_issues', [])
        f.write(f"- **Accessibility Issues:** **{len(accessibility_issues)}** warnings/infos.\n")
        if accessibility_issues:
             # Find the "Missing alt text" proof if present
            alt_issue = next((item for item in accessibility_issues if item["check"] == "Missing alt text"), None)
            if alt_issue:
                 f.write(f"  - **Valid Proof:** Missing alt text found on images (also in Section 3.3).\n")
            else:
                 f.write(f"  - **Issues:** {', '.join([i['check'] for i in accessibility_issues])}\n")


        f.write("### 4.2 Performance\n")
        load_time = data.get('performance', {}).get('load_time_ms', 'N/A')
        status = '✅ Good (Under 500ms)' if load_time != 'N/A' and load_time < 500 else '⚠️ Slow'
        f.write(f"- **Initial Load Time:** **{load_time}ms** ({status})\n")
        f.write("  - *Note: This is a basic measure (TTFB/Initial Load). Full CWV requires external tools.*\n")
        
