---
name: cro-baseline-audit
description: Use when auditing one storefront's conversion and UX on mobile and desktop. Read-only, ranked backlog with evidence per row.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [cro, ux, audit, ecommerce, ranked-backlog]
    category: web-quality
related_skills: [browser-smoke, competitor-site-teardown, regulated-catalog-content, data-artifact-adversarial-review]
---

# CRO and UX Baseline Audit (One Storefront, Read-Only)

## Overview
A conversion and UX baseline for one live storefront, measured on mobile and desktop and delivered as a ranked backlog. Every row carries the URL, the viewport and the captured evidence a reviewer can re-check. The audit observes the site as a signed-out visitor would and changes nothing: no orders, no sign-ups, no form submissions and no settings.

## When to Use
- The operator asks to audit the storefront on mobile and desktop, or to rank the biggest UX or conversion problems.
- The question is what is blocking conversion on the live site, and a live URL exists.
- You need a baseline of the current experience before a change ships.

Skip when the task is a happy-path purchase test (`browser-smoke`), a competitor teardown (`competitor-site-teardown`), or copy review for regulated products (`regulated-catalog-content`).

## Features
- Pre-flight checklist that pins the live URL, viewports, catalog size and compliance framing before any browsing.
- Click policy that allows only public, idempotent links, plus one visible confirm click on storefronts you operate.
- One browser session with a single capture round-trip per page and viewport.
- Ranked `backlog.csv` with per-row evidence, effort and qualitative impact.
- Narrative `audit.md` with headline findings, per-page notes, what works and method limits.
- Draft-PR handoff with a sign-off checklist a reviewer can run in minutes.

## Benefits
- Findings are reproducible: each evidence cell can be checked against the saved captures.
- Coverage is honest: every product page in the catalog is checked, or the gap is named.
- Read-only by design, so the audit cannot change orders, accounts or stock.
- Rankings follow user impact, not whatever is easiest to fix.
- Compliance wording is checked before any "fix" text is proposed.

## Procedure

1. **Pin four facts before browsing.**
   - *Live URL.* Take it from the operator, or infer it from deployment config, the README or an env example, and record the derivation. Confirm the host returns 200 on the home page and that the title and H1 match the brand. An inferred URL stays "inferred" until the operator confirms it.
   - *Viewports.* Use 390 x 844 at device pixel ratio 2 (mobile) and 1440 x 900 (desktop). A tablet pass at 768 x 1024 is a stretch goal. State the pair in the audit.
   - *Catalog size.* Fetch the category index once with the audit's descriptive User-Agent and count the product cards (N). Check all N product pages, not three hand-picked ones, or name the coverage gap.
   - *Compliance framing.* For a regulated store, find the repo's banned-claim list (usually a test or constants file) and the mandated disclaimer copy. Proposed copy must not introduce a banned term, even in a "fix" column.

2. **Decide what to click and what to only measure.**
   - Click only public, idempotent links: category filters, the 404 page, an empty search page, footer policy links.
   - On a storefront you operate (never a third-party site), click the visible age-gate or consent confirm control exactly as a visitor would, once per fresh browser session. The control must sit outside any form. Record which control was clicked, then capture the page. Use no CSS, cookie or storage presets to get past the gate.
   - For an account wall, a region picker or any other gate that needs a choice, record its class, stacking order, ARIA role and overlay mechanism, then stop. Write the limit into the audit.
   - Never submit a form: sign-up, login, search, newsletter, restock notice. Never click a control inside a form, including an age form that submits data. Record that these flows were not auditable.

3. **Drive one browser session.** Open one headless Chromium with remote debugging enabled. Write a short helper with Playwright, Puppeteer or chrome-remote-interface that opens a tab, navigates, evaluates a snippet and takes a screenshot. Reuse one tab per viewport. Keep the browser profile in a scratch directory for this task and close the browser when the audit ends.

4. **Measure each (page, viewport) pair.**
   - Navigate with `domcontentloaded`, then wait a short fixed interval (about 400 to 600 ms) for client hydration. Do not use a long blind sleep.
   - Gather title, H1, JSON-LD, button states and overlay presence in one page evaluation. Use a second evaluation only for a specific probe, such as whether a "Notify me" button appears on an out-of-stock size.
   - Save one screenshot per page, named with the issue slug and the viewport, for example `issue02a-card-choose-size-m.png`.
   - Save a text capture per page and viewport as JSON with `title`, `h1`, `jsonld`, `buttons` and `overlay`. A screenshot alone is not auditable.
   - Keep the request rate at or below 1.5 requests per second, with at least 600 ms between navigations. Faster crawling trips bot walls, and the resulting 403s look like defects.

5. **Build the evidence table.** `backlog.csv` has one row per problem with these columns, in order: `rank`, `page`, `issue`, `evidence`, `fix`, `effort`, `expected_impact`.
   - `rank` orders by user impact, not by effort.
   - `issue` is one sentence and names no fix.
   - `evidence` gives the exact URL and what was seen, with counts derived from the captured data. Example: "30 of 48 cards show a 'Sizes' button; all 48 product pages carry only OutOfStock offers."
   - `fix` is one paragraph of engineering work.
   - `effort` is S (under a day), M (a sprint) or L (a quarter).
   - `expected_impact` is High, Medium, Low or Unknown, with a one-line reason. Give no conversion numbers; none were measured.

6. **Write `audit.md` as narrative, not a matrix.** Sections in this order:
   1. Scope and live URL: the URL and its derivation, viewports, request rate, pages covered, compliance framing.
   2. Headline findings: the top five rows in CSV order, each with one caveat (for example, "may be pre-launch; every product is also out of stock").
   3. Per-page notes: a small table of page, mobile, desktop and the points that surprised you.
   4. What is working: a short list, so the reader can see nothing was cherry-picked.
   5. Method and limits: what was tested, what was not, and when the snapshot was taken.
   6. Screenshots: a table of rank to file for the top five.
   7. A one-line pointer to `backlog.csv`. Do not duplicate the table.

7. **Open one draft PR.** One issue, one branch, one commit, one draft. Use a conventional docs message such as `docs(research): CRO baseline audit - mobile and desktop ranked backlog`. The PR body gives the top three findings in one line each, the scope and safety notes (read-only, request rate, gates left in place, what was not clicked), the URL derivation with a request that the operator confirm it, and a line stating the diff is docs-only so the build was skipped on purpose. Do not merge.

8. **Run the sign-off checks.**
   - The CSV has N ranked rows, and every row has non-empty evidence.
   - Every evidence URL was probed in this session, and its status and captured text are in `data/` or the PR body.
   - Screenshots exist for the top five, named with slug and viewport.
   - For a regulated store, a keyword scan of `audit.md` and `backlog.csv` returns zero hits on the banned-claim list.

### Deliverable layout

```
docs/research/<slug>/
├── audit.md
├── backlog.csv          # columns: rank, page, issue, evidence, fix, effort, expected_impact
├── data/                # captured text per page per viewport
└── screenshots/         # named <issue-slug>-<page>-<viewport>.png
```

## Pitfalls
- **The repo rarely names the live host.** An inferred URL is fine when the derivation is stated. A bare "the URL is X" with no provenance is the first thing a reviewer checks.
- **Structured data beats card text for stock.** If a card says "Sizes" but the product page's JSON-LD offer is OutOfStock, the offer wins. Cite the JSON-LD path in the evidence cell.
- **A uniform dead end is one finding.** When every card leads to an out-of-stock page, say that shoppers reach a dead end. Do not estimate the conversion loss.
- **A header count that ignores filters is its own finding.** If a filtered category shows 7 cards under a header that says 48, note the mismatch in the per-page table.
- **All-pending states depend on launch timing.** "Every certificate is pending" is high impact in steady state and little impact on launch day. State the caveat next to the rank.
- **Never hand-count large sets.** Counts above about ten come from a parse or regex over the captured text, not from reading the page.
- **Self-descriptive numbers drift.** Derive every number in `audit.md` (row counts, screenshot counts, byte totals) from the files before writing it.
- **A gated screenshot is not the page layout.** A capture of a blocking gate shows what a visitor sees at the gate. Say so in the filename and in the audit.
- **One issue, one PR.** A second batch of issues is a new audit with its own branch and draft.

## Verification
- Parse `backlog.csv` with any CSV reader: expect N data rows and N non-empty `evidence` cells.
- Re-fetch one evidence URL and confirm the saved JSON in `data/` shows the text the row cites.
- Open the top screenshot and confirm its filename matches the rank row.
- For a regulated store, run the keyword scan on `audit.md` and `backlog.csv` and expect zero hits.
