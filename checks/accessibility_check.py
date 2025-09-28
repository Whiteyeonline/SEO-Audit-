from bs4 import BeautifulSoup
import re 

def run(url, html_content):
    soup = BeautifulSoup(html_content, "lxml")
    issues = []
    
    # 1. Missing Alt Text (re-checked for redundancy/proof)
    missing_alt = [img.get("src") for img in soup.find_all("img") if not img.get("alt") and img.get("src")]
    if missing_alt:
        issues.append({"type":"error","check":"Missing alt text","elements":missing_alt})

    # 2. Heading Structure Check (Crucial for accessibility and SEO)
    headings = soup.find_all(re.compile(r'^h[1-6]$'))
    h1_count = len(soup.find_all('h1'))
    
    # Check for multiple H1s
    if h1_count > 1:
        issues.append({"type":"error","check":f"Multiple H1 tags found ({h1_count} total).","element":"Check the first H1 tag for content."})
    
    # Check for skipping heading levels (e.g., H1 followed by H3)
    last_level = 0
    for h in headings:
        current_level = int(h.name[1]) # h1 -> 1, h2 -> 2
        
        if last_level == 0:
            # If no H1 is found, start with the first found heading
            last_level = current_level
            continue

        if current_level > last_level + 1:
            # Issue: Skipping a level (e.g., H2 straight to H4)
            issues.append({"type":"warning","check":f"Skipped heading level (H{last_level} followed by H{current_level})","element":h.get_text(strip=True)[:50]})
        
        last_level = current_level

    return {"accessibility_issues": issues}
            
