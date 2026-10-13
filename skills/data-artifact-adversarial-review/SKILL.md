---
name: data-artifact-adversarial-review
description: Use when reviewing another agent's data deliverable. Covers CSV, JSON and other data outputs, such as a list, extract, or catalog audit, before a merge. Verifies claims by re-execution.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [data-review, adversarial-review, csv, verification, data-pipeline]
    category: agent-orchestration
related_skills: [adversarial-review, ar-verify-findings, independent-static-review, merge-reconciler]
---

# Data-Artifact Adversarial Review

## Overview
A data deliverable (a CSV of records, a JSON registry, a vendor extract, an audit table) is research data, not code. The reviewer's job is to verify the builder's claims, not to read the diff. Verification is by re-execution: run the builder's checker, then run an independent check through a different code path, rebuild the file from its raw inputs and compare hashes, and re-fetch a sample of the cited sources. Builder-admitted gaps are treated as confirmed findings, not as footnotes.

## When to Use
- A builder agent delivers a data file in a pull request, and the acceptance criteria include counts, uniqueness, resolvable sources, or coverage.
- A deliverable is described with words like "files only," "unique rows," "draft pull request," or "DONE-MEANS."
- Work covers prospect or vendor lists, registry dumps, enrichment outputs, catalog audits, or copy drafts with per-row citations.

Use the code-review variant of this protocol (`adversarial-review`) for executable changes. Skip this skill for a single-file edit with no acceptance matrix.

## Features
- A verdict model with three outcomes: APPROVE, NEEDS_CHANGES, or ESCALATE when the spec's intent is disputed.
- A re-execution procedure: builder checker, independent recount, rebuild from raw, and a byte-level hash comparison.
- A fixed-seed live sample for large sets, with a full re-fetch for small or cheap sources.
- Checks for cross-counts between prose and data, and for attribution and licence text.
- A rule that every number in the prose is a testable claim.
- A fix-round check that proves a named defect was removed and nothing else changed.

## Benefits
- Claims are confirmed from the file the reviewer actually sees, not from a summary.
- A builder's own checker cannot pass a file it wrote to pass, because an independent path also runs.
- A rebuild from raw inputs proves the deliverable is reproducible and that no hand edit leaked in.
- Known-bad rows are caught by row-level tests, not by trust in the builder's counts.
- Honest gaps reach the operator as explicit findings, and nothing is silently rebuilt during review.

## Procedure
1. Extract the acceptance criteria verbatim from the issue or work order into a numbered list. That list is the review checklist, not the reviewer's own rubric. If the builder restated the criteria in the pull request body, the original wording governs.
2. Pin the artifact. Record the head and base SHAs, the file list, and the file hashes.
   ```bash
   gh pr view <pr-number> --repo <owner>/<repo> --json number,isDraft,state,headRefOid,baseRefOid,files
   gh pr view <pr-number> --repo <owner>/<repo> --json body -q .body
   shasum -a 256 <deliverable.csv>
   ```
   Compare every hash in the body to the file you hold. A mismatch means you are reviewing a different file than the builder reported on.
3. Work in a scratch directory. Copy the files out with `git show <sha>:<path>` or the contents API, and never edit the builder's tree or check out the branch into a shared checkout.
4. Re-run the builder's checker from your copy and save its output and exit code. Then write one independent check with a different code path, covering at least the uniqueness keys, the value ranges, and the unique-source count, and compare the two outputs. If they disagree, report the disagreement. Do not pick the more pleasing number.
5. Rebuild from raw. If the builder ships raw inputs and a build script, run the script in a fresh directory that contains only the script and the raw inputs, then compare each output hash to the committed file.
   ```bash
   mkdir -p <scratch>/rebuild && cp <build-script> <scratch>/rebuild/ && cp -R <raw-dir> <scratch>/rebuild/
   cd <scratch>/rebuild && python3 <build-script>; echo "exit=$?"
   ```
   A match on every output file shows the file is reproducible from the raw inputs alone. A mismatch is a finding: the raw inputs do not cover the file, the build is not deterministic, or the file was edited after the build.
6. Verify each row's citation resolves to that row's record, not to a page or a search. Accept per-record identifiers such as an API object id or an element id. Reject a document page URL whose fragment the server ignores, because every row sharing that page returns the same bytes.
7. Re-fetch a sample of the cited sources. Use a fixed seed that differs from the builder's seed, and cite the seed and the sample size. For a small set (under about 200 rows) or a free, fast source, re-fetch every row instead.
8. Re-derive each number in the prose from the data file, not from the builder's sidecar. Recount the rows by category and compare the counts to every table and sentence. Recompute totals, percentages, and sort order.
9. Read the prose for builder-admitted failures, such as "I believe this is a real shortfall" or "may not meet the spec." Treat each admission as a confirmed finding against the criterion it names. The builder's honesty does not waive the criterion.
10. Check attribution and licence text. If any row comes from a dataset with a required attribution, grep the deliverable for the attribution terms, and report the result even when it is empty.
11. Write the verdict with a findings list (severity, criterion, file and line, and the builder's own words where they apply), an evidence block of real command output, the claims you reproduced, and the items you could not verify, each with the reason. End with the verdict line.
    ```text
    FINDINGS (<n> blocking, <n> minor, <n> low)
    EVIDENCE
    CLAIMS THAT HOLD
    NOT VERIFIED
    VERDICT: NEEDS_CHANGES: <one-line summary>
    ```
    Use `VERDICT: APPROVE` when every criterion holds, and `VERDICT: ESCALATE` when the reviewer and the builder read the spec differently and only the operator can decide.

### Fix-round check
When the implementer pushed a new head after a rejection, prove the named defect was removed and nothing else moved. Load the rejected version and the current version with `git show <sha>:<path>`. Remove exactly the rows the finding named from the rejected set, then assert the result equals the current file byte for byte. A match shows the fix was applied, that no replacement rows were added, and that no other row changed. Run this once per finding, and still re-test each finding's underlying defect, because the byte match alone does not prove the defect is gone.

## Pitfalls
- **Do not fix the data during review.** Editing a copy and calling the deliverable fixed hides the builder's responsibility. Report the gap and let the builder rework it.
- **Sample coverage is not full coverage.** A small sample of a large set proves only the sample. For example, if you checked 20 rows out of 1,000, say that, and cite the full run from the builder's log. Do not write that every row was verified.
- **A checker written by the builder is not an independent check.** It can pass a file it was written to pass. Always run a second, different code path.
- **A verifier that re-derives values from the same source is self-consistent, not correct.** If the verifier re-fetches a value from the same service the builder used, it proves the link is live, not that the value is right. Cross-check against an independent ground-truth source where one exists.
- **Use the same fetch method the builder documented.** A scrape of a rendered page and an API call can disagree on character counts. If your probe disagrees, switch to the builder's method before you call it a finding, and note the method in the report.
- **Count distinct values, not occurrences.** For example, 40 distinct handles linked across 250 occurrences is 40 handles, not 250. Compare the distinct set to the catalog, not the occurrence count.
- **A "0 hits" claim needs its own grep.** Rerun the scan with your own word list, and use a union of the builder's list and an independent list with different stems. Zero hits on the builder's list alone is not enough.
- **Word-boundary matching prevents false positives.** A bare substring match flags innocent names. Normalize the way the builder's matcher is supposed to, then probe only the rows that still match.
- **Normalize both sides before a set comparison.** A phone or name can differ only in punctuation. Compare the digits-only form and report which normalization you used, alongside the string-equality result.
- **Test each count against the rule the file itself states.** A word count that does not reproduce under the file's own exclusion rule is a finding, even when the worst case still passes.
- **Re-derive every score and tier from the documented rule.** Assert `score == rule(row)` and `tier == bucket(score)` on every row, and assert the sort order equals a sorted copy of the key.
- **Check every count against the live source at the same time as the build.** A later pull can grow the pool. Compare against the snapshot timestamp, not today's data.
- **Name the freeze time when a claim depends on it.** A claim that a pull request did not exist yet is true at the freeze time even if it is false today.
- **Compare canonical content, not gzip bytes.** Two gzip files of identical JSON can have different hashes. Hash the decompressed, key-sorted JSON when a "byte-identical" claim is made.
- **Sort the enumeration before you trust a dedupe total.** Enumerate every sibling file on every relevant ref, not only the ones the builder named. A curated list can hide a sibling.
- **A vacuous overlap check proves nothing.** If the cited batches cannot share a key with the deliverable by construction, a zero overlap says nothing. Report that and enumerate the real siblings.
- **Check exclusion rules for token order.** A regex that matches "gram" then "device" can miss the same words in reverse order. Probe with a list of records that contain both words in each order.
- **Decide severity after instrumenting a silent drop.** A branch that drops rows without a counter may drop correct, out-of-scope rows or real targets. Count the dropped rows by type before you grade the finding.
- **Include quarantine and excluded files in dedupe.** A delivered row can match a row the builder excluded earlier. Check the exclusion files as well as the delivered file.
- **Check that a "live" claim was true at the time it was made.** Pin the live check to the build's timestamp, and report drift separately from defects.
- **Scan the diff for secrets and host paths before approval.** Grep the changed files for private-key headers, common provider token prefixes, and home-directory paths. Any hit is blocking. Mask the matched value in the report, and tell the operator to rotate the credential, because the secret now exists in git history.
- **Make sure the reviewer can run the builder's documented command.** Run the regenerate command on a stock interpreter, with the deliverable deleted, and byte-compare the output. A script that needs a newer interpreter is a real defect.
- **A headline in the pull request body can disagree with the file.** Reconcile every integer in the title and body with the deliverable. Report drift, and count the most important drift as a finding, not as decoration.
- **A draft pull request's blocked merge state is expected.** A draft cannot merge until it is marked ready, so do not treat that state as a finding. Judge readiness from the criteria.
- **Work from the artifact, not from the builder's chat summary.** When a chat reply and the file disagree, the file governs.

## Verification
- The acceptance criteria list in the review matches the issue text, word for word.
- Every hash reported in the body matches the hash of the file you reviewed.
- The builder's checker output and your independent check are both quoted, with exit codes.
- The rebuild from raw produces a hash match for every output file, or each mismatch is listed as a finding.
- The sample seed and size are stated, and any failing row is cited by its source URL.
- Every number in the prose traces to a command you ran against the file.
- The verdict line is the last line, and it matches one of the allowed forms exactly.
