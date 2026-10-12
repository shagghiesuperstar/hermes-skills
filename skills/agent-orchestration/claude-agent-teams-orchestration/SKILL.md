---
name: claude-agent-teams-orchestration
description: Use when Claude Code leads an Agent Teams swarm. Covers a parallel swarm on a multi-module task. Sets the spawn contract, file ownership, and proof fields.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [claude-code, agent-teams, orchestration, parallel-work, verification]
    category: agent-orchestration
related_skills: [adversarial-review, claude-cli-model-switching, hermes-kanban-harness-dispatch, external-coding-agent-orchestration]
---

# Claude Agent Teams Orchestration

## Overview
Claude Code Agent Teams let one lead session coordinate several teammate sessions that share a task list and a mailbox. They pay off on parallel work with separate file ownership, and they cost far more tokens than a single session. The common failure is a prompt that asks for a team and silently gets ordinary subagents, or a team that edits the same files and overwrites itself. This skill sets the contract for when to use a team, how to spawn one, and what proof to return.

## When to Use
- A task splits into two or more independent modules with separate file ownership.
- You want parallel review lenses (security, performance, tests) on the same change.
- Several debugging hypotheses should be tested at once and compared.
- A feature crosses layers (API, UI, and tests) and each layer can be built in parallel.

Do not use a team for a one-file fix, sequential edits to the same file, or a tight dependency chain. Use one session or plain subagents instead.

## Features
- A spawn prompt template that forces a real team, not subagents, and names each teammate's file ownership.
- Rules for plan approval before risky writes, and for a lead that waits for every teammate.
- A review role that keeps the implementer from reviewing its own files.
- An outer graph that runs each harness in its own worktree, with an independent verifier gate.
- A proof list the lead returns with every completed run.

## Benefits
- Parallel work finishes faster when the modules really are independent.
- File ownership rules prevent two teammates from overwriting each other.
- An honest `agent_teams: false` flag makes a subagent fallback visible instead of hidden.
- Independent verification means the team's own review is never the only check.
- Risky schema, auth, and payment changes wait for an approved plan.

## Procedure
1. Decide whether a team is justified. If the work is sequential or touches the same files, run a single session and stop here.
2. Enable the experimental feature. Agent Teams are off by default and need Claude Code v2.1.178 or later. Set the flag in the user settings:
   ```json
   {
     "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" },
     "teammateMode": "in-process"
   }
   ```
   Use `in-process` as the default for automation. Split panes need tmux or iTerm2.
3. Launch the lead from the exact task worktree, not from a shared checkout:
   ```bash
   cd "<project-dir>"
   claude --teammate-mode in-process
   ```
   Set the permission rules in the settings file before the run, and review them there. For unattended runs, start the session under tmux and keep a transcript.
4. Write the spawn prompt. It must contain the items in the lead prompt template below. The phrase "spawn an agent team with teammates" must appear literally. A vague prompt degrades to subagents.
5. Give each teammate a name, a role, an exact file-ownership list, and a concrete deliverable. Use three to five teammates by default. No two teammates may edit the same file unless ownership is handed over explicitly.
6. Require plan approval for risky areas. The lead rejects any plan that lacks tests, a rollback path, or respect for protected paths.
7. Add a reviewer teammate for anything ship-critical. The reviewer flags defects with citations and does not edit. Implementers never review their own files.
8. Wait for every teammate. The lead must not do teammate work or summarize before all relevant tasks finish. Inspect task state, because it can lag behind real output.
9. Shut teammates down gracefully, then collect the proof list below.
10. Hand the commit, diff, and test evidence to an independent verifier from a different model vendor than the lead. The team's own review is not acceptance.

### Lead prompt template
State every item below in the spawn prompt:
- Spawn an agent team with teammates, not regular subagents.
- Name three to five teammates, each with non-overlapping file ownership.
- Build a shared task list with dependencies.
- Require plan approval before implementation in risky areas.
- Teammates must message findings to each other and challenge weak ones.
- Run the project's tests and include the exact output.
- Wait for all teammates and nudge or reassign any that fail.
- Shut teammates down, then return the summary fields.

### Headless run
A headless run has no person to answer a permission prompt, so set the permission rules for its worktree in advance and use headless mode only in a disposable worktree:
```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
cd "<project-dir>"
claude -p "$(cat "<workspace>/team-prompt.md")" --max-turns <n>
```
Teammates inherit the lead's permission mode, so keep those rules narrow. If a run needs a permission the rules do not grant, stop and ask the operator rather than widening the rules.

### Outer graph for a substantial goal
```text
orchestrator plan
  ├─ Claude Code agent-team lane (own worktree)
  ├─ independent alternative implementation (own worktree)
  └─ independent analysis lane (own worktree)
        ↓
verifier gate (depends on every relevant lane)
        ↓
fix-forward task to the owning lane if rejected
        ↓
final verifier and synthesis
```
Give each lane its own branch and worktree. Two harnesses must never edit one worktree.

## Pitfalls
- **Subagents look like a team but are not one.** Subagents report only to the caller. Teammates share a task list and message each other. If the lead spawned subagents, redirect it and ask for a real team.
- **Headless runs stall on permission prompts.** With no interactive panel, prompts go to the lead with nobody to answer. Settle the permission rules before the run, so the run never needs an answer it cannot get.
- **Never let a team judge its own ship-critical work.** Route the result to an independent verifier from another model vendor.
- **Do not edit while a review loop is running.** Changing the artifact mid-loop invalidates the review.
- **Teammates do not get the lead's chat history.** Put the full task context in the spawn prompt. Teammates do load project instructions, skills, and MCP servers.
- **Teammates do not inherit the lead's model setting.** Set the teammate model in the settings or in each spawn request.
- **In-process teammates do not survive a resume.** After resuming a session, spawn the replacements again.
- **A team is expensive.** Token cost grows with each teammate, so keep the team to the parallel modules that justify it.
- **Split panes need tmux or iTerm2.** They do not work in every terminal, so do not assume them in automation.
- **Be honest about fallbacks.** If the team did not form, record `agent_teams: false` with the reason, and do not claim a team ran.

## Verification
Before marking the run complete, capture:
- The lead session identifier and the team's task directory.
- Each teammate's name, role, file ownership, and final task outcome.
- `git status --short`, the diff stat, and the list of changed files.
- Each test, lint, and security command with its exit code.
- The commit SHA, if a commit was requested.
- Remaining risks and the rollback procedure.

If the team fails to form, permissions deadlock, or a teammate fails, steer the lead once, replace the failed teammate if needed, and block the task with the exact evidence if it still fails. Do not claim completion.

## Attribution
Behavior follows Anthropic's public Claude Code documentation for agent teams: https://code.claude.com/docs/en/agent-teams
