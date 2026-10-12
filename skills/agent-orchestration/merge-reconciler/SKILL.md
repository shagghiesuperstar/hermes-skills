---
name: merge-reconciler
description: Use when two agents' branches conflict in a git merge or rebase and neither agent should decide the outcome alone. A neutral third party reconciles the conflict.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [multi-agent, git, merge-conflict, arbitration, reconciliation]
    category: agent-orchestration
related_skills: [adversarial-review, independent-static-review, hermes-kanban-harness-dispatch]
---

# Merge Reconciler

## Overview
When two agents change the same files in parallel, a merge conflict is a disagreement about intent, not only about text. An agent asked to resolve a conflict against its peer's work tends to do one of two bad things: it overwrites the peer's change, or it drops its own. Both agents lack the other's full context and are biased toward their own side. This skill sets up a neutral reconciler, a third party that receives both diffs and both sides' stated intents, and produces one merged result, the way a merge-queue arbiter would. The reconciler resolves only the conflicted regions and explains every decision.

## When to Use
- Two agent branches or worktrees collide during a parallel campaign, such as a set of parallel pull requests or a multi-worktree refactor.
- A merge or rebase stops on conflicts between two agents' work, and neither original agent should decide alone.

Do not use this for conflicts inside one agent's own work, or for trivial generated-file or lockfile conflicts. Regenerate those instead.

## Features
- A neutral reconciler assigned to a third worker, not to either side.
- A gathering step that collects both diffs and writes down each side's intent before any file changes.
- A three-class model for each conflicted hunk: disjoint intent, same question with different answers, and superseded premise.
- An impartiality contract: edit only conflict regions, never favor the spawning side, and list every design choice.
- A verification step that diffs each file against both sides, not only against a compile check.

## Benefits
- Neither original agent decides the merge about its own work.
- Disjoint changes both survive, instead of one side being dropped wholesale.
- Every design choice appears in the hand-back, so a person can veto it.
- Silent drops from automatic merging are caught before the merge is committed.
- A repeated conflict on the same file is flagged as a hotspot to split, not a routine fix.

## Procedure
1. Gather both sides before you touch any file. Confirm the conflicted state, list the conflicted files, and find the common base.
   ```bash
   git status
   git merge-base "<branch-a>" "<branch-b>"
   git log --oneline "<base>..<branch-a>"
   git log --oneline "<base>..<branch-b>"
   git diff "<base>..<branch-a>" -- "<conflicted-file>"
   git diff "<base>..<branch-b>" -- "<conflicted-file>"
   ```
   In a halted merge, the current head is one side and the incoming merge head is the other.
2. Collect each side's intent. Use the task completion summaries, the pull request bodies, or the commit messages, in that order of preference. Write one sentence of intent per side in your own words. If neither side's intent can be recovered, stop and escalate instead of guessing.
3. Classify every conflicted hunk, not every file. Each conflict block gets exactly one class, judged by the stated intents:
   - **Disjoint intent:** the two changes serve different goals and can coexist. Combine both.
   - **Same question, different answer:** both sides answered one design question differently. Pick one answer that best serves the stated intents, and record the question and the pick.
   - **Superseded:** one side's premise no longer holds after the other side's change. Keep the surviving side and note why.
   A single hunk can hold several independent decisions. Split it and classify each part. One file often mixes classes, so classify per hunk.
4. Resolve under the impartiality contract:
   - Merge disjoint changes so each intent is fully served.
   - For a same-question conflict, choose the answer that best matches the stated intents. Do not invent a hybrid that neither side proposed.
   - For a superseded premise, delete the dead premise.
   - Change nothing outside the conflict markers. No formatting, renames, or opportunistic fixes.
   - If the intents genuinely tie, escalate. Do not pick a side by default.
   Stage each resolved file, then confirm that no conflict markers remain in the tree.
5. Verify, and do not stop at a successful compile. Run the project's build and tests, and check that both intents are visible in the merged behavior. Then diff each conflicted file against both sides:
   ```bash
   diff <(git show HEAD:"<file>") "<file>"
   diff <(git show MERGE_HEAD:"<file>") "<file>"
   ```
   Automatic merging can keep one side's whole block when both sides redeclare the same names, and it drops the other side's lines without leaving a marker. For each symbol one side introduced that is now missing, port the lost block back in before you commit.
6. Commit the merge with the default merge message, plus a body that lists each hunk decision.
7. Hand back a summary that names every hunk: file, line range, class, which side was kept, and the rationale. For each same-question conflict, state the question and the answer you chose, so a person can reject it.

## Pitfalls
- **Self-favoring bias.** A reconciler spawned by one of the conflicting agents is structurally biased. Assign the reconciler to a third worker, with both conflicted tasks as parents, so its context carries both completion summaries.
- **Splitting the difference produces a design nobody asked for.** Pick one answer for a design collision, and surface the pick.
- **Classifying a whole file as one class drops disjoint changes.** Classify each hunk.
- **Drive-by edits make the merge unreviewable.** They also take decisions away from the original agents.
- **Thin commit messages hide intent.** Prefer the task completion summaries or the pull request body. Escalate when neither exists.
- **A repeated conflict on the same file is a hotspot.** Flag the file for the orchestrator to split, instead of reconciling every new collision on it.
- **A successful compile does not prove a merge is complete.** Automatic merging can drop a whole block of one side while the file still compiles, so always diff against both sides.
- **Changes outside the conflict markers are out of scope.** A cleanup inside a merge commit hides what the merge actually decided.

## Verification
- The working tree is clean on the target branch, and a merge commit exists.
- A search for conflict markers in the repository returns nothing.
- The build and tests pass, and both sides' intents are visible in the merged behavior. Any side that was not kept is named in the summary.
- The diff of each conflicted file against each side accounts for every line, and no symbol introduced by either side is missing without an explanation.
- The hand-back summary lists every hunk with its class and rationale, and every design choice is named.
