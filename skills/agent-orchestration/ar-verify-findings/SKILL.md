---
name: ar-verify-findings
description: Use when an adversarial review returns REQUEST_CHANGES. Findings must be verified before any rework. Confirms or dismisses each finding first.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [adversarial-review, verification, false-positives, code-review, triage]
    category: agent-orchestration
related_skills: [adversarial-review, kanban-card-lifecycle, say-do-verify]
---

# Verify Adversarial-Review Findings Before Rework

## Overview
A high-recall reviewer finds real defects, but it also raises false alarms. Treat its REQUEST_CHANGES findings as unverified until a separate, read-only verifier reproduces each one. The builder then fixes only what was confirmed, so a wrong finding never sends correct code back for rework. The split is deliberate: one agent optimizes for recall, another for precision, and the routing rules decide what happens to each result.

## When to Use
- An adversarial review ends with REQUEST_CHANGES or BLOCK.
- A rework task is about to be created from review findings.
- The reviewer is known to over-flag, and the change is not trivially safe.
- Findings touch money, authentication, age gating, or personal data, where an unresolved finding must be treated as real.

## Features
- A FIND → VERIFY → FIX loop with one tag per finding: CONFIRMED, FALSE_POSITIVE, or UNCLEAR.
- A routing table that turns the verifier's counts into one of three next actions.
- Pre-decided fix dispositions, written before the verifier reports, so rework is not re-derived under time pressure.
- A waiver path for mechanical blockers (merge conflict, failed build) that is checked live.
- A rule that a rework task closes the defect class, not only the cited rows.

## Benefits
- Builder time goes only to real defects, not to false alarms that could break correct code.
- Each dismissed finding keeps a recorded reason, so the audit trail explains why nothing changed.
- Verification runs once per verdict, so rework is not blocked by repeated full re-reviews.
- Security and money paths fail closed: an unclear finding counts as confirmed.
- Fixes are checked for whether they address the defect, not only whether the defect exists.

## Procedure
1. List every finding from the review with its file, line, and the fix the reviewer proposed. If the only blockers are mechanical, go to step 8.
2. Dedupe first. Search the task tracker for an existing verify task that cites the same review id and head SHA. Create one only if none exists.
3. Create one verify task per verdict. Title it with the change identifier and the frozen head SHA. Assign a verifier from a different model family than the builder and the reviewer. In the body, name the review id and the SHA, and state the verifier's limits: read-only, with no commits, pushes, merges, deploys, or external comments.
4. Before the verifier reports, comment on the review with a fix disposition for each finding, in the form "If CONFIRMED: fix by <change> under <constraint>." Mark any product or business-rule question as "ask the owner."
5. The verifier reproduces each finding on the frozen head with command output, a `file:line` reference, or a screenshot path. It tags each finding CONFIRMED, FALSE_POSITIVE with the evidence, or UNCLEAR with the missing item. It checks only the listed findings and puts new issues in a separate NOTED section.
6. Grade the fix as well as the bug. For each CONFIRMED finding, check that the proposed fix targets the element, rule, or line that causes the defect. If it does not, tag the finding FIX_MISATTRIBUTED and send only the bug to the builder, with the correct fix supplied by the orchestrator.
7. Route by the verifier's counts:
   - One or more CONFIRMED: create one rework task for the original builder that quotes only the confirmed findings, then re-review the new head.
   - Zero CONFIRMED and zero UNCLEAR: record each dismissed finding with its evidence in a comment, then treat the verdict as APPROVE.
   - UNCLEAR only: decide with a narrower probe. On money, age-gate, personal-data, or security paths, treat UNCLEAR as CONFIRMED.
8. For mechanical blockers only (a merge conflict, a failed build, or a failed test), confirm each one live, for example by checking the mergeable state or re-running the build. Record a waiver comment with the live output. Judgment findings (logic, security, copy, UX) always get a verifier.
9. Close the class, not the rows. If a finding is a row-level defect in a data list, the rework must name the key that let the row through, make the validator fail any row missing that key, add a broader fallback match one level looser than the cited one, and add a must-fail test case for each new match.

## Pitfalls
- **Do not create a rework task from an unverified high-recall verdict.** It sends a builder after bugs that may not exist and can push it to "fix" correct code.
- **Write the disposition before the verifier reports.** The rework is then built from a recorded decision, and the reasoning survives if the finding is dismissed.
- **Grade the fix, not only the bug.** A real defect with a fix aimed at the wrong selector, class, or line leaves the defect in place and may add a new one. Read the cited rule and its surrounding context, including any media-query scope the rule sits inside.
- **Selector and tap-target findings often name the wrong node.** The same label can appear in a header and in a footer. Match the flagged element's full path and classes, not only its visible text.
- **A different vendor's confirmation can stand in for a verifier run.** If another vendor's reviewer reproduced the same finding on an earlier build, and you can see the defect in the frozen source, record the code lines and that earlier run as the verification. Agreement from the same vendor does not count.
- **A builder's own audit can confirm a judgment finding.** If the builder's evidence file marks the same item below the same bar, cite that file and line on the rework task.
- **Treat UNCLEAR as CONFIRMED on sensitive paths.** Ambiguity on money, authentication, age gating, or personal data is not a reason to ship.
- **The verifier does not re-review the whole change.** Scope creep reopens the review and delays the merge.
- **Out-of-diff findings do not hold a change.** Record them as follow-up work with their own verification, and merge the change on its own scope.
- **Deduplicate verify tasks.** Two verify tasks for one review double the cost and produce conflicting verdicts.

## Verification
- Every finding in the review has exactly one verifier tag: CONFIRMED, FALSE_POSITIVE with evidence, or UNCLEAR with the missing item.
- The verifier's summary counts add up to the number of findings in the review.
- Each CONFIRMED finding cites a command or file read at the frozen head, and the rework task quotes only those findings.
- Exactly one verify task exists for the review id and head SHA. A search for that pair returns one row.
- Each mechanical waiver names the live check and includes its output.
