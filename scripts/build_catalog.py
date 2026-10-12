#!/usr/bin/env python3
"""Build catalog.json and README.md from the skills in the library.

Usage: python3 scripts/build_catalog.py [--root DIR]

Runs the same checks as validate.py and writes nothing if any fail.
Output is deterministic: rerunning on an unchanged tree gives identical files.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import validate

REPO_NAME = "hermes-skills"
REPO_URL = "https://github.com/shagghiesuperstar/hermes-skills"
SITE_URL = "https://pixelrainbow.ai/skills/"
RAW_BASE = "https://raw.githubusercontent.com/shagghiesuperstar/hermes-skills/main/"
BLOB_BASE = "https://github.com/shagghiesuperstar/hermes-skills/blob/main/"
UPSTREAM_REPO = "NousResearch/hermes-agent"
MAX_REPOS_PER_SKILL = 4
KEYWORD_RE = re.compile(r"^[a-z0-9]+$")


def load_repos(root):
    return json.loads((root / "scripts" / "related_repos.json").read_text(encoding="utf-8"))


def words(text):
    """Lowercase alphanumeric tokens; hyphens and punctuation split words."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def related_repos_for(record, repos):
    """Upstream repo first, then keyword matches in file order, capped at MAX_REPOS_PER_SKILL."""
    tokens = words(" ".join([record["name"], *record["tags"], record["description"]]))
    upstream = [r for r in repos if r["name"] == UPSTREAM_REPO]
    matched = [r for r in repos if r["name"] != UPSTREAM_REPO and tokens & set(r["keywords"])]
    return (upstream + matched)[:MAX_REPOS_PER_SKILL]


def catalog_skill(record, repos):
    raw_url = RAW_BASE + record["path"]
    return {
        "name": record["name"],
        "title": record["title"],
        "category": record["category"],
        "tags": record["tags"],
        "description": record["description"],
        "features": record["features"],
        "benefits": record["benefits"],
        "version": record["version"],
        "path": record["path"],
        "raw_url": raw_url,
        "html_url": BLOB_BASE + record["path"],
        "install": f"hermes skills install {raw_url} --category {record['category']}",
        "related_skills": record["related_skills"],
        "related_repos": [
            {"name": r["name"], "url": r["url"], "description": r["description"]}
            for r in related_repos_for(record, repos)
        ],
    }


def category_rows(categories, skills):
    counts = {}
    for skill in skills:
        counts[skill["category"]] = counts.get(skill["category"], 0) + 1
    return [
        {"id": c["id"], "label": c["label"], "blurb": c["blurb"], "count": counts.get(c["id"], 0)}
        for c in categories
    ]


def table_cell(text):
    return " ".join(text.split()).replace("|", "\\|")


def category_list(categories):
    return "\n".join(
        f"- **{c['label']}** (`{c['id']}`), {c['count']} skill(s): {c['blurb']}" for c in categories
    )


def index_table(skills):
    if not skills:
        return "_No skills published yet._"
    rows = ["| Skill | Category | What it does |", "| --- | --- | --- |"]
    for skill in skills:
        rows.append(f"| [`{skill['name']}`]({skill['path']}) | {skill['category']} | {table_cell(skill['description'])} |")
    return "\n".join(rows)


def repo_list(repos):
    return "\n".join(f"- [{r['name']}]({r['url']}): {r['description']}" for r in repos)


def render_readme(template, catalog, repos):
    skills = catalog["skills"]
    filled = {
        "{{COUNT}}": str(catalog["count"]),
        "{{CATEGORY_LIST}}": category_list(catalog["categories"]),
        "{{INDEX_TABLE}}": index_table(skills),
        "{{INSTALL_EXAMPLE}}": skills[0]["install"] if skills else "# No skills published yet",
        "{{REPO_LIST}}": repo_list(repos),
    }
    text = template
    for placeholder, value in filled.items():
        text = text.replace(placeholder, value)
    return text


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build catalog.json and README.md from skills/.")
    parser.add_argument("--root", type=Path, default=validate.REPO_ROOT, help="repo root (default: this repo)")
    args = parser.parse_args(argv)
    root = args.root.resolve()

    records, problems, warnings = validate.parse_library(root)
    repos = load_repos(root)
    for repo in repos:
        for keyword in repo["keywords"]:
            if not KEYWORD_RE.match(keyword):
                problems.append(f"scripts/related_repos.json: keyword '{keyword}' for {repo['name']} must be one lowercase word")
    for warning in warnings:
        print(warning)
    if problems:
        for problem in problems:
            print(problem)
        print(f"FAILED: {len(problems)} violation(s); nothing written")
        return 1

    categories = validate.load_categories(root)
    template = (root / "scripts" / "readme_template.md").read_text(encoding="utf-8")
    skills = [catalog_skill(record, repos) for record in records]
    catalog = {
        "name": REPO_NAME,
        "repo": REPO_URL,
        "site": SITE_URL,
        "license": validate.LICENSE,
        "count": len(skills),
        "categories": category_rows(categories, skills),
        "skills": skills,
    }

    (root / "catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (root / "README.md").write_text(render_readme(template, catalog, repos), encoding="utf-8")
    print(f"Wrote catalog.json and README.md for {len(skills)} skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
