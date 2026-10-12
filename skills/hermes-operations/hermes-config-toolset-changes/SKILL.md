---
name: hermes-config-toolset-changes
description: Use when changing Hermes toolsets or MCP servers. The change is made in a profile config. Covers live-config checks, CLI limits, list-valued keys and operator-approved edits.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, config, toolsets, mcp, profiles, config-yaml]
    category: hermes-operations
related_skills: [config-verify-before-write, hermes-architecture-reference, hermes-profile-config-yaml-debug]
---

# Hermes Config Toolset Changes

## Overview
A profile enables tools through lists in its `config.yaml`: a top-level `toolsets:` list, MCP server blocks, and a few
other list-valued keys. The curated CLI commands show only part of the tool registry, so they can reject a toolset that
the runtime supports. The correct workflow is to read the live config first, confirm the change against the docs, and
make it through the CLI where the CLI can do it. A direct edit to a config file is an operator decision. It is never a
workaround for a refused write.

## When to Use
- A profile needs a toolset that the curated list does not show, such as an orchestrator-only toolset.
- You are adding, removing or verifying an MCP server entry on a profile.
- You are about to change any list-valued key, such as `toolsets:`, `mcp_servers:` or a `custom_providers:` list.
- A managed capability looks down on one profile but works on others.

## Features
- Live-config check that reads the full list, not a truncated view.
- Doc check for toolsets that the docs say must be enabled in config.
- CLI decision table: what the CLI can set, what it stores as text, and what it cannot touch.
- Rules for list-valued sections and for multi-line entries.
- Post-change checklist that ends with a fresh session test.

## Benefits
- A missing toolset is found from the real config, not from a guess about the CLI.
- List values are not corrupted into strings by a scalar-only setter.
- Operators approve every direct edit before it happens.
- A "service is down" report gets checked against the profile's toolset list first.

## Procedure
1. Read the live config for the target profile in full. Confirm the path first:
   ```bash
   hermes --profile <profile> config path
   grep -n -B2 -A12 "^toolsets:" "$(hermes --profile <profile> config path)"
   ```
   Read the whole block. A short view that shows only the first items can make a present toolset look absent.

2. Check the docs page that governs the toolset. Some orchestrator-only toolsets are enabled in config, and the docs
   say so. Check the docs before you conclude what the CLI should do.

3. Check what the CLI can show and set. Use these probes, and treat each result as a fact to report:
   ```bash
   hermes --profile <profile> config path
   hermes tools list          # shows only the curated subset
   hermes tools enable <name> # rejects toolsets outside the curated list
   ```
   The interactive tools screen needs a terminal, so it cannot be driven from an agent shell.

4. Choose the change path:
   - If the CLI supports the change, use it, then read the config back.
   - If the change needs a list edit the CLI cannot do, prepare the exact change as a diff, with the current block
     quoted, and ask the operator to apply it or to authorize the agent to apply it in this session.
   - If the file tools refuse to write a config file, that refusal is the signal to stop and ask. Do not route the
     write around it.

5. For an authorized edit, use the verification ladder in `config-verify-before-write`: back up, check the list
   structurally, replace one exact block that matches once, write atomically, and read the key back. Build the block
   from the live file's exact bytes, not from an example in this skill.

6. Restart the gateway from the operator's terminal. Config changes take effect only in a new process.

7. Verify in a new session. Ask the agent to call the tool that was previously gated out, and confirm it appears in
   the tool list.

### List-valued keys and multi-line entries
- A key such as `custom_providers:` is a list of mappings, not a mapping. Iterate it with a guard that skips non-dict
  items, not with `.items()`:
  ```python
  for item in cfg.get("custom_providers", []):
      if isinstance(item, dict) and item.get("name") == "<provider-name>":
          ...
  ```
- A scalar-only setter stores a list as text. Use it only for top-level scalar keys. For any nested list or mapping, edit
  the structure as a whole and read it back.
- Removing a multi-line list entry means removing every line of that entry. Removing only its first line leaves orphaned
  sub-keys at the wrong indent, and the file no longer parses.
- After any multi-line removal, parse the result before writing it anywhere.

## Pitfalls
- **Truncated reads hide list items.** Read the block in full, with context lines, every time.
- **Curated lists are not the full registry.** `hermes tools list` and the interactive screen show a subset. The live
  `config.yaml` is the authority on what a profile enables.
- **A missing toolset looks like a dead service.** A profile that lacks the web toolset reports its web tool as down.
  Read the profile's toolset list before you diagnose a managed capability as broken, or you will re-architect around a
  service that was fine.
- **Keys with similar names are not the same key.** A file can contain several lines that mention `toolsets:`, such as
  per-platform overrides and disabled lists. Print every occurrence with its line number, and identify the one
  top-level block by its column.
- **Indentation differs between profiles.** One profile indents list items and another does not. Copy the exact bytes
  of the target profile's file, not an example.
- **Do not match a list item with a regex that stops at the next column-zero line.** Unindented list items end the
  match early. Enumerate lines instead.
- **Do not use "is X already in the list" regex checks.** A nested block can contain the same item. Parse the file and
  check the top-level key.
- **Config changes do not reach a running process.** A session that made the change still has the old tool schema.
- **Secrets never go into a config list or into chat.** Add provider keys through the secrets CLI or the profile's env
  file. Validate a key with one minimal request and read only the status code.
- **Do not change a profile's default model or provider as a side effect** of a toolset or key change. Check those keys
  before and after the change.
- **A new provider block needs its upstream checked.** Confirm the provider's base URL and API style from its own docs
  before you copy a block from memory. A native API style needs a native block, not the generic OpenAI-compatible one.

## Verification
- The live `toolsets:` list, read in full, contains the expected entries and no others.
- The config check command reports no schema error.
- After the gateway restart, a new session can call the newly enabled tool.
- A profile that was reported as having a down service shows that service's toolset enabled, or the report is corrected.
