---
name: codex-cli-integration
description: Use when driving the OpenAI Codex CLI on a local repo. Covers exec flags, sandbox modes, timeouts, and checking changes that landed.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [codex, openai, coding-agent, sandbox, cli]
    category: agent-orchestration
related_skills: [external-coding-agent-orchestration, claude-cli-model-switching, independent-static-review]
---

# Codex CLI Integration

## Overview
The Codex CLI runs a coding agent against a local repository, either one-shot with `codex exec` or as a stdio MCP server. It is most reliable when you run it directly in a terminal on a focused task, and least reliable when a subagent wraps a long task. Its edits land incrementally, so a timed-out run can still have changed the tree. This skill covers the flags that matter, the timeout behavior, the handoff between Codex and a reviewer, and the checks that prove the work landed.

## When to Use
- Delegating a bounded coding or refactor task to Codex on a local checkout.
- Running a code review or a read-only analysis through Codex.
- Choosing between a direct terminal call and an MCP tool call for a Codex task.
- Recovering after a Codex run that timed out or returned an error.
- Deciding whether a task needs fresh implementation or only a commit of work already in the tree.

## Features
- A direct `codex exec` pattern with the working directory, sandbox mode, and model set explicitly.
- A sandbox ladder: read-only, workspace-write, and danger-full-access, with a rule that the broadest mode needs the operator's approval.
- Task decomposition rules that keep each prompt small enough to finish inside the timeout.
- An MCP server setup and its restart limitation.
- Session commands for resuming, forking, and applying changes.
- A pre-work check that compares the working tree to the task before Codex is invoked.

## Benefits
- Direct terminal runs avoid the long hangs that wrapped delegations showed on network-bound work.
- Explicit sandbox and approval flags stop a run from silently widening its permissions.
- Small, focused prompts finish inside the timeout, so fewer runs die halfway.
- A `git diff` check after a timeout tells you whether edits landed without a costly rerun.
- A pre-work check avoids paying Codex to re-implement changes that already exist.

## Procedure
1. Confirm the installed version and the active configuration before you rely on either.
   ```bash
   codex --version
   codex exec --help
   grep -o '^[^=]*=' ~/.codex/config.toml   # key names only, so no values are printed
   ```
2. Check the repository state so you know what Codex will see.
   ```bash
   git -C "<repo>" status
   git -C "<repo>" diff
   ```
   If the diff already holds the intended change, use Codex only for the commit step. If the diff is empty, Codex implements from scratch.
3. Split the task. Give each prompt one file or one question, and keep each prompt short, ideally under about 100 words. A single large brief tends to time out.
4. Run the task directly in a terminal with explicit flags:
   ```bash
   cd "<repo>" && codex exec -m "<model>" -s workspace-write -C . "<focused task>"
   ```
   Add `--json` for machine-readable events, `-o <file>` to save the final message, and `--ephemeral` to skip session files.
5. Use the narrowest sandbox the task needs. Full access (`-s danger-full-access`) needs the operator's approval for that task. Do not add a flag that skips approvals or the sandbox. If a task cannot finish inside the sandbox, stop and ask.
6. If the run times out, do not rerun it yet. Check the tree first:
   ```bash
   git -C "<repo>" diff
   ```
   Rerun only when the diff is empty.
7. Route the output to a reviewer. Codex does the work, and a separate reviewer (another agent or a person) reads the diff and decides what gets committed. Do not connect Codex directly to a remote repository for commits.
8. For a review pass, use the review command and then apply only the findings you accept:
   ```bash
   codex review -m "<model>" --search "<repo>"
   codex apply
   ```
9. To resume or branch earlier work, use the session commands:
   ```bash
   codex resume --last
   codex fork --last
   ```
10. To expose Codex to an agent as tools, add an MCP server entry that runs `codex mcp-server`, then restart the agent. Servers added to the config do not load into a running session. Use MCP for quick queries (under about 30 seconds) and the terminal for longer work.

## Pitfalls
- **Subagent wrappers around Codex time out on network-bound work.** A wrapped delegation can stall for the full timeout with no output. Call `codex exec` directly in a terminal for anything longer than about a minute.
- **`-a` and `--ask-for-approval` do not exist on `codex exec`.** Passing them fails with an unexpected-argument error. Remove `-a` and use the sandbox level the task needs.
- **`--reasoning-level` is not a flag.** Set reasoning effort through config, for example `-c model_reasoning_effort="<level>"`.
- **A timeout does not mean nothing landed.** Codex applies edits as it goes, so the working tree can hold the changes even when the tool reports a timeout. Check the diff before rerunning.
- **Do not rerun on top of a partial change.** A second run on a half-applied tree can duplicate or conflict with the first. Rerun only from an empty diff.
- **MCP tools need a restart to load.** Changing the server list mid-session does nothing until the agent restarts, and the restart drops the session context. Keep a terminal fallback ready.
- **The MCP transport has a hard ceiling.** Long tasks run out the MCP timeout even when the same work finishes in a terminal. Put long tasks in the terminal.
- **Local inference is limited to the providers Codex supports.** The `--oss` option accepts only the local providers it names, so check the error text before you assume a local endpoint will work.
- **Work already in the tree needs a commit, not a rewrite.** Check the diff before invoking Codex, so you do not pay for a second implementation.
- **Honor an explicit request for a specific tool.** If the user asks for Codex, send new coding actions to Codex rather than continuing with other tools. Reconnaissance you already started can finish first, because Codex needs that context.
- **Edit configuration files with a structure-aware method.** Do not use sed on YAML or TOML, and back up the file first.

## Verification
- `codex --version` and `codex exec --help` match the flags used in the command.
- `git diff --stat` after the run shows the expected files changed, and no unexpected files appear.
- The run's final message, saved with `-o`, names the same files as the diff.
- After a timeout, the diff is inspected before any rerun, and the rerun happens only from an empty diff.
- Each commit comes from a reviewer's accepted diff, not directly from Codex's own output.

## Attribution
Flags and configuration keys follow the public Codex CLI reference: https://github.com/openai/codex/blob/main/docs/config.md. Model names change often, so confirm the current slug in a live session with `/model` before you script it. The public model catalog is at https://developers.openai.com/api/docs/models/all.
