---
name: storefront-accessibility-audit
description: Use when auditing storefront WCAG 2.2 AA accessibility with axe-core across several pages and viewports. Read-only, per-rule CSV, draft PR.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [accessibility, wcag, axe-core, lighthouse, storefront, audit]
    category: web-quality
related_skills: [storefront-code-audit, cro-baseline-audit, page-speed-baseline]
---

# Storefront Accessibility Audit (WCAG 2.2 AA, axe-core, Draft PR)

## Overview
A read-only accessibility audit of a few live storefronts: home, one category, two product pages and the cart, at a mobile and a desktop viewport. axe-core runs on the live document and records every violation and every "incomplete" result. Each finding is checked before it is reported, then mapped to repository files and ranked. The deliverable is a set of CSVs, a report and one draft PR. axe covers only part of WCAG 2.2 AA, so a clean run is never presented as conformance.

## When to Use
- The request is an accessibility audit of live storefronts, or a re-run that checks whether a finding from an earlier audit still reproduces.
- The result must be a per-rule CSV with evidence, plus a report and a draft docs PR.
- For static source patterns such as empty buttons or click handlers on non-interactive elements, use `storefront-code-audit`. For conversion and mobile-versus-desktop UX, use `cro-baseline-audit`.
- For a keyboard, screen-reader, zoom or reflow walkthrough, axe cannot cover it. Do the manual pass and cite axe only as partial evidence.

## Features
- axe-core run on the live document with the WCAG 2.0, 2.1 and 2.2 AA tag set plus best-practice rules, keeping violations and incomplete results.
- Separate tables for violations, incomplete results ("needs review") and per-run summaries.
- Viewport emulation at 390 x 844 (mobile) and 1440 x 900 (desktop), with an optional tablet pass.
- Gate classification for each page, so walls and redirects are named instead of silently scanned.
- Comparison against earlier accessibility reports in the repository, with a status for each earlier finding.
- Build script that generates every table from the raw JSON, so no number is typed by hand.

## Benefits
- Every number in the report can be re-derived from the raw axe output.
- "Needs review" results stay separate, so the violation total is not padded.
- Walls and redirects are reported as coverage limits, not as passes.
- Earlier findings are tracked, so a reader can see what was fixed.
- The scan is passive apart from one visible confirm click on sites you operate: no form input, no account creation.

## Procedure

1. **Pre-flight.**
   - Find the live hosts. The repository README and config rarely name them, so state how each host was inferred. Confirm each host answers 200 on its locale path, and note any redirect to a sign-in page.
   - Choose the page set: home, category, product, cart and any public information page. Use real category and product paths from the storefront's own navigation or sitemap, and confirm each returns the status you expect.
   - Set viewports: 390 x 844 at device pixel ratio 1 with touch emulation, and 1440 x 900. A 768 x 1024 pass is optional. Name the pair in the report.
   - Find earlier accessibility work in the repository (`find docs -ipath '*a11y*' -o -ipath '*accessibility*'`) and read each prior CSV or report. Give every prior finding ID one of four statuses in the new report: STILL PRESENT, NO LONGER REPRODUCED, NOT axe-detectable (manual check needed), or STILL PRESENT (needs review).

2. **Classify each page's gate before scanning.**
   - A public age or consent dialog with a plain confirm control outside any form: on a site you operate, click that control once per fresh browser context, exactly as a visitor would, then scan the post-gate page and record the state as `gate-passed`. On a third-party site, scan the page as first shown.
   - A region picker or other dialog that needs a choice: scan the page as first shown and name the dialog as a coverage limit.
   - A login or register wall, or a dialog that wraps a form: scan the wall and name it as a coverage limit.
   - An anonymous redirect to sign-in: scan the sign-in page, and record each redirected page type as a coverage row, not as a scanned page.
   - No gate: scan as shown.

   Never click a control inside a form, never submit a form, never preset a stored gate choice, and never hide a dialog with CSS. A scan of a wall describes the wall.

3. **Run axe on the live document.** Load the page in a fresh browser context, wait about six seconds for client rendering, inject the axe-core source, and run it with `runOnly` set to the tags `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22aa` and `best-practice`. Request the `violations` and `incomplete` result types. Record each run's violations, incomplete results, pass count, inapplicable count and axe version. Keep the `best-practice` tag, and label each row so a reader can tell a WCAG-tagged violation from a best-practice-only one.

4. **Pace the scan.** Make one top-level page load at a time, and pause at least two seconds between loads. Retry a failed load once after two seconds, and log every attempt. Set each request's timeout explicitly, because a slow response that trickles data can stall a socket read indefinitely.

5. **Set small viewports through device emulation.** Use the browser's device-metrics emulation for widths below about 500 px. An OS window-size flag is clamped near 500 px, so it does not produce a phone-sized viewport. Assert that the document's client width equals the requested width before trusting the run.

6. **Write the raw output.** Save every run's raw axe JSON, plus any keyboard, zoom and probe output, under `raw/`, one file per page, viewport and state. Write the CSVs and the report from a build script that reads the raw files.

7. **Verify each heuristic before it becomes a finding.** Open the file or run a targeted check for every top issue. Pixel-sampling contrast scripts have produced false failures on obvious contrast pairs, so do not report a contrast result from one. Use axe's violations as definite results, and leave contrast verdicts to a manual measurement on named selectors.

8. **Map issues to code.** Find the file and line for each top issue by reading the code. The live site may lag the main branch, so label each mapping "likely source at <commit>" unless you have confirmed the deployed commit.

9. **Rank and merge.** Rank by severity multiplied by reach (site-wide before single-page), then by effort. Merge rows that share one fix, such as a skip link repeated on several sites.

10. **Open one draft PR.** Put only the audit directory in the commit. The PR body states the one-line headline, the scope and safety notes (passive scan, user-agent, pace, viewports, gates not passed), and a line stating the diff is docs-only so the build was skipped on purpose. Do not merge.

### Deliverables

```
docs/qa/<audit-id>/
├── REPORT.md                 # headline, method, pages, counts, top violations, prior-work table, limits, files
├── axe.csv                   # one row per violation node-hit
├── axe-pages.csv            # one row per axe run
├── axe-needs-review.csv     # one row per incomplete rule per run
├── raw/                      # raw axe JSON per run
└── tools/scan.mjs            # the scanner, with the axe version pinned
```

`axe.csv` columns, in this order: `site`, `page_type`, `requested_url`, `final_url`, `viewport`, `state`, `rule_id`, `impact`, `wcag_tags`, `axe_tags`, `selector`, `count_on_page`, `html_snippet` (trimmed to 200 characters, whitespace normalised), `help` (axe's text, not paraphrased).

`axe-pages.csv` columns: `site`, `page_type`, `viewport`, `state`, `requested_url`, `final_url`, `http_status`, `violation_rules`, `violation_nodes`, `needs_review_rules`, `needs_review_nodes`, `axe_passes`, `axe_inapplicable`, `raw_file`.

`axe-needs-review.csv` columns: `site`, `page_type`, `viewport`, `state`, `final_url`, `rule_id`, `impact`, `wcag_tags`, `count_on_page`, `example_selector`, `reason`. Needs-review rows are never counted as violations.

`REPORT.md` sections, in order:
1. Headline: violation total, per-site counts by impact, and the caveat that zero violations does not mean WCAG conformance. State the axe version, the run time, and the commit measured.
2. Tool and command: versions of axe-core, the browser and Node, the `axe.run` call, viewports, user-agent, pace, and gate handling. A reader should be able to reproduce the run from this section.
3. Pages scanned: requested URL, landed URL and gate class for each page.
4. Violation matrix: page by viewport, with the initial state and the post-gate state. Write `n/a` where no gate was passable.
5. Top violations: one row per rule, with impact, WCAG tag, pages affected, node count, example selector and a one-line fix idea. If there are no violations, list the top needs-review rules in their own table and label it as needs review.
6. Prior work: the status of each earlier finding ID.
7. Limits and side effects: every coverage limit, every confirm click the scanner made, every page-initiated request the scanner did not cause, and every incomplete result whose verdict needs a manual check.
8. Files.

Derive every self-described number from the files before writing it: row counts, run counts, node counts and the axe version.

## Pitfalls
- **A Lighthouse score of 100 is not a clean bill.** Lighthouse can score 100 while axe reports serious rules, such as nested interactive elements or focusable scrollable regions. Report both.
- **Incomplete is not a violation.** A contrast result that axe cannot decide, because the text sits on a gradient, an image or an overlay, is a needs-review item. Keep it out of the violation total, and say so in the headline.
- **axe covers only part of WCAG 2.2 AA.** Its rules check static DOM patterns: roles, names, labels, alternative text, ARIA validity and focusability. They do not check keyboard operation beyond focusability, announcement quality, reflow at 200 or 400 percent, text spacing, focus order or cognitive load. Name these gaps in every report.
- **Wall pages describe the wall.** A page that is only a dialog over inert content means every result describes the dialog. Say so in the matrix and in the CSV.
- **Redirects collapse page types.** When anonymous visitors are redirected to sign-in, several page types resolve to one page. Report "one page covered, four redirects observed" rather than a five-page scan.
- **Page-initiated requests are not the scanner's.** Many server-rendered frameworks send requests on load. Record non-GET requests the page sent without the scanner's involvement, so a reader can tell them apart from anything the scanner did.
- **Verify the user agent.** The UA recorded in each raw file must match the constant in the scanner and the value quoted in the report.
- **A sandboxed worker cannot run the scan.** A worker with no network or no browser can write the scaffold. The host runs the scan, regenerates the raw files and CSVs, and pushes the branch. Keep the worker's commit and the host's corrections as separate commits.
- **Check the remote before pushing.** A remote URL with an embedded token, or a Git rewrite rule that adds one, leaks the token on push. Use a clean remote and the credential helper that your GitHub CLI manages.
- **A critical default impact is not a critical finding.** An `incomplete` result can carry axe's default impact for the rule. State the page-level status separately from that default.
- **Do not import unrelated audit caveats.** A stock or pricing note from a conversion audit does not belong in an accessibility report.

## Verification
- Every row in `axe.csv` has a `raw_file` that opens and contains the rule's node.
- For each run, `violation_nodes` in `axe-pages.csv` equals the sum of node counts in its raw file.
- The per-site totals in the headline match a re-count of the raw files, and the per-rule totals match `axe.csv`.
- Every prior finding ID from the earlier reports appears in the prior-work table with one of the four statuses.
- The limits section names every gate, every redirect, and every needs-review rule.
- `gh pr view <n> --json isDraft,files` shows a draft with only files under the audit directory.
