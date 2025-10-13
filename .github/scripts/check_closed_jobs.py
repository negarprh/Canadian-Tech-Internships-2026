import re, time, pathlib, requests, urllib.parse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

README = pathlib.Path("README.md")
REPORT = pathlib.Path("link-check-report.md")

APPLY_MD = re.compile(r"\[!\[Apply\]\([^)]+?\)\]\((https?://[^)\s]+)\)", re.I)

CLOSED_PHRASES = {
    "generic": [
        "this position has been filled",
        "no longer accepting",
        "no longer available",
        "job not found",
        "this job posting is no longer active",
        "this posting has closed",
        "position closed",
        "requisition closed",
        "is no longer posted",
        "no longer posted",
        "job unavailable",
    ],
    "workday": ["job closed", "no longer accepting applications", "job is no longer posted"],
    "greenhouse": ["this job is no longer available", "looks like this job no longer exists"],
    "eightfold": ["this job is no longer available", "job not found"],
    "lever": ["this job is no longer available"],
    "successfactors": ["this job is no longer available", "this position has been filled"],
}
OPEN_PHRASES = ["apply now", "submit application", "start your application"]

SEARCH_REDIRECT_HINTS = [
    "/jobs/search", "/jobsearch", "/careers/search", "/careers?","/search/?","/search?"
]

UA = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
}

def session():
    s = requests.Session()
    r = Retry(total=3, backoff_factor=0.6, status_forcelist=[429,500,502,503,504])
    s.mount("https://", HTTPAdapter(max_retries=r))
    s.headers.update(UA)
    return s

def domain_key(u:str):
    h = urllib.parse.urlparse(u).hostname or ""
    if "workday" in h or "myworkdayjobs" in h: return "workday"
    if "greenhouse" in h: return "greenhouse"
    if "eightfold" in h: return "eightfold"
    if "lever.co" in h: return "lever"
    if "successfactors" in h or "sapfioritalent" in h: return "successfactors"
    return "generic"

def looks_like_search(url:str):
    path = urllib.parse.urlparse(url).path.lower()
    return any(h in url.lower() or h in path for h in SEARCH_REDIRECT_HINTS)

def is_closed(s, url:str):
    try:
        r = s.head(url, allow_redirects=True, timeout=15)
        final = r.url
        # head often blocked -> GET
        if r.status_code >= 400 or r.status_code in (403,405):
            r = s.get(url, allow_redirects=True, timeout=20)
            final = r.url
        # redirect to generic search/list page => closed
        if looks_like_search(final) and not urllib.parse.urlparse(final).path.endswith(("job","jobs")):
            return True, f"Redirected to search: {final}"
        if r.status_code >= 400:
            return True, f"HTTP {r.status_code}"
        text = r.text.lower()
        k = domain_key(url)
        closed_hits = any(p in text for p in CLOSED_PHRASES["generic"] + CLOSED_PHRASES.get(k, []))
        open_hits = any(p in text for p in OPEN_PHRASES)
        if closed_hits and not open_hits:
            return True, f"Closed phrase ({k})"
        return False, "OK"
    except requests.RequestException as e:
        return True, f"Exception: {type(e).__name__}"

def main():
    s = session()
    md = README.read_text(encoding="utf-8")
    report_lines = ["# Link Check Report\n"]
    changed = False

    def repl(m):
        nonlocal changed
        url = m.group(1)
        time.sleep(0.5)  # be polite; reduce blocks
        closed, reason = is_closed(s, url)
        report_lines.append(f"- {url} → {'CLOSED' if closed else 'OPEN'} ({reason})")
        if closed:
            changed = True
            return "Closed🔒"
        return m.group(0)

    new_md = APPLY_MD.sub(repl, md)
    REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    if changed:
        README.write_text(new_md, encoding="utf-8")
        print("Updated README with Closed🔒. See link-check-report.md for details.")
    else:
        print("No changes. See link-check-report.md for details.")

if __name__ == "__main__":
    main()
