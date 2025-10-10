import re
import requests
import pathlib

README = pathlib.Path("README.md")

# Finds all markdown Apply buttons with a link (e.g. [![Apply](...)](https://...))
APPLY_PATTERN = re.compile(
    r"\[!\[Apply\]\([^\)]*Apply[^\)]*\)\]\((https?://[^\s)]+)\)",
    re.IGNORECASE,
)


def is_closed(url):
    """Return True if the link is dead or unreachable."""
    try:
        # HEAD first (fast), fallback to GET if needed
        res = requests.head(url, allow_redirects=True, timeout=10)
        if res.status_code >= 400:
            return True
        # Optional: confirm with GET to avoid false positives
        if res.status_code in (403, 405):  # Some sites block HEAD
            res = requests.get(url, allow_redirects=True, timeout=10)
            if res.status_code >= 400:
                return True
        return False
    except requests.RequestException:
        return True  # Treat network issues as closed


def main():
    text = README.read_text(encoding="utf-8")
    changed = False

    def replacer(match):
        nonlocal changed
        url = match.group(1)
        print(f"Checking: {url}")
        if is_closed(url):
            changed = True
            print(f"❌ Closed: {url}")
            return "Closed🔒"
        print(f"✅ Active: {url}")
        return match.group(0)

    new_text = APPLY_PATTERN.sub(replacer, text)

    if changed:
        README.write_text(new_text, encoding="utf-8")
        print("✅ Updated README with Closed🔒 tags.")
    else:
        print("✅ No closed links found.")


if __name__ == "__main__":
    main()
