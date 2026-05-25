#!/usr/bin/env python3
"""Check URLs in Markdown and YAML files for broken links."""
import sys
import re
import time
import argparse
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).parent.parent
URL_PATTERN = re.compile(r'https?://[^\s\)\]\"\'<>]+')
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv"}
SKIP_DOMAINS = {"localhost", "127.0.0.1", "example.com"}
REQUEST_DELAY = 1.0
TIMEOUT = 10
broken = []
checked = set()


def check_url(url, source_file):
    url = url.rstrip(".,;:)'\"")
    if url in checked:
        return True
    checked.add(url)
    domain = re.sub(r'^https?://', '', url).split('/')[0]
    if domain in SKIP_DOMAINS:
        return True
    try:
        req = Request(url, headers={"User-Agent": "awesome-ai-link-checker/1.0"})
        resp = urlopen(req, timeout=TIMEOUT)
        time.sleep(REQUEST_DELAY)
        return resp.status < 400
    except HTTPError as e:
        if e.code == 429:
            return True
        broken.append((url, f"HTTP {e.code}", source_file))
        return False
    except Exception as e:
        broken.append((url, str(e)[:50], source_file))
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hard", action="store_true")
    args = parser.parse_args()

    print("=== Checking links ===")
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".yaml", ".yml"}:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for url in URL_PATTERN.findall(text):
            check_url(url, str(path.relative_to(ROOT)))

    print(f"\nChecked: {len(checked)}  Broken: {len(broken)}")
    if broken:
        for url, reason, src in broken:
            print(f"  {src}: {url} — {reason}", file=sys.stderr)
        if args.hard:
            sys.exit(1)
    else:
        print("All links OK")


if __name__ == "__main__":
    main()
