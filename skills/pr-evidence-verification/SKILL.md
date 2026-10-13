---
name: pr-evidence-verification
description: Use when verifying a pull request's head files. Checks hashes, sizes, existence and branch state without a clone, or runs a repository's acceptance script against a PR head read-only.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [pr, review, verification, read-only, evidence, hash, git]
    category: devops
related_skills: [adversarial-review, dispatch-proof, github-issue-to-pr]
---

# PR Evidence Verification (Read-Only Reviews)

## Overview
Review briefs often assert facts about a pull request's head: a file's SHA-256, its line or byte count, whether it exists, or how the branches are laid out. Check every such claim against the actual head ref, not against the pull request description. Stay read-only while doing it: no approval, no merge, no push and no edits to product files. The one permitted write is a result comment that the brief explicitly requests.

## When to Use
- A review brief asserts facts about the head files of a pull request (hashes, sizes, existence, branch state).
- You must run the repository's own acceptance or hash script against a pull request head that you cannot push to and must not merge.
- The review result has hard constraints, such as a length cap or a required final line.

## Features
- A head-verification recipe that needs no clone: resolve the branch, the blob SHA, decode the blob, and hash it.
- A full-clone recipe for scripts that need a working tree, pinned to the head branch and deleted afterwards.
- Existence checks across every branch.
- Structural checks against the file's real schema.
- Pre-merge state checks for any later step that merges (see the section below).

## Benefits
- Claims are checked against the artifact, not against the description.
- Full hashes in the result let a downstream reviewer re-verify without recomputing.
- A failing script is recorded as evidence rather than hidden.

## Procedure

1. **Confirm the head branch first.** Run `gh api repos/OWNER/REPO/branches/BRANCH --jq '.name + " " + .commit.sha'`. A pull request body or a lagging head SHA can both be wrong.

2. **Resolve the file at the head.** Run `gh api "repos/OWNER/REPO/contents/PATH/FILE.md?ref=BRANCH" --jq '.sha + " " + (.size|tostring)'` to get the blob SHA and size.

3. **Fetch and hash locally.** Run `gh api repos/OWNER/REPO/git/blobs/BLOB_SHA --jq '.content' | base64 -d > <scratch>/file.md`, then `shasum -a 256` and `wc -l` on that file.

4. **Compare and report.** Compare the computed hash with the claimed prefix. Report the full hash either way.

5. **Check existence across all branches.** Run `git ls-remote origin` first, then list each branch's tree recursively with `gh api repos/OWNER/REPO/git/trees/<sha>?recursive=1 --jq '.tree[].path'`, or use a shallow clone.

6. **Run repository scripts only in a throwaway clone.** Shallow-clone the head branch into a scratch directory, run the acceptance script there, then remove the clone. Change to a stable directory first, in the same command (see Pitfalls).

7. **Post a result comment only when the brief asks for one.** Post it as the review identity the brief names, confirm the comment URL came back, and record it. Everything else stays read-only.

8. **Check the result's constraints.** If the brief caps the result's length or requires a specific final line, check the line count with `wc -l` and rewrite tighter rather than trimming the truth.

### Before Any Merge
This skill does not merge, but a later step may. Apply these checks in that step:
- **Pin the reviewed head SHA.** A sign-off is bound to the commit the reviewer read. If the head moves after sign-off, the sign-off no longer applies. Re-review the new head, or refuse the merge.
- **Re-read the pull request state immediately before merging.** Confirm the state is open, the draft flag is false, and the head SHA equals the reviewed SHA. Re-read again right after the merge attempt. A pull request that is already merged is a success only when the merged state and the merge commit are confirmed.
- **Refresh the branch before merging.** If the base has moved, update or rebase the branch first, then re-check the head SHA. The rebase changes the head, and the sign-off applies only to the new head after a fresh review.
- **Do not disable review requirements or use admin overrides to get a merge through.** If a gate blocks the merge, stop and report which gate blocked it and why.
- **Check existing reviews before approving.** A parallel reviewer's approval makes a duplicate review; list reviews first.

## Pitfalls
- **Never delete the directory your shell is in.** A persistent shell keeps its working directory between calls. Removing a temporary clone while the shell sits inside it breaks every later call. Change to a stable directory in the same command before the removal.
- **A shallow clone checks out the default branch.** Verify the HEAD SHA and branch name inside the clone before trusting any hash computed there. Fetch the head branch explicitly if it is missing.
- **A prefix match is not verification.** Compute the full hash and compare the prefix. Report the full hash so a downstream reviewer can verify without recomputing.
- **A script that exits non-zero by design is evidence.** Some acceptance scripts exit with a code that signals a known missing prerequisite. Capture the exit code and the error line. When the brief predicts that outcome, the match is the finding.
- **Placeholder literals are findings.** A config value that still holds scaffold text means the step never ran upstream. Report that instead of treating the field as populated.
- **Recompute every blob row in a pull request body at the head.** Blob tables go stale when the author commits after drafting the body. A stale table is a metadata finding even when every file is correct.
- **A 40-character hex reference is often a blob SHA, not a commit.** Resolve it with the contents API and compare two claimed versions by fetching each from its own branch. A commits lookup on a blob returns 404, which is the signal that it is a blob.
- **Check the head SHA before reusing staged inputs.** If the head has moved since an earlier attempt, archive the staged inputs under a name that carries the old SHA. Never delete them.
- **Write validators against the file's real schema.** Dump the actual key paths first, then assert against them. Checkers written from a brief's description of the schema fail on correct files.
- **Strip scratch folders before delivery.** Harness scratch directories left in a working folder are residue, not evidence.

## Verification
- The full hash in the result matches a local hash of the fetched blob.
- The head branch and SHA were confirmed before any computed hash was trusted.
- Existence checks cover every branch named in the brief.
- Before any merge, the pull request state, draft flag and head SHA were re-read immediately beforehand and confirmed afterwards.
