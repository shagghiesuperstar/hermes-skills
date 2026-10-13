---
name: work-order-execution
description: Use when a dispatched work order ends in a gated merge. Covers reading the order first, pinning the head SHA, merging only the reviewed commit, verifying the merge in the tree, and keeping the results ledger intact.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [work-orders, merge-gates, pinned-merge, results-ledger, verification]
    category: agent-orchestration
related_skills: [dispatch-proof, independent-static-review, adversarial-review, merge-reconciler, git-remote-hygiene]
---

# Work Order Execution: Gated Merges and the Results Ledger

## Overview
A work order (WO) is a brief that tells an agent to change code and get the change merged. The agent is not done when a merge command exits 0. It is done when the merged content is read back from the target branch and the result is recorded. This skill covers the gated-merge shape: read the whole order, stage read-only inputs, run a pre-review, collect approval, merge with the head commit pinned, verify the merge in the tree, and record the result in a ledger that other runs share. Review loops belong to the review skills, and claims about what a run did belong to `dispatch-proof`. This skill owns the order of the gates and the proof at the end.

## When to Use
- A work order names a pull request that must be reviewed, approved, and merged.
- The brief gives a PR number, a base and head SHA, a comment budget, and a deliverable path.
- A merge has to be proven after the fact, not inferred from a command's exit code.
- Several runs append to one shared results ledger.

Do not use this skill for a read-only verdict or for draft-only work. Use `independent-static-review` for a read-only verdict.

## Features
- Hard rules that run before any staging: read the order first, approve under a separate review identity, post one comment, pin the head, verify live, back up the ledger, and write one section per PR.
- A head-pin check: the SHA is confirmed before approval and again before merge, and the merge refuses a head that has moved.
- A two-gate rule that keeps a merge approval separate from a release approval.
- Short shapes for the other order types: draft-only verification, push-only, read-only deep review, local file edits, and operator packs.
- A closing checklist with receipts that a reviewer can re-check.

## Benefits
- A merge lands only on the commit that was reviewed.
- The tree read-back proves the change, so a metadata state change is not mistaken for a shipped fix.
- The ledger keeps one clean section per PR, so later runs can cite it without relying on memory.
- A merge approval is not mistaken for permission to release.
- Every claim in the report has a receipt that someone else can check.

## Procedure

### Hard rules
1. **Read the whole order first.** Note the PR number, base and head SHAs, comment budget, deliverable path and shape, and every gate: who pre-reviews, who approves, and under which identity. Staging before reading produces evidence for the wrong run.
2. **Approve under the review identity, never a personal token.** The repository's rules name the identity that owns review. Run `gh` from inside a clone, or pass `-R <owner>/<repo>` on every call. A bare `gh pr view` outside a repository fails on a working-directory check, not on auth.
3. **Post one comment per order.** If an earlier review asked for changes, put the corrections in one new comment. Do not reply in a thread, and do not post a second full review.
4. **Confirm the head SHA twice, and merge pinned.** Check it right before approval and again right before merge. Merge with `gh pr merge <n> --merge --match-head-commit <head-sha>`, so a head that moved after review makes the merge fail. On a mismatch, stop, review the new head from the start, and never merge blind.
5. **Verify the merge live before reporting done.** Re-fetch `gh pr view -R <owner>/<repo> <n> --json state,mergedAt,mergeCommit,headRefOid`. Then run `git fetch origin` and read the changed file with `git show origin/main:<path>`. The state field is metadata. Only the tree read proves the change landed.
6. **Back up the results ledger before touching it.** Copy it to a backup whose suffix names this run, then list both paths with `ls -l`. A corrupted ledger turns every later evidence claim into a memory.
7. **Write one deliverable section per PR in the ledger.** The section carries the verdict line, the reviewer's model, cost, turn count, and elapsed time (read from the reviewer's structured output, not recalled), the merge SHA, the URLs of the comment and the approval, and the done status line.
8. **Keep merge approval and release approval as two gates.** A merge into the branch that a release reads from is one gate. Shipping the change to users is a second gate, usually run by a release process on its own schedule. Merge when the operator gives merge approval. Then, before declaring done, create a separate follow-up task for the release. Name the exact change (one commit or one PR number), the branch the live build reads, the environment state, and any precondition. Mark the task as waiting for its own approval. Treating a merge approval as a release approval can push a half-checked change to customers.

### Gated-merge sequence
1. Re-read the brief, and mark each stage as complete when it passes.
2. Stage read-only inputs in the order's input folder: the diff, the PR body as JSON, the head SHA, and any candidate files. Delete empty scaffold folders only after the shell has left them.
3. Run the pre-review with the runner the brief names. Restrict its tools to what the brief allows, such as read-only tools with no shell and no network. Write the prompt to a file in the input folder instead of passing it inline. Keep stdout and stderr in separate files. Empty stdout is a failure. An empty stderr file is fine.
4. Parse the reviewer's structured output as JSON, after stripping any trailing sentinel token. Post the one comment with the verdict line and the evidence paths, and record its URL.
5. Check the head SHA, run the approval step, and confirm `reviewDecision` reads `APPROVED`. Check the head SHA again. Merge with `--match-head-commit`. Re-fetch and read the tree (Hard rule 5).
6. Write the deliverable file the brief names. Keep it short: verdict, reviewer identity, SHAs, and receipts. Append one ledger section, anchored on a line that appears only once in the ledger. Report done with the evidence.

### Other order shapes
- **Verify and draft PR (no merge).** The dispatcher pins the head. After adding the worktree, run `git rev-parse HEAD` first, and stop on a mismatch, since that means a stale pin. Run every test suite the CI workflow runs, and report one row per suite with its result line. Never report a roll-up. Write the PR body to a file and open the draft with `gh pr create --draft --body-file <file>`. Read back `url`, `headRefOid`, and `isDraft` with `gh pr view <n> -R <owner>/<repo> --json url,headRefOid,isDraft`, and quote `isDraft: true` from the API. If the remote tip is stale, the push needs `git push origin HEAD:refs/heads/<branch> --force-with-lease`. That is still a force push, so run it only when the order names it and the operator has given an explicit go-ahead for that push. Otherwise stop and report the stale tip. Never use `--force`.
- **Push only (no merge gate).** Back up any uncommitted work a previous worker left, read its diff, and continue it rather than restart. Do not copy environment files between worktrees. If a full build needs environment values the worktree lacks, run the type checker on the touched files plus the targeted tests, and report "full build unverified" as a limitation. Restore generated stamp files that build steps overwrite before staging. Close by grepping for the negation of each acceptance criterion.
- **Read-only deep review (verdict only).** Answer the operator's question set in the order asked, each answer with its file and line range. Confirm the head and base SHAs after `git fetch origin`, and report them, since a base can move. Compare type-check error counts between base and head with the same tooling and the same dependencies. Write the verdict file to the path the brief names, and check it with `ls -l`. Edit no file the brief does not name.
- **Local file edits (no git).** Derive the input format from the code that reads the file, not from a sample. Back up with a tag unique to the order, and back up the code and the data file it feeds under the same tag. Back up before an append too. If a required source is missing, run bounded searches, report NOT_FOUND with the exact commands, and do not invent the content. Derive database statements from the statements the owning code already runs.
- **Operator pack (a folder on disk, no PR).** Back up the destination folder before the first write, and verify the copy with `ls -l`. Pin one source field per metric, and write its name into every column header. Move a superseded run into a `_superseded-prior-run/` subfolder instead of deleting it, and name the change in the result.

## Pitfalls
- **Never anchor a patch on a repeated line.** Ledger blocks often repeat a status line such as `Status: DONE`. Anchor the insert on a line that appears once, such as the block's merge-SHA line, or on the file's tail. If a duplicate section lands, restore the backup and append once. Do not patch the patch.
- **Deleting your working directory breaks the shell.** After removing the folder you were in, every later call fails until you change directory. Leave the folder first, and delete last.
- **A zero exit code from an install is not an install.** `npm ci` can exit 0 with an empty `node_modules`. Count the modules with `ls node_modules | wc -l` before trusting it. If the next command reports a missing module, run `rm -rf node_modules && npm ci` in the foreground.
- **A scoped test filter is not a green build.** A narrow filter can skip sibling suites that pin sizes, byte outputs, or fixtures. When an artifact is referenced from several spec files, run the full unit command CI uses, and report its count separately.
- **Test counts alone hide the delta.** A "717 pass" line does not say whether the change added tests or fixed failures. Report the head count, the base count, and one line of difference.
- **Re-derive every number.** Provisional numbers in a brief are claims. Re-run each count with the same command on the same host. Only same-host, same-command deltas are comparable.
- **Compute sha256 yourself.** Print the default run's hash and the brief's expected hash side by side. Do not write "matches expected" without printing both. A drifted default output is a silent regression.
- **A 401 from an admin API usually means the auth header has the wrong shape.** Check the key's length, then try the header form the API documents before concluding the key is bad. Do not swap in a different API and call the result equivalent. Diff the two lists instead.
- **Square brackets in URLs need `-g`.** Curl treats brackets as glob ranges. Pass `-g` when a query uses bracket operators, and quote the URL.
- **Quote paths that contain parentheses.** A route-group folder such as `(main)` breaks an unquoted `cd`. Wrap the path in single quotes.
- **macOS `ls` lacks GNU options.** `ls --time-style=full-iso` fails on macOS. Use `stat -f "%Sm %z %N" <file>` to get the same timestamp and size.
- **`gh` outside a clone can hide errors.** Appending `|| echo 0` to a `gh pr view` call prints a fake zero when the command fails. Pass `-R`, and keep the real output.
- **A merge command's exit code is not a merge proof.** Exit 0 can mean the pinned head merged, or that the head moved and nothing merged. Keep the SHA chain visible in the report, and rely on the tree read-back.
- **Report discovered infrastructure, do not fix it.** When the order says to change only the named files, a second writer or a duplicate ledger found mid-run goes into a REPORTED section. Fold the fix into a follow-up order.
- **An order without a stop-conditions section should be refused.** Every order needs an explicit list of what the worker must not do. When you chain a fix order from a parent, copy that list verbatim. "Same as parent" is not enough.
- **A worker whose own rules forbid deploys stops at them.** If a task asks such a worker to deploy, it stops at its own rule and the release never moves. Do not send the deploy to another identity to get around that rule. Have the worker build and verify the change, then send the deploy to the operator's gate as its own request that names the exact commit.
- **A policy or allow-list change is not safe on review alone.** When the change swaps lists that live data tags depend on, the data keeps the old tags until a retag runs. Before merging, compute which records each side would wrongly allow or block, and name them in the merge approval. Run the data update with the merge only after the operator gives an explicit go-ahead for that update, named in the same approval.
- **Same-model review passes do not diversify.** If the reviewer and the critic run on one model, the diversity premise fails with no error. Report the model each pass used. When they match, lean on reproduced evidence such as failing test output, not on the verdicts.
- **Superseding a prior run is normal.** Move the earlier files into `_superseded-prior-run/`, and name in the result what changed (the field, threshold, or scope) and why.

## Verification
For a gated merge:
- [ ] The head SHA was quoted before approval and again before merge, and the merge used `--match-head-commit`.
- [ ] After the merge, `state` is MERGED, the merge commit is recorded, and the changed file reads back from the target branch.
- [ ] One comment URL and one approval URL are recorded, and the ledger gained exactly one new section.
- [ ] A ledger backup exists on disk, and a diff against it shows only the new section.
- [ ] If the release is a separate gate, a follow-up task exists, waits for its own approval, and the report says so.

For the other shapes:
- [ ] Each draft PR was read back with `isDraft: true`, and each test suite has its own row.
- [ ] Each deliverable file exists on disk, with its size and time from `ls -l`.
- [ ] Every count, hash, and SHA in the report was re-derived in this run, not copied from the brief.
- [ ] Every skipped check is named as a limitation, with its reason.
