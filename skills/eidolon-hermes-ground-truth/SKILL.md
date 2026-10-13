---
name: eidolon-hermes-ground-truth
description: Use when a Hermes issue needs an upstream check. Check it before you report, file or change anything. Covers upstream verdicts, drift and safe apply.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, upstream, ground-truth, audit, planning, verification]
    category: hermes-operations
related_skills: [hermes-upstream-contribution, hermes-architecture-reference]
---

# Hermes Ground-Truth Check Before Reporting

## Overview
A Hermes finding, plan or config proposal is only as good as the evidence behind it. Local clones fall behind, summary docs
paraphrase and drop details, and a remembered error message may already be fixed upstream. This skill is the check to
run first: compare the symptom with the upstream main branch and the canonical per-feature README, assign a verdict,
and make any change through the Hermes CLI with a log line.

## When to Use
- You are about to write a Hermes bug, finding or ticket.
- You are about to propose a config change, a provider fix or a Hermes update.
- You are drafting a plan that an operator has to approve.
- An error matches one you remember, and you do not know whether it is still present in the current release.

## Features
- Upstream lookup: local clone revision, commit search for the symptom's keywords, and upstream commits and pull
  requests.
- Drift check: how far the local install is behind upstream main, and which of those commits touch the affected area.
- Four verdicts: fixed upstream, still reproducible, local-only quirk, and unverifiable.
- Canonical-first reading order: per-feature README before any summary.
- Apply rule: change Hermes only through its CLI, never by editing config, auth or credential files, with an
  append-only action log.
- Checklist for operator-facing plans.

## Benefits
- Reports cite evidence instead of inference.
- An issue that is already fixed becomes an update recommendation, not a new bug.
- Plans use the real flag names, variable names and install steps.
- Every change has a log line that says what was done and why.

## Procedure
1. Write down the exact symptom: the error text, the Hermes version, and the provider or setting involved.

2. Find the local revision and how far it is behind upstream. Fetch first, then compare with the upstream main branch
   and not with the local branch alone:
   ```bash
   git -C <hermes-clone> rev-parse HEAD
   git -C <hermes-clone> fetch origin
   git -C <hermes-clone> rev-list --count HEAD..origin/main
   ```

3. Search upstream for the symptom's keywords and identifiers:
   ```bash
   git -C <hermes-clone> log origin/main --oneline --grep='<keyword>'
   git -C <hermes-clone> log origin/main --oneline -S '<code-identifier>'
   ```
   For pull requests and merge dates, query the upstream repository's public commit and pull-request listings.

4. Read the official reference for the feature. Open the per-feature README in the upstream repository, then the
   official Hermes docs for that feature. Use the docs site's llms index for discovery, and do not crawl the site.

5. Assign one verdict and act on it:
   - **Fixed upstream, not local:** recommend an update in the report. Do not file a bug.
   - **Still reproducible upstream:** file a bug with the reproduction, or record a workaround.
   - **Local-only quirk:** the install has drifted from its config or state. Propose the repair command the docs name.
   - **Unverifiable:** say so in the report. Do not state it as a fact.

6. Confirm that a fix covers the symptom by reading its diff. A commit title is not proof.

7. Apply any approved change through the CLI the docs name, then append one line to an audit file with the time, the
   command, the reason and the result.

8. Before sending an operator-facing plan, check every item:
   - The plan is shown in the chat with a short summary, not only saved to a file.
   - Each technical term is either familiar to the reader or explained in one plain paragraph first.
   - Each item can be explained in one sentence, including why it is in scope.
   - Anything the operator did not mention is written as a question, not added to the plan.

## Pitfalls
- **Do not treat the local clone as current.** It can be hundreds of commits behind. Compare with the upstream main
  branch every time.
- **Read the per-feature README before any summary.** A plan drafted from a summary got mode names, environment
  variable names, install commands and client version requirements wrong. The README is authoritative.
- **Never edit config, auth or credential files by hand to apply a fix.** Use the CLI. Hand edits bypass its
  validation and leave no record.
- **A commit title is not evidence that a bug is fixed.** Read the diff and check that it touches the failing path.
- **Do not file a bug for something fixed upstream.** Recommend an update, and say which commit fixes it.
- **Watch the API rate limit.** Unauthenticated requests are limited. Batch lookups, cache the answers, and keep any token out of logs and reports.
- **Every plan item needs provenance.** "I found it on disk" is not a reason. State the goal the item serves. If you
  cannot, drop the item.
- **Ask before adding unmentioned work.** A plan with no open questions usually means the scope was not checked.
- **Show the plan in the conversation.** A file on disk is for the agent's own continuity. The operator reads the
  inline summary.
- **Explain jargon before using it.** For a non-specialist reader, put one plain-language paragraph ahead of any
  internal file, table or enum name.

## Verification
- Run the lookup for a symptom you know is fixed upstream. It should return the fixing commit and the verdict "fixed
  upstream".
- Run the drift count and confirm it matches the commit range you searched.
- After any applied change, confirm the audit file gained one line and that the CLI status command shows the new value.
- Re-read the operator-facing plan against the four checklist items before sending it.

## Attribution
Eidolon-Soul-For-Hermes-Agent-Universal is a public project: https://github.com/shagghiesuperstar/Eidolon-Soul-For-Hermes-Agent-Universal.
