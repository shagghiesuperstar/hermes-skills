---
name: independent-static-review
description: Use when briefing a read-only reviewer on a code path. Covers a second, read-only session that audits a composed path, such as checkout, payment, or access gates, for defects that no single diff shows.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [code-review, static-analysis, read-only-review, money-path, independence]
    category: agent-orchestration
related_skills: [adversarial-review, ar-verify-findings, data-artifact-adversarial-review, say-do-verify]
---

# Independent Static Review

## Overview
A pull-request review checks one change. It misses defects that live in a path the change touches but does not modify, and it misses flows where several changes combine. An independent static review is a second session that reads the composed path in the code and reports file-and-line findings. It is read-only. It does not fix anything, and its findings become new builder tasks that are reviewed afterward. The reviewer's independence is the point: a reviewer that also writes fixes is a second builder, and nobody checks its work.

## When to Use
- The operator asks for a static audit of a sensitive path, such as checkout, payment, age checks, or shipping gates.
- A dynamic walk through the product found a break that had been in the code all along.
- A brief asks for a comprehensive review and an automatic fix-and-ship pass in one session.

Skip it for typo or documentation changes, and for a review of one already-scoped diff. For a diff, use the adversarial review skill.

## Features
- A read-only brief that pins one frozen tree and forbids edits, hook installs, secret reads, pushes, and merges.
- A pre-read scan with pattern rules for bugs already seen, run before the prose walk.
- A per-criterion evidence table with file-and-line citations and a status for each row.
- A procedure for numbered criteria, and a shorter procedure for a re-confirm under a tool-call cap.
- A refusal rule for briefs that give the reviewer write access or ask for a fixed-looking report template.

## Benefits
- Defects in composed flows are found, not just defects in the latest diff.
- Reviewer and builder stay separate, so a change is always checked by someone who did not write it.
- Each claim in the report points to a line, so the next reader can verify it without re-running the review.
- A reviewer that never edits cannot quietly "fix" the evidence it was asked to collect.

## Procedure
1. Record the frozen commit before reading anything. Create a detached worktree at that exact commit and confirm it:
   ```bash
   git worktree add --detach "<review-dir>" "<commit-sha>"
   git -C "<review-dir>" rev-parse HEAD
   ```
   Refuse to continue until the printed commit equals the review target. A branch tip can be many commits ahead of the commit that was actually reviewed.
2. Use a different model from the builder when one is available, and keep the reviewer's session separate from any session that is writing to the same checkout.
3. Run the pattern rules against the frozen tree first. Pin the rules to the bugs already found, and exclude dependency and build folders. A hit is a regression of a known defect. A clean run does not mean the path passes.
   ```bash
   semgrep --config "<rules-file>" --error --exclude node_modules --exclude dist "<frozen-tree>/<app>"
   ```
   Never point a scanner at credential files, and never use a generic auto-selected rule set in place of the pinned rules.
4. Brief the reviewer in writing. The brief names the path under review, the criteria to answer, the read-only rules, and the report format. It does not ask the reviewer to fix anything.
5. Read the composed path end to end: the entry point, the guards, the service calls, and the writes. Do not stop at the function the change touched.
6. Verify framework behavior in the installed packages at the locked version, not in the documentation. Find the function that handles the step and read what it returns.
7. Write the report as a table with one row per criterion: the criterion, the finding, the file and line, and a status of VERIFIED, UNVERIFIED, or NOT-PRESENT. Add a verdict line of SAFE, UNSAFE, or CONDITIONAL, with the smallest code change that would change the verdict.
8. Hand the findings to the operator. Fixes become new builder tasks, and each fixed change then gets its own adversarial review. The independent reviewer does not return as the fixer.

### Running a read-only reviewer from the command line
When the reviewer is a command-line agent run in print mode:
- Restrict the toolset, not only the permissions. Allow read, search, and find tools only, so writing and shell tools are absent entirely.
- Do not combine the CLI's bare (API-key-only) mode with an OAuth login. The bare mode reads only an API key and reports that the user is not logged in.
- Give read access to a staged evidence folder outside the working directory with a directory-add option, and set the working directory to that folder.
- Prove the model from the result record, not from the flag you passed. Read the model usage field in the output, and keep the full output as the record next to the readable verdict.

### Re-confirming a prior run under a tool-call cap
When the brief asks you to confirm or refute an earlier run's findings within a small number of tool calls:
1. Run the commands the brief gives, verbatim. A substitute command breaks the comparison with the earlier run.
2. Use one command per criterion. Do not add setup or exploration to a criterion. Put any follow-up in the next command.
3. Filter output with a count, a head, or a tail. Never print a large file in full.
4. For a before-and-after criterion, run the base and the head reads in the same block, and cite the line numbers from both.
5. Check the tree state once at the start: the commit at the head and the base, and the change summary between them.
6. If the earlier run stopped because the model backend changed, say so in the verdict file.

## Pitfalls
- **A reviewer that edits is a second builder.** Refuse any brief that grants authority to overwrite files, install hooks, or patch and recompile. Hooks in one local clone are not a gate for other worktrees, and the real gates belong in continuous integration.
- **Never read secrets into a report.** Do not open credential files, and do not copy environment values into the output.
- **Check every factual claim in the brief against the code.** A brief can assert that a flow works a certain way, and that assertion may be wrong. Treat each one as a question to verify.
- **Do not accept a fixed report template.** A template titled as if the blockers are already fixed pushes the reviewer toward fake patches. Use the evidence table instead.
- **A review scoped to one pull request misses composed flows.** The defect may be in code that no recent diff touched.
- **A dynamic walk only finds the path someone took.** Read the code paths the walk did not exercise.
- **Two sessions writing the same checkout corrupt each other.** The reviewer reads a frozen copy, and the writer works elsewhere.
- **Do not claim "tests pass" for a money control without checking the test's data.** A test that stubs a data call with a hand-written shape can pass while the real data path breaks. Confirm the shape the test expects exists in the real output.
- **A field that a workflow computes is not stored on the record.** Find the function that populates it, and confirm the implementation calls that path before you trust any test that reads it.
- **Do not mark a criterion VERIFIED from one commit.** A re-review compares two commits, so both must appear in the file-and-line column.
- **Work-order questions get their own answers.** When the brief numbers its questions, answer each one with its evidence. Do not reorganize the answers into severity tiers.

## Verification
- The reviewer's worktree reports the review commit, and the commit matches the one in the report.
- The report has one evidence row per criterion, each with a file and line.
- No file in the reviewed tree changed during the review, which a status check of the worktree confirms.
- Every pattern-rule hit is listed in the report with its file and line, or the report states that the run was clean.
- The verdict line is present, and it names the smallest change that would change the verdict.
