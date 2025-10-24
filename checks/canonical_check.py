from urllib.parse import urlparse
from bs4 import BeautifulSoup

def _clean_url(url):
    """
    Normalizes URLs for canonical comparison.
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip('/')


def _get_soup(response):
    """
    Returns BeautifulSoup object for response HTML.
    """
    return BeautifulSoup(response.body, "lxml", from_encoding="utf-8")


def run_audit(response, audit_level):
    """
    Checks canonical URL correctness, missing tags, AMP linking.
    """
    try:
        soup = _get_soup(response)
    except Exception as e:
        return {"error": f"Failed to parse content: {str(e)}"}

    current_url = response.url
    canonical_tag = soup.find("link", rel="canonical")
    canonical_url = canonical_tag.get("href") if canonical_tag and canonical_tag.get("href") else None
    amphtml_tag = soup.find("link", rel="amphtml")
    amphtml_url = amphtml_tag.get("href") if amphtml_tag and amphtml_tag.get("href") else None
    is_amp_page = "/amp/" in current_url.lower()

    canonical_mismatch = False
    canonical_missing = False
    note = ""

    if canonical_url:
        normalized_current = _clean_url(current_url)
        normalized_canonical = _clean_url(canonical_url)

        if not urlparse(canonical_url).netloc:
            canonical_mismatch = True
            note = f"FAIL: Canonical must use absolute URL (found '{canonical_url}')."
        elif normalized_current != normalized_canonical:
            canonical_mismatch = True
            note = f"FAIL: Canonical points to different URL ({canonical_url})."
            if is_amp_page and "/amp/" not in canonical_url.lower():
                canonical_mismatch = False
                note = f"PASS: AMP correctly points to non-AMP page ({canonical_url})."
        else:
            note = f"PASS: Canonical correctly points to itself ({canonical_url})."
    else:
        canonical_missing = True
        note = "WARN: No canonical tag found. Add if duplicate content exists."

    if amphtml_url and not is_amp_page:
        note += f" | INFO: AMP version linked: {amphtml_url}."
    elif not amphtml_url and is_amp_page:
        note += " | WARN: AMP page found, missing canonical to non-AMP page."

    return {
        "canonical_url": canonical_url,
        "current_url": current_url,
        "is_amp_page": is_amp_page,
        "canonical_mismatch": canonical_mismatch,
        "canonical_missing": canonical_missing,
        "amphtml_url": amphtml_url,
        "note": note
    }
