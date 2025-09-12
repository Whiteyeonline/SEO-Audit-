import sys
import requests
import time
from bs4 import BeautifulSoup
from markdownify import markdownify

from report_generator import generate_report

def get_html(url):
    try:
        start = time.time()
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        load_time = round(time.time() - start, 2)  # page load time in seconds
        return resp.text, load_time
    except Exception as e:
        return None, None

def check_meta(soup):
    title = soup.title.string if soup.title else "Missing"
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    desc = meta_desc['content'] if meta_desc and meta_desc.has_attr('content') else "Missing"
    return title, desc

def check_headings(soup):
    headings = {f'h{i}': len(soup.find_all(f'h{i}')) for i in range(1, 7)}
    return headings

def check_links(soup, url):
    links = soup.find_all('a', href=True)
    broken = []
    for l in links[:100]:  # Increased limit from 20 → 100
        href = l['href']
        if href.startswith('http'):
            try:
                r = requests.head(href, timeout=5)
                if r.status_code >= 400:
                    broken.append(href)
            except:
                broken.append(href)
    return broken

def check_mobile_friendly(soup):
    viewport = soup.find('meta', attrs={'name': 'viewport'})
    return bool(viewport)

def check_images(soup):
    images = soup.find_all('img')
    missing_alt = [img['src'] for img in images if not img.has_attr('alt')]
    return len(images), len(missing_alt)

def main():
    url = sys.argv[1]
    html, load_time = get_html(url)
    if not html:
        with open("seo_audit_report.md", "w") as f:
            f.write(f"# SEO Audit Report\n\nCould not fetch {url}.\n")
        return

    soup = BeautifulSoup(html, 'html.parser')
    title, desc = check_meta(soup)
    headings = check_headings(soup)
    broken_links = check_links(soup, url)
    mobile = check_mobile_friendly(soup)
    img_total, img_missing_alt = check_images(soup)

    data = {
        "url": url,
        "title": title,
        "description": desc,
        "headings": headings,
        "broken_links": broken_links,
        "mobile_friendly": mobile,
        "image_total": img_total,
        "image_missing_alt": img_missing_alt,
        "page_speed": load_time if load_time else "Error measuring",
        "raw_html": html[:1000]  # For context
    }

    report = generate_report(data)
    with open("seo_audit_report.md", "w") as f:
        f.write(report)

if __name__ == "__main__":
    main()
