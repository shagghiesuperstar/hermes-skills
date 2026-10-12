---
name: read-only-discovery
description: Use when assembling facts from files, git history or running processes without changing the trees under study. Search in a fixed order, record metadata for every hit, mark what could not be proven as unknown, and keep secrets out of the report.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [discovery, evidence, git-ledger, secrets, read-only, audit]
    category: agent-discipline
related_skills: [independent-static-review, source-grounded-investigation, hermes-profiles, agent-honesty]
---

# Read-Only Discovery

## Overview
A discovery packet collects facts for another reviewer or for an operator who will decide what to do next. The packet must not change the files, repositories or processes it studies. This skill sets the order for finding named files, the metadata to record for each hit, how to read git history without writing to it, how to report secret-shaped text without leaking it, and how to label each fact as verified or unknown.

## When to Use
- Locating named documents, configuration files or notes across a home directory or a set of checkouts.
- Building a git ledger: which branches, commits or checkouts exist, and which are not on a remote.
- Checking which file a running process actually loads.
- Preparing a fact sheet for a review, where the reviewer must not be misled by a copy.
- Running a draft-only pass by a bounded worker that may read sources and write one deliverable.

## Features
- A fixed search order for named files, with exact-basename matching after a fast index search.
- A per-file metadata record: absolute path, size, modification time, hash, first line, and git status.
- A git ledger built only from read commands.
- A secret-report format of path, line and pattern, never the matched value.
- A `[VERIFIED]` and `[UNKNOWN]` tag for every fact, with the probe list behind each negative.

## Benefits
- Reviewers can reproduce every fact from the probes listed beside it.
- A negative result is either backed by a probe list or marked unknown.
- The studied trees are unchanged when the packet is delivered.

## Procedure
### 1. Establish the write allowlist
Before any search, write down what may be written: normally one output folder, and at most one new scratch location if the task names it. Nothing else changes. No edits to configuration, skills, instructions or live services, and no merge, push, fetch, prune or restart.

### 2. Search named files in this order
Record which step found each hit.
1. The expected path, if the task gives one.
2. A fast index search for the basename. Treat the result as a substring match, and keep only exact basename matches.
3. `find` or `fd` for the exact basename, limited to the stated depth. Prune `node_modules`, `.git`, and cache folders.
4. For an unknown location, list files by name, then search content only to find the named file, not to copy every mention.

If several files share a basename, report all of them. When staging copies, rename on collision with the parent folder name, then the grandparent if the collision remains.

Index search skips many hidden folders. An empty index result is normal for a hidden path, so still run `find`.

Do not copy a whole tree because a phrase matched two files in it. Copy only the matching files.

### 3. Record metadata for each match
For each match, record: absolute path, size in bytes, modification time in local time, SHA-256, first non-empty line, the search step that found it, and git status.

For git status, resolve the git directory from the file's parent folder with `rev-parse --absolute-git-dir` and `--git-common-dir`. Do not resolve a relative `.git` path against the current working directory. That can point at an unrelated home-level repository.

### 4. Build the git ledger with read commands only
Allowed: `status`, `log`, `rev-parse`, `show-ref`, `cat-file -t`, `merge-tree` when both commits exist locally, and `bundle create` into the output folder.

Not allowed under a read-only stop: `fetch`, `pull`, `checkout`, `rebase`, `worktree add`, `reset`. A worktree add writes to the repository's metadata folder. A fetch writes to the object store.

If a commit you need is not in the local object store, report it as unknown along with the command that would fetch it. Do not fetch to get it.

Settle commit-count claims by running the count command in the repository, and check ancestry with `merge-base --is-ancestor`. A commit later on a branch is not an ancestor of an earlier tag. Do not assume a tag's position from a number written in a document.

Classify a folder as a real repository by checking whether `.git` is a directory, a file (a worktree), or absent. A glob of sibling folders can mix real repositories, extra clones and plain folders.

### 5. Fleet-wide checkout inventory
When the question is which work exists only on one machine:
- Walk the home folder to a bounded depth. Prune build output, dependency folders, caches and media folders.
- At each folder whose listing contains `.git`, record the common git directory, the current branch, the count of uncommitted paths, and the origin URL.
- Treat a `.git` file as a worktree. If its common directory no longer exists, the worktree is broken.
- For each local branch with a remote, compare it with the default branch using `git cherry`. A branch with commits not on the default branch and no matching pull request needs a push.
- Match branches to pull requests by name. `git cherry` does not recognize squash-merged work, so it can report a merged branch as unpushed.
- Report uncommitted work by count, and name the largest changed file so the operator can tell real work from noise.
- List checkouts with no origin remote separately. Their commits have no remote copy.

### 6. Propose changes as diffs, never as applied edits
When the task asks for a text change to a document, write a unified diff and leave the original alone:
- Change only the sentences named in the task.
- Insert an added pointer next to the changed sentence, not at the top of the file, so the diff shows only the real edit.
- Record the source path, the SHA-256 before the edit, and the diff path.
- Re-hash the live file after writing the diff. It must still match the recorded hash.

### 7. Verify which file a running process loads
1. Find the process by its port: a listening-socket listing, then the process's start time and command line.
2. Confirm the load rule from the software's own documentation, and quote the line.
3. Read only the active file, not a backup, an installed template or a copy with the same name elsewhere.
4. Check the file's modification time and birth time. A birth time equal to the modification time means the file was created, not edited.
5. Use a script with a parser for structured files, instead of a text search. A text search can miss a key that a parser finds.

### 8. Report secrets without their values
A secret-shaped match is reported as `path:line:pattern` only. Never print the matched text, because the printed line is the leak the search was meant to flag. Stage copies only when the task orders it, and redact in a separate sanitized copy, never in the source.

### 9. Tag every fact
Each fact is `[VERIFIED]` with its probe, or `[UNKNOWN]` with the reason. A negative result is `[VERIFIED]` only when the probe list is shown beside it. Without the probe list, a "not found" is `[UNKNOWN]`.

### 10. Draft-only passes by a bounded worker
When a bounded worker has a token or call budget:
- Count every read, search and fetch against the total budget, not per tool.
- Write one deliverable at the end. Do not rewrite it in the same run.
- Put a scope header at the top of the deliverable: job, author, scope, output, and `Status: DRAFTS ONLY`, with the retrieval date on each cited source.
- A public source establishes a rule. It does not establish the operator's live configuration. Say so in the draft, and mark the operator's state unknown.
- A preview or test-environment result is a probe, not a production sign-off.

## Pitfalls
- **Index-search false positives.** Substring matches and skipped hidden folders make both false hits and false empties the default. Confirm with an exact-basename `find`.
- **Relative git paths.** A relative `.git` resolved from the wrong folder reports a home-level repository that does not own the files.
- **Fetching to answer a question.** A fetch writes to the object store and breaks the read-only stop. Report the gap as unknown.
- **Merged counts.** Adding a tag range and a later commit range into one count inverts ancestry. Run each count separately.
- **Top-of-file insertions.** A pointer inserted at the top of a document makes every line look changed.
- **Printed secrets.** Reporting the matched line repeats the secret into the packet.
- **Negatives without probes.** Downstream readers treat "not found" as authoritative. Without the probe list it must be unknown.
- **Reviewer lacks context.** A digest that assumes the reader saw the conversation fails. Write each rule so it stands alone.
- **Code-only audits of deployed pages.** For a claim about what a live page shows, fetch the page. A code read describes intent, not what visitors receive.

## Verification
- The write allowlist was stated before the first probe, and no file outside it changed.
- Every hit has its metadata record and the search step that found it.
- Every git statement comes from a read command, and the listed commands are the ones the packet relies on.
- No secret value appears anywhere in the packet, only path, line and pattern.
- Each fact is tagged verified with its probe, or unknown with its reason.
- The studied trees re-hash to the values recorded at the start.
