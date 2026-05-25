#!/usr/bin/env python3
"""Discover new AI venture and idea candidates from public sources."""
import sys
import json
import argparse
import datetime
import time
from pathlib import Path
from urllib.request import urlopen, Request

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"

GITHUB_API = "https://api.github.com"
HN_SEARCH_API = "https://hn.algolia.com/api/v1"


def fetch_json(url):
    headers = {"User-Agent": "awesome-ai-venture-playbook/1.0"}
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  Fetch error: {e}", file=sys.stderr)
        return None


def discover_from_github(mode):
    print("\n[GitHub] Searching AI venture repos...")
    candidates = []
    days = 7 if mode == "weekly" else 1
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    url = f"{GITHUB_API}/search/repositories?q=ai+saas+OR+llm+tool+language:python+created:>{since}&sort=stars&per_page=15"
    data = fetch_json(url)
    if not data:
        return candidates
    for repo in data.get("items", []):
        stars = repo.get("stargazers_count", 0)
        if stars < 30:
            continue
        candidates.append({
            "id": f"candidate_{repo['full_name'].replace('/', '_').lower()}",
            "title": repo.get("name", ""),
            "summary": repo.get("description") or "No description",
            "category": "ai_saas",
            "target_users": ["developer"],
            "pain_points": ["See repository"],
            "difficulty": "medium",
            "risk_level": "medium",
            "tags": repo.get("topics", [])[:5] or ["automation"],
            "source": repo.get("html_url", ""),
            "status": "candidate",
            "_meta": {"stars": stars, "source": "github", "discovered_at": datetime.datetime.utcnow().isoformat()}
        })
        print(f"  {repo['full_name']} ({stars} stars)")
        time.sleep(0.2)
    return candidates


def save_candidates(candidates, dry_run):
    if not candidates:
        print("\nNo new candidates found")
        return
    print(f"\nFound {len(candidates)} candidates")
    if dry_run:
        print("DRY RUN — not saving")
        return

    import yaml
    ideas_path = DATA / "ideas.yaml"
    data = {}
    if ideas_path.exists():
        with open(ideas_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

    existing_ids = {i["id"] for i in data.get("ideas", [])}
    new = [c for c in candidates if c["id"] not in existing_ids]

    if not new:
        print("All candidates already exist")
        return

    data.setdefault("ideas", []).extend(new)
    with open(ideas_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"Added {len(new)} new candidates")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["weekly", "daily"], default="weekly")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"=== Discovering new entries (mode={args.mode}) ===")
    candidates = discover_from_github(args.mode)
    save_candidates(candidates, args.dry_run)
    print("\nDone")


if __name__ == "__main__":
    main()
