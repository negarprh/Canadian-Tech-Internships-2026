# .github/scripts/check_closed_jobs.py
import re
import pathlib
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

README = pathlib.Path("README.md")

APPLY_PATTERN = re.compile(
    r"\[!\[Apply\]\([^)]+?\)\]\((https?://[^)\s]+)\)", re.IGNORECASE
)

CLOSED_PHRASES = [
    "sorry, this position has been filled",
    "no longer accepting",
    "no longer available",
    "requisition closed",
    "job not found",
    "position has been filled",
    "this job posting is no longer active",
    "this posting has closed",
    "is no longer posted",
    "position closed",
    "page not found",
    "No longer accepting applications.",
    "this job is closed",
    "this position is closed",
    "this role is closed",
    "this vacancy is closed",
    "this opportunity is closed",
    "this listing is closed",
    "no longer available",
    "the job you are looking for is no longer available",
]

UA_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
    "Accept-Language": "en,en-US;q=0.9",
}


def make_session():
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5,
                  status_forcelist=[429, 500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update(UA_HEADERS)
    return s


def url_is_closed(s: requests.Session, url: str) -> bool:
    try:
        r = s.head(url, allow_redirects=True, timeout=15)
        # Many ATS block HEAD; fall back to GET or treat 405/403 specially.
        if r.status_code >= 400 or r.status_code in (403, 405):
            r = s.get(url, allow_redirects=True, timeout=20)
        if r.status_code >= 400:
            return True
        text = r.text.lower()
        return any(p in text for p in CLOSED_PHRASES)
    except requests.RequestException:
        return True


def main():
    s = make_session()
    content = README.read_text(encoding="utf-8")
    changed = False

    def repl(m):
        nonlocal changed
        url = m.group(1)
        print(f"Checking: {url}")
        if url_is_closed(s, url):
            print(f"❌ Closed: {url}")
            changed = True
            return "Closed🔒"  # remove the Apply button
        print(f"✅ Active: {url}")
        return m.group(0)

    new_content = APPLY_PATTERN.sub(repl, content)
    if changed:
        README.write_text(new_content, encoding="utf-8")
        print("✅ Updated README.")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
