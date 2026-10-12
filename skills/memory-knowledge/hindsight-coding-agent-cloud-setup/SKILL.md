---
name: hindsight-coding-agent-cloud-setup
description: Use when installing cloud-mode Hindsight coding agents. The goal is that every supported harness writes to one designated memory bank. Captures a baseline, pins routing keys, backs up harness configs, and verifies that no extra bank or mental model appeared.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hindsight, coding-agents, cloud, opt-in, install, verification]
    category: memory-knowledge
related_skills: [hindsight, hermes-memory-providers, memory-stack-snapshot]
---

# Hindsight Coding-Agent Cloud Setup

## Overview
The `@vectorize-io/hindsight-coding-agents` package connects supported coding harnesses to Hindsight memory. In cloud mode it sends their memories to a hosted bank, not to a local daemon. This skill covers a rollout where every opted-in path writes to one designated bank, and the rollout proves three things: no extra bank was created, the bank's identity is unchanged, and each harness retained at least one document.

## When to Use
- Bringing a new host into an existing Hindsight Cloud setup with the same opt-in routing.
- Installing the package on a host whose package version differs from the one a reference host used. Re-check the config key names against that version's README.
- Rolling out the package to a set of harnesses and needing per-harness evidence.

### Do not use for
- Local embedded mode, which runs a daemon on the loopback interface. Use the Hindsight memory setup skill for that.
- A Hermes profile's own memory settings. The Hermes gateway handles those, not this package.

## Features
- A baseline capture of banks, bank configuration and mental models before any change.
- A coding-agent configuration file with opt-in paths and a path-to-bank map.
- A backup of each harness's config files before its install.
- Per-harness smoke tests with evidence files and a fixed set of pass checks.
- A verification set that compares the baseline with the final state.

## Benefits
- The operator knows exactly which harness wrote where.
- Installer changes to routing keys are caught, because each install is checked against the baseline.
- A blocked harness is named with its cause, and the rest of the rollout continues.

## Procedure
### 1. Prepare the preconditions
1. **Store the API key in a secret manager.** Load it into a shell variable for the install step only. Never echo it. The installer writes the token in plain text to its configuration file, so set that file to owner-only (mode 600), and report only its path and permissions.
2. **Name the approved checkout paths.** Use only the paths the task names, typically the main checkout and one worktree of the same repository. Do not invent paths.
3. **Inventory the installed harnesses.** Find each harness on the search path, then compare the names with the list the package prints:
   ```zsh
   npx @vectorize-io/hindsight-coding-agents --help
   ```
   Skip any installed harness that is not on that list.
4. **Check for live agent sessions.** The installer changes configuration that a harness reads at its next start. Live sessions keep the old configuration until they restart.

### 2. Capture the baseline against the live API
Save the bank list, the target bank's configuration and its mental-model list before any change:
```bash
curl -sS -H "Authorization: Bearer $HINDSIGHT_API_KEY" \
  https://api.hindsight.vectorize.io/v1/default/banks -o smoke/baseline-banks.json
curl -sS -H "Authorization: Bearer $HINDSIGHT_API_KEY" \
  https://api.hindsight.vectorize.io/v1/default/banks/<bank>/config -o smoke/baseline-bank-config.json
curl -sS -H "Authorization: Bearer $HINDSIGHT_API_KEY" \
  https://api.hindsight.vectorize.io/v1/default/banks/<bank>/mental-models -o smoke/baseline-mental-models.json
```
Record the total bank count, the count of banks whose names begin with `coding-agent::`, and the mental-model names.

### 3. Write the coding-agent configuration before installing
The file is `~/.hindsight/coding-agent.json`. Write it at mode 600 with these routing keys:
```jsonc
{
  "apiUrl": "https://api.hindsight.vectorize.io",
  "optInOnly": true,
  "optInPaths": ["<approved-path-1>", "<approved-path-2>"],
  "mapPathToBank": {
    "<approved-path-1>": "<bank>",
    "<approved-path-2>": "<bank>"
  },
  "manageBankConfig": false,
  "pages": {
    "Component map": false,
    "Core concepts": false,
    "Conventions and patterns": false,
    "Key decisions and rationale": false,
    "Initiatives and enhancements": false
  },
  "customPages": {},
  "codebaseSurvey": false,
  "retainTags": ["agentHarness:{harness}", "project:{gitProject}", "device:<hostname>"],
  "autoUpdate": true,
  "autoSeed": false,
  "seedLimit": 300,
  "logLevel": "info"
}
```
The pitfalls section explains why each non-default key matters.

### 4. Back up each harness's configuration files
For every supported installed harness, copy its settings, hooks and MCP files to a dated backup folder. These copies are the rollback path. Typical files include the settings file for the Claude Code CLI, the hooks and config files for the Codex CLI, the JSON config for opencode, and the config file for the Grok CLI. Confirm each path on the host before copying.

### 5. Install one harness at a time and re-check the routing keys
```zsh
npx -y @vectorize-io/hindsight-coding-agents@<pinned-version> install <harness> --server cloud
```
Check `install --help` first. If it lists an environment variable or a prompt for the token, use that and leave the token out of the command. If the only way to pass the token is an `--api-token` argument, stop and ask the operator to run the install interactively, because the token would appear in the process list.
After each install, re-read the coding-agent file. The installer adds `serverMode` and `apiToken`, which is expected. The routing keys (`optInOnly`, `optInPaths`, `mapPathToBank`, `manageBankConfig`, `pages`, `retainTags`) must be unchanged. If any of them changed, stop and roll back that harness from its backup.

### 6. Smoke-test each harness with the cheapest headless invocation
Run one short prompt that exercises recall, from an approved checkout path, not from the home folder. Use the harness's print or single-prompt mode, and the cheapest model it offers. Those modes run the session hooks, which is what writes the retained documents. Use the harness's default permission mode. If a prompt blocks the run, answer it in the session; do not turn on a no-prompt mode for a smoke run.

Save each reply to `smoke/<harness>-reply.txt`. Some harnesses cannot run headless on a given host, for example one that is not logged in, or one whose native binary failed to install. Mark those BLOCKED with the exact host error. Do not uninstall the wiring for a blocked harness.

### 7. Run the per-harness checks
For each harness that ran:
- **(a) Bank routing.** The diagnostic log's session-start and retain events name the target bank, not a `coding-agent::` bank.
- **(b) Recall banner.** The reply starts with the package's recall banner, which shows that recall was injected.
- **(c) Retention.** A new document exists in the target bank with the tags `agentHarness:<harness>`, `project:<project>` and `device:<hostname>`. Filter the document list by creation time.
- **(d) Turns.** The package's stats command shows non-zero turns for the harness.
- **(e) No new bank.** Re-fetch the bank list. The `coding-agent::` count is still zero.
- **(f) Config unchanged.** A semantic diff of the baseline and final bank configuration is empty, and the mental-model names match the baseline. Use `jq -S` for both files, because the server does not return keys in a stable order.
- **(g) Opt-in holds.** Run the same prompt from a path that is not approved. The reply must not show the recall banner, and the diagnostic log must have no session-start event for that path.

Checks (d) through (g) can run once at the end, if every harness passed (c).

### 8. Clean up auto-seeded pages, then turn off auto-seeding
If the package seeded pages despite `manageBankConfig: false`, delete each page that appeared after the baseline. The mental-model list gives each page's ID, and its creation time separates auto-seeded pages from curated ones. Then set `autoSeed` to `false`, so the pages do not return at the next session start.

### 9. Write the rollout report
Write a short report with a per-harness table of checks (a) through (g), each marked PASS, FAIL or BLOCKED, with the evidence file names. Include the final configuration with the token value replaced by `REDACTED`, the semantic-diff result, and the token file's path and permissions. End with one status: DONE, PARTIAL or BLOCKED.

## Pitfalls
- **Reserved tag prefixes are dropped silently.** The package reserves the `source:` and `harness:` prefixes. A tag in a reserved prefix is ignored with a warning, and it never lands on a document. Use a non-reserved namespace such as `agentHarness:`. The package adds its own `harness:` tag automatically.
- **Page names must match the package's built-in names exactly.** A wrong key is ignored with a warning, and the page still seeds on the first session start. Read the names from the README of the pinned version.
- **`manageBankConfig: false` does not stop seeding.** The package still seeds its pages on the first session start while auto-seed is on. Set `autoSeed` to `false` and clean up.
- **Raw hashes of server responses are not stable.** The server returns keys in a different order on each request. Compare sorted JSON, never raw bytes.
- **A mental-model count change is a failure.** Delete the auto-seeded pages and confirm the count returns to the baseline. Roll back the harnesses only when cleanup is not enough.
- **Non-headless or wrong-mode invocations skip the hooks.** A bare or ephemeral mode can skip the retain hook, so the check fails for a reason that has nothing to do with the install.
- **Opt-in success looks like a failure.** From an unapproved path the memory server refuses to start, so the harness has no memory tools. That is the expected result. A recall banner from an unapproved path means the model copied the banner from an earlier smoke file, not that memory was used.
- **Installer rewrites of the server address or key.** `serverMode` and `apiToken` change on every install. Only the routing keys are a regression.
- **Tokens in command lines.** A token passed as a command argument can appear in shell history and process listings. Prefer the installer's environment or prompt option if its help output lists one, and check that help output first.

## Verification
- The bank list has the target bank and no `coding-agent::` bank.
- The mental-model names match the baseline.
- A semantic diff of the bank configuration is empty.
- Each non-blocked harness has at least one retained document with the expected tags.
- The configuration file is mode 600, and no token value appears in any saved file.

## Attribution
The Hindsight memory system and its coding-agents package are published by Vectorize. The package is available on npm as `@vectorize-io/hindsight-coding-agents`, and the hosted API is at `https://api.hindsight.vectorize.io`.
