---
name: catalog-data-audit
description: Use when auditing a storefront catalog for drift. Produces a per-row CSV of defects and a named-rule report, without changing live data.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [catalog, audit, data-quality, naming, ecommerce]
    category: commerce
related_skills: [cro-baseline-audit, data-artifact-adversarial-review, regulated-catalog-content, git-remote-hygiene]
---

# Catalog Data Audit (Files Only)

## Overview

A read-only audit of a storefront catalog. It compares the data of record in the repo with the public feed and the shopper-facing pages, then lists every row that breaks a named rule for naming, SKUs, sizes, categories, prices, media or copy. The deliverable is evidence for an owner to decide on. The audit changes no SKU, price, category, setting or order.

## When to Use

- Titles, SKUs or categories need a consistency review before a launch, migration or feed change.
- The spreadsheet or source JSON and the live feed disagree, and the drift must be listed row by row.
- A files-only pull request with a CSV of catalog defects is the requested output.

Skip it for UX or conversion reviews, for reviewing a CSV someone else produced (use data-artifact-adversarial-review), and for building a new prospect list.

## Features

- Confirms the live host and the data-of-record file before any rule runs.
- Joins the repo catalog to the public feed and asserts that every field both expose agrees.
- Applies named rule codes (R1 to R7 plus SKU, size, category, price, image and data codes) that a script can re-run and count.
- Writes a six-column CSV where every row cites the repo path or live URL that proves it.
- Generates the CSV and the per-code counts from one regenerator script, so no row is typed by hand.

## Benefits

- Every finding can be reproduced: a reviewer re-runs the script and gets the same counts.
- Proposals and flags stay separate from changes, so nothing ships by accident.
- Pre-launch states and bot-wall failures are labelled, so they are not counted as defects.
- Stock-sync and sitemap risks are named before anyone renames a SKU or moves a category.

## Procedure

1. Confirm the live host from the repo's published config (site metadata, redirects, proof or launch notes), not from memory. Request the feed and expect 200. State any inference in the report's first paragraph.

   ```bash
   curl -sI "https://<storefront-host>/feeds/catalog.json"
   ```

2. Identify the data of record. Many repos ship two copies of the catalog JSON: a source copy and a build-time copy. Diff them and record the SHA of the copy you used. The diff is itself a sanity check.

   ```bash
   diff -q "<source-dir>/catalog.json" "<storefront-dir>/catalog.json"
   ```

3. For a regulated catalog, find the repo's claim test and any mandated footer. Keep mandated text verbatim. Do not introduce claim terms that the banned-claims list covers into the audit's prose or the proposed values.

4. Clone the repo as a blobless sparse checkout. A full clone of a large storefront can exceed a 180-second foreground timeout.

   ```bash
   git clone --filter=blob:none --no-checkout https://github.com/<owner>/<repo>.git
   cd <repo>
   git sparse-checkout init --cone
   git sparse-checkout set <data-dir> <scripts-dir> <lib-dir>
   git checkout main
   ```

5. Read every file that establishes catalog identity: both JSON copies, any CSV sheet, the build script, the seed script that assigns categories and images, and any sidecar copy. Reading is the only operation on the repo.

6. Keep live access to GET requests at 1.5 per second or fewer. Fetch the feed, product pages and image files only. Never submit a form, log in, pass an age gate, or call an admin API. Record a 403 as "bot wall or rate limit, not a defect", not as a finding.

7. Join repo to live before writing any rule. For handle, title, SKU, size and price, assert that repo equals feed. A mismatch becomes its own row, class `DATA_REPO_VS_LIVE_DRIFT`. Do not propose SKU, title or category changes for a field where repo and live disagree.

8. Express every finding as a named code, not a free-text reason. The script re-applies each code, and the report counts them. The codes used in this audit:
   - `R1` formula, code or sequence string inside a title (a long identifier string belongs in the spec block)
   - `R2` title longer than the cap (for example 60 characters)
   - `R3` non-ASCII punctuation such as dashes or smart quotes
   - `R4` parenthetical that expands an abbreviation, not a code or an alternate name
   - `R5` category name or boilerplate phrase inside a title
   - `R6` title does not lead with the house code that the handle and sheet use
   - `R7` title less specific than the item its description names
   - `CATEGORY_PLACEMENT`, `COA_MISSING`, `IMAGE_DUPLICATE`, `IMAGE_ALT`, `PRICE_PER_UNIT_OUTLIER`, `PRICE_TIER_SPREAD`, `SIZE_NOTATION`, `SKU_PATTERN`
   - `DATA_CSV_TITLE_DRIFT`, `DATA_STALE_COPY`, `DATA_NULL_PLACEHOLDER`, `DATA_MIXED_TYPE`, `DATA_FEED_VS_PAGE_CATEGORY`

9. Write `audit.csv` with six columns, in this order: `product`, `field`, `issue`, `current`, `proposed`, `source`. Truncate `current` to about 70 characters and `proposed` to about 60. Every cell in every column must be non-empty. `issue` is the code followed by one clause of reason. `source` is the repo path or the live URL that proves the row.

10. Gate every SKU rename. The script checks each proposed SKU against the full existing SKU set and refuses duplicates. A rename that needs an external stock or order map is written as `rename gated on <external SKU map>; no change made`.

11. Write the regenerator script (`build_audit.py`). It reads both JSON copies and the CSV, asserts they agree, reads a cached copy of the live feed, applies each rule, writes `audit.csv`, and prints per-code counts on one line. A reviewer re-runs `python3 build_audit.py --repo .` and must see the same counts the report cites.

12. Write `report.md` in this order: scope and live URL with the feed hash prefix; what was read; result at a glance (fields that agree, fields that disagree, clean checks with zero findings); the named rule definitions; issue counts per code with rows, distinct products and draft-only rows, all taken from the script; products that break the standard, grouped by code; risks and pre-mortem; limits of the audit.

13. Open one draft pull request from `origin/main` with one commit. Do not merge it. A second batch of issues is a new branch and a new pull request.

## Pitfalls

- **Storefront URLs are often missing from the repo.** Inferring one is fine when the inference and its derivation are stated, and the owner is asked to confirm it.
- **Publishable keys are often absent from the page source.** Many storefronts fetch on the server. When no key appears in the HTML or linked scripts, use the public feed as the anonymous read and say so in the first paragraph of the pull request body.
- **A key scoped to one project is rejected by another.** A `400 not_allowed` from one project means the key belongs to a different sales channel. Do not retry the key across endpoints; ask the owner for the correct key.
- **Two catalog copies can drift.** The reference copy is the record. A difference between the copies is a finding, not a reason to pick the more convenient one.
- **An empty field in the feed is not an empty field in the shop.** When the feed has no categories but the product page shows one, file a `DATA_FEED_VS_PAGE_CATEGORY` row. Do not count every product as uncategorised.
- **A stale sidecar copy is deleted or regenerated, not hand-edited.** Propose deletion or regeneration only. Writing replacement values by hand turns the audit into an editor.
- **A brand field that is empty on every row needs a recovery rule.** Name the rule in the report's method section (for example, matching the first variant SKU against a public brand listing) and label unmatched rows `(no brand listed)`.
- **Repeated images across products usually come from a hash or a fixed pool.** Name the mechanism in the report. The proposed fix is one product-specific image per product with real alt text.
- **Duplicate titles across variants are often intentional.** Option or size variants published as separate products with the same title are the usual cause. Say so, and leave the proposed value as `<owner decision; no rename proposed>`.
- **A price outlier is a flag, not a fix.** The proposed value is `no price change proposed; confirm against supplier data`. A number in that cell is a defect.
- **A SKU rename without the external stock map orphans stock and open orders.** Gate the rename and name the map the rename depends on.
- **A pre-launch "every item is N of N" finding needs its caveat.** "No certificates published" carries no impact before launch. State the caveat next to the count.
- **A finding concentrated in one regulated class is a policy question.** Split the count by class and ask the owner which document applies before calling the rest defects.
- **Carried-forward URLs go stale.** Re-probe every URL cited as found in an earlier run, and record the probe time next to it.
- **A setting that is off on purpose is not drift.** A stock-tracking flag disabled by decision is the default state. Say so in the report instead of dropping the check.
- **Every self-described number is derived.** Row counts, byte totals, request counts and hash prefixes come from the files and the script output, not from memory.

## Verification

- Every row of `audit.csv` has non-empty `product`, `field`, `issue`, `current`, `proposed` and `source`.
- Re-running the regenerator prints the same per-code counts that `report.md` cites.
- Repo and live agree on every field both expose. `DATA_REPO_VS_LIVE_DRIFT` has zero rows, or each row is listed with its source.
- No proposed SKU duplicates an existing SKU (`jq -r '.products[].variants[].sku' catalog.json | sort | uniq -d` prints nothing).
- For a regulated catalog, a keyword scan of `audit.csv`, `report.md` and the script returns zero hits on the banned-claims list.
- Re-fetching one `source` URL from the CSV still matches the recorded value.
