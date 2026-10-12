---
name: kanban-board
description: Use when managing tasks on a Hermes kanban board, such as creating, dispatching, linking, checking status, or diagnosing a run that keeps cycling.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [kanban, multi-agent, task-management, dispatch, diagnostics]
    category: agent-orchestration
related_skills: [kanban-orchestration, kanban-card-lifecycle, kanban-worker-spawn-failures]
---

# Kanban Board

## Overview
The Hermes kanban board is a task system built into Hermes Agent. It holds tasks, their dependencies, their runs, and their comments, and it dispatches ready tasks to agent profiles. The board is command-line only. The database is the source of truth, and the workspace files a worker writes are supporting material. This skill covers the commands, the task lifecycle, how to read a run history, how to structure a sprint of parent and child tasks, and how to answer a status question without over-reporting.

## When to Use
- Creating, assigning, linking, completing, or archiving tasks on a board.
- Checking whether work is running, blocked, or finished, and reading why a task keeps restarting.
- Decomposing a goal into a sprint, with a parent task and child phase tasks.
- Holding implementation tasks behind an operator approval.

## Features
- A command set for listing, showing, creating, linking, commenting, dispatching, and archiving tasks.
- A task lifecycle and a run-cycling model, so repeated restarts are read correctly.
- Sprint decomposition with parent and child tasks, and an approval-gated variant.
- Read-only diagnostic queries against the board database.
- A short heartbeat check that answers idle or busy with one line.
- A rule that separates a comment nudge from a real-time interrupt.

## Benefits
- Operators find the state of a task from the run history, not from a worker's last message.
- Sprints are visible as one parent with linked children, so the operator can track each phase.
- Approval gates keep implementation tasks waiting until the operator decides.
- Duplicate tasks are removed on purpose, so the board stays accurate.
- Status checks stay fast, because the answer is one line.

## Procedure
1. Initialize the board once, and list its tasks to confirm the state.
   ```bash
   hermes kanban init
   hermes kanban ls
   hermes kanban stats
   ```
2. Inspect a task before acting on it. The full view shows its events and runs.
   ```bash
   hermes kanban show <task-id>
   hermes kanban runs <task-id>
   hermes kanban tail <task-id>
   ```
3. Create a task with a title as the positional argument, the body flag, and the assignee flag. Keep the body short, and put the detail in a spec file.
   ```bash
   hermes kanban create --assignee <profile> --body "<short body>" "<title>"
   hermes kanban create --assignee <profile> --body "<short body>" "<title>" --parent <parent-id>
   ```
4. Link children to a parent after you create them. Name the parent first.
   ```bash
   hermes kanban link <parent-id> <child-id>
   ```
5. Dispatch ready tasks, and check the dispatcher without spawning anything first when you are unsure.
   ```bash
   hermes kanban dispatch --dry-run
   hermes kanban dispatch
   ```
6. Comment to record a blocker or a decision. The comment takes its message as a positional argument, not a flag.
   ```bash
   hermes kanban comment <task-id> "<message>"
   ```
7. Read a crash-looping task by its latest run, not by its earlier crashes. A task with several crashed runs before a completed one is normal, because the gateway reclaims stale locks and starts new runs. Read the latest run's summary, and look at the earlier crashes only when they show a specific error.
8. Run a sprint as one parent task and child phase tasks. Create the parent first, then create each child under it and link it. Do not reuse titles or bodies across sprints, even when two phases look alike.
9. For work that must wait for the operator, create a parent approval task assigned to the operator. Put the planned implementation tasks under it, and leave them in the waiting state. State in the approval body that nothing changes before approval. After approval, complete the approval task, and the children proceed.
10. Remove a duplicate or badly created task in this order: complete it, then archive it. Create the correct task before you archive the wrong one, so the work never loses its card and the board never holds two cards for it.
11. Answer a heartbeat question in one line. Check the newest task created in the last few minutes for the profile or title in question, and reply idle or busy with that task's identifier. Do not add totals, lists, or queries to the reply.
12. Nudge a running task correctly. A comment asking for a status update is a queued request for the worker's next checkpoint, not an interrupt. Post the comment, read the task's heartbeat timestamps for the real signal, and report both facts to the operator.

## Pitfalls
- **A worker never sees a comment mid-run.** Most workers read their comment thread only at the next claim or after a block and unblock. Report a comment as queued, not as delivered.
- **Read the board database at the path of the active board.** A current-board link can point at a different board with a different schema, and queries then fail with "no such table."
- **Know the time columns.** Tasks and runs use different time columns. A run has start and end times, not a creation time. Querying a time column that does not exist fails with "no such column."
- **Do not over-answer a heartbeat.** The reply is the deliverable. Extra totals or task lists belong in a follow-up request.
- **Choose the time window from the operator's words.** "Recent" means about ten minutes. Scale the window if the operator names another.
- **A title pattern with wildcard characters matches more than the text you typed.** Escape or quote the pattern so that it matches what you meant.
- **Never leave duplicate tasks on the board.** A duplicate created by a failed command sends two workers to the same work.
- **An approval gate needs its children created in the waiting state.** Children that start ready run before the operator decides.
- **Keep the database as the record.** Workspace files help a reader, but the database holds the events and runs that decide the state.
- **Do not write to the board database by hand.** Use the commands, so the events and runs stay consistent.

## Verification
- `hermes kanban show <task-id>` lists the expected parent and child links for each sprint.
- `hermes kanban ls` shows no duplicate titles from the same sprint.
- Each approval-gated child shows the waiting state until the approval task is complete.
- A heartbeat reply is one line in the expected form, with the newest matching task identifier when the answer is busy.
- A nudge is reported as a queued request, with the heartbeat timestamp as the evidence.
