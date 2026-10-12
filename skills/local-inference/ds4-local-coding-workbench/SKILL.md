---
name: ds4-local-coding-workbench
description: Use when pairing a local DeepSeek engine with two coding agents on one Mac. Covers worktree isolation, role split, approval gates, and config for each client.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [ds4, deepseek, opencode, coding-agent, worktree, local-inference]
    category: local-inference
related_skills: [ds4-system-health, claude-code-local-stack, darkbloom-fleet-ops]
---

# DS4 Local Coding Workbench

## Overview
One local inference engine can serve several coding clients at once. The workbench runs one shared server, then gives each client its own git worktree and a fixed job. A judge (the orchestrating agent) compares the diffs, runs the tests, and decides what to keep. The clients never edit the same dirty working tree, and every edit passes an approval gate by default.

## When to Use
- You want two local coding agents working on one repository without stepping on each other.
- You need a fast, broad scouting client plus a slower, precise implementation client against one local model.
- A codebase is unfamiliar, a bug has no clear cause, or a refactor touches many files.
- You want a local-only coding loop with no data leaving the machine.

## Features
- One OpenAI-compatible endpoint on loopback that every client points at.
- A role split: a breadth client for reconnaissance and patch drafts, a precision client for narrow edits and diff cleanup, and a judge for comparison and tests.
- Worktree doctrine that keeps parallel edits in separate trees and integrates only by cherry-pick.
- Approval defaults: review mode first, auto-approve only in throwaway sandbox repositories.
- Client configuration for an OpenAI-compatible provider, with thinking kept low to protect the token budget.
- Escalation rules and a list of tasks that should never run in parallel.

## Benefits
- Parallel exploration costs local tokens instead of cloud spend, and no source code leaves the machine.
- A failed attempt in one worktree cannot corrupt another attempt or the integration branch.
- Every change is reviewed as a diff before it lands, so the review gate is the default, not an option.
- The division of labor matches each client's strength, so reconnaissance and implementation do not compete for one context.

## Procedure
1. Confirm the engine answers and names the model it serves:
   ```zsh
   curl -s http://127.0.0.1:<engine-port>/v1/models | python3 -c "import sys,json; print(json.load(sys.stdin)['data'][0]['id'])"
   ```
   Check whether the engine is current with its upstream before a long session (see `ds4-system-health`).
2. Point each client at the endpoint through environment variables, not hardcoded keys. The key can be a placeholder for a local server:
   ```zsh
   export OPENAI_BASE_URL="http://127.0.0.1:<engine-port>/v1"
   export OPENAI_API_KEY="<local-placeholder-key>"
   export OPENAI_MODEL="<served-model-id>"
   ```
   Allow plain HTTP only for loopback, and only when the client requires an explicit flag for it.
3. Create one worktree per client from the same base commit. Use `-b` so each worktree gets its own branch; checking out an already-checked-out branch fails:
   ```zsh
   git worktree add -b scout/<task> ../<repo>-scout HEAD
   git worktree add -b impl/<task> ../<repo>-impl HEAD
   ```
4. Run the breadth client in its worktree for reconnaissance and draft patches. Stay in review mode:
   ```zsh
   cd ../<repo>-scout
   deepseek exec "Map the modules that touch <area> and list the risky call sites"
   ```
5. Run the precision client in its own worktree for the narrow change, with a clear target:
   ```zsh
   cd ../<repo>-impl
   opencode run -m <provider>/<served-model-id> "Implement <fix> in <file>, then run <test-command>"
   ```
6. Judge in the main checkout. Compare the two branches, run the test suite, and cherry-pick only the parts that pass:
   ```zsh
   git diff main scout/<task> > /tmp/scout.patch
   git diff main impl/<task> > /tmp/impl.patch
   git cherry-pick <sha-from-the-chosen-branch>
   ```
7. Remove the worktrees and their branches once the result is merged or discarded. Use `git branch -d`, which refuses a branch with unmerged commits. Use `git branch -D` only after the operator approves losing those commits:
   ```zsh
   git worktree remove ../<repo>-scout
   git worktree remove ../<repo>-impl
   git branch -d scout/<task> impl/<task>
   ```
8. Commit after each logical change inside the worktree, so a session interruption loses at most one step.

### Client Configuration
- **Breadth client (DeepSeek-TUI or similar).** Use the OpenAI-compatible provider with the endpoint and model above. Set the approval policy to on-request, the sandbox to workspace-write, and thinking to low. Keep the config in the client's own file (for example `~/.deepseek/config.toml`). Check the repository's `config.example.toml` for the current format before editing. Put the default model at the top level and the provider settings in a `[providers.openai]` table with `api_key`, `base_url`, and `model`. A `[settings]` table with a `model` key does not take effect in the tested client version, so the client silently keeps its built-in default.
- **Precision client (OpenCode or similar).** Define a provider using an OpenAI-compatible package with the endpoint and model, and set it as the default model. Set context and output limits to match the engine's configured context. Keep session sharing off.
- **Plugins.** Give plugin entries absolute paths. Tilde paths and git-backed plugin specs may not resolve in some OpenCode versions, so the plugin fails to load. Install the plugin locally with npm and reference it by its absolute path.

## Pitfalls
- **Never run both clients in the same dirty tree.** They will overwrite each other's edits, and the judge can no longer tell which change came from which client.
- **Expect slow non-interactive runs.** A local engine that serializes requests turns each agent loop into many sequential roundtrips, so even simple prompts can take minutes. Use interactive mode when you need streaming output, and reserve non-interactive runs for unattended jobs that can wait.
- **Review mode does not execute tools.** A non-auto run prints code blocks and changes no files. That is the safe default. Auto mode executes writes and shell commands, one slow roundtrip at a time.
- **Auto-approve only in throwaway sandbox repos.** Never auto-approve in a production checkout, a repo with secrets, or a repo you do not trust.
- **Never share an agent session.** Session-sharing flags publish the transcript; keep them off in every config and never pass them.
- **Keep backups and caches out of commits.** Add `.gitignore` entries for backup files, caches, and virtual environments before the first commit, or push size grows without limit.
- **Clean up worktrees after each merge.** Stale worktrees and branches accumulate quickly across sessions.
- **Escalate instead of guessing.** Hand architecture and security decisions, production changes, wallet or trading code, and any task that fails three times to the human operator.

### Hard Rules
1. No public tunnel or funnel for the engine. Keep the endpoint on loopback or the private network.
2. Review mode is the default. Auto-approve only where the operator has allowed it for that repo.
3. No two clients edit the same working tree at once.
4. Run only in repositories you trust. Treat any third-party repo as untrusted until reviewed.
5. Never commit `.env` files, tokens, or keys.
6. Session sharing is permanently off.
7. Wallet, trading, and production deploy paths need explicit human approval.

### When Not to Run Both Clients
- A dirty production branch, or a repo with secrets and no sandbox.
- Destructive migrations, deploy scripts, and network or infrastructure configuration.
- Requirements that are unclear. Clarify first, then parallelize.
- An untrusted third-party repository.

## Verification
- The engine returns the expected model id on `/v1/models`, and a one-line completion request returns text.
- Each worktree shows only its own branch's changes in `git status` before the judge step.
- The chosen patch applies cleanly to the main checkout, and the test command passes there after cherry-pick.
- `git worktree list` shows no stale entries after cleanup.

## Attribution
- DS4 inference engine by antirez: https://github.com/antirez/ds4
- DeepSeek-TUI client: https://github.com/Hmbown/DeepSeek-TUI
- Superpowers skills plugin used with OpenCode: https://github.com/obra/superpowers
