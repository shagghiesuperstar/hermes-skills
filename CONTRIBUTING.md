# Contributing

Thanks for helping build the Hermes skills library. Each skill is one folder, `skills/<category>/<name>/`, holding a single `SKILL.md`.

## The SKILL.md contract

- Frontmatter: `name` (matches the folder), `description` (starts with `Use when`, 400 characters or fewer), `version` (`x.y.z`), `author` (`Pixel Rainbow (shagghiesuperstar)`), `license` (`MIT`), `metadata.hermes.tags` (2 to 8 lowercase strings), `metadata.hermes.category` (matches the parent folder), and optional `related_skills` (names of skills in this repo).
- Body: one H1, then H2 sections in this order: Overview, When to Use, Features, Benefits, Procedure, Pitfalls, Verification, and optionally Attribution last. Features and Benefits each list 3 to 8 bullets.
- Skills stand alone. The skill folder holds only `SKILL.md`, and the body must not point at `scripts/`, `references/`, `templates/` or `assets/`.

`scripts/validate.py` enforces these rules and prints every violation it finds. A body mention of a support path prints a `WARN` line for review instead of failing the run.

## Before you open a pull request

```bash
python3 scripts/validate.py
python3 scripts/build_catalog.py
```

`validate.py` must print `OK <n> skills`. `build_catalog.py` regenerates `catalog.json` and `README.md`, so commit both with your change.

## Sanitization rule

Skills are public. Remove everything personal, machine-specific, network-specific or customer-specific before you commit:

- No personal names, email addresses, phone numbers or social handles.
- No hostnames, IP addresses, private network names or local home-directory paths.
- No API keys, tokens, passwords or other credentials.
- No customer, order or account data.

Replace each of these with a placeholder in backticks, such as `<your-api-key>`, `<host>` or `<project-dir>`, so it renders on GitHub.

## Pull request flow

1. Fork the repository and create a branch.
2. Keep each pull request to one skill or one fix.
3. Run both scripts and confirm `validate.py` prints `OK`.
4. Open the pull request with a short description of what the skill does and how you tested it.
