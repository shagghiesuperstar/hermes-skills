#!/usr/bin/env python3
"""Validate every skills/<name>/SKILL.md in the library.

Usage: python3 scripts/validate.py [--root DIR]

Every violation is collected before exiting, so one run lists them all.
Prints "OK <n> skills" and exits 0 when clean; prints violations and exits 1 otherwise.
WARN lines are advisory: they are printed for review and never change the exit code.
build_catalog.py imports parse_library() so both scripts read skills the same way.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

AUTHOR = "Pixel Rainbow (shagghiesuperstar)"
LICENSE = "MIT"
NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
DESCRIPTION_START = "Use when"
TRIGGER_MAX = 60  # the first sentence ("Use when ...") must be a self-contained trigger within ~57 characters
DESCRIPTION_MAX = 400
TAG_RANGE = (2, 8)
BULLET_RANGE = (3, 8)
REQUIRED_H2 = ["Overview", "When to Use", "Features", "Benefits", "Procedure", "Pitfalls", "Verification"]
OPTIONAL_H2 = "Attribution"
BULLET_SECTIONS = ("Features", "Benefits")
IGNORED_NAMES = {".DS_Store"}
FENCE_RE = re.compile(r"^(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^(#{1,6})\s+(\S.*?)\s*$")
BULLET_RE = re.compile(r"^[-*] (\S.*?)\s*$")
SUPPORT_PATH_RE = re.compile(r"(?<![\w./-])(?:\./)?(?:scripts|references|templates|assets)/[\w./-]+")


def load_categories(root):
    """Category list from <root>/scripts/categories.json, in file order."""
    return json.loads((root / "scripts" / "categories.json").read_text(encoding="utf-8"))


def split_frontmatter(lines):
    """Return (index of the first body line, frontmatter text or None)."""
    if not lines or lines[0].strip() != "---":
        return 0, None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return idx + 1, "\n".join(lines[1:idx])
    return 0, None


def prose(lines, start):
    """Yield (1-based line number, text) for body lines outside fenced code blocks."""
    fence = None
    for idx in range(start, len(lines)):
        stripped = lines[idx].strip()
        if fence:
            if stripped.startswith(fence) and not stripped.strip(fence[0]):
                fence = None
            continue
        opener = FENCE_RE.match(stripped)
        if opener:
            fence = opener.group(1)
            continue
        yield idx + 1, lines[idx]


def bullet_items(lines):
    """Top-level bullets; an indented line continues the bullet above it."""
    items = []
    for line in lines:
        match = BULLET_RE.match(line)
        if match:
            items.append(match.group(1))
        elif items and line.startswith("  ") and line.strip():
            items[-1] += " " + line.strip()
    return items


def parse_skill(skill_dir, root, category_ids):
    """Check one skill directory. Returns (record, problems, warnings).

    The record is returned even when it has problems, so related_skills can still be resolved.
    """
    rel = skill_dir.relative_to(root).as_posix()
    path = f"{rel}/SKILL.md"
    problems, warnings = [], []

    def fail(message):
        problems.append(f"{path}: {message}")

    def warn(message):
        warnings.append(f"WARN {path}: {message}")

    record = {
        "name": skill_dir.name,
        "title": "",
        "category": "",
        "path": path,
        "tags": [],
        "description": "",
        "features": [],
        "benefits": [],
        "version": "",
        "related_skills": [],
    }

    extras = sorted(p.name for p in skill_dir.iterdir() if p.name not in IGNORED_NAMES and p.name != "SKILL.md")
    if extras:
        fail(f"skill dir must contain only SKILL.md, also found: {', '.join(extras)}")
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        fail("missing SKILL.md")
        return record, problems, warnings

    lines = skill_md.read_text(encoding="utf-8").splitlines()
    body_start, frontmatter = split_frontmatter(lines)
    if frontmatter is None:
        fail("no closed frontmatter block (--- ... ---) at the top of the file")
        fm = {}
    else:
        try:
            fm = yaml.safe_load(frontmatter)
        except yaml.YAMLError as exc:
            fm = None
            fail(f"frontmatter is not valid YAML: {' '.join(str(exc).split())}")
        if fm is None:
            fm = {}
        elif not isinstance(fm, dict):
            fail("frontmatter must be a mapping of keys")
            fm = {}

    name = fm.get("name")
    if not isinstance(name, str) or not NAME_RE.match(name):
        fail("name must match ^[a-z][a-z0-9-]*$")
    if isinstance(name, str) and name != skill_dir.name:
        fail(f"name '{name}' must equal the directory name '{skill_dir.name}'")

    description = fm.get("description")
    if not isinstance(description, str):
        fail("description must be a string")
    else:
        record["description"] = description
        if not description.startswith(DESCRIPTION_START):
            fail(f'description must start with "{DESCRIPTION_START}"')
        if len(description) > DESCRIPTION_MAX:
            fail(f"description is {len(description)} characters, max is {DESCRIPTION_MAX}")
        trigger = re.split(r"(?<=[.!?])\s", description, maxsplit=1)[0]
        if len(trigger) > TRIGGER_MAX:
            fail(f"description's first sentence is {len(trigger)} characters; the trigger must end within {TRIGGER_MAX}")

    version = fm.get("version")
    if not isinstance(version, str) or not SEMVER_RE.match(version):
        fail(f"version must be x.y.z (a string such as 1.0.0), got {version!r}")
    else:
        record["version"] = version

    if fm.get("author") != AUTHOR:
        fail(f"author must be '{AUTHOR}'")
    if fm.get("license") != LICENSE:
        fail(f"license must be '{LICENSE}'")

    metadata = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}
    hermes = metadata.get("hermes") if isinstance(metadata.get("hermes"), dict) else {}

    tags = hermes.get("tags")
    if not isinstance(tags, list) or not TAG_RANGE[0] <= len(tags) <= TAG_RANGE[1]:
        fail(f"metadata.hermes.tags must be a list of {TAG_RANGE[0]} to {TAG_RANGE[1]} strings")
    if isinstance(tags, list):
        record["tags"] = tags
        bad_tags = [t for t in tags if not isinstance(t, str) or not t or t != t.lower() or t != t.strip()]
        if bad_tags:
            fail(f"metadata.hermes.tags must be lowercase strings, bad: {bad_tags}")

    category = hermes.get("category")
    if not isinstance(category, str) or category not in category_ids:
        fail(f"metadata.hermes.category must be present and one of scripts/categories.json, got {category!r}")
    else:
        record["category"] = category

    related = fm.get("related_skills") or []
    if not isinstance(related, list) or not all(isinstance(r, str) for r in related):
        fail("related_skills must be a list of skill names")
    else:
        record["related_skills"] = related

    for line in lines[body_start:]:
        match = SUPPORT_PATH_RE.search(line)
        if match:
            warn(f"mentions support path '{match.group(0)}'")

    headings, sections, current = [], {}, None
    for line_no, line in prose(lines, body_start):
        match = HEADING_RE.match(line)
        if match:
            level, title = len(match.group(1)), match.group(2)
            headings.append((level, title, line_no))
            if level == 1:
                current = None
            elif level == 2:
                current = title
                sections.setdefault(title, [])
        elif current is not None:
            sections[current].append(line)

    h1s = [h for h in headings if h[0] == 1]
    if len(h1s) != 1:
        fail(f"body needs exactly one H1, found {len(h1s)}")
    else:
        record["title"] = h1s[0][1]
        first_h2 = next((no for level, _, no in headings if level == 2), None)
        if first_h2 is not None and h1s[0][2] > first_h2:
            fail("H1 must come before the first H2")

    h2_titles = [title for level, title, _ in headings if level == 2]
    if h2_titles not in (REQUIRED_H2, REQUIRED_H2 + [OPTIONAL_H2]):
        fail(
            f"H2 sections must be {', '.join(REQUIRED_H2)}, optionally then {OPTIONAL_H2}; "
            f"found: {', '.join(h2_titles) or 'none'}"
        )

    for section in BULLET_SECTIONS:
        items = bullet_items(sections.get(section, []))
        record[section.lower()] = items
        if section in sections and not BULLET_RANGE[0] <= len(items) <= BULLET_RANGE[1]:
            fail(f"{section} needs {BULLET_RANGE[0]} to {BULLET_RANGE[1]} top-level bullets, found {len(items)}")

    return record, problems, warnings


def parse_library(root):
    """Parse and check the whole library. Returns (records sorted by name, problems, warnings)."""
    category_ids = {c["id"] for c in load_categories(root)}
    skills_dir = root / "skills"
    records, problems, warnings = [], [], []
    if not skills_dir.is_dir():
        return records, problems, warnings

    for skill_dir in sorted(skills_dir.iterdir()):
        if skill_dir.name in IGNORED_NAMES:
            continue
        if not skill_dir.is_dir():
            problems.append(f"{skill_dir.relative_to(root).as_posix()}: only skill directories belong under skills/")
            continue
        if skill_dir.name.startswith((".", "_")):
            problems.append(f"{skill_dir.relative_to(root).as_posix()}: skill directory names must not start with '.' or '_'; Hermes taps skip them")
            continue
        record, found, notes = parse_skill(skill_dir, root, category_ids)
        records.append(record)
        problems.extend(found)
        warnings.extend(notes)

    paths_by_name = {}
    for record in records:
        paths_by_name.setdefault(record["name"], []).append(record["path"])
    for name, paths in sorted(paths_by_name.items()):
        if len(paths) > 1:
            problems.append(f"duplicate skill name '{name}': {', '.join(paths)}")

    for record in records:
        for target in record["related_skills"]:
            if target not in paths_by_name:
                problems.append(f"{record['path']}: related_skills entry '{target}' is not a skill in this repo")

    records.sort(key=lambda r: r["name"])
    return records, problems, warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate skills/<name>/SKILL.md.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repo root (default: this repo)")
    args = parser.parse_args(argv)

    records, problems, warnings = parse_library(args.root.resolve())
    for warning in warnings:
        print(warning)
    if problems:
        for problem in problems:
            print(problem)
        print(f"FAILED: {len(problems)} violation(s) across {len(records)} skill(s)")
        return 1
    print(f"OK {len(records)} skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
