---
name: repo-backup
description: Use when backing up a git repository or worktree before risky work. Makes tarballs with checksums, runs a secret scan, pushes to a private backup remote and verifies each ref.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [backup, git, secrets-scan, github, reliability]
    category: devops
related_skills: [incident-forensics, repo-sanitization-publishing, repo-ssot-hygiene]
---

# Repo Backup

## Overview
A zero-data-loss snapshot of a repository and its worktrees, taken before anything riskier touches them. The pipeline writes full tarballs with checksums, scans for secrets, pushes every branch and tag to a private remote, verifies each ref, and reports in a fixed key-value shape. Uncommitted work is the part most at risk, so the tarball is the primary copy, not the remote.

## When to Use
- Before long-running work that leaves uncommitted changes in a repository or worktree with no remote.
- Before a delete, rotate or wipe operation on a local directory that holds the only copy of some work.
- When a brief asks for a backup with checksums, a secret scan and verified evidence.
- For a freeze across many checkouts, run this once per repository and combine the results.

## Features
- A full tarball of each working tree, including its `.git` directory.
- One checksum file beside the tarballs.
- A secret scan with triage rules by path and by key type.
- A private backup remote under its own name, so the origin is not touched.
- Per-ref verification that compares maps, not raw text.
- A report with a fixed field list.

## Benefits
- Uncommitted files and local-only branches survive a bad operation.
- A backup is proven, not assumed.
- Secret findings are reported without exposing any value.

## Procedure

1. **Inventory with counts.** For each tree, record the HEAD SHA, the branch, the number of uncommitted files (`git status --porcelain | wc -l`), and any dependency versions the brief asks for. Read versions from the lockfile or manifest, not from memory.

2. **Write the tarballs and checksums.** Create `~/Backups/<context>-<date>/`. For each tree, run `tar -czf <name>.tar.gz -C <parent> <name>`. Do not use `git archive`, because it drops uncommitted files. Then run `shasum -a 256 *.tar.gz > SHA256SUMS` in that directory before anything reports the backup as existing.

3. **Back up worktrees and their parents.** For a git worktree, back up the worktree directory and its parent repository. The worktree's `.git` is a pointer into the parent, which holds every object. Uncommitted worktree files exist only in the tarball, so say so in the report.

4. **Scan for secrets.** Run a secret scanner on each tree (for example `gitleaks detect --source <path> --no-git --report-path <report>`). Triage by path first: build output, dependency folders and generated manifests produce generic false positives. Then triage by key type. Publishable client keys are safe by design. Live server-side keys, private keys and JWT-shaped strings are real findings. Stop, do not push, and escalate.

5. **Create the backup repository as private.** Run `gh repo create <org>/<name> --private`. If it already exists, view it instead of recreating it, and confirm visibility with `gh repo view <org>/<name> --json visibility`. A public backup is a leak.

6. **Push to a second remote.** Add a remote with its own name (for example `github-backup`), then push all branches, then all tags. Never force-push a backup. If a ref already exists, compare its SHA instead of overwriting it.

7. **Verify each ref.** Parse the local ref list and the remote ref list into maps of ref to SHA, then compare per ref. Do not diff the two raw listings line by line: their separators differ, so a clean push looks like missing rows. Proceed only when no ref is missing or mismatched.

8. **Report.** Write the brief's fields as KEY=value lines in a result file, and reply with the same block. Name steps that other people own, such as an off-host copy or a restore test, as pending. Never fold them into done.

## Pitfalls
- **Never print a secret value.** Report findings as a count, a file path, and the key type or prefix. Apply this to the report, the result file and chat.
- **GitHub rejects ref path components that begin with a dot.** When you turn checkout paths into ref names, rename those components, for example `.config/x` to `dot.config__x`.
- **Very large repositories are rejected on a bulk push.** Push in chunks of about 100 refs.
- **Save uncommitted work without touching the user's index.** Build a temporary index file, write the working tree to a throwaway commit with `git commit-tree`, and push that commit under a clearly named `wip/` ref. Archive untracked files separately, and exclude environment files, dependency folders and build caches.
- **Squash merges make merged branches look unique.** Find local-only work by counting commits not reachable from any remote, after a fetch. Back up branches merged by name too, rather than trusting a patch-equivalence check.
- **A broken worktree is invisible to git.** When a worktree's pointer leads into a deleted repository, archive it as a tarball.
- **Do not call work stale, dead or shipped without a citation.** Cite the commit or pull request that proves each status. A status with no citation is unclear.
- **Define the terms before proposing a delete.** A branch is a working copy. Merged means the change is in the main branch. Shipped means the change is in the deployed build, which you check by ancestry against the deployed commit.
- **A pull request whose base branch was merged is not automatically obsolete.** Measure whether its files match the main branch before proposing that it be closed.

## Verification
- `shasum -a 256 -c SHA256SUMS` passes in the backup directory.
- A secret scan report exists for each tree, and no unresolved live-key finding remains.
- The backup repository reports private visibility.
- The ref comparison reports zero missing and zero mismatched refs.
- The result block lists the HEAD SHA, the uncommitted-file count and the push status for each repository.
