---
name: claude-cli-model-switching
description: Use when choosing, pinning, or switching the Claude Code CLI model, effort level, or fallback, or exposing extra models through a local bridge.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [claude-code, models, cli-bridge, effort, launchd]
    category: agent-orchestration
related_skills: [claude-agent-teams-orchestration, codex-cli-integration, cursor-agent-cli]
---

# Claude Code CLI Model Switching

## Overview
The Claude Code CLI picks its model from several places: a flag, an environment variable, the interactive picker, settings files, and managed policy. Aliases such as `opus` and `sonnet` move to new versions silently, which is convenient interactively and dangerous for a provider that an orchestrator depends on. A local OpenAI-compatible bridge adds its own layer: an advertised model list that enforces nothing, and environment variables that a service manager may override. This skill covers how to choose a model, verify it before use, switch it safely, and debug a bridge that answers with the wrong model.

## When to Use
- Choosing a model or effort level for a Claude Code CLI invocation.
- Registering a Claude model as a provider in an orchestrator, where version drift would be silent.
- Adding a model to a local bridge's advertised list, or fixing a bridge that shows only one model.
- Installing a local bridge on a host that runs it as a background service.
- Deciding whether a long-context or extended-effort variant is available on the current plan.

## Features
- A table of aliases and their intent, plus pinned full slugs for stable registration.
- The switching precedence order, from session flag down to managed policy.
- Effort and fallback controls, with the value each one accepts.
- A slug verification procedure that separates a real rejection from a bridge translation or a plan-tier gate.
- Bridge configuration rules for services that read a plist instead of a `.env` file.
- A cost-shape diagnostic for checking which model actually answered.

## Benefits
- Pinned slugs prevent a provider from changing version without notice.
- A verified slug list means no model is advertised that the account cannot run.
- Knowing the precedence order stops a setting from silently doing nothing.
- A bridge edit that takes effect on the first restart, not the second.
- A fast way to tell whether a request reached the model you asked for.

## Procedure
1. Check the live options on the installed version. Official references are the model configuration page (https://code.claude.com/docs/en/model-config), the settings reference (https://code.claude.com/docs/en/settings), and the docs index (https://code.claude.com/docs/llms.txt). If your notes are older than about 30 days, re-read them before you act.
   ```bash
   claude --help | grep -E 'model|effort|print'
   ```
2. Verify each candidate slug before you register or advertise it. An exit code of 0 with `ok` in the output means the slug was accepted.
   ```bash
   claude --print --model <slug> "reply with exactly: ok"
   ```
3. Choose the reference style by use. Interactive sessions can use aliases. Provider registrations and bridge model lists should use pinned full slugs.
4. Pick the scope of the change:
   - `--model` flag: this session only.
   - `ANTHROPIC_MODEL` environment variable: this session, and it persists if exported in a shell profile.
   - Interactive `/model` picker: switches now, and can save as the default.
   - `model` key in the user or project settings file: the persistent default for a repository or account.
   - Managed policy file: enforced by an organization and overrides all of the above.
5. Set effort and fallback deliberately. Check the accepted values in the table below before you write them into a settings file.
6. For a local bridge under a service manager, edit the service's environment block, not only the `.env` file. Use a plist-aware tool to change it, read the value back, and mirror the change into `.env` so manual runs match.
7. Reload the service fully. A kickstart restarts the process but may not reread the environment block, so bootout and bootstrap the service instead.
8. Add each verified model to the provider's model map in the orchestrator config. Edit that file surgically (see Pitfalls), not with a full parse-and-dump round trip.
9. Check the bridge end to end: list its models, then send one chat request and confirm the answering model with the cost-shape check below.
10. Report the verified model list, the config diff, the process identifier, every slug you dropped with its exact error, and any blocker verbatim.

### Aliases and pinned slugs
| Alias | Resolves to | Use |
|---|---|---|
| `default` | account or organization default | clears an override |
| `best` | the strongest model the account can use | exploratory work |
| `fable`, `opus`, `sonnet`, `haiku` | the current model in each family | interactive use |
| `sonnet[1m]`, `opus[1m]` | the same family with a 1M-token context | long sessions, when the plan allows it |
| `opusplan` | Opus for planning, Sonnet for execution | hybrid work |

Pinned slugs change with each release. Read the current list from `/model` or the model configuration page rather than copying one from an old note.

### Effort and fallback
| Setting | Accepted values | Notes |
|---|---|---|
| `--effort` flag | `low`, `medium`, `high`, `xhigh`, `max`, `auto` | `xhigh` works only on the newest Opus releases; `max` works on Opus releases from 4.6 onward |
| `CLAUDE_CODE_EFFORT_LEVEL` | a level name or `auto` | session scope |
| `effortLevel` in settings | `low`, `medium`, `high`, `xhigh` | does not accept `max` |
| `--fallback-model` | an alias or a comma-separated list | print mode (`-p`) only |

### Alias-pinning environment variables
- `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`, and `ANTHROPIC_DEFAULT_FABLE_MODEL` set what each alias resolves to. Use them to stop silent drift.
- `CLAUDE_CODE_SUBAGENT_MODEL` sets the model used by the CLI's own subagents.
- Alias resolution differs by provider (direct API, Bedrock, Vertex, Foundry). Confirm the provider before you assume a mapping.

### Local bridge pattern
A local bridge exposes an OpenAI-compatible `POST /v1/chat/completions` endpoint and runs `claude --print --model <slug>` for each request. Keep it bound to the loopback address. Its advertised model list is not enforced: any model id in a request is passed to the CLI. A synthetic id such as a `-max` suffix can be translated by the bridge into a base model plus an effort flag. Do not register such an id for models that do not support that effort level.

## Pitfalls
- **Aliases drift silently.** An alias that tracks the latest model is fine interactively, but a provider registration should use a pinned slug, or the orchestrator's model changes without a record.
- **Editing only the `.env` file under a service manager is a silent no-op.** The loader does not override variables that are already set, so the service's own environment block wins.
- **A kickstart after an environment change keeps the old values.** A full bootout and bootstrap of the service is required to reread the block.
- **Never kill the service's process by hand.** A keep-alive setting restarts it, and the two actions fight each other.
- **Edit service plists with a plist library, never by hand-editing XML or with sed.** Read the value back after each write.
- **A bridge that shows one model is usually a configuration gap.** The advertised list and the provider's model map must both contain the new slug. The CLI is not the bottleneck.
- **Verify before you blame a slug.** Two failures look alike and are not the same. A synthetic suffix that the CLI rejects can be valid when the bridge translates it, so test it through the bridge before you drop it. A plan-tier gate on a context variant is a real account restriction, so drop that slug and record the exact error. A 1M-context gate can apply to one family and not another on the same account.
- **Check which model answered with the cost shape.** Each model has a characteristic token count and cost for a short prompt. If a request labeled with one model shows another model's numbers, the routing is broken. Look at the usage and cost fields in the response.
- **Strip the provider prefix before you debug a missing model.** Some clients send `provider/model`. A bridge that keeps only the last path segment accepts it, so the advertised list is not the test.
- **Use the query flag for one-shot chat tests.** Check the CLI's help for the exact flag, and use the quiet form for a scripted smoke test.
- **An "event loop is closed" trace after a one-shot run is shutdown noise.** If the session identifier and the answer printed first, the test passed.
- **Do not round-trip a hand-curated config through a YAML dump.** A parse, edit, and dump reformats indentation and produces diff noise. Make a timestamped backup, do a text replacement on a unique anchor, assert the anchor count is 1, then parse the result read-only to check the structure.
- **A tool that refuses to edit a protected config file is a stop sign.** Protected config often guards the inference path. Send the change to the operator for approval rather than working around the refusal.
- **Do not set a bridge as the default or the fallback model without an explicit decision.** It changes what every session uses.

## Verification
- `claude --print --model <slug> "reply with exactly: ok"` exits 0 and prints `ok` for every slug you keep.
- The service's effective environment shows the new model list after a full reload, and the bridge's models endpoint lists the same models.
- A single chat request through the bridge returns a successful answer, and the usage shape matches the model you asked for.
- The orchestrator's configuration diff shows only the intended keys, and the structure still parses.
- Every dropped slug has its exact error text in the report.

## Attribution
- Model and settings behavior follows Anthropic's public Claude Code documentation: https://code.claude.com/docs/en/model-config and https://code.claude.com/docs/en/settings.
- The local bridge pattern builds on the cli-bridge project by Daimon-Law, published as the Daimon-Law/cli-bridge repository.
