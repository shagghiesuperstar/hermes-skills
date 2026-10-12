---
name: page-speed-baseline
description: Use when measuring a live storefront's page speed. Uses Lighthouse and ships the baseline as a docs-only draft PR.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [lighthouse, core-web-vitals, performance, baseline, docs-only]
    category: web-quality
related_skills: [storefront-code-audit, cro-baseline-audit, live-link-audit, preview-env-qa]
---

# Page-Speed Baseline (Live Storefront, Lighthouse)

## Overview
A page-speed baseline is a measurement, not a change. Lighthouse runs against named live URLs several times, the results are summarised as medians with spreads, and the raw median-run JSON is committed with a report in a docs-only draft PR. The goal is a number a reviewer can reproduce, together with its caveats: host load, simulated versus observed timing, and which run the phases came from.

## When to Use
- The task asks for a Core Web Vitals or Lighthouse baseline of a live storefront, delivered as a report.
- The deliverable is a docs-only PR that contains the report and the raw artifacts.
- You need a list of pixel-neutral fixes a developer can act on.

Skip when the job is a preview-deployment visual check (`preview-env-qa`) or a source-code audit (`storefront-code-audit`).

## Features
- Round-robin runs across pages, with host load recorded before every run.
- Median run chosen by LCP, with its phase breakdown kept whole.
- Simulated and observed (unthrottled) timings reported side by side.
- Ranked opportunities quoted from Lighthouse's own savings fields.
- Dedupe table of prior docs and PRs before any new measurement.
- Hygiene checks that scrub machine-identifying strings before commit.

## Benefits
- Reviewers can rerun the same command and compare the same median run.
- Outliers caused by host load stay visible instead of being dropped.
- The LCP phases add up for the run they came from.
- Prior work is found first, so a finished baseline is not repeated.
- No machine names, user paths or private hostnames reach the public history.

## Procedure

1. **Dedupe first.** Check the repo's `docs/` tree and open PRs for prior work on the same page, metric, domain or tool. Tabulate what each covers and how this run treats it. Cite only the paths that git actually returned.

2. **Confirm the pages.** Each URL must return 200. Follow redirects and record the final URL. If a named page has no direct product link, follow the catalogue link it does contain, take the first product link in document order, and record the gap. Do not invent a direct link.

3. **Record the deployed version.** If the site exposes a version endpoint, record its output at measurement time. The report names the commit that was measured, because a live site can deploy during a session.

4. **Run Lighthouse with a pinned version.**
   ```sh
   npm install --prefix <scratch-dir> lighthouse@<pinned-version>
<scratch-dir>/node_modules/.bin/lighthouse "<url>" --only-categories=performance --output=json --output-path="<run-file>"
   ```
   - Add `--preset=desktop` only when the request asks for desktop. Mobile is the default.
   - Pin the Lighthouse version in the run record. Do not install Lighthouse globally, and do not switch tools without noting the deviation.
   - Add `--chrome-flags="--headless=new"` for headless runs, as the performance-audit recipe does. Do not add cookies or other Chrome flags unless the request says so.
   - Run from a scratch directory, not from inside the repo.
   - Confirm `configSettings.formFactor` and `screenEmulation.mobile` match the preset you asked for.
   - If a run times out, kill its whole process group so Chrome does not leak into the next run.
   - Keep Chrome's sandbox on. If Chrome cannot start inside a container, fix the container's sandbox support first. The `--no-sandbox` flag is a last resort, and only for a disposable container that holds no credentials or secrets.

5. **Try the PageSpeed Insights API once per URL and strategy.** PSI returns Chrome UX Report field data when it succeeds, which a local run cannot provide. Use this form, and space calls at least five seconds apart:
   ```
   https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=<url>&strategy=mobile&category=performance
   ```
   Keyless quota is shared. On a daily-quota 429, stop, save the error JSON as evidence, retry once at the end, and do not loop. If PSI gives no field data, report total blocking time as the lab proxy and state that INP was not measured.

6. **Round-robin the runs.** Run one round across every page, then the next round, rather than all runs of page A followed by all runs of page B. Start-up cost in the first runs of a fresh shell then lands on a different page each round. Run sequentially, never in parallel.

7. **Log host load before each run.** Record `uptime` and a UTC timestamp immediately before each invocation, and save the lines in `uptime_log.tsv`. Strip any hostname banner from the output. Load averages do not identify a machine and are fine to commit.

8. **Use enough runs.** Use at least five runs per page for a baseline. Single runs swing widely (for example, one page once scored 57 on one run and 96 on another), so a three-run sample is acceptable only when the report labels it as a three-run sample.

9. **Choose the median run and summarise.**
   - For the headline table, take the median of each metric across runs: LCP, CLS, TBT, performance score, and SEO score if captured. Show min to max in parentheses.
   - The median run is the run whose LCP is the median LCP. Report that run's phases and LCP element. CLS, TBT and scores are medians of their own series, so they may not match the median run's values. State this definition in the report.
   - Do not average phases across runs. Phases belong to one run.
   - Commit only the median run's raw JSON per page. Keep the other runs as rows in the CSV.
   - Check that the LCP element selector is the same across runs of a page. If it shifts, the median run is misleading, so flag it.

10. **Report observed timings too.** Read `observedFirstContentfulPaint` and `observedLargestContentfulPaint` from the metrics audit's details. Give them as a second table. The gap between simulated and observed timings is what explains "it loads in a second on my machine".

11. **Rank the opportunities.** For each page's median run, take the top three opportunities by `overallSavingsMs`, then by `overallSavingsBytes`, and quote Lighthouse's text. Read those fields from the audit's details. See the version notes below for where savings live.

12. **Write the report in this order.**
    1. Dedupe table: prior work, what it covers, how this run treats it.
    2. Median table with min to max and the median-run number for each metric.
    3. Observed table.
    4. Per-page LCP element and phase breakdown for the median run.
    5. Top three opportunities per page from the median run, with savings quoted verbatim.
    6. Caveats: load outliers and the runs they affect, simulated versus observed, the commit measured versus the live commit, the raw artifacts kept, and the median-run rule.
    7. Fix ideas, ranked by evidence and limited to changes that keep pixels the same. Exclude image re-encoding and resizing, because a new encode is not pixel-identical. Put anything that changes motion, copy or layout under a "For human decision" subsection.

13. **Scrub and check before commit.** Grep the staged files for the hostname, the local user path and IP addresses. Commit only when those searches return nothing. Replace every template token with the real host fact, and leave no placeholder in the report. For automated commits to a repository you do not own, use a no-reply commit identity so no personal address reaches the history.

14. **Open a draft PR.** Title: `[<ticket-id>] <noun phrase>: <scope> (docs only)`. The body starts with the line `build skipped: docs-only diff`, then a headline table or summary, then the path to the report. Create the PR as a draft against the default branch, with the body in a file. Confirm with `gh pr view <n> --json isDraft,url,files` that it is a draft and that every changed file is under `docs/`. Do not mark it ready for review.

### Lighthouse version notes

- **Lighthouse 12.** The LCP element comes from `audits['largest-contentful-paint-element']`. Opportunity savings sit in `details.overallSavingsMs` and `details.overallSavingsBytes`, and the audit root has no savings field.
- **Lighthouse 13.** `largest-contentful-paint-element` no longer exists. The LCP phases live in `audits['lcp-breakdown-insight'].details.items`, a list containing a table with `timeToFirstByte`, `resourceLoadDelay`, `resourceLoadDuration` and `elementRenderDelay`. The `details` savings fields are often empty, and the figure appears only in `displayValue` (for example, "Est savings of N ms"). Parse `displayValue` when `details` is empty.
- Check that `details.items` is a list before slicing it. Insight audits can return a non-list value.
- Read both locations so the ranking works on either major version. A filter on a single field returns an empty opportunity set on one of them.

## Pitfalls
- **Read the LCP element from its own audit.** The numeric LCP audit carries the value only. Quote Lighthouse's snippet field for the element rather than reconstructing it.
- **Phases come from one run.** Averaging phases across runs mixes unrelated runs, so the column totals stop matching the LCP.
- **A text LCP has no load phases.** Text has zero load delay and zero load time. Do not invent a resource load for a heading or paragraph.
- **Per-item wasted bytes are not additive.** Estimates overlap, so one URL's wasted milliseconds can exceed the audit's overall savings. Report both, and say they do not sum.
- **Observed timings do not sum to the simulated LCP.** The observed subparts are unthrottled, and the score is driven by the simulated LCP. Say so beside the observed table.
- **Do not drop outliers.** Keep every run in the CSV and explain high-load runs in the caveats.
- **Keep cache headers out of the headline table.** Cache details belong in their own section, unless the claim depends on caching.
- **A fresh headless profile shows whatever the page shows.** If a consent or age gate is the LCP element, report the gate as the LCP element. Do not remove it to get a better number.
- **Do not let the diff touch code.** A measurement PR that edits source has left its scope.
- **Do not present design changes as fixes.** Motion, copy and layout changes go under "For human decision".

## Verification
- `git diff --name-only origin/main...HEAD` lists only paths under `docs/`.
- The median table matches a recomputation from the CSV rows (medians and min to max).
- Each page's phases in the report sum to that run's LCP within rounding.
- `gh pr view <n> --json isDraft,url,files` reports `isDraft: true` with only docs paths.
