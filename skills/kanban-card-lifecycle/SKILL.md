---
name: kanban-card-lifecycle
description: Use when creating, blocking, or unblocking a kanban card. Covers splitting a card, and tasks that look stalled, duplicated, or orphaned on the board.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [kanban, task-lifecycle, stalls, orchestration, handoff]
    category: agent-orchestration
related_skills: [harness-task-prompting, kanban-orchestration, adversarial-review]
---

# Kanban Card Lifecycle

## Overview
A kanban card is the platform's task object: one unit of work with an assignee, a status, parent and child links, runs, and comments. Most stalls on a board are not technical failures. They come from a small set of lifecycle mistakes: a task that waits on a parent that never resolves, a fix that is cut for a pull request that has already merged, a duplicate created by an earlier turn, or a status reported from memory instead of read from the board. This skill sets the rules for creating, blocking, unblocking, and splitting cards, and it names the check that enforces each rule.

## When to Use
- Creating a card, or about to create one that may duplicate an existing one.
- Blocking or unblocking a card, or splitting one into smaller cards.
- Handing a lane from one orchestrator or session to another.
- A card looks stalled, a dependent card never starts, or a status claim has to be checked.

## Features
- A handoff procedure for moving a lane to a new owner, with an owner-change comment on each in-flight card.
- Checks that run before a card is created: a search for an existing card on the same outcome, a read of the live pull-request state, and a check of the lane's engine quota.
- Blocking rules that tell a stuck pull request apart from a stuck card.
- Splitting and superseding rules that keep the history intact.
- A closing checklist for any turn that changed the board.

## Benefits
- A duplicate card is found before a second worker starts on the same work.
- A dependent card starts when its parent is actually done, not when someone remembers it should.
- Status reports are read from the board, so the operator is not told a task is running when it is not.
- A card is never resumed on a pull request that has already changed under it.
- Superseded work is archived in order, so no orphan writer survives.

## Procedure
1. Before creating a card, search the board for an existing card with the same outcome. A card with the same goal, even under another title, counts. If one exists, comment on it instead of creating another.
   ```bash
   hermes kanban ls
   ```
2. If the card depends on a pull request, read the pull request's live state first: whether it is a draft, whether it is open or merged, and its base branch. Use the commit identifier the pull request reports.
   ```bash
   gh pr view "<pr-number>" --json state,isDraft,baseRefName,headRefOid,mergedAt
   ```
3. Create the card with a short body, and link its parents at creation time. A child linked to a parent stays waiting until the parent is done. Write the spec file in the card's workspace before the card is dispatched.
4. Check that the engine the card is routed to can serve the work now. A pinned model that is out of quota stops the card, however the card is written. Check the engine, not only the card's pin.
5. To block a card, record the reason as a comment on the card, then block it with the matching kind of block. Name the blocker in plain language, with the decision or input needed.
6. To unblock a card, read its current state first. Confirm that the blocker is resolved, then unblock it and comment with the reason.
7. To split a card, create the child cards, link each one to the parent, and move the original work into them. Do not reuse titles or bodies from the original card.
8. To supersede a card, comment on it with the replacement, then archive it. Archive child cards before their parents.
   ```bash
   hermes kanban archive "<task-id>"
   ```
9. To hand a lane to a new owner, write a handoff note in the lane's workspace. It should list what shipped, what is open, and the next step. Post an owner-change comment on every in-flight card in that lane during the same turn.
10. Before you report a card as pending or running, read it from the board in that turn. A status from memory is not evidence.
11. Before ending any turn that changed the board, check that every card you created or changed has a parent link, a current status, and a comment that explains any block or supersede.

### Pre-create checklist (in addition to the steps above)
- Search the target project for the term the task names, such as a product handle, a route, or a configuration key. Zero matches on a named item means the request is wrong or the item is missing. Stop and report it before you dispatch.
- Confirm that each credential the worker needs is present for that worker before it starts. A worker that discovers a missing credential mid-task loses its turn.
- Check whether a tool already exists in the repository for the query. Point the worker at it instead of asking it to build a new probe.
- Pass only skill names that resolve on the worker's profile. An unresolved skill name is silently ignored.
- Inline the directives into the spec file, and reference that file from the card body.

### Board integrity audit
Run a periodic audit of the whole board, and treat each open card as a claim to check. Each open card must be real, routed to an owner, and still needed.
- A card whose outcome has already happened, or whose pull request is closed, is overtaken by events. Archive it, or comment with its replacement.
- A card that is held or parked needs a valid reason, a named owner, and a date after which the hold is re-checked. A hold is not a way to silence an alert. A parked card counts as open debt until the audit confirms the hold still applies.
- Dependencies must be links on the board. A dependency written only in prose is invisible to the board's checks.
- Before you ask the operator about a hold, re-check its premise live. A hold such as "waiting for approval" can go stale while it waits.
- Read the audit's denominator before you trust a clean result. Compare the count of held and idle cards with what you expect. A zero count of high-severity findings is not a healthy board by itself.
- Ask the operator only from the session that owns that business. Each decision you hand over states the choice in plain language, the options, your recommendation, and the reason.

## Pitfalls
- **A dependency is a link, not a sentence.** A card that says "wait for the other card" in its body never starts on its own. Link the parent.
- **A hold is a condition, not a to-do item.** Express a wait as a blocked status with a named condition, not as a line in the body.
- **Triage parents do not promote children.** A child behind a triage parent stays waiting until the parent is resolved. Resolve or replace the parent first.
- **Check the pull request's base branch before you cut a fix.** A change merged to the wrong base has not reached the release branch. Create a follow-up card that ports the fix to each release branch that needs it.
- **Merged is not applied everywhere.** A merge to one branch does not reach a release branch that is built separately. Confirm the branch the work landed on.
- **A card with an open pull request cannot simply resume after a block.** Resuming it on the old head makes the reviewed code and the running code different. Split the work into a new card on the current head.
- **A reviewer's approval is not a merge.** Mark a draft pull request ready before you merge it, and merge only after the approval applies to the current head and the operator has given an explicit go-ahead to merge.
- **Do not work around a safety block on a push.** When a push is refused by a guard, report the refusal to the operator. Do not force the push or rebuild the branch to evade the guard.
- **One live writer per pull request.** Before dispatching a card that edits a file, check that no running card edits the same file. Two writers on one branch produce conflicts that look like failures.
- **Dedupe review follow-ups across sessions.** Before you open a fix card from a review, search for an existing fix card on the same finding.
- **A review that rejects a pull request that is already closed is out of date.** Comment on the old review, and do not cut rework for a closed pull request.
- **Rework cards carry the reviewer's findings.** A rework card that says "reuse earlier work" without the findings sends the worker back to the wrong place.
- **Low-severity findings on an approval still become a fix.** Create the fix card in the same turn. Logging a finding and moving on is how it gets lost.
- **An engine outage is a fact about the lane, not a reason to stop.** Re-route to a live lane when one exists, and report the re-route.
- **A worker saying its lane is dead is a claim.** Smoke-test the lane yourself before you re-route the card.
- **Never merge onto a red production backend.** When a migration fails, revert first and fix second. A revert on production needs the operator's explicit go-ahead, so report the failure and ask for it before you revert.
- **Two approved branches that touch the same files need one integration card.** Build and merge them together, not one after the other.
- **Check each merge commit's build, not the platform's clean status.** A clean merge status does not prove the build passes.
- **Decide what you can decide.** Do not hold work behind a question you can answer from the spec and the board.
- **A lesson becomes a skill edit.** A note kept only in memory is lost at the next session.
- **Same-shape churn by the third round is a design problem.** Stop adding fix cards for the same defect family, and change the design.
- **Never call a card pending or running from memory.** Read it first.
- **A builder names its reviewer, and a reviewer cannot override the critic.** The approval chain stays separate from the implementation chain.
- **A sign-in-only probe is not a done criterion.** A worker card should prove the outcome, not that a login page loads.

## Verification
- A search for the card's outcome before creation returned no open duplicate, or the duplicate was commented on instead.
- Each child card shows its parent link, and each blocked card has a comment that names the blocker.
- A pull request's live state was read before any card depending on it was created or resumed.
- Each superseded card was archived after its children, and each archived card has a comment that names its replacement.
- Each owner change has a matching comment on each in-flight card and a handoff note.
- The board read at the end of the turn matches each status you reported.
