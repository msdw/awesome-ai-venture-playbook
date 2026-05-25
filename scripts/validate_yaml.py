#!/usr/bin/env python3
"""Validate all YAML data files against required schema."""
import sys
import yaml
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"

REQUIRED_IDEA_FIELDS = [
    "id", "title", "summary", "category", "target_users",
    "pain_points", "difficulty", "risk_level", "tags", "source", "status"
]

REQUIRED_VENTURE_FIELDS = [
    "id", "name", "description", "category", "target_users",
    "stage", "business_model", "outcome", "lessons", "tags", "source", "status"
]

VALID_STATUSES = {"candidate", "needs_review", "accepted", "rejected", "duplicate", "deprecated"}
VALID_STAGES = {"idea", "prototype", "beta", "launched", "revenue", "shut_down", "acquired"}
REGULATED_INDUSTRIES = {"legal", "healthcare", "finance", "insurance"}

ERRORS = []
WARNINGS = []


def error(msg):
    ERRORS.append(msg)
    print(f"  ERROR: {msg}", file=sys.stderr)


def warn(msg):
    WARNINGS.append(msg)
    print(f"  WARN:  {msg}")


def load_yaml(path):
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        error(f"YAML parse error in {path.name}: {e}")
        return None
    except FileNotFoundError:
        error(f"File not found: {path}")
        return None


def validate_collection(path, collection_key, required_fields, name):
    print(f"\nValidating {path.name}...")
    data = load_yaml(path)
    if data is None:
        return

    items = data.get(collection_key, [])
    seen_ids = set()

    for i, item in enumerate(items):
        prefix = f"{collection_key}[{i}] id={item.get('id', '?')}"
        item_id = item.get("id")
        if item_id in seen_ids:
            error(f"{prefix}: duplicate id '{item_id}'")
        seen_ids.add(item_id)

        for field in required_fields:
            if field not in item:
                error(f"{prefix}: missing required field '{field}'")

        status = item.get("status")
        if status and status not in VALID_STATUSES:
            error(f"{prefix}: invalid status '{status}'")

        industries = item.get("industries", [])
        if any(ind in REGULATED_INDUSTRIES for ind in industries):
            if not item.get("compliance_notes"):
                warn(f"{prefix}: regulated industry but no compliance_notes")

    print(f"  Checked {len(items)} {name}, {len(seen_ids)} unique IDs")


def validate_ventures(path):
    print(f"\nValidating {path.name}...")
    data = load_yaml(path)
    if data is None:
        return

    ventures = data.get("ventures", [])
    seen_ids = set()

    for i, v in enumerate(ventures):
        prefix = f"ventures[{i}] id={v.get('id', '?')}"
        vid = v.get("id")
        if vid in seen_ids:
            error(f"{prefix}: duplicate id '{vid}'")
        seen_ids.add(vid)

        for field in REQUIRED_VENTURE_FIELDS:
            if field not in v:
                error(f"{prefix}: missing required field '{field}'")

        stage = v.get("stage")
        if stage and stage not in VALID_STAGES:
            error(f"{prefix}: invalid stage '{stage}'")

    print(f"  Checked {len(ventures)} ventures")


def validate_taxonomy(path, key):
    print(f"\nValidating {path.name}...")
    data = load_yaml(path)
    if data is None:
        return set()
    items = data.get(key, [])
    ids = {item["id"] for item in items if "id" in item}
    print(f"  Found {len(ids)} entries")
    return ids


def main():
    print("=== Validating YAML schemas ===")

    for fname, key in [
        ("categories.yaml", "categories"),
        ("business_models.yaml", "business_models"),
        ("industries.yaml", "industries"),
        ("roles.yaml", "roles"),
        ("tags.yaml", "tags"),
        ("tools.yaml", "tools"),
        ("channels.yaml", "channels"),
    ]:
        p = DATA / fname
        if p.exists():
            validate_taxonomy(p, key)

    if (DATA / "ideas.yaml").exists():
        validate_collection(DATA / "ideas.yaml", "ideas", REQUIRED_IDEA_FIELDS, "ideas")

    if (DATA / "ventures.yaml").exists():
        validate_ventures(DATA / "ventures.yaml")

    print(f"\n=== Summary ===\n  Errors: {len(ERRORS)}  Warnings: {len(WARNINGS)}")

    if ERRORS:
        print("\nFAILED", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nPASSED")


if __name__ == "__main__":
    main()
