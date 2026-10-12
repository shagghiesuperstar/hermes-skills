---
name: hermes-spec-first
description: Use when a kanban task spawns coding or analysis work. Covers architecture work too. Writes a spec file first, then runs readiness and course-correct gates.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [spec-first, kanban, readiness-gate, course-correction, handoff]
    category: agent-orchestration
related_skills: [kanban-card-lifecycle, harness-task-prompting, kanban-orchestration]
---

# Hermes Spec-First Convention

## Overview
Free-form task bodies cause three problems. A worker finishes its work and exits without a completion or block call. The task body says one thing and the work does another, with no artifact the next phase can use. And there is no named gate before work starts. This convention fixes each one: a spec file is written before dispatch, a short readiness check runs before work begins, and a course-correct block is the only way a worker changes direction. The convention is a set of handoff rules, not a separate runtime.

## When to Use
- Creating a kanban task that will spawn coding, architecture, or analysis work.
- Resuming a task that will take more than a few tool calls and needs a written spec.
- Reviewing an existing task body to decide whether it needs a companion spec file.
- Deciding whether a task is too small for the convention.

Skip the convention for a trivial one-off task with a body under about 500 characters and one concrete change. Such a task needs no spec file.

## Features
- A spec file written beside the task, before any worker is dispatched, with a referenced path in the task body.
- A readiness gate in which the worker blocks once with three to five task-specific checks before it starts.
- A course-correct gate that is the only route for a worker to change scope.
- A vocabulary lock for allowed values in a spec, with new values sent back to the operator.
- A scope-change gate that re-inventories a source before any code is written.
- A deliverable bundle, with a digest printed in the completion metadata, and a tracker comment drafted when the tracker is not reachable.

## Benefits
- Workers have one document to read, and the next phase can check the work against it.
- Scope drift is caught at the readiness check, before the work is done, not after.
- A worker that discovers the spec is wrong stops and asks, rather than quietly doing something else.
- Operators read one bundled deliverable instead of several scattered files.
- Missing credentials degrade to a visible pending item, not a silent skip.

## Procedure
1. Create the task with a short routing body, no more than about 500 characters. The body holds the assignee, priority, and parent links. It does not hold the detail.
2. Write the spec file in the task's workspace before the dispatcher starts a worker. Use the spec template: goal, scope, out of scope, acceptance checks, files that matter, and open questions.
   ```text
   <workspace>/spec-<slug>.md
   ```
3. Reference the spec from the task body by its workspace path. Put the order identifier, such as a ticket number, in the task title and in the spec's first heading, so later dispatches can find earlier work with one search.
4. When a worker starts, it reads the task, then reads the spec. Before any edit, it blocks the task once with a capability reason that lists three to five checks specific to this task, for example whether every referenced file was read, whether the dependencies are present, and whether the spec is unambiguous. The operator reviews the checks and unblocks the task.
5. If the worker finds that the spec is wrong, incomplete, or out of date, it blocks the task with a needs-input reason that names what changed and what decision is needed. It does not expand scope on its own. The operator then either updates the spec in place and unblocks, or closes the task as superseded and creates a corrected one.
6. Bundle the deliverable for the operator when the work order asks for it. Write one readable markdown file with the analysis and the design inlined, so it can be read cold. Save it to the operator's drop folder with the order identifier as the file name prefix, then print its digest:
   ```bash
   shasum -a 256 "<drop-dir>/<order-id>-<slug>.md"
   ```
   Put the digest in the completion metadata.
7. If the work order names an issue tracker, draft the comment as a file in the task workspace. Include the drop location and digest, the task identifiers, the decisions the orchestrator locked, the checklist with its checked and pending items, and a line stating what the claim cannot detect.
8. If the tracker's credential is not available, do not try to post and do not skip silently. Leave the draft file as the deliverable, mark the tracker item as pending in the completion metadata, and add a comment on the parent task that points to the draft.

### Guarded dispatch for externally reachable or money-touching work
Apply these five guardrails in the spec and the task graph before any worker is dispatched, when the deliverable is a public API, an MCP server, or a payment flow.
1. Separate trust boundaries into separate servers, repositories, or processes. Never combine a write-capable surface with a public read-only surface in one service. A compromised read-only surface must not reach write tools.
2. Allow exactly one human approval gate per mission, worded as a yes-or-no question in the anchor spec. Every other checkpoint is a check the orchestrator runs and reports. A failed check goes to a HALT condition, so the operator sees it. Several fuzzy gates lead to rubber-stamping.
3. List the HALT conditions in the anchor spec before fan-out. Examples are drift between an upstream surface and its fork, behavior that cannot be proven at the SDK level, and legal ambiguity about a public field.
4. Cap every fix loop on a test or verify stage. After the cap, revert and block the task, so a worker does not spend a night polishing an approach that cannot work.
5. Create the synthesis task at dispatch time and block it at once. Do not rely on an initial blocked status with parents alone, because children promote to ready when their parents complete.
Record legal and regulated-data exclusions as spec decisions made at dispatch. Workers implement them and never decide them.

## Pitfalls
- **Do not let a spec exceed about 2,000 words.** A long spec is hard for a worker to reason over. Split it into a context file and a scope file, and reference each by path.
- **The readiness checks must be specific to the task.** Reusing the same generic checks across tasks means the spec was too vague to read as a contract.
- **A course-correct block is for replanning, not for review.** If the work is already done and you want to flag a problem, comment on the completed task instead.
- **Never fabricate metadata on raw material.** When a source is a set of raw transcripts or exports rather than records, skip any field the spec asks for that the source does not hold. Filling it in by template pollutes the record with material that does not belong.
- **Inventory before you classify a new corpus.** Count the files, list the extensions, note the folder structure, and check the size spread. If the count is large, sample first and report before you commit to a strategy.
- **Surface a changed source corpus at the scope gate.** A source that changes mid-task invalidates the first inventory, so the code written against it is the wrong artifact. Re-validate the spec before writing code.
- **Lock the vocabulary in the spec.** A worker that adds a value to a locked list is inventing a rule the operator has not approved. Send the new value back as a needs-input block.
- **Write the drop to the folder the operator reads.** A drop in the wrong place is effectively a missing deliverable.
- **Do not claim a comment was posted without a returned identifier.** Report it as posted only when the tracker's response includes the comment's id.
- **Never paste a draft into a chat as a substitute for the tracker.** The tracker stays the record, and the draft file is what a later session posts.

## Verification
- Each task with a spec has a spec file in its workspace, written before the first worker started. The file's modification time is earlier than the worker's first action.
- The task body references the spec path, and the title and the spec heading both carry the order identifier.
- Every worker blocked once with a readiness reason, and the reason lists task-specific checks.
- Every scope change appears as a needs-input block, with the operator's decision recorded in the spec.
- The completion metadata includes the digest of each drop, and the digest matches a fresh run of the checksum command on the drop file.
- Each tracker item is either posted with a returned identifier or marked pending with its draft file path.
