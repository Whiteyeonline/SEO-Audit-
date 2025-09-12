import sys
import requests
import time
import urllib.parse
from bs4 import BeautifulSoup
import json

def get_html(url):
    """Fetches the HTML content of a given URL and measures the page load time."""
    try:
        start = time.time()
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        load_time = round(time.time() - start, 2)
        return resp.text, load_time
    except Exception as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        return None, None

def check_robots_txt(base_url):
    """Checks for the existence of a robots.txt file."""
    try:
        robots_url = urllib.parse.urljoin(base_url, '/robots.txt')
        resp = requests.head(robots_url, timeout=5)
        return resp.status_code == 200
    except requests.exceptions.RequestException:
        return False

def check_meta(soup):
    """Extracts and checks the title tag and meta description."""
    title = soup.title.string.strip() if soup.title and soup.title.string else "Missing"
    meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
    meta_desc = meta_desc_tag['content'].strip() if meta_desc_tag and meta_desc_tag.has_attr('content') else "Missing"
    return title, meta_desc

def check_canonical_tag(soup):
    """Checks for the presence of a canonical tag."""
    canonical_tag = soup.find('link', rel='canonical')
    return canonical_tag['href'] if canonical_tag and canonical_tag.has_attr('href') else "Missing"

def check_headings(soup):
    """Counts the number of each heading tag (h1-h6)."""
    headings = {f'h{i}': len(soup.find_all(f'h{i}')) for i in range(1, 7)}
    return headings

def check_links(soup, base_url):
    """Counts and categorizes internal and external links, and checks for broken links."""
    internal_links = 0
    external_links = 0
    broken_links = []
    
    links = soup.find_all('a', href=True)
    for a_tag in links[:100]:  # Limit to 100 links to prevent very long scan times
        href = a_tag['href']
        parsed_href = urllib.parse.urlparse(href)

        # Classify the link as internal or external
        if parsed_href.scheme and parsed_href.netloc:
            if parsed_href.netloc == urllib.parse.urlparse(base_url).netloc:
                internal_links += 1
            else:
                external_links += 1
        elif not parsed_href.netloc:
            internal_links += 1

        # Check for broken links (only for absolute URLs)
        if href.startswith('http'):
            try:
                # Use HEAD request for efficiency
                resp = requests.head(href, timeout=5, allow_redirects=True)
                if resp.status_code >= 400:
                    broken_links.append(href)
            except requests.exceptions.RequestException:
                broken_links.append(href)
                
    return broken_links, internal_links, external_links

def check_mobile_friendly(soup):
    """Checks for the presence of a viewport meta tag."""
    viewport = soup.find('meta', attrs={'name': 'viewport'})
    return bool(viewport)

def check_images(soup):
    """Counts total images and images with missing alt attributes."""
    images = soup.find_all('img')
    missing_alt = [img['src'] for img in images if not img.has_attr('alt') or not img['alt'].strip()]
    return len(images), len(missing_alt)

def check_content_length(soup):
    """Provides a simple word count of the body content as a proxy for content quality."""
    body_text = soup.body.get_text() if soup.body else ""
    word_count = len(body_text.split())
    return word_count

def main():
    if len(sys.argv) < 2:
        print("Usage: python seo_audit.py <URL>")
        return

    url = sys.argv[1]
    html, load_time = get_html(url)
    if not html:
        print(f"Could not fetch {url}.", file=sys.stderr)
        return

    soup = BeautifulSoup(html, 'html.parser')
    robots_txt_exists = check_robots_txt(url)
    title, desc = check_meta(soup)
    canonical_url = check_canonical_tag(soup)
    headings = check_headings(soup)
    broken_links, internal_links, external_links = check_links(soup, url)
    mobile_friendly = check_mobile_friendly(soup)
    img_total, img_missing_alt = check_images(soup)
    word_count = check_content_length(soup)
    
    data = {
        "url": url,
        "robots_txt_exists": robots_txt_exists,
        "title": title,
        "description": desc,
        "canonical_url": canonical_url,
        "headings": headings,
        "broken_links": broken_links,
        "internal_links": internal_links,
        "external_links": external_links,
        "mobile_friendly": mobile_friendly,
        "image_total": img_total,
        "image_missing_alt": img_missing_alt,
        "word_count": word_count,
        "page_speed": load_time if load_time else "Error measuring"
    }

    # Save the data to a JSON file
    with open("seo_data.json", "w") as f:
        json.dump(data, f, indent=4)
    print("SEO data saved to seo_data.json. Please open report_generator.html to continue.")

if __name__ == "__main__":
    main()
