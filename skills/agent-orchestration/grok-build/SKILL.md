---
name: grok-build
description: Use when driving the Grok Build CLI on a named git branch with its memory feature on. Covers memory setup, prompt ordering, interrupted runs, and safe commits.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [grok-build, coding-agent, memory, git, cli]
    category: agent-orchestration
related_skills: [external-coding-agent-orchestration, claude-agent-teams-orchestration, cursor-agent-cli, git-remote-hygiene]
---

# Grok Build CLI

## Overview
The Grok Build CLI runs a coding agent against a repository. This skill covers how to drive it on a named branch with its memory feature on, how to order the prompt so memory consolidation happens before editing, how to recover when a run stops partway, and how to commit only the work that was in scope. The main failure modes are a memory setting that is set in one place but not another, a prompt ordered so the consolidation step is skipped, and a stopped run whose partial edits get thrown away.

## When to Use
- Assigning a bounded coding task to Grok Build on a specific branch.
- Setting up or checking memory for a Grok Build profile that launches from another profile.
- Recovering from a Grok Build run that was cancelled, stalled, or left edits on disk.
- Committing and pushing the result of a Grok Build run.

## Features
- Memory is enabled in two places: an environment variable for the process and a configuration entry for the tool.
- A prompt order that runs memory consolidation before the task, so the agent consolidates, then dreams, then edits.
- A prompt file kept outside the working tree, so it is never staged by accident.
- A recovery rule for a stopped run: keep the working tree, check the diff, then commit.
- A commit sequence that fetches first and stashes named paths before any fast-forward.
- An operator summary that lists the commit SHA, the changed files, and one line of notes.

## Benefits
- Memory is on for every run, so the agent carries context between tasks.
- Work already on disk survives an interrupted run, so the task does not restart from zero.
- Staging only named paths keeps unrelated files out of the commit.
- The commit always sits on top of the latest branch tip, so a concurrent change is not overwritten.
- The operator gets one short packet to act on.

## Procedure
1. Enable memory in both places. Export `GROK_MEMORY=1` in the process environment, and set `enabled = true` under the `[memory]` section of the tool's configuration file. Back up the configuration file first. If the profile that launches the tool does not inherit the parent shell's variables, set the variable in that profile's environment file as well.
   ```bash
   cp "<tool-config-file>" "<tool-config-file>.bak"
   ```
   Never pass a flag that turns memory off.
2. Confirm memory from the configuration file and the process environment, not from the structure of a status command's output. A status report can omit a memory field even when memory is on.
3. Check the installed skills, and load only the ones the operator approved for this profile. Do not copy a whole third-party skill pack to get one skill.
4. Check out the named branch. Set a local user name and email in the clone if the global configuration does not apply to that path.
5. Write the task to a prompt file outside the repository. Begin the prompt with the memory steps, in this order: the memory consolidation command first, then the dream command, then the task itself. Put the hard limits in the prompt too, such as paths that must not change and actions that are not allowed.
6. Launch the run in the repository. Run it headless, pointed at the prompt file, with the approval and permission settings the operator has already agreed to for this profile. Do not widen those settings to get past a prompt.
7. Poll the process until it exits. Then check the state of the work:
   ```bash
   git status --short
   git diff --stat
   ```
8. If the run was cancelled, or it sits idle after files have already changed, stop the process and keep the working tree. Do not discard the changes. Check that the diff is within scope, then commit. Do not wait for an optional preview step to finish.
9. Before committing, fetch the branch. If the local branch is behind, stash only the named paths, fast-forward, and pop the stash. Then commit.
   ```bash
   git fetch origin "<branch>"
   git stash push -- "<path>"
   git pull --ff-only
   git stash pop
   ```
10. Scan the change for secrets and unexpected files, following the repository's hygiene procedure (see the git-remote-hygiene skill). Then push the branch:
    ```bash
    GIT_TERMINAL_PROMPT=0 git push origin HEAD
    ```
11. Report the commit SHA, the list of changed files, and one line of notes to the operator.

## Pitfalls
- **Setting memory in only one place does nothing.** The tool needs both `GROK_MEMORY=1` in the process environment and `enabled = true` under `[memory]` in its configuration file. A slash command typed into the prompt is not a substitute. A profile that launches the tool may not inherit the parent shell's variables.
- **Prompt order matters.** Put the consolidation and dream commands before the task. Running them after the edit skips the consolidation step.
- **Keep the prompt file outside the working tree.** A scratch prompt in the repository root gets staged by a broad add.
- **Stage explicit paths only.** A broad add of the whole tree pulls in unrelated edits.
- **Do not discard the work of an interrupted run.** The edits on disk are the deliverable. Check the diff and finish the commit instead of restarting the run.
- **Do not rebase uncommitted edits onto a moving branch.** Stash the named paths first, then fast-forward. Hand-merging edits in the same index can silently drop one side.
- **Install only the approved skills.** Copying a whole third-party skill pack to get one skill also installs everything else in it, including parts the operator did not approve.
- **A design-only task stays design-only.** Do not expand the task into build or deployment fixes that belong to a separate task.
- **Do not claim a result the diff does not show.** The commit's file list is the evidence.

## Verification
- The memory configuration file shows the memory flag on, and the process environment shows the variable set, both before the run.
- The prompt file begins with the consolidation and dream commands, and it sits outside the repository.
- `git diff --stat` after the run lists only in-scope files.
- The commit includes only the named paths, and `git log -1` shows the commit SHA reported to the operator.
- The push succeeds, and the remote branch shows the same SHA as the local branch.
