---
name: git-remote-hygiene
description: Use when pushing from a repository or when a remote URL may carry a token. Covers redacted remote checks, credential helpers, explicit push refspecs, and token rotation.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [git, remotes, credentials, tokens, push-safety, hygiene]
    category: security
related_skills: [github-repo-preflight-scan, chat-safe-secret-staging, bitwarden-secrets-manager-hermes]
---

# Git Remote Hygiene

## Overview
A git remote can silently carry a personal access token in its URL, and a global configuration rule can re-insert that token even after the remote is cleaned. A push can also go to a branch you did not intend, because a worktree's upstream points at the main branch. This skill sets a short checklist that runs before every push: scan the remotes and the global configuration with redacted output, confirm where the push will land, keep credentials in a helper rather than in URLs, and treat any token that was ever embedded as burned.

## When to Use
- Before any `git push` from a repository you maintain, especially one with several remotes.
- When a remote was set up from a copied URL, or by a script that embedded a token.
- After a worktree was created from a remote branch, and you are about to publish it.

## Features
- A redacted scan of repository remotes for embedded user information and token-shaped strings.
- A check of the global git configuration for URL rewrite rules that re-inject credentials.
- A check of the upstream branch, so a push cannot land on the wrong branch.
- A scrub procedure that rewrites remotes to clean URLs and verifies access without a prompt.
- A rule that exposed tokens are rotated, not merely removed.

## Benefits
- Tokens are not printed to chat, logs, or shared notes while the scan runs.
- A push lands only where you meant it to.
- A cleaned remote does not quietly regain its token from a global rule.
- Credentials stay in the system's credential store, where they can be rotated.

## Procedure
1. Scan the repository's remotes with redacted output. Look for user information before the host name, and for token-shaped strings. Print only a DIRTY or CLEAN result and the remotes with their secret parts replaced:
   ```zsh
   git remote -v | sed -E 's#(https?://)[^@/]*@#\1***@#'
   ```
   Report DIRTY or CLEAN. Never print the original line.
2. Scan the global configuration for rewrite rules that insert credentials into a host's URL. A rule that maps a short form to a URL with a token in it re-adds the token even after you change the remote:
   ```zsh
   git config --global --get-regexp '^url\.'
   ```
   Check the result for a token-shaped string, and report PRESENT or NONE without printing the rule.
3. Prefer authentication through the system's credential helper, or the platform's CLI credential helper. Do not keep personal access tokens in URLs.
4. Before you push, confirm the upstream of the current branch:
   ```zsh
   git rev-parse --abbrev-ref '@{upstream}'
   ```
   A worktree created from a remote main branch can set its upstream to that main branch. A plain `git push -u origin HEAD` then publishes to main. If the upstream is the main branch, push with an explicit target branch:
   ```zsh
   git push -u origin HEAD:<branch-name>
   ```
5. Push only to the intended remote. If a project has a backup remote, use the backup remote only when the project's rules say so.
6. If a token was ever embedded in a remote URL or in the global configuration, tell the operator to rotate it. Removing it from the file does not make it safe, because the copy in history and in any backup is still readable.

### Scrub Recipe
Rewrite each affected remote to its clean URL. Then, after the operator approves the exact rule key, remove the global rewrite rule that carries a token. Use the key from the scan, and do not type the token into the command:
```zsh
git remote set-url <remote-name> https://<host>/<owner>/<repo>.git
git config --global --unset-all '<exact-rule-key-from-the-scan>'
```
Then verify access without an interactive prompt. A prompt-disabled read should succeed without asking for a password:
```zsh
GIT_TERMINAL_PROMPT=0 git ls-remote <remote-name> HEAD
git remote -v | sed -E 's#(https?://)[^@/]*@#\1***@#'
```
If the read asks for credentials, the credential helper is not set up. Set it up, then repeat the check.

## Pitfalls
- **A clean remote can be re-dirtied by a global rule.** Check the global configuration after every scrub.
- **Printing a remote URL to show its state.** Redact it first, every time.
- **Assuming a deleted token is a revoked token.** Rotate it.
- **A worktree's upstream can point at the main branch.** Check the upstream before any publish, and use an explicit target.
- **Pushing to a backup remote by habit.** Use the remote the project's rules name.
- **A credential in a shell history file.** Clear it from the history, then rotate the token.

## Verification
- The scan reports CLEAN for the repository remotes and for the global configuration, with the redacted remote list shown.
- The upstream of the branch you are about to publish is the branch you intend.
- A prompt-disabled read of each remote succeeds without a password prompt.
- Any token that was embedded is listed for rotation, and the operator has been told.
