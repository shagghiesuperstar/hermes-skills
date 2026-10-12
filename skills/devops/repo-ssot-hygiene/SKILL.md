---
name: repo-ssot-hygiene
description: Use when repository docs or remote git state mislead the agents and teammates who rely on them. Keeps one current-truth document accurate and reconciles remote state with local history.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [documentation, onboarding, single-authority, git, reconciliation]
    category: devops
related_skills: [repo-backup, github-issue-to-pr, prod-deploy-verification]
---

# Repo Single-Authority Hygiene

## Overview
Autonomous agents build their picture of a repository from whatever it offers: the description, the README, and any document that looks authoritative. When those are stale, an agent can verify the wrong system and report findings that look rigorous but describe a retired environment. This skill has two parts. Part A keeps one current-truth document accurate for live facts. Part B reconciles what the remote holds with local history and with what the team's documents say.

## When to Use
- You onboard a new agent or teammate to a repository.
- An agent reports findings that trace back to a stale host, a deleted project or a superseded architecture.
- Remote git state, local commits and planning documents disagree, or a reviewer cannot tell whether an artifact was committed.

## Features
- One short current-truth document with the live hosts, a retired-host list and a verification recipe.
- Warning banners on superseded documents, and a pointer at the top of the README.
- A corrected repository description and homepage.
- Remote-state reconciliation: fetch, compare, check branch state and push correctly.
- A check that a file was updated, not created.

## Benefits
- Agents verify live facts instead of trusting a description.
- A 404 on a retired host is recorded as expected rather than as an outage.
- Remote and local history can be shown to match.

## Procedure

### Part A: the current-truth document
1. Create one short, dated file (for example `docs/CURRENT-TRUTH.md`) and state that it supersedes every other document for live-environment facts.
2. Put the live URLs in a table. List only the real ones.
3. Add a retired list. Name each retired host and say why it fails, so an agent that receives a 404 reports it as expected.
4. Describe the stack in one paragraph.
5. Add a verification recipe: curl probes with the expected status codes, so agents verify rather than trust.
6. State a trust order: live systems first, then this file, then everything else as historical record.
7. Mark each superseded document with a warning banner that names its replacement and the date. Keep it, because it is audit history.
8. Put a pointer at the top of the README that sends agents to the current-truth file first.
9. Update the repository description and homepage with `gh repo edit --description ... --homepage ...`. Name the live host and disclaim the retired one. The description is the first thing a connected agent reads, and the most often forgotten.
10. If a document has become harmful and the owner rules that it must go, delete it in a single-file change that touches no other path. Prove the deletion with a direct request for the file's path on the default branch, which should return 404. Do not rely on the merge command's exit code.

### Part B: reconciling remote git state
1. Fetch with `git fetch origin`, then compare `git log --oneline origin/<branch> -10` with what the team's documents or the requester expect.
2. Compare local with remote. Commits listed by `git log --oneline origin/<branch>..HEAD` exist locally but not on the remote.
3. Check branch state. `git branch -a --contains <sha>` shows where a commit lives. Check for a detached HEAD left by a rebase.
4. Push what is missing with a normal push first. Use `--force-with-lease` only on your own branch, against the exact commit you expect. Never force-push the default branch.
5. Verify artifacts. `git show --stat <sha>` lists the changed files, and `git log --follow -- <file>` shows a file's history.
6. To prove that a pre-existing file was updated rather than created, read the commit's diff for that file (`git diff <old>..<new> -- <file>`), not only the list of changed files.

### Rules that keep it fixed
- Update the current-truth file in the same change that alters an environment: a project deleted, a domain repointed, a host renamed.
- Brief every agent to probe before reporting. An agent does not infer a host from a document or a description. A status code is the evidence.
- When you correct an agent that inferred the wrong target, reply with four things: the document was stale and is fixed at a named commit; the file to re-read; a short table of the corrected facts; and the probe-before-report rule. Keep its method, because only its target was wrong.
- Version chains rot silently. Keep one mutable file with a last-verified date for environment facts, and keep version chains only for audit history.
- Verify data facts before recommending a write. Partition records into correct, missing and incorrect, and never overwrite a manual correction with a stale audit.
- Before you escalate a blocker from a scheduled brief, read the cited task's current status, its dependencies and its evidence, then compare them with the live state. Name the real owner of the blocker.
- Check that a claimed single authority works as claimed. Trace its inputs, each consumer's evaluator, the behaviour for missing values and the cache boundaries. Equal file hashes do not prove equal decisions. Read the active call path, not a nearby script or an old comment.
- Keep the authority of each input clear. A product classification is a fact about an item. A destination policy is a rule about where the item may go. A shared authentication key proves trust only. Trace the actual endpoint and payload before claiming that one channel synchronizes policy.
- Consistency is not correctness. A centralized rule can be consistent and still wrong, so check the provenance of each rule separately. A proposed consolidation is a proposal until it is implemented and verified.

## Pitfalls
- **Trusting a repository description.** The description is written once and forgotten. Check it on every onboarding.
- **Deleting superseded documents.** Brand them. They are the record of what was true.
- **Reporting an outage for a retired host.** Read the retired list first.
- **Declaring a deletion done from the merge exit code.** Read the path on the default branch.
- **Assuming a file in a commit is new.** Check the diff.
- **Forcing a push to the default branch.** Read the remote log, and fix the cause.
- **A stale index lock or untracked files blocking a checkout.** Remove the lock only after confirming no git process is running. Move untracked files aside before a checkout, rather than forcing it.
- **Planning documents drift from the task queue.** If a task is marked open but its completion document exists, update the status at once and cite the document.
- **A source build from a pinned commit needs a matching artifact.** Check the release assets for your platform and architecture before attempting a build. If none match, a prebuilt artifact is the correct path.

## Verification
- The current-truth file's live URLs answer with the status codes it lists, and the retired hosts fail as it says.
- The README's first pointer and the repository description name the same live host.
- After a push, the remote SHA of the branch equals the expected local SHA.
- A file described as updated shows a non-empty diff against its earlier version.
