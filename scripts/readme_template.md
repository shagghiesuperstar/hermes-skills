# Hermes Skills

Reusable skills for [Hermes Agent](https://hermes-agent.nousresearch.com/). Every skill is sanitized of the publisher's personal, machine and network data.

Browse the library on the web at [pixelrainbow.ai/skills](https://pixelrainbow.ai/skills/).

## Add as a tap

```bash
hermes skills tap add shagghiesuperstar/hermes-skills
hermes skills search <query> --source github
hermes skills install shagghiesuperstar/hermes-skills/skills/<name> --category <category>
```

Per the Hermes docs, custom GitHub taps are searched with `--source github`.

## What is this

Generic, reusable Hermes Agent skills from Pixel Rainbow. Each one is written to work on any machine: the publisher's names, hostnames, addresses, paths and secrets are replaced with `<placeholders>` that you fill in. Cited third-party attribution stays.

## Install

Install a skill from the tap:

```bash
{{INSTALL_TAP_EXAMPLE}}
```

Or install it straight from its raw URL:

```bash
{{INSTALL_EXAMPLE}}
```

`--category` sets the local category folder. The CLI help for it reads "Category folder to install into".

Per the Hermes docs: Install SKILL.md directly from any HTTP(S) URL ([skills guide](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)).

## Skill format

Each skill is one folder, `skills/<name>/`, holding a single `SKILL.md`.

- Frontmatter: `name` (matches the folder), `description` (starts with "Use when", 400 characters or fewer), `version` (x.y.z), `author`, `license`, `metadata.hermes.tags` (2 to 8 lowercase strings), `metadata.hermes.category` (one of the categories below; the install commands pass it as `--category`, which sets the local category folder), and optional `related_skills` (skills in this repo only).
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
