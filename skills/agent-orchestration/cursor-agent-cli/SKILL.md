---
name: cursor-agent-cli
description: Use when running Cursor's cursor-agent CLI headless for code inspection or edits. Covers login, print-mode flags, sandbox limits, and host-side verification.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [cursor, cursor-agent, headless, coding-agent, sandbox]
    category: agent-orchestration
related_skills: [external-coding-agent-orchestration, claude-agent-teams-orchestration, codex-cli-integration, hermes-kanban-harness-dispatch]
---

# Cursor Agent CLI

## Overview
The `cursor-agent` CLI runs Cursor's agent without an editor, so an orchestrator can send it a task and read the result. It works well for codebase inspection and for focused edits. Its sandbox blocks the network, so it cannot push or open pull requests, and its own build and test claims are self-reports. The reliable pattern is a split: the agent writes code inside the checkout, and an unsandboxed driver does the network, build, commit, push, and pull request work, then re-checks everything the agent claimed.

## When to Use
- Inspecting a codebase's structure, dependencies, or patterns through a non-interactive call.
- Making a bounded edit or writing a set of files from a written work order.
- Choosing between an agent lane and a Claude Code or Codex lane for a short task.
- Setting up or repairing the CLI login on a host.
- Reviewing a draft pull request that a cursor-agent run produced.

Do not use it as a second orchestrator. It has no task board, scheduler, or memory of its own that the orchestrator can rely on.

## Features
- Login through a device-code flow that the operator completes in a browser.
- Non-interactive print mode with explicit trust, output, model, and read-only flags.
- A smoke test that proves login, credits, and dispatch work before any real order runs.
- A sandbox mode that confines writes to the checkout and blocks network access.
- A handoff pattern: the agent ends with a completion line, and the driver pushes and opens the pull request.
- Revision rules for a draft pull request that already exists.

## Benefits
- A bounded task runs in one command with a clear success signal, so a silent hang is not mistaken for progress.
- The sandbox keeps a stray edit out of the wider machine.
- Splitting the network work away from the agent means the driver controls what reaches the remote.
- Host-side re-checks catch the common agent failures: invented citations, wrong file paths, and stale numbers.
- Revisions stack on the existing branch, so the audit trail stays intact.

## Procedure
1. Confirm the binary and the login state. The IDE and the web login do not carry over to the CLI.
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   cursor-agent status
   ```
   For a first install, use the vendor's installer at https://cursor.com/install, then check the status again.
2. If the status is "not logged in," start the login as a background process, read its output for the browser challenge URL, and have the operator open that URL and finish the sign-in. Verify with `cursor-agent status` before you treat the login as done. Do not type credentials for the operator, and do not script past a human-verification step.
3. Run a smoke test before any real work. It proves login, credits, and dispatch in one call:
   ```bash
   cursor-agent -p --sandbox enabled "Reply with exactly: TASK_SMOKE_OK"
   ```
   If the tool stops with a message about an untrusted directory, do not add a trust flag to a shared or personal checkout. Run the same smoke test in a disposable, isolated checkout that holds no credentials or secrets, with the trust flag added, and only there:
   ```bash
   cursor-agent -p --sandbox enabled --trust "Reply with exactly: TASK_SMOKE_OK"
   ```
   The trust flag skips the tool's trust prompt for that directory. The sandbox flag is the safer option, and it comes first in every command.
   On macOS there is no `timeout` binary. For a short call, wrap the sandboxed command with a perl alarm, for example `perl -e 'alarm 120; exec @ARGV' cursor-agent -p --sandbox enabled "<prompt>"`.
4. Write the order to a file and pass the file's contents as the prompt. End the order with a completion line such as `TASK_<id>_DONE` and grep for it afterwards. A missing line means the run is incomplete, whatever the exit code says.
5. Run the agent from the task workspace, pin the model, and keep the sandbox on:
   ```bash
   cd "<workspace>"
   cursor-agent -p --sandbox enabled --workspace "<repo>" --model "<model>" "$(cat order.md)" > cursor-out.txt 2>&1; echo "EXIT=$?" >> cursor-out.txt
   ```
   If the tool stops with an untrusted-directory message, follow the isolated-checkout variant in step 3 instead of adding the trust flag to this command. Redirect to a file and capture the exit code right after the command. A pipe into `tail` replaces the exit code with the pipe's own exit code.
6. Use read-only modes for inspection. Plan mode proposes changes without writing them, and ask mode answers questions without edits. Use them first when latency or scope is a concern.
7. Verify the result yourself. Read the diff, check for files outside the order's scope, and confirm the tree state:
   ```bash
   git -C "<repo>" show --stat HEAD
   git -C "<repo>" status --porcelain
   ```
   Treat the agent's own report as a claim to re-run, not as evidence.
8. Run the build and tests from the driver with a lockfile-matched install command, logging to files outside the repository so the logs are not committed. If the build needs an environment variable the order did not supply, stop with `BLOCKED: build needs env <NAME>`. Never invent or fetch a secret.
9. Revert any tracked file that a build regenerated and that the order did not ask for. Commit only the intended changes, with an explicit path list.
10. Push and open a draft pull request from the driver. Never force-push, never push to a protected branch, and never merge or mark the draft ready.
11. Close with an evidence section that quotes the agent's exit code, the build command and its exit code, the commit SHA, and the pull request state as returned by the host.

### Sandbox handoff (agent writes, driver ships)
- The sandbox blocks the network, so `git push` and pull request creation from inside it fail. Do not retry the agent for that.
- Have the agent commit the work locally, then end with a clear handoff line such as `DONE_FILES_LOCAL`.
- Treat that line as a handoff, not a success. The driver pushes the branch, opens the draft pull request, and records in the body that the build, commit, and push happened on the host.

### Live data the agent cannot fetch
- Fetch every live page or API the task depends on from the driver, store the raw captures and trimmed facts files outside the repository, and point the agent at them in an addendum appended to the order.
- Do not let the agent cite a live check it could not perform. Any "verified against the live site" claim in its output is unsupported unless a capture backs it.
- For each cited URL, the driver checks the HTTP status and the page title with curl, and compares the title with the claim. A redirect to a sign-in page or a bot-wall page can return 200 with the wrong content, so read the body too.
- For PubMed or similar records, look up by identifier through the official E-utilities API rather than by URL string, and quote the abstract the agent actually summarized.

## Pitfalls
- **A "login succeeded" message from a partial step proves nothing.** Confirm with the status command after the browser step completes.
- **`-p` without `--trust` exits with an untrusted-directory message.** It looks like an auth failure, but it is a trust prompt. Use the trust flag only in the isolated, disposable checkout that step 3 describes, and never add the force flag, which allows writes without confirmation, to a shared checkout.
- **Never use the flags that skip every confirmation outside a disposable checkout.** They let the agent run arbitrary shell commands and rewrite files without a check.
- **A silent `-p` run is usually a stall, not progress.** If no output appears for about 30 seconds on a large tree, the agent is likely scanning or waiting on the network. Enforce a timeout and rerun.
- **Long build jobs need the task's runtime cap, not the smoke-test wrapper.** A short alarm kills a legitimate multi-hour run.
- **A JSON output envelope is brittle in shell.** Prefer the plain text format for scripts, or parse the JSON content field explicitly.
- **Name the file and the change in every prompt.** A request to "improve" or "refactor" with no target produces clarifying questions or several competing plans.
- **Ask for a fresh context when the run must be isolated.** Earlier session memory can leak into an unrelated run, so say "ignore prior context" when that matters.
- **The sandbox loses graph and MCP tools.** The agent falls back to grepping local files. Its "tool unavailable" note is not a reason to skip the driver's own re-check.
- **Map each named file to the canonical copy before the agent edits it.** Monorepos often hold several copies of a catalog or config. The agent may pick a stale one, so name the path the loader actually imports.
- **Do not let the agent add extra files when the order names an exact file count.** Leftover helpers and index files break the deliverable's scope.
- **Notes you wrote for the agent can leak into the deliverable.** Grep the output for driver-side words and reword them as neutral facts before the commit.
- **Do not amend the agent's commit to hide its mistakes.** Add a new commit on top so the audit trail shows the correction.
- **Stop the original task before you launch a second engine on the same worktree.** Two writers on one checkout overwrite each other, so stop the first child process, confirm it is gone, and only then start the second run.
- **Join an existing pull request instead of opening a second one.** Check for an open draft on the branch first, and update its body with the edit command rather than creating a duplicate.
- **Stop the agent once its pull request is open and mergeable.** A live run keeps writing, so terminate it before the review freezes the head. An exit code of 143 after a deliberate stop is expected.
- **Pre-check a docs-only waiver against the path list.** A "build skipped: docs-only diff" line is valid only when every changed path is under the docs folder. Confirm with the paginated file list, and put the replacement checks in the body.
- **Compute word counts with front matter stripped.** Raw counts overstate length and make a borderline file look compliant.
- **Scan for banned terms with a case-insensitive, word-boundary regex.** When a term hits, reword the sentence. Do not add a disclaimer, because the disclaimer usually repeats the term.
- **Quote the exact scan command and its empty result in the body.** A reviewer can then rerun the check.

## Verification
- `cursor-agent status` reports a signed-in account before any order runs.
- The smoke test returns the exact expected string.
- The completion line is present in the output file, and the recorded exit code is the agent's own.
- `git status --porcelain` and `git show --stat HEAD` list only the files the order allowed.
- The driver's build or test output, with its exit code, is quoted in the evidence section.
- The pull request state, read from the host after the push, shows a draft that is not merged.
- Every cited URL has its status and title checked by the driver, and each claim matches a capture.
- The banned-term scan prints no matches, and its command and output are in the body.

## Attribution
The install step follows the vendor's public installer page at https://cursor.com/install. The vendor's behavior can change between releases, so check the flags with `cursor-agent --help` before you script them.
