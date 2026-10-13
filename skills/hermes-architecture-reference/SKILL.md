---
name: hermes-architecture-reference
description: Use when debugging or changing Hermes Agent internals. Covers the module map, config and profile layout, subsystem pitfalls and how to verify claims upstream.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, architecture, troubleshooting, internals, config, maintenance]
    category: hermes-operations
related_skills: [hermes-profiles, hermes-config-toolset-changes, hermes-profile-config-yaml-debug]
---

# Hermes Architecture Reference

## Overview
Hermes Agent has several entry points that feed one agent loop, and each subsystem keeps its state in a known place:
config and secrets in the Hermes home, sessions in a SQLite store, and profiles as isolated copies of that layout. This
reference maps those pieces so you can find the right file or subsystem before you change anything. It is an offline
orientation, not a substitute for the official docs or the upstream repository. Where they differ, the live docs and the
upstream repository win.

Authoritative sources:
- Official docs: `https://hermes-agent.nousresearch.com/docs/`
- Source repository: `https://github.com/NousResearch/hermes-agent`

## When to Use
- A Hermes issue spans more than one subsystem (gateway, provider, tools, sessions, cron, MCP, memory) and you need the
  right starting point.
- You are about to add a tool, a plugin, a memory provider, an MCP server or a gateway hook.
- You are changing provider routing, context compression, prompt caching or session storage.
- You are about to claim which config is active, or where a value comes from.

## Features
- A symptom-to-subsystem lookup table for the agent loop and its internal subsystems.
- Layout of the Hermes home: config, secrets file, persona, memory files, session store, and per-profile copies.
- Subsystem pitfalls for tools, memory, sessions, cron, gateway keys and profile isolation.
- Config-change rules: use the CLI, validate model slugs, and confirm each change by reading it back.
- A procedure for keeping a local copy of this reference in line with upstream.

## Benefits
- You start in the right module instead of grepping the whole tree.
- Common traps (frozen memory snapshots, cron prompts without history, hand-built session keys) are avoided.
- Config changes land in the file the active profile actually reads.
- Claims about behavior are checked against the official docs or the code before they are repeated.

## Procedure
1. Establish the active install and config before you reason about anything:
   ```bash
   hermes --version
   hermes config path
   hermes config check
   git -C <hermes-clone> rev-parse HEAD
   ```
   The clone path differs between machines. Locate it first. Do not assume a default path.

2. Pick the subsystem from the symptom, then read only that area:

   | Symptom area | Start here |
   |---|---|
   | Gateway, messaging platforms, session keys | Gateway internals, then the platform adapter |
   | Provider, API mode, model routing | Provider runtime resolution |
   | Tool not offered, tool error, tool dispatch | Tool registry, toolsets, dispatch |
   | Session data, search, corruption | Session storage (SQLite with full-text index) |
   | Context too large, slow first turn | Context compression and prompt caching |
   | MCP server missing or failing | MCP integration: naming, filtering, OAuth, reloads |
   | Cron job not running or wrong output | Cron scheduler and job lifecycle |
   | Memory not recalled | Memory system and provider plugin lifecycle |

3. Use the layout of the Hermes home. Resolve paths through the CLI, not by hand:

   | Item | Purpose |
   |---|---|
   | `config.yaml` | Non-secret configuration |
   | `.env` | Secrets such as API keys and tokens |
   | `SOUL.md` | Agent persona |
   | `MEMORY.md`, `USER.md` | Agent-maintained memory and user notes |
   | `state.db` | Session store and search index |
   | `profiles/<profile>/` | A profile's own copy of config, memory, skills |

4. For a design or code change, check the dependency order and the extension contract before editing:
   - a custom tool follows the tool contract (returns a JSON string, declares an availability check);
   - a memory provider implements the provider interface and is the only external provider active at a time;
   - a plugin ships a manifest and registers through the plugin API;
   - an MCP server is configured in the profile's config and its tool names follow the documented pattern.

5. Make configuration changes through the official CLI. Read each change back before reporting it:
   ```bash
   hermes config set <key> <value>
   hermes config check
   ```

6. Verify any claim you are about to repeat against the docs or the repository. Note the commit or version you checked.

### Keeping a local copy current
Use this when you maintain a local architecture note against upstream.

1. Record three revisions and keep them separate: the revision of the local install, the upstream main revision after a fetch, and the upstream revision that this note last reviewed. The changes to review are the commits between the last-reviewed revision and upstream main. The local install's revision does not set that range.
2. Group those commits by architecture area, not by commit. Spot-check each high-impact commit with `git show --stat --format= <sha>` before you quote it. Guard the call so that one missing commit does not stop the run: `git show --stat --format= <sha> 2>/dev/null || echo "missing: <sha>"`.
3. Choose one action by the size of the change. A small set of changes gets an inline note in the main document. A medium set gets a dated changelog entry, and the main note stays as it is. A very large set, or a note that has not been reviewed for a long time, gets a full rewrite of the note.
4. Never make a partial edit to the main note. It looks current while it is not.
5. Check the note's frontmatter by parsing it as YAML, not with a regular expression. A multi-line header defeats most regular expressions.
6. Re-count the commits on each run. Do not copy a count from an earlier note.

## Pitfalls
- **Never hardcode the Hermes home path.** Use the config-path command and the profile-aware helpers. A profile may use
  a different home than the default.
- **Confirm which profile is active before you claim a value.** Cross-profile writes break isolation.
- **Keep secrets in the `.env` file only.** Do not put a key in `config.yaml`, a skill, a prompt or a log.
- **Tool handlers return a JSON string and do not raise.** An exception breaks the turn instead of reporting the error
  to the model.
- **A tool availability check that returns false removes the tool silently.** Test availability before you assume a
  tool exists.
- **Memory snapshots are frozen at session start.** A mid-session write does not change the prompt the model already
  has. Start a new session to see it.
- **Cron jobs have no conversation history.** A cron prompt must be self-contained, with every fact it needs.
- **A wildcard toolset does not enable every toolset.** Name the toolset you need explicitly.
- **Build gateway session keys with the provided builder.** Never construct one by hand.
- **Memory sync must not block the turn.** Run it on a background thread.
- **Set `model.default` to a real model slug.** The literal word `default` makes a picker fall back to a stale label.
- **Do not route routine chat through a multi-model council provider.** It multiplies cost on every turn.
- **Validate every provider model slug against the provider's live catalog** before writing it into config or a routing
  table.
- **A routing table row is not a runnable profile.** Only a profile directory with its own config file is real.
- **When cloning a profile for a worker, rewrite the inherited persona file.** Otherwise the worker keeps the
  orchestrator's identity.
- **If a file tool refuses to write a config file, do not route around the refusal with a script.** Ask the operator to
  make the edit or approve it.
- **Never report a config change as done without a read-back.** Check the file or the CLI output after the change.

## Verification
- `hermes config check` passes, and `hermes config path` names the file you edited.
- A claim you repeat cites the commit, version or doc page you checked.
- For a fix, the subsystem behaves as expected in a short test run, and the config read-back matches what you set.
