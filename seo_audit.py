import sys
import requests
import time
import urllib.parse
from bs4 import BeautifulSoup
import json

def get_html(url):
    """Fetches the HTML content and measures load time."""
    try:
        start = time.time()
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        load_time = round(time.time() - start, 2)
        return resp.text, load_time
    except Exception:
        return None, None

def check_robots_txt(base_url):
    """Checks if robots.txt exists."""
    try:
        robots_url = urllib.parse.urljoin(base_url, '/robots.txt')
        resp = requests.head(robots_url, timeout=5)
        return resp.status_code == 200
    except requests.exceptions.RequestException:
        return False

def check_meta(soup):
    """Checks title & description."""
    title = soup.title.string.strip() if soup.title and soup.title.string else "Missing"
    meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
    meta_desc = meta_desc_tag['content'].strip() if meta_desc_tag and meta_desc_tag.has_attr('content') else "Missing"
    return title, meta_desc

def check_canonical_tag(soup):
    """Checks canonical tag."""
    canonical_tag = soup.find('link', rel='canonical')
    return canonical_tag['href'] if canonical_tag and canonical_tag.has_attr('href') else "Missing"

def check_headings(soup):
    """Counts headings h1-h6."""
    return {f'h{i}': len(soup.find_all(f'h{i}')) for i in range(1, 7)}

def check_links(soup, base_url):
    """Checks internal, external, broken links."""
    internal_links, external_links, broken_links = 0, 0, []
    links = soup.find_all('a', href=True)

    for a_tag in links[:100]:  # limit to 100 for speed
        href = a_tag['href']
        parsed_href = urllib.parse.urlparse(href)

        # Internal vs external
        if parsed_href.scheme and parsed_href.netloc:
            if parsed_href.netloc == urllib.parse.urlparse(base_url).netloc:
                internal_links += 1
            else:
                external_links += 1
        else:
            internal_links += 1

        # Broken link check
        if href.startswith('http'):
            try:
                resp = requests.head(href, timeout=5, allow_redirects=True)
                if resp.status_code >= 400:
                    broken_links.append(href)
            except requests.exceptions.RequestException:
                broken_links.append(href)

    return broken_links, internal_links, external_links

def check_mobile_friendly(soup):
    """Checks viewport tag."""
    return bool(soup.find('meta', attrs={'name': 'viewport'}))

def check_images(soup):
    """Counts images and missing alts."""
    images = soup.find_all('img')
    missing_alt = [img['src'] for img in images if not img.has_attr('alt') or not img['alt'].strip()]
    return len(images), len(missing_alt)

def check_content_length(soup):
    """Counts words in body."""
    body_text = soup.body.get_text() if soup.body else ""
    return len(body_text.split())

def main(url):
    """Runs SEO audit and saves results to seo_data.json."""
    html, load_time = get_html(url)
    if not html:
        print("Error: Could not fetch the URL.")
        return

    soup = BeautifulSoup(html, 'html.parser')

    data = {
        "url": url,
        "robots_txt_exists": check_robots_txt(url),
        "title": check_meta(soup)[0],
        "description": check_meta(soup)[1],
        "canonical_url": check_canonical_tag(soup),
        "headings": check_headings(soup),
        "broken_links": check_links(soup, url)[0],
        "internal_links": check_links(soup, url)[1],
        "external_links": check_links(soup, url)[2],
        "mobile_friendly": check_mobile_friendly(soup),
        "image_total": check_images(soup)[0],
        "image_missing_alt": check_images(soup)[1],
        "word_count": check_content_length(soup),
        "page_speed": load_time if load_time else "Error measuring"
    }

    with open("seo_data.json", "w") as f:
        json.dump(data, f, indent=4)

    print("✅ SEO data saved to seo_data.json")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("Usage: python seo_audit.py <URL>")
