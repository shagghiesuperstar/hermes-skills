# Hermes Skills

Reusable skills for [Hermes Agent](https://hermes-agent.nousresearch.com/). Every skill is sanitized of personal, machine and network data.

Browse the library on the web at [pixelrainbow.ai/skills](https://pixelrainbow.ai/skills/).

## What is this

Generic, reusable Hermes Agent skills from Pixel Rainbow. Each one is written to work on any machine: names, hostnames, addresses, paths and secrets are replaced with `<placeholders>` that you fill in.

## Install

Install any skill straight from its raw URL:

```bash
{{INSTALL_EXAMPLE}}
```

`--category` is optional; the docs show it on the direct-URL form (`--category productivity`). Use the skill's category from this repo.

Per the Hermes docs: Install SKILL.md directly from any HTTP(S) URL ([skills guide](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)).

## Skill format

Each skill is one folder, `skills/<category>/<name>/`, holding a single `SKILL.md`.

- Frontmatter: `name` (matches the folder), `description` (starts with "Use when", 400 characters or fewer), `version` (x.y.z), `author`, `license`, `metadata.hermes.tags` (2 to 8 lowercase strings), `metadata.hermes.category` (matches the folder), and optional `related_skills` (skills in this repo only).
- Body: one H1, then H2 sections in this order: Overview, When to Use, Features, Benefits, Procedure, Pitfalls, Verification, and optionally Attribution. Features and Benefits each list 3 to 8 bullets.

## Index

Skills in this library: {{COUNT}}. Machine-readable index: [catalog.json](catalog.json).

### Categories

{{CATEGORY_LIST}}

### All skills

{{INDEX_TABLE}}

## Related repos

The upstream runtime and public companion repos:

{{REPO_LIST}}

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the SKILL.md contract, the sanitization rule and the pull request flow.

## License

MIT. See [LICENSE](LICENSE).
