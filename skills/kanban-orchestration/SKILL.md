---
name: kanban-orchestration
description: Use when several agent workers share one kanban goal. Covers card contracts, dependency links, dispatch checks, review gates, blocker routing, and recovery after crashes or timeouts.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [kanban, orchestration, dispatch, dependencies, multi-agent]
    category: agent-orchestration
related_skills: [kanban-card-lifecycle, kanban-board, kanban-worker-spawn-failures, hermes-role-orchestration, external-coding-agent-orchestration, adversarial-review, merge-reconciler, dispatch-proof, steer-protocol]
---

# Kanban Orchestration: Multi-Worker Goals on a Board

## Overview
An orchestrator turns one goal into cards on a durable board. Each card goes to a worker profile, and a dispatcher claims ready cards and starts the workers. The board outlives the orchestrator's session, so a restart loses no in-flight work. The orchestrator owns scope, dispatch, review gates, recovery, verification, and the final report. A worker executes one card and does not widen it. Every claim that a card is done is checked against the outside world (the pull request state, the commit on the branch, or a live request). A worker's own report is not enough.

## When to Use
- The goal has more than two parallel workstreams, runs past about 30 minutes, must survive a session restart, or spans hosts or engines.
- The goal has explicit done, partial, and blocked gates that someone must track.
- Several workers must hand work to each other in a fixed order, with reviewers in between.

Not for a single bounded lookup that finishes in one tool call (use in-session delegation), a single repository edit handed to one headless CLI (use `external-coding-agent-orchestration`), or installing and signing in to an engine (use `local-agent-cli-setup`).

## Features
- A card contract: a one-line TELOS naming the mission, and three to seven DONE-MEANS criteria, each checkable by a command, a file, or a cited source.
- Dependency links set at creation, so a child waits for its parent without anyone remembering to release it.
- Per-card workspace modes: scratch for read-only work, an isolated worktree for edits, or a fixed directory.
- A review gate that needs an approval and an independent second opinion on a frozen commit before any merge.
- Blocker routing that names the owner of each block: the operator, the orchestrator, or a third party.
- Loop stop rules: a maximum number of rounds, a no-progress check, and a stop when the source is stale.
- A recovery checklist for crashed, timed-out, and blocked cards.

## Benefits
- Board state is durable, so a restarted session reads the board instead of rebuilding its memory.
- A card's criteria stop a worker from declaring its own work done.
- The operator gets one status table: card, status, assignee, and process ID.
- One writer per checkout means two runs cannot overwrite each other's edits.
- Blockers reach the right owner in the turn they appear, not at the next check-in.
- Work is spread across engines, so one subscription's limit does not stall the whole run.

## Procedure

### 1. Plan the goal
1. Break the goal into cards. Set each dependency with a parent link at creation (step 2), not later.
2. Before writing cards for a repository, list its open pull requests and classify each one. LAND-FIRST: reviewed or already decided by the operator, and changes what users see; it becomes the base. PARALLEL: no file overlap; run alongside. STALE: superseded or already on the main branch; propose closing it with a comment to the operator, and close it only after an explicit go-ahead. Open drafts are queued future state, not noise.
3. Before dispatching a second builder into a repository that already has one in flight, compare the two file lists. On overlap, give one card ownership of the shared file, or chain the second card behind the first.
4. Write each card with TELOS and DONE-MEANS. No criteria, no dispatch. A trivial card (a typo or a one-line docs fix) may skip the contract, and the skip reason goes on the card.
5. Put every cross-card decision (URLs, IDs, names, schemas, versions) verbatim into each card body that depends on it. Workers read their own card body, not sibling cards or the parent board, so a spec file alone is not enough.
6. Keep secrets out of card bodies, comments, and metadata. Stage them through the team's secret-handling step.
7. In the same turn a goal is accepted, create the board, at least one card, and post the board listing to the requester. If you cannot do all three, say "deferred until <when>". Specs on disk are not progress the operator can see.

### 2. Create cards and links
A typical create call, with placeholders:
```bash
hermes kanban create \
  --body "<context, success criteria, TELOS and DONE-MEANS lines>" \
  --assignee <profile-name> \
  --workspace scratch | worktree | worktree:<path> | dir:<path> \
  --branch <branch-name> \
  --priority <integer> \
  --goal --goal-max-turns <N> \
  --max-runtime <seconds> --max-retries <N> \
  --model <model-id> --provider <provider> \
  --skill <skill-name> --skill <another-skill> \
  --parent <parent-id> \
  --created-by <label> \
  --idempotency-key <unique-key> \
  "Card title"
```
- `--goal` makes the body the goal prompt. Without it, the body is a context note.
- `--assignee` is required. A card with no assignee is invisible to the dispatcher.
- `--priority` takes an integer, where a lower number runs first. Words such as "high" are rejected.
- `--skill` takes one bare skill name per flag. Comma-joined names are rejected, and a category path fails at worker startup.
- Give every review or verification card an explicit `--max-runtime`. The default limit can kill a verifier while it is writing its verdict.
- A review card whose parent is already finished promotes at creation. Parent it on the current round only.
- Show the card by ID in the same turn. A returned task ID is not proof that the card was stored.

Dependencies:
```bash
hermes kanban link <parent-id> <child-id>     # positional; link has no --parent flag
hermes kanban unlink <parent-id> <child-id>
```
- Link at creation, or in the same turn before the next dispatcher tick. A link added after both cards are claimed does not stop them.
- A blocked child moves to ready when every linked parent is done. Create the prerequisite cards and link them in the same turn.
- A child whose parent sits in triage never promotes. Supersede the dead parent: create a fresh card, copy the spec, comment "SUPERSEDED by <id>" on the old card, and link the new one.

### 3. Write the spec before dispatch
For workers that read a per-card spec directory, write the spec first, verify it with `ls -l`, then create the card. A worker that claims before the spec is on disk blocks itself on the missing file. The spec holds the full context: repository, branch tip, prior verdicts, shared values, and DONE-MEANS with proof commands. Keep the card body short. If the scope changes, re-write the spec and say so on the card.

### 4. Dispatch and watch
- The dispatcher runs inside the gateway, and there is no separate daemon to start. It ticks about every 60 seconds (`kanban.dispatch_interval_seconds`), claims ready cards for their assignee, and writes lifecycle events to the board.
- A worker that exits without completing, requesting review, or blocking is recorded as crashed.
- Before a real goal, run a smoke card: it claims, prints an exact string, and completes. If it stays ready for more than two ticks, check the gateway, the assignee listing, and the dispatch log.
- A ready card has no process ID until it is claimed. Do not report it as running.
- Subscribe the operator's channel to card events with a delivery mode: `notify` (silent), `notify+wake` (also wakes the orchestrator), or `wake`.
- Confirm which engine really ran from the run's log or the model field in the JSON output, not from the profile's pin or the worker's self-report.
- Between turns nothing runs. Arm a heartbeat that reports, and a watchdog that inspects blocked, crashed, and stale cards. Schedule both through the goal's horizon, and emit a final packet once every card is terminal.
- A direct "continue" from the operator is an action trigger. Re-read board state, act on the blocking edge, or name the outside blocker. Repeating the last status is not a response.

### 5. Review and merge gate
- A worker's "done" is not a review. Merge only after an approval from a named reviewer, an agreement from a critic of a different vendor, both on the frozen commit, and the operator's explicit go-ahead to merge. Keep receipts: model used, session ID, elapsed time, and cost.
- A builder's self-review, even from a sub-run, never counts.
- Request review with an explicit reviewer. A review request with no reviewer re-routes the card to the profile that built it, and that result is void.
- Do not request review on a parent that already has a reviewer child. The child is the review of record.
- A child that promotes when a review completes also fires on NEEDS_CHANGES. Link it to the post-repair review instead.
- Do not accept a builder's own verifier as evidence. Write the gate yourself, take its vocabulary from the live artifact, and re-run it before declaring PASS. Put the gate in the builder card and the reviewer card as step zero.
- Evidence rows must cite a live command, a real request, or a timestamped probe. Unit tests against mock clients, self-blocks, and "residual risk" notes are not PASS.
- A fix that passes review can still miss the failing path. Confirm which code path the failing user actually reaches.
- After a merge-main sync, compare the sha256 of each reviewed file at the approved commit with the same file at the new merge commit. Any mismatch means the sync changed reviewed code; stop and queue a fix.
- For a batch of approved merges, after the operator's go-ahead, the named integration owner runs each merge with `--match-head-commit`. The owner checks the start point against live main at queue time and again before the first merge, then diffs main against the tested commit. Only the expected files may differ.
- A builder whose lane forbids merging into main is not a failure. The card ends at the review gate, and the operator, or the named integration owner after the operator's go-ahead, does the merge.

### 6. Classify blockers and recover
- Classify each blocker when it appears:
  - OPERATOR_ONLY: credentials, a vendor dashboard, spend, DNS, or a live visual approval. It waits for the operator.
  - MINE: anything decidable from disk, live state, or documented rules. Clear it the same turn, and never queue it behind an operator-only gate.
  - VENDOR: a third party. Block the card, log the contact, and do not present it as yours.
- Read each card's block reason before unblocking after an outage. Some blocks are outage artifacts and some are real needs. A blanket unblock re-runs the real ones into crash loops.
- After repointing a profile to a new provider, set the model on each blocked card with `hermes kanban --board <board> set-model --provider <provider> <task-id> <model>`. Cards keep their spawn-time override, and unblocking alone re-spawns them on the dead lane.
- A worker that dies within about a minute with an empty log died at spawn. Read the log before retrying.
- Unknown-skill errors repeat until the dispatcher gives up. Fix the skill set or create a new card. Do not re-unblock the same card.
- Diagnose before retrying. HTTP 404 on a pinned model is a capability block, HTTP 429 is a quota limit, and an empty log at about 60 seconds is a spawn failure.
- A timed-out run whose commit is already pushed, clean, and open for review is complete. Do not rewrite it. Stop the process with TERM (exit 143 is expected), then spawn review on the frozen commit.
- An expired login on one engine is a capability block on that card. Route the card to another authenticated engine only if the card does not need the first one. Otherwise ask the operator for the single login command.
- A CLI's usage limit is separate from the provider's API. When a review card names a critic engine, name a fallback engine on the same card.
- Before stopping an idle interactive session, check that its work is in git and on the board, back up uncommitted files, stop it, and report the list.
- Do not kill a slow run. Check `git -C <worktree> log --since "<launch time>" --oneline`, the files changed since launch, and the last log turn. Stop a run only when it is provably stuck.
- For a mid-run scope change, wait until the worker reaches a clean point with no merge in flight. Stop it with TERM, confirm it exited, and resume the same session with a new order that holds the new stop conditions.
- Never kill a process group that the orchestrator shares. Kill the child process and its descendants.
- A fossil card (already on main, superseded, or met elsewhere) is completed or archived. Do not unblock a goal card just to close it.
- Use `archive` to retire a mis-specified card, since the board has no cancel command.
- Block kinds: `dependency` waits and promotes when its parent finishes, and promotes at once if it has no parent. `needs_input` and `capability` wait for a person. `transient` routes to triage after repeated re-blocks.
- Two `needs_input` blocks on one card trip a loop guard that moves it to triage. Fix the cause first, then park the card with `dependency` linked to the fix card.

### 7. Report
- Each status reply has a table of card, status, assignee, and process ID for every running card, then one bottom-line sentence.
- State what did not happen, with its time: "no review yet, requested 17:20, 40 minutes stale."
- Give each decision with a recommendation, a reason, and the trade-off on one line. Do not present an open menu.
- Use plain words for buttons and places, and put the link first.
- An obligation the operator gave is never closed by the orchestrator. If the facts change, re-scope it and say so in one line.
- A gap noticed during a card goes in a one-line comment on that card, not into a new card in the same turn.
- A watcher that scans one tracker misses approvals in another. List every tracker the goal uses.

## Pitfalls
- A shared workspace root shadows stdlib imports. Never name a helper after a stdlib module (`json.py`, `types.py`, `inspect.py`); every worker on that root can break silently. Put helpers in a `scratch/` folder.
- Worktree creation races when two workers add worktrees on the same repository. Create the checkouts in the orchestrator's turn before the workers start. On failure, prune and re-add, and never force-unlock the index.
- If every worktree card dies at spawn while directory cards run, switch to directory cards, record the finding, and keep one writer per checkout.
- Scratch workspaces are deleted when a card completes. Only paths listed as artifacts survive.
- Delegated child runs can leak parent-context variables into the parent shell. Unset `HERMES_DELEGATED_CHILD_CONTEXT`, `HERMES_PARENT_PID`, `HERMES_PARENT_NONCE`, and `HERMES_PARENT_START_MARKER` before any board command.
- Sub-sessions launched from a worker inherit its board identity. Unset `HERMES_KANBAN_TASK` and `HERMES_KANBAN_BOARD`, and restrict tools so a reviewer can only write its verdict.
- Print-mode runs do not start agent-team teammates. Use an interactive session, and require teammate IDs and messages as proof.
- Pass a long brief to a harness through a file on stdin. Do not inline it in a shell heredoc.
- A wrapper that runs a CLI through npm can consume its `-p` flag. Pass the command after `--` (for example `npm exec --package=<pkg> -- <cli> ...`) or feed the prompt on stdin.
- A squash merge orphans the source branch. Before squash-merging a branch that still has a live worktree, rebase the worktree onto main, or freeze the branch and cut new work from main.
- Idle sessions still draw on a shared quota. Keep queued work for every engine that has spare quota, since idle paid capacity is a planning gap.
- A deploy that waits behind an in-flight build needs the queue time in its ETA.
- When swapping two values in an edit, make two separate edits and re-read the file after each one.
- Name the cause only after the timeline is mapped: the exact failure time, the error or signal, and what the process was doing just before.
- A local patch that an update erases is not a fix. After every update, confirm the patch survived, and track the upstream fix.
- If a delegated second opinion ran on a different model than requested, say so on the first line of the report.
- A "fixed" or "should work now" claim is a hope until a live check runs. Verify it in the same turn.
- A feature that ships behind a flag while the default keeps the old behavior is not delivered. Name the default in the spec.
- A worker's artifact claim is a citation. Re-run the check yourself before you repeat it.
- A status that shows only the wall clock tells the operator nothing new. Include the card table with process IDs.

## Verification
- Each card has TELOS and three to seven DONE-MEANS criteria, and its assignee appears in the board's assignee listing.
- Each dispatched card shows by ID in the same turn, and each running card has a process ID confirmed in the process list.
- Each review names a frozen commit, a reviewer and a critic from different vendors, receipts, and live evidence rows.
- Each merge has a `--match-head-commit` receipt, a read of the changed file from the target branch, and a sha256 sync check when main was merged in.
- Each recovery records the block reason that was read, the model that was repointed, and the process that was stopped.
- Each status reply has the card table with process IDs and one bottom-line sentence.
- At the end, every card is terminal, or the board carries an expiration packet that names the open cards.
