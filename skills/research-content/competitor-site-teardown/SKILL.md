---
name: competitor-site-teardown
description: Use when comparing competitor storefronts by feature. Every cell cites a fetched URL or says UNKNOWN; output is a draft PR.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [research, competitors, teardown, ecommerce, matrix, citations]
    category: research-content
related_skills: [ai-search-question-bank, official-source-claim-factcheck, storefront-copy-drafts]
---

# Competitor Site Teardown (Cited Matrix, Draft PR)

## Overview
A teardown compares several competitor stores on the same fields: offers, bundles, certificate or test-report surfacing, trust signals, reviews, educational depth and capture forms. Every cell holds either a fact with the URL it came from, or the word UNKNOWN with the URLs that were checked. Claims the store makes about itself are reported as claims, not as verified facts. The output is a matrix, a report and a draft PR.

## When to Use
- You need to know what competitor stores actually do, and the answer must survive review.
- You are asked to compare your own store with several others on a fixed set of fields.
- The deliverable is a cited matrix and a short report, opened as a draft.

Skip when the question is about a single page's wording (use `storefront-copy-drafts`) or about answer-engine presence (use `ai-search-question-bank`).

## Features
- A selection rule and an exclusion log, written before any page is read.
- A cached, rate-limited fetcher that logs every request, and that serves as the evidence appendix.
- Field extraction from page source, not from visible text alone.
- A build script that generates the report and the matrix from one dataset, and asserts the citation rules.
- A baseline check against your own repository, when the question is "versus us".

## Benefits
- A reviewer can redo the selection, the fetches and every count.
- Gated or hidden features are reported as limits, not as absence.
- Brand claims and observed data stay separate.
- Matrices from several teardowns use the same columns, so they can be compared over time.

## Procedure

1. **Find earlier teardowns and match their columns.** Search the repository and open pull requests for an earlier teardown folder. If one exists, use its field list. If none exists, write the field list you used in the report.

2. **State the selection rule before fetching.** Pick a public, citable signal for the candidate pool, such as a domain popularity rank. Keep only stores that sell the category on a product page a visitor can buy. Record the candidate pool and every exclusion with its reason. A reviewer who disagrees with the selection needs that table to redo it.

3. **Build a cached fetcher.** Write one file with a per-host throttle of at least 0.6 seconds between requests, a disk cache keyed by URL, and a log line for every request: requested URL, final URL, status, bytes and timestamp. Follow redirects explicitly. Send a descriptive User-Agent that names the audit and says it is read-only. Make plain GET requests only, with no cookies, logins, forms, clicks or carts, and never apply a discount code you see in the HTML.

4. **Fetch the pages for each store.** Read `robots.txt` and the sitemap index, then each child sitemap. Skip every path that robots.txt disallows, and record each skipped path as a coverage limit. Count URLs by path prefix (product, article, certificate, location). Then fetch the homepage, the navigation links that match the fields you are checking, one representative product page, the certificate hub, one certificate page, one bundle or category page, one educational page, and the footer.

5. **Extract signals from page source.** Visible text can be hidden, cached or absent for guests; the page markup is not. Look for:
   - Review platforms by their script URLs and class-name prefixes, and structured rating data.
   - Email capture by the platform's script, its form ids, and any newsletter endpoint.
   - The shop platform by its asset paths.
   - Certificate detail by lot or batch identifiers, test dates and lab names in the product text, plus counts on the hub page.
   - Volume pricing from the variation data and tier text.
   - Gating by login-to-see-price text, application forms and age modals.

   Identify third-party platforms by source fingerprints. A loader script with no visible widget is not a working integration. A form for a stock alert is not a newsletter.

6. **Sanity-check counts.** A sitemap URL count does not equal an article count unless the page says so. When a store's own numbers disagree across pages, report the disagreement; do not reconcile it.

7. **Keep cells in one dataset.** Hold the cells in one Python structure: each store has a field name mapped to a text value and a list of source URLs. Generate `matrix.csv` and `report.md` from that structure in one build script. The script must assert that every cell is filled or marked UNKNOWN, that every cited URL appears in the fetch log, and that every field is present. Put UNKNOWN follow-ups in their own section, before the baseline and the tactics.

8. **Compute every derived number in the script.** Counts, medians and ranges come from the dataset, with one assertion per derived claim in the report. A hand-typed count next to a matrix with a different count is the error that survives draft review.

9. **Check each cited URL once more.** Request each cited URL a second time. Record a 404 as evidence (a missing product feed endpoint can show a custom storefront). Record a 403 as a bot wall or a block, not as a dead link.

10. **Open a draft PR.** Add only the topic folder: the report, the matrix and the fetch log, on a new branch from the default branch. Never merge. Post a short status note to whoever requested the teardown, with what shipped, the PR link, the gaps for reviewers, and the per-host rate you used.

### Report layout

Scope and method (with the request count and the measured request rate), store selection and exclusions, a one-page summary matrix, a table per store (field, finding, sources), cross-store patterns, the UNKNOWN list, your own baseline with repository paths (only when the question is "versus us"), ranked tactics last. Date-stamp the snapshot in the first paragraph, because storefronts change.

Ranked tactics come last. Rank each one by how many competitors do it, by its effect on conversion or trust, and by how little you already have. Check what you already ship before you call something a gap: search your repository at the default branch. A gap that is a deliberate choice is reported as deliberate, not as a backlog item.

## Pitfalls
- **Do not work around bot walls.** A challenge page or a 403 from a managed fetcher is a limit of the audit. Record the store as excluded with the reason, and let the reviewer decide. Do not change headers or user agents to get past it.
- **Page source can expose third-party keys.** Keep key-shaped strings out of files and out of output. Truncate long attribute dumps before you print them.
- **The first regex hit is not the answer.** Confirm a match in the page markup or in its specific section. Re-fetch category pages that load empty for anonymous visitors before calling them populated.
- **Mixed catalogs need a scope note.** A store that sells several product types stays in scope only for the side that matches your category. Say so in a scope note for that store.
- **Discount codes are observations.** A code you see in the HTML is evidence. Cite it as "observed in HTML", and never run it through a cart.
- **Popularity ranks are not sales.** Do not claim one store has more revenue than another from a rank.
- **Brand-asserted numbers are claims.** "Four stars from two hundred thousand customers" is a claim the store makes. A rating next to a product is observed data. Quote them separately.
- **Absence is limited to the pages you fetched.** "Not observed" means absent from the pages you read. List those pages; do not write a sweeping "no".
- **Review gating is not an absence of reviews.** When a store shows zero reviews with a notice that only verified buyers may post, mark the cell as gated and quote the notice. Different review totals on the homepage and the product page are different aggregation scopes. Name the scope in each cell.
- **Subscription intervals stay in the store's own words.** Record "every two months" as written. Put any normalised form in a derived column, because two months is not six weeks.
- **A repository search needs its term stated.** When you search your own code for a construct, report the exact term and what its neighbours matched. A zero-hit search on a narrow term can miss the construct.
- **Self-described numbers are derived from logs.** Compute elapsed time, request counts and file counts from the fetch log in the build script. Do not write them from memory.
- **Collapse host variants before you compare counts.** The `www` and apex forms and the protocol variants are one host for the per-host count, or the log and the matrix will appear to disagree.

## Verification
- Every cell in `matrix.csv` is either a fact with at least one cited URL, or `UNKNOWN` with a reason.
- Every cited URL appears in `fetch-log.csv`.
- The build script's assertions pass, and the report's counts match the dataset.
- The request rate in the report matches the throttle the fetcher enforced, as read from the log.
- The draft PR adds only the topic folder, and `isDraft` is true.
