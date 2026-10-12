---
name: docs-pr-batch-landing
description: Use when several open, reviewed, docs-only pull requests should land together as one draft pull request. Covers snapshotting live state, skip rules, per-PR commits copied from each source head, gates before push, and a verification block for the description.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [github, pull-requests, docs, batch, git, review, verification]
    category: devops
related_skills: [pr-evidence-verification, github-issue-to-pr]
---

# Docs-Only PR Batch Landing

## Overview
Many small documentation pull requests are easier to review as one. This procedure copies the files from several reviewed, docs-only pull requests into one new draft pull request, one commit per source. The file contents are copied exactly, with no edits. The source pull requests are left alone. A reviewer then merges the one batch pull request, and the source pull requests close through their own state, not through any action in this procedure.

## When to Use
- Several open documentation pull requests have passed review, and each touches only documentation paths.
- A reviewer asks for one pull request that carries them together.

Do not use this for code, for configuration, or for any source pull request that has not passed review.

## Features
- A scratch worktree, so the working checkout is not touched.
- A live snapshot of each source pull request's state, base, head, and file list, checked against the fetched head commit.
- Skip rules for pull requests that are closed, touch paths outside the documentation folder, collide with main, or collide with another open pull request.
- One commit per landed source, with asserts that stop the run on a bad source.
- Gates on the changed paths before the push, and a verification block that compares every file's blob with its source head.

## Benefits
- A bad source stops the run instead of landing partially.
- Every landed file's content is proven identical to its source.
- Skipped pull requests are listed with the reason, so nothing is dropped silently.
- The batch pull request is opened as a draft, so a reviewer makes the final call.

## Procedure
1. **Work in a scratch worktree.** Fetch the main branch and the source pull request heads, then create a new branch from main in a scratch folder:
   ```zsh
   git fetch origin main '+refs/pull/*/head:refs/remotes/origin/pr/*'
   git worktree add -b <batch-branch> <scratch-dir>/wt origin/main
   ```
   If an HTTPS fetch or push fails on authentication, run that one command with the credential helper set to the code host's CLI, for example `-c credential.helper= -c 'credential.helper=!gh auth git-credential'`. Do not change the stored configuration, and do not print a token.

2. **Snapshot the live state once.** For each source pull request, read its state, draft flag, base branch, head commit, and file list. Also list the open pull requests for collision checks. Assert that each source's head commit equals the fetched `refs/remotes/origin/pr/<n>` commit.

3. **Decide skip or land, in number order.** Skip a pull request, and record the reason, if any of these hold:
   - It is not open.
   - Any of its paths is outside the documentation folder.
   - Any of its paths already exists on main. For a path already on main, compare the blobs. Identical content means it landed earlier. Different content means it needs a rebase.
   - Another open pull request changes any of its paths.

4. **Land each pull request as one commit.** For each landed pull request, check out its files from its head commit, and commit them with a message that names the pull request. Run this in a loop that asserts the pull request is open, the head matches, the paths are under the documentation folder, and none of them is on main. A failed assert stops the run.
   ```zsh
   git checkout <head-commit> -- <paths>
   git commit -m "docs: land #<n>"
   ```

5. **Gate the changes before the push.** Changed files outside the documentation folder must number zero. The total number of changed files must equal the sum of the per-pull-request path counts.

6. **Build the verification block.** For each pull request and each of its paths, compare the blob at the batch branch's `HEAD` with the blob at the source head. Print one line per pull request, showing its head, its path count, its blob count, and `MATCH`, plus a total. Paste the block verbatim into the batch pull request description.

7. **Open the batch pull request as a draft.** Push the branch, then create the draft against main. The title states the number of pull requests actually landed, not the number considered:
   ```zsh
   gh pr create --draft --base main --title "docs: land <k> reviewed docs PRs" --body-file <body-file>
   ```

8. **Write the description.** Include a note that the build was skipped for a documentation-only diff, the list of landed pull requests with their file counts and heads, the skipped pull requests with their reasons, any flags for the reviewer, and the verification block. Re-read the new pull request's state, and confirm it is a draft against main.

## Pitfalls
- **Ignoring the draft rule.** A run's instructions can ask for a ready-for-review pull request. Open it as a draft unless the run's rules say otherwise, and say so in the description.
- **A source pull request based on another branch.** Its files pass every path rule, but landing them on main changes what the pull request means. Include it only if the rules allow it, and flag it with the exact commit to drop.
- **No merge base.** A merge-base lookup can fail for such a pull request, and a diff against the base then errors. Use the live file list as the source of paths. Cross-check with a diff against the merge base only where one exists.
- **A partial landing.** A pull request that modifies files main already has can be a skip even when its other files are new. Do not land part of it.
- **Flooding the output with missing-path errors.** A check that a path exists on main prints an error for each missing path. Send standard error to `/dev/null` in those checks.
- **Padding the final report.** Report the skipped list with reasons, the flags, and the verification totals. Do not list every file.
- **A missing graph or index.** If a code-intelligence index is unavailable for the repository, say so in the report, and do not skip the path rules.

## Verification
- The batch pull request is a draft against main.
- Every landed file's blob matches its source head, as shown in the verification block.
- No changed file lies outside the documentation folder.
- Every skipped pull request has a reason in the description.
- The source pull requests are unchanged. This procedure did not merge, approve, close, or comment on them.
