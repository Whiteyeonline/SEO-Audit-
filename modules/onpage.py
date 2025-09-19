# modules/onpage.py
import requests
import re
import tldextract
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import Counter
import math

# Limits & timeouts
MAX_LINKS_TO_CHECK = 100
REQUEST_TIMEOUT = 8

STOPWORDS = set([
    "the", "and", "or", "for", "to", "of", "in", "on", "at", "is", "a", "an", "with",
    "by", "this", "that", "from", "it", "as", "be", "are", "was", "were", "but", "if", "then",
    "we", "you", "they", "their", "our", "has", "have", "will", "can", "also", "not", "i"
])

def _safe_get(session, url, method="get", **kwargs):
    try:
        if method == "head":
            return session.head(url, allow_redirects=True, timeout=REQUEST_TIMEOUT, **kwargs)
        return session.get(url, allow_redirects=True, timeout=REQUEST_TIMEOUT, **kwargs)
    except Exception:
        return None

def fetch_page(session, url):
    r = _safe_get(session, url, method="get", headers={"User-Agent": "Mozilla/5.0"})
    if r is None:
        return {"error": True, "message": f"Failed to fetch {url}"}
    return {"text": r.text, "status": r.status_code, "final_url": r.url, "headers": dict(r.headers)}

# ----- Basic tag checks -----
def check_title(soup):
    try:
        t = soup.title.string.strip() if soup.title and soup.title.string else ""
    except Exception:
        t = ""
    return {"value": t, "length": len(t), "ok": 50 <= len(t) <= 60}

def check_meta_description(soup):
    tag = soup.find("meta", attrs={"name": "description"})
    desc = tag.get("content","").strip() if tag and tag.get("content") else ""
    return {"value": desc, "length": len(desc), "ok": 120 <= len(desc) <= 160}

def check_headings(soup):
    counts = {f"h{i}": len(soup.find_all(f"h{i}")) for i in range(1,7)}
    return {"counts": counts, "has_one_h1": counts.get("h1",0) == 1}

# ----- Content & readability -----
def _count_sentences(text):
    # simple sentence splitter
    sentences = re.split(r'[.!?]+', text)
    return max(1, sum(1 for s in sentences if s.strip()))

def _syllables_in_word(word):
    # heuristic syllable counter
    word = word.lower()
    word = re.sub(r'[^a-z]', '', word)
    if not word:
        return 0
    vowels = 'aeiouy'
    syll = 0
    prev_was_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_was_vowel:
            syll += 1
        prev_was_vowel = is_vowel
    # drop silent 'e'
    if word.endswith('e') and syll > 1:
        syll -= 1
    # minimum 1
    return syll if syll > 0 else 1

def compute_readability(text):
    words = re.findall(r'\w+', text)
    word_count = max(1, len(words))
    sentence_count = _count_sentences(text)
    syllables = sum(_syllables_in_word(w) for w in words)
    # Flesch Reading Ease
    try:
        fre = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllables / word_count)
        fre = round(fre, 2)
    except Exception:
        fre = None
    return {"words": word_count, "sentences": sentence_count, "syllables": syllables, "flesch_reading_ease": fre}

def keyword_extraction(text, top_n=20):
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    cleaned = [w for w in words if w not in STOPWORDS]
    freq = Counter(cleaned)
    most = freq.most_common(top_n)
    return [{"keyword": w, "count": c} for w, c in most]

# ----- Images (including AMP & noscript) -----
def _resolve_src(src, base):
    try:
        return urljoin(base, src)
    except:
        return src or ""

def gather_images(soup, base_url):
    imgs = []
    # normal <img>
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy") or ""
        src = _resolve_src(src, base_url)
        alt = img.get("alt") or ""
        imgs.append({"src": src, "alt": alt.strip()})
    # amp-img
    for amp in soup.find_all("amp-img"):
        src = amp.get("src") or amp.get("data-src") or ""
        src = _resolve_src(src, base_url)
        alt = amp.get("alt") or ""
        imgs.append({"src": src, "alt": alt.strip(), "amp": True})
    # images inside <noscript> (often used in AMP)
    for nos in soup.find_all("noscript"):
        try:
            inner = BeautifulSoup(nos.decode_contents(), "lxml")
            for img in inner.find_all("img"):
                src = img.get("src") or ""
                src = _resolve_src(src, base_url)
                alt = img.get("alt") or ""
                imgs.append({"src": src, "alt": alt.strip(), "noscript": True})
        except Exception:
            continue
    # dedupe by src while preserving order
    seen = set()
    out = []
    for i in imgs:
        s = i.get("src") or ""
        if not s:
            continue
        if s in seen:
            continue
        seen.add(s)
        out.append(i)
    missing_alt = [i["src"] for i in out if not i.get("alt")]
    return {"images": out, "total": len(out), "missing_alt_count": len(missing_alt), "missing_alt_examples": missing_alt[:30]}

# ----- Links (+ broken list) -----
def check_links(soup, base_url, session, max_check=MAX_LINKS_TO_CHECK):
    raw_links = []
    for a in soup.find_all("a", href=True):
        href = a.get("href").strip()
        if href.startswith("mailto:") or href.startswith("tel:") or href.startswith("#"):
            continue
        raw_links.append(urljoin(base_url, href))
    # dedupe
    links = list(dict.fromkeys(raw_links))
    total = len(links)
    domain = tldextract.extract(base_url).registered_domain or urlparse(base_url).netloc
    internal = external = 0
    broken = []
    checked = 0
    for link in links:
        if checked >= max_check:
            break
        checked += 1
        try:
            r = _safe_get(session, link, method="head", headers={"User-Agent":"Mozilla/5.0"})
            if r is None:
                r = _safe_get(session, link, method="get", headers={"User-Agent":"Mozilla/5.0"})
            if r is None:
                broken.append({"url": link, "status": None, "error": "request_failed"})
            elif r.status_code >= 400:
                broken.append({"url": link, "status": r.status_code})
            # classify
            parsed = urlparse(link)
            if domain and domain in parsed.netloc:
                internal += 1
            else:
                external += 1
        except Exception as e:
            broken.append({"url": link, "status": None, "error": str(e)})
    return {"total": total, "checked": checked, "internal": internal, "external": external, "broken_count": len(broken), "broken_list": broken, "limited_to": max_check}

# ----- canonical, schema, hreflang, robots, sitemap, viewport, https -----
def check_canonical(soup, base):
    tag = soup.find("link", rel=lambda r: r and "canonical" in r)
    return {"canonical": urljoin(base, tag["href"])} if tag and tag.get("href") else {"canonical": None}

def check_schema(soup):
    scripts = soup.find_all("script", type="application/ld+json")
    samples = []
    for s in scripts[:5]:
        try:
            text = s.string or ""
            samples.append(text.strip()[:500])
        except:
            continue
    return {"schema_blocks": len(scripts), "sample": samples}

def check_lang(soup):
    html_tag = soup.find("html")
    return {"lang": html_tag.get("lang") if html_tag and html_tag.get("lang") else None}

def check_hreflang(soup, base):
    tags = []
    for t in soup.find_all("link", attrs={"rel": "alternate"}):
        hreflang = t.get("hreflang")
        href = t.get("href")
        if hreflang and href:
            tags.append({"hreflang": hreflang, "href": urljoin(base, href)})
    return {"hreflangs": tags}

def check_meta_robots(soup, headers):
    meta = soup.find("meta", attrs={"name": "robots"})
    meta_val = meta.get("content") if meta and meta.get("content") else None
    x_robots = headers.get("X-Robots-Tag") if headers else None
    return {"meta_robots": meta_val, "x_robots": x_robots}

def check_robots_txt(session, base):
    robots_url = urljoin(base, "/robots.txt")
    r = _safe_get(session, robots_url, headers={"User-Agent":"Mozilla/5.0"})
    if r and r.status_code == 200:
        return {"found": True, "snippet": r.text[:1000]}
    return {"found": False}

def check_sitemap(session, base):
    for path in ["/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml"]:
        u = urljoin(base, path)
        r = _safe_get(session, u, headers={"User-Agent":"Mozilla/5.0"})
        if r and r.status_code == 200 and ("<urlset" in r.text or "<sitemapindex" in r.text):
            return {"found": True, "url": u}
    return {"found": False}

def check_viewport(soup):
    meta = soup.find("meta", attrs={"name": "viewport"})
    return {"viewport": bool(meta)}

def check_https(original, final):
    return {"original_https": original.lower().startswith("https://"), "final_https": final.lower().startswith("https://")}

def detect_amp(soup, final_url):
    # if page contains <html amp> or <amp> tags or '/amp' in url
    amp_present = bool(soup.find("amp-img") or soup.find(attrs={"⚡": True}) or re.search(r'/amp', final_url))
    return {"is_amp": amp_present}

# ----- recommended title & meta generation -----
def recommend_title(orig_title, max_len=60):
    if not orig_title:
        return ""
    # remove site suffix after | or - or —
    first = re.split(r'[\|\-—–]+', orig_title)[0].strip()
    words = first.split()
    out = []
    for w in words:
        if len(" ".join(out + [w])) <= max_len:
            out.append(w)
        else:
            break
    suggested = " ".join(out)
    if len(suggested) > max_len:
        suggested = suggested[:max_len].rsplit(" ",1)[0]
    return suggested

def recommend_meta(orig_meta, min_len=120, max_len=160):
    if not orig_meta:
        return ""
    # shorten to max_len but try to cut at sentence end
    if len(orig_meta) <= max_len:
        return orig_meta
    snippet = orig_meta[:max_len]
    # try to cut to last sentence-like boundary
    m = re.search(r'([.!?])\s', snippet[::-1])
    # simpler: cut to last full stop before limit if exists
    cut = snippet.rfind('. ')
    if cut != -1 and cut >= 60:
        return snippet[:cut+1].strip()
    # fallback: return first max_len characters (trim trailing word)
    return snippet.rsplit(' ',1)[0].strip()

# ----- main run -----
def run(url, keywords=None, max_links_check=MAX_LINKS_TO_CHECK):
    session = requests.Session()
    page = fetch_page(session, url)
    if page.get("error"):
        return {"error": True, "message": page.get("message"), "url": url}

    soup = BeautifulSoup(page["text"], "lxml")
    base = page["final_url"]
    text_body = soup.get_text(" ", strip=True)

    result = {}
    result["url"] = url
    result["final_url"] = base
    result["http_status"] = page["status"]
    result["headers"] = page.get("headers", {})

    # Core checks
    result["title"] = check_title(soup)
    result["meta_description"] = check_meta_description(soup)
    result["headings"] = check_headings(soup)
    # content/readability/keywords
    result["content"] = {"word_count": len(re.findall(r'\w+', text_body))}
    result["readability"] = compute_readability(text_body)
    result["keywords"] = {"top": keyword_extraction(text_body, top_n=20)}
    # images (AMP-aware)
    imgs = gather_images(soup, base)
    result["images"] = imgs
    # links
    result["links"] = check_links(soup, base, session, max_check=max_links_check)
    # canonical, schema, etc.
    result["canonical"] = check_canonical(soup, base)
    result["schema"] = check_schema(soup)
    result["lang"] = check_lang(soup)
    result["hreflang"] = check_hreflang(soup, base)
    result["meta_robots"] = check_meta_robots(soup, page.get("headers", {}))
    result["robots_txt"] = check_robots_txt(session, base)
    result["sitemap"] = check_sitemap(session, base)
    result["https"] = check_https(url, base)
    result["viewport"] = check_viewport(soup)
    result["deprecated"] = {"deprecated_tags": [t for t in ["font","center","marquee"] if soup.find(t)]}
    result["amp"] = detect_amp(soup, base)

    # recommended title & meta (human-editable)
    result["recommendations"] = {
        "suggested_title": recommend_title(result["title"].get("value","")),
        "suggested_meta": recommend_meta(result["meta_description"].get("value",""))
    }

    # issues (detailed)
    issues = []
    if not result["title"].get("ok", False):
        issues.append("Title length not optimal (50-60 chars recommended)")
    if not result["meta_description"].get("ok", False):
        issues.append("Meta description length not optimal (120-160 chars recommended)")
    if not result["headings"].get("has_one_h1", False):
        issues.append("Page should have exactly one H1")
    if result["links"].get("broken_count",0) > 0:
        issues.append(f"{result['links']['broken_count']} broken links found (checked first {result['links']['checked']})")
    if result["images"].get("missing_alt_count",0) > 0:
        issues.append(f"{result['images']['missing_alt_count']} images missing alt text (AMP-aware)")
    if not result["sitemap"].get("found"):
        issues.append("Sitemap not found at common locations (sitemap.xml)")
    result["issues"] = issues

    return result
