# modules/onpage.py
import requests
import re
import tldextract
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Configurable limits
MAX_LINKS_TO_CHECK = 100    # limit number of links we will HEAD/GET to avoid long runs
REQUEST_TIMEOUT = 8         # seconds per request

def _safe_get(session, url, method="get", **kwargs):
    try:
        if method == "head":
            return session.head(url, allow_redirects=True, timeout=REQUEST_TIMEOUT, **kwargs)
        return session.get(url, allow_redirects=True, timeout=REQUEST_TIMEOUT, **kwargs)
    except Exception as e:
        return None

def fetch_page(session, url):
    """Return tuple: (text, status_code, final_url, headers) or error dict."""
    r = _safe_get(session, url, headers={"User-Agent": "Mozilla/5.0"})
    if r is None:
        return {"error": "request_failed", "message": f"Failed to fetch {url}"}
    return {"text": r.text, "status": r.status_code, "final_url": r.url, "headers": dict(r.headers)}

def check_title(soup):
    title = ""
    try:
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
    except Exception:
        title = ""
    return {"value": title, "length": len(title), "ok": 50 <= len(title) <= 60}

def check_meta_description(soup):
    tag = soup.find("meta", attrs={"name": "description"})
    desc = ""
    if tag and tag.get("content"):
        desc = tag.get("content").strip()
    return {"value": desc, "length": len(desc), "ok": 120 <= len(desc) <= 160}

def check_headings(soup):
    counts = {f"h{i}": len(soup.find_all(f"h{i}")) for i in range(1,7)}
    return {"counts": counts, "has_one_h1": counts.get("h1",0) == 1}

def check_word_count(soup):
    text = soup.get_text(" ", strip=True)
    words = re.findall(r'\w{3,}', text.lower())
    wc = len(words)
    return {"word_count": wc, "ok": wc >= 300}

def check_keywords(soup, keywords=None):
    if not keywords:
        return {"keywords": {}}
    text = soup.get_text(" ", strip=True).lower()
    found = {}
    total_words = max(1, len(re.findall(r'\w{1,}', text)))
    for kw in keywords:
        c = text.count(kw.lower())
        found[kw] = {"count": c, "density_percent": round(100 * c / total_words, 4)}
    return {"keywords": found}

def _resolve_src(src, base_url):
    try:
        return urljoin(base_url, src)
    except:
        return src

def check_images(soup, base_url):
    imgs = soup.find_all("img")
    missing = []
    oversized = []
    total = len(imgs)
    for img in imgs:
        src = img.get("src") or img.get("data-src") or ""
        resolved = _resolve_src(src, base_url)
        alt = img.get("alt")
        if not alt or not alt.strip():
            missing.append(resolved)
        # try to check width attribute if present
        width = img.get("width") or img.get("data-width")
        if width:
            try:
                w = int(re.sub(r'[^\d]', '', str(width)))
                if w >= 2000:
                    oversized.append(resolved)
            except:
                pass
    return {"total": total, "missing_alt": len(missing), "missing_list": missing[:200], "oversized": oversized[:50]}

def check_links(soup, base_url, session, max_check=MAX_LINKS_TO_CHECK):
    links = []
    for a in soup.find_all("a", href=True):
        href = a.get("href").strip()
        if href.startswith("mailto:") or href.startswith("tel:") or href.startswith("#"):
            continue
        links.append(urljoin(base_url, href))
    links = list(dict.fromkeys(links))  # dedupe while preserving order
    total = len(links)
    domain = tldextract.extract(base_url).registered_domain or urlparse(base_url).netloc
    internal = external = broken = 0
    checked = 0
    for link in links:
        if checked >= max_check:
            break
        checked += 1
        try:
            r = _safe_get(session, link, method="head", headers={"User-Agent":"Mozilla/5.0"})
            if r is None:
                # try GET as fallback
                r = _safe_get(session, link, method="get", headers={"User-Agent":"Mozilla/5.0"})
            if r is None or r.status_code >= 400:
                broken += 1
            # classify internal/external
            if domain and domain in urlparse(link).netloc:
                internal += 1
            else:
                external += 1
        except Exception:
            broken += 1
    return {"total": total, "checked": checked, "internal": internal, "external": external, "broken": broken, "limited_to": max_check}

def check_canonical(soup, base_url):
    tag = soup.find("link", rel=lambda r: r and "canonical" in r)
    if tag and tag.get("href"):
        return {"canonical": urljoin(base_url, tag["href"])}
    return {"canonical": None}

def check_schema(soup):
    scripts = soup.find_all("script", type="application/ld+json")
    count = len(scripts)
    # quick scan for common types
    types = []
    for s in scripts[:10]:
        try:
            text = s.string or ""
            if "@type" in text:
                types.append(text[:200])
        except:
            pass
    return {"schema_blocks": count, "sample": types[:5]}

def check_lang(soup):
    html_tag = soup.find("html")
    lang = html_tag.get("lang") if html_tag and html_tag.get("lang") else None
    return {"lang": lang}

def check_hreflang(soup, base_url):
    tags = []
    for t in soup.find_all("link", attrs={"rel": "alternate"}):
        hreflang = t.get("hreflang")
        href = t.get("href")
        if hreflang and href:
            tags.append({"hreflang": hreflang, "href": urljoin(base_url, href)})
    return {"hreflangs": tags}

def check_meta_robots(soup, response_headers):
    meta = soup.find("meta", attrs={"name": "robots"})
    meta_val = meta.get("content") if meta and meta.get("content") else None
    x_robots = response_headers.get("X-Robots-Tag") if response_headers else None
    return {"meta_robots": meta_val, "x_robots_tag": x_robots}

def check_robots_txt(session, base_url):
    robots_url = urljoin(base_url, "/robots.txt")
    r = _safe_get(session, robots_url, headers={"User-Agent":"Mozilla/5.0"})
    if r and r.status_code == 200:
        snippet = r.text[:1000]
        return {"found": True, "snippet": snippet}
    return {"found": False}

def check_sitemap(session, base_url):
    for path in ["/sitemap.xml", "/sitemap_index.xml"]:
        url = urljoin(base_url, path)
        r = _safe_get(session, url, headers={"User-Agent":"Mozilla/5.0"})
        if r and r.status_code == 200 and ("<urlset" in r.text or "<sitemapindex" in r.text):
            return {"found": True, "url": url}
    return {"found": False}

def check_https(original_url, final_url):
    return {"original_https": original_url.lower().startswith("https://"), "final_https": final_url.lower().startswith("https://")}

def check_viewport(soup):
    meta = soup.find("meta", attrs={"name": "viewport"})
    return {"viewport": True if meta else False}

def check_deprecated(soup):
    deprecated_tags = ["font", "center", "marquee"]
    found = [t for t in deprecated_tags if soup.find(t)]
    return {"deprecated_tags": found}

def run(url, keywords=None, max_links_check=MAX_LINKS_TO_CHECK):
    session = requests.Session()
    page = fetch_page(session, url)
    if "error" in page:
        return {"error": True, "message": page.get("message", "failed to fetch page"), "url": url}

    soup = BeautifulSoup(page["text"], "lxml")
    base = page["final_url"]

    result = {}
    result["url"] = url
    result["final_url"] = base
    result["http_status"] = page["status"]
    result["headers"] = page.get("headers", {})

    result["title"] = check_title(soup)
    result["meta_description"] = check_meta_description(soup)
    result["headings"] = check_headings(soup)
    result["content"] = check_word_count(soup)
    result["keywords"] = check_keywords(soup, keywords)
    result["images"] = check_images(soup, base)
    result["links"] = check_links(soup, base, session, max_check=max_links_check)
    result["canonical"] = check_canonical(soup, base)
    result["schema"] = check_schema(soup)
    result["lang"] = check_lang(soup)
    result["hreflang"] = check_hreflang(soup, base)
    result["meta_robots"] = check_meta_robots(soup, page.get("headers", {}))
    result["robots_txt"] = check_robots_txt(session, base)
    result["sitemap"] = check_sitemap(session, base)
    result["https"] = check_https(url, base)
    result["viewport"] = check_viewport(soup)
    result["deprecated"] = check_deprecated(soup)

    # lightweight issues summary (simple rules)
    issues = []
    if not result["title"]["ok"]:
        issues.append("Title length not optimal (50-60 chars recommended)")
    if not result["meta_description"]["ok"]:
        issues.append("Meta description length not optimal (120-160 chars recommended)")
    if not result["headings"]["has_one_h1"]:
        issues.append("Page should have exactly one H1")
    if not result["content"]["ok"]:
        issues.append("Low content word count (recommend >=300 words)")
    if result["images"]["missing_alt"] > 0:
        issues.append(f"{result['images']['missing_alt']} images missing alt text")
    if result["links"]["broken"] > 0:
        issues.append(f"{result['links']['broken']} broken links found (checked first {result['links']['checked']})")
    if not result["canonical"]["canonical"]:
        issues.append("Canonical tag not present")
    result["issues"] = issues

    return result
