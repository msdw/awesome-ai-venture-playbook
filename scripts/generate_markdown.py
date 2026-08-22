#!/usr/bin/env python3
"""Generate browseable index pages from YAML data."""
import sys
import argparse
import yaml
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
IDEAS_DIR = ROOT / "ideas"
VENTURES_DIR = ROOT / "ventures"

HEADER = "<!-- AUTO-GENERATED — do not edit manually. Run: python scripts/generate_markdown.py -->\n\n"

# Pages that --check found out of date. main() exits non-zero when this is not
# empty, so a data change committed without regenerating its pages fails the gate
# instead of passing silently.
STALE = []

# Set from --force: generate-pages.yml passes it so a page is rewritten even
# when unchanged, which is what makes the auto-commit step deterministic.
FORCE = False


def load_yaml(path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_accepted(path, key):
    data = load_yaml(path)
    if not data:
        return []
    return [i for i in data.get(key, []) if i.get("status") == "accepted"]


def write_page(path, content, check_only):
    path.parent.mkdir(parents=True, exist_ok=True)
    full = HEADER + content
    if not FORCE and path.exists() and path.read_text(encoding="utf-8") == full:
        return False
    if check_only:
        STALE.append(path)
        print(f"  WOULD WRITE: {path.relative_to(ROOT)}")
        return True
    path.write_text(full, encoding="utf-8")
    print(f"  WROTE: {path.relative_to(ROOT)}")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--force", action="store_true",
                        help="Rewrite every page even when its content is unchanged")
    args = parser.parse_args()

    global FORCE
    FORCE = args.force

    print(f"=== {'Checking' if args.check else 'Generating'} Markdown pages ===")

    ideas = load_accepted(DATA / "ideas.yaml", "ideas")
    ventures = load_accepted(DATA / "ventures.yaml", "ventures")
    print(f"Loaded: {len(ideas)} ideas, {len(ventures)} ventures")

    # Ideas index
    if ideas:
        lines = ["# AI Ideas\n\n"]
        for idea in ideas:
            lines.append(f"- [{idea['title']}](../data/ideas.yaml) — {idea.get('summary','')[:100].strip()}\n")
        write_page(IDEAS_DIR / "index.md", "".join(lines), args.check)

    # Ventures index
    if ventures:
        lines = ["# AI Ventures\n\n"]
        for v in ventures:
            lines.append(f"- [{v['name']}](../data/ventures.yaml) — {v.get('description','')[:100].strip()}\n")
        write_page(VENTURES_DIR / "index.md", "".join(lines), args.check)

    if args.check and STALE:
        print(f"\n{len(STALE)} page(s) out of date — run: python scripts/generate_markdown.py")
        sys.exit(1)

    print("\nDone")


if __name__ == "__main__":
    main()
