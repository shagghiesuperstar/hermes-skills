---
name: github-issue-to-pr
description: Use when carrying a GitHub issue to a verified pull request with honest CI reporting. Covers reading the full thread, sweeping for duplicate work, validating the premise against design intent, fixing the bug class, proving the regression test, and reporting CI from live evidence.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [github, issues, coding, pull-requests, ci, regression-tests]
    category: devops
related_skills: [pr-evidence-verification, review-then-ship, docs-pr-batch-landing]
---

# GitHub Issue to Pull Request

## Overview
An issue is a snapshot from the day it was filed, and the work it describes may already be partly done, duplicated, or intentional. This skill turns an issue into one tested pull request in a fixed order: read the live thread, check for existing work, prove the problem in current code, define the acceptance criteria, fix the whole bug class, prove the regression test catches the bug, and then report CI from live results only. The discipline matters more than the mechanics. The mechanics belong to the GitHub CLI and the repository's own tools.

## When to Use
- "Fix issue N and open a pull request."
- "Implement this feature request from the tracker."
- "Take this bug from issue to passing CI."

Do not use this for reviewing an existing pull request, or for answering a code question that asks for no change.

## Features
- A read of the issue body and every comment, plus the repository's contribution instructions.
- A duplicate sweep of pull requests and recent commits, using the issue number and at least two keyword variants.
- A premise check that reproduces the problem on the default branch and checks the history for intentional design.
- An acceptance contract that maps each criterion to a test or an explicit check.
- A sibling-site sweep, so the same bug shape is fixed everywhere in one change.
- A sabotage run that proves the regression test fails without the fix.
- A CI report built from live check results.

## Benefits
- Work is not duplicated, and credit is not lost to an earlier fix.
- A feature gap that was left on purpose is not "fixed" against the design.
- A partial fix that leaves known siblings broken is avoided.
- A passing test is shown to fail on the old code, so it proves something.
- The issue thread ends with a link to the change and an honest status.

## Procedure
### 1. Read the live issue, body and full thread
Run `gh issue view <N> --comments`. The body is a snapshot from filing time. The newest comments carry the live state: a partial fix that already merged, a new root-cause analysis, a maintainer decision, or a question addressed to you. Read the repository's contribution instructions as well. You are done when you know the behavior being requested, the non-goals, and any open question in the thread.

### 2. Sweep for existing and duplicate work
Before you write anything, search for pull requests that mention the issue, in every state:
```zsh
gh pr list --search "#<N>" --state all
gh pr list --search "<subsystem> <symptom>" --state open
```
Run at least two keyword or synonym searches for the symptom. Popular issues attract several independent fixes. Also check whether a recent commit already fixed it:
```zsh
git log --oneline -20 -- <relevant-files>
```
You are done when you know every open pull request and recent commit that touches this issue, or you know there are none.

### 3. Validate the premise against current code and design intent
Reproduce the bug, or show the missing behavior, on the current default branch with a failing test or fixture. Trace the reported path through the code. Then ask a second question: is the behavior deliberate? Search the history of the code the issue wants changed:
```zsh
git log -p -S "<symbol>" -- <file>
```
Read the commit that introduced the restriction. A missing link or a restriction is often the feature. Challenge an issue's prose when it is stale or wrong, instead of implementing it as written. You are done when the root cause or the gap is shown in current code, and the change does not work against an intentional design.

### 4. Define acceptance and risk
List the acceptance criteria, the interfaces, any data or state changes, compatibility, security and privacy effects, the rollout, and the rollback. Map each criterion to a test or to an explicit check. You are done when the review has a finite contract to check against.

### 5. Implement the smallest complete change, and fix the class
Work on an isolated branch or worktree. Write the regression test first, then the fix. Once the fix works, search for the same bug shape at the sibling call sites, and fix the whole class in this change. A fix that leaves known siblings broken is worse than no fix, because it looks finished. Every changed line must trace back to the issue. Leave out drive-by cleanup.

You are done when the targeted tests pass, the original failure no longer reproduces, and each sibling site is either fixed or explicitly ruled out.

### 6. Prove the regression test bites
Temporarily restore the old behavior of the function under test, run the new test, and confirm it fails. Then restore the fix and confirm it passes. A regression test that passes with and without the fix proves nothing. You are done when the test demonstrably fails on the pre-fix code.

### 7. Run the quality gates, then open the pull request
Run the repository's formatter, linter, type checker, and its main test command on the affected areas. Review the diff once, with a fresh read. Then push and open the pull request right away. The pull request starts the CI run, and CI is the slowest step, so do not hold finished work.

Use a conventional branch name and commit message. The pull request body links the issue, and it covers the problem, the approach, the tests, the risk, and the exclusions. Read the pull request back and check its head commit, its base branch, its title, and its file list. You are done when the pull request exists with the intended diff and CI is running.

If the repository needs a specific account for pushes, select it for each command, for example with `GH_TOKEN="$(gh auth token --user <account>)" gh ...`. A "repository not found" error on a repository you know exists usually means the wrong stored account is active. Check that before you conclude the repository is missing.

### 8. Follow CI honestly and close the loop
Read the live checks with `gh pr checks <N>`, and the failure logs with `gh run view <run-id> --log-failed`. Separate the failures your diff caused from failures that were already on the default branch or are caused by infrastructure. When you are unsure, reproduce the failure on the default branch. Rerun a job once only when the failure looks like an infrastructure flake.

Do not say "green", "merged", or "released" without live evidence of that exact state. When the pull request lands, comment on the issue with the link and one line that explains the resolution, so the reporter can trace it. You are done when the CI state, the remaining blockers, and the issue thread all match reality.

## Pitfalls
- **Coding before reading the thread, the duplicate pull requests, and the current code.** Each of these can change the plan.
- **"Fixing" behavior the original commit shows was intended.** Read the history before the change.
- **Fixing one call site while its siblings keep the bug.** Search for the same shape and fix the class.
- **A regression test that also passes without the fix.** Run the sabotage check.
- **A pull request with untested changes or unrelated formatting.** Run the gates, and keep the diff to the issue.
- **Treating an open pull request as a delivered issue.** Delivery means the change is merged and the issue is updated.
- **Pairing UI text and structured data by hand.** When a visible element must match structured data, such as a JSON-LD block or a feed, derive both from one shared function.

## Verification
- The full issue thread was read, and the newest comments are reflected in the plan.
- The duplicate-pull-request sweep was run with the issue number and at least two keyword variants.
- The problem was reproduced on current code, and the history was checked for intentional design.
- The regression test fails on the pre-fix code and passes with the fix.
- Each sibling call site is fixed or ruled out in the description.
- Every changed line traces to the issue.
- The CI state in any report comes from live check results, and the issue has a comment with the pull request link.

## Attribution
- Adapted from a GitHub issue-to-pull-request skill by Ben Barclay (benbarclay).
