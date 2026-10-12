---
name: storefront-code-audit
description: Use when auditing a storefront's source for a pattern. Read-only, per-row CSV of file:line findings, report, draft PR.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [source-audit, storefront, ecommerce, named-rules, code-review]
    category: web-quality
related_skills: [catalog-data-audit, cro-baseline-audit, data-artifact-adversarial-review, storefront-accessibility-audit]
---

# Storefront Source-Code Audit (Read-Only, Per-Row CSV, Named Codes)

## Overview
A read-only audit of a storefront repository's source for one class of pattern: image components, accessibility attributes, imports, hydration patterns, dead code or compliance copy. Every finding is a row in a CSV with a file and line, and carries a named code that a script can re-apply and a reader can count. The audit changes no application code. The deliverable is the CSV, a report and one draft PR, and the rows are verified against the files before the PR goes out.

## When to Use
- The request names a file pattern and a class of element, such as "every raw image tag and image-component call in every app".
- The request asks for a dependency graph, dead exports, or hydration or bundle-import patterns across the apps.
- The request asks whether a mandated disclaimer appears on every route and template, with the exact wording.
- The deliverable is a per-row CSV of file and line findings, a report and one draft docs PR.

Skip when the task is a live-page UX audit (`cro-baseline-audit`), a catalog naming or price audit (`catalog-data-audit`), a live accessibility scan (`storefront-accessibility-audit`), or a review of one pull request's diff.

## Features
- One regex per pattern, applied to a stated file glob, with the regex recorded as part of the audit.
- Named codes in the form `<CATEGORY>_<DEFECT>`, so each finding is countable.
- A per-row CSV with a fixed column order, and a report that leads with flagged rows.
- A driver-side verification pass that re-opens every cited line and checks the snippet.
- A two-commit history, so the first commit stays visible when the host corrects it.

## Benefits
- Coverage is provable: the candidate count from the regex matches the CSV rows plus named exclusions.
- Findings can be re-checked by any reader with the repository and the same regex.
- Exclusions (test files, inline SVG, comments) are named, so they cannot hide defects.
- Codes make the ranking and the fix list reproducible.

## Procedure

1. **Confirm the repository, the apps and the pattern.**
   - Clone the repository with its full history, not a sparse checkout, so every app in scope is readable. A sparse checkout that misses one app is a coverage gap. If a large clone times out, retry in the background instead of deleting the partial clone.
   - List the apps read and the apps excluded. Say which apps are in the repository but outside the scope.
   - Write the file glob (for example `apps/*/src/**/*.tsx`, excluding tests) and the regex used to find candidate sites. The regex is part of the audit's evidence.

2. **Run the candidate regex from scratch.** Run the regex over the glob and capture every `file:line` hit. Exclude test files by name pattern, and exclude nothing else silently. Keep the hit list as an artifact.

3. **Reconcile hits and rows.** Every hit either has a CSV row or is named as an exclusion in the report's method section. Common exclusions are inline SVG components that match an image pattern, comments, type-only imports and test files. The headline check is: CSV rows equal unique hits minus named exclusions.

4. **Assign a named code to each row.** Use the form `<CATEGORY>_<DEFECT>`. For image-component audits the set is:
   - `RAW_IMG_PRODUCT`: a product tile or product-page photo uses a raw image tag, or a wrapper that emits one, where the optimised image component is expected. Record any documented exception.
   - `RAW_IMG_HERO`: a marketing or hero image uses a raw image tag. This is not always wrong, for example when the optimiser is turned off on purpose for the platform. Record the setting.
   - `MISSING_SIZES`: a fill-mode image has no `sizes` prop, or a raw image needs a srcset and has none. Fixed-width avatars and small thumbnails are not findings when `width` and `height` are set.
   - `PRIORITY_BELOW_FOLD`: a priority hint is set on an image that is not the largest visible element for its route.
   - `NO_PRIORITY_LCP`: the first visible product on a listing or category route has no priority hint and is lazy-loaded. Flag it only with the caveat that the route's largest element must be confirmed by profiling.

   Codes that flag raw images also record whether the optimiser is turned off in the framework configuration, because the fix depends on it. A row for a deliberate exception is not the same as a row for a skipped component.

5. **Build the CSV.** Use these columns, in this order: `app`, `site`, `file` (path relative to the repository root), `line` (integer), `component`, `element`, `sizes`, `priority`, `loading`, `dimensions`, `above_fold` (yes, no or route-dependent, with a reason), `flags` (semicolon-separated codes), `notes` (the exception, the call site, or the inference behind a flag).

6. **Verify every row against the file.** For each row, open the file at the line and check that the five surrounding lines contain the expected element pattern. A row whose snippet does not contain the pattern is a defect: re-read the file, correct the line, or drop the row with a note. Keep the verification output as an artifact.

7. **Write the report.** Sections, in order:
   1. Verified findings: any finding the host re-checked, what was confirmed, and any correction. Put this first, above the worker's table.
   2. Scope and repository: URL, branch, commit SHA, apps read, file glob, regex, excluded paths and run date.
   3. What was read: candidate hit count and CSV row count, both derived from the artifacts.
   4. Result at a glance: per app, the counts of optimised components, raw images and excluded hits, with the wrapper rule for each app.
   5. Flagged rows, sorted by code, then app, then file and line.
   6. One fix per code: one paragraph each, with the documented exception where it exists.
   7. Method: the regex, the per-file reads, the exclusion rules, and any tool that was tried and why it was not used.
   8. Evidence: commands, the candidate count, the verification count, the commit, the push result and the PR URL.

8. **Keep the audit trail.** The worker's commit stays as it was. Corrections from the host go in a second commit. Do not amend the first commit, because the trail shows what the worker produced and what the host verified.

9. **Open one draft PR.** Put the CSV and the report in the audit directory. The PR body states the top three codes in one line each, the scope and safety notes (read-only, apps in scope, nothing in application code changed), the verification the host re-ran, and a line stating the diff is docs-only so the build was skipped on purpose. If a sandboxed worker produced the audit, the body names the worker's engine and model and which steps the host ran. Do not merge.

### Compliance copy variant

For a mandated disclaimer, the per-row granularity is the route, not the file and line. Each row records whether the disclaimer renders on that route, its literal wording as found in the file (not a paraphrase), and a code such as `NO_DISCLAIMER`, `PARTIAL_DISCLAIMER`, `ALTERNATE_WORDING`, `CLIENT_ONLY` or `META_ONLY`. Anchor each search on the approved string, not on a paraphrase. The driver asserts that each recorded string is character-identical to the file at the cited line.

## Pitfalls
- **The worker's "I verified" is a claim until the host re-runs it.** Re-run the candidate regex, the per-app counts and the per-row snippet check on the host before the PR goes out.
- **A wrapper component is not always a defect.** A wrapper that emits a raw image can be the documented pattern when the optimiser is off in the configuration, and the wrapper handles the srcset itself. Record the wrapper's purpose in `notes`; do not drop the row silently.
- **`fill` needs `sizes`; fixed size does not.** A fill-mode image without `sizes` is a finding. An image with explicit `width` and `height` is intrinsic, so `sizes` is optional and the verifier should skip it.
- **The largest element is not always the image you expect.** A route whose largest element is a logo does not need its first product tile to be a priority image. Mark the inference in `notes`, and do not state it in the headline.
- **A priority hint below the fold is a finding, with a caveat.** For a banner that is the first image on a page but sits below the fold on sub-pages, recommend removing the hint "unless profiling shows it is the largest element". A recommendation without the caveat is one a reviewer will reject.
- **Inline SVG shares the hit list with image tags.** A pattern search for image elements returns SVG wrappers and comments. Exclude them by a content check, and name the exclusion rule in the report.
- **Tests document patterns; they are not rows.** A test that asserts a lazy-loading attribute is evidence for the report, not a CSV row. Cite it in the method section.
- **A regex for banned terms can match mandated text.** Word-boundary patterns for claim terms can match the mandated disclaimer, neutral product copy the store publishes, or unrelated text in a README. After the lint reports zero hits in the bodies, read each regex against the mandated text and against the copy you cite. Narrow the regex rather than rephrasing text the store has already approved.
- **A `build skipped` line is only honest for docs-only diffs.** A change under an application folder is not docs-only, even when the change is to a Markdown file inside that folder. The waiver applies only when every changed path is under a docs folder.
- **Counts in prose drift from the CSV.** A report that says 48 pages when the CSV has 57 rows usually counts only one kind of route. Reconcile the prose against `wc -l` on the CSV and against a find of each route type, and fix the prose. Do not delete rows to make the prose match.
- **A host-side count can differ from the worker's count.** State both counts and name the difference, and trust the host count.
- **Sparse checkouts hide files from `git add`.** Disable sparse checkout before adding the audit directory, rather than forcing the add.
- **Self-described numbers are derived, not remembered.** The commit SHA, the row count, the per-app counts and the verification count each come from a command you ran.

## Verification
- `wc -l` on the CSV matches the report's row count plus one header line.
- Every row's `file:line` opens to a snippet that contains the expected element pattern, with zero mismatches.
- The candidate regex hit count equals the CSV rows plus the named exclusions.
- The per-app counts in the report match a fresh count per app.
- For a regulated store, a banned-term scan of the report, the CSV and any script returns zero hits, and each regex hit in the mandated text has been reviewed.
- `gh pr view <n> --json isDraft,files` shows a draft with only files under the audit directory.
