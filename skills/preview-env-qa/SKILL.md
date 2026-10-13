---
name: preview-env-qa
description: Use when running a QA matrix on a preview storefront. Playwright runner, JSON evidence, generated report.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [qa, testing, playwright, evidence, preview-environments]
    category: web-quality
related_skills: [browser-smoke, medusa-api-verification, regulated-commerce-compliance-gates, storefront-visual-acceptance, storefront-accessibility-audit]
---

# Preview Environment QA Matrix (Playwright, JSON Evidence)

## Overview
A QA run against a preview or staging build treats the work as data: a matrix of buyer states by routes, run by one Playwright script that writes one machine-readable result file. Human-readable reports are generated from that file, so they cannot drift from it. The run reports defects and never fixes the code under test. Every cell records what was observed, and every expectation is set per state and route.

## When to Use
- You need a repeatable QA matrix (several buyer states times several routes) against a preview build.
- The evidence must be machine-readable, so a later run can diff it against this one.
- A reviewer needs screenshots, console errors and a defect list with the state, route, code and evidence for each item.
- The preview is gated (age, region, account) and the gates themselves need checking.

Skip when you only need one happy-path check (use `browser-smoke`).

## Features
- One JSON result file as the single source of truth, with Markdown and HTML indexes generated from it.
- A state-by-route matrix that records HTTP status, redirect target, final path, surface, price-string count and product-link count per cell.
- Price and PII leak counts measured on rendered text, with expectations set per state.
- UI gate and backend gate both checked, so a visible gate cannot hide an open API.
- Checks for text that only shows in screenshots, using OCR.
- Secret-shaped and PII-shaped scans before anything is shared.

## Benefits
- Runs stay comparable across builds because the result shape is fixed.
- A "blocked" result caused by a failed login is separated from a real defect.
- Each defect arrives with the state, route, code, detail and evidence needed to fix it.
- Report-only runs leave the product tree untouched, and a timestamp check proves it.
- Evidence can be handed off without leaking credentials or customer data.

## Procedure

1. **Ground the build.** Confirm the preview returns 200 on each route you will test. If the build exposes a version endpoint, record `commit_sha` and `build_timestamp` at run time. If it does not, grep the commit SHA in the served homepage HTML, and record `sha_in_html: false` as a finding rather than a runner error. A report stamped with a commit the deploy does not contain blames every defect on the wrong build.

2. **Check the served build for a local preview.** Before sending any link to a reviewer, run these checks in the same turn:
   - `lsof -nP -iTCP:<port> -sTCP:LISTEN` to record the listening PID (the same port check the storefront preview gate uses).
   - `lsof -p <pid> | grep cwd` to confirm the working directory is the worktree you claim.
   - `curl` the exact route the reviewer will open, and grep the HTML for the strings your change should produce. HTTP 200 alone is not proof.
   Then quote one matching snippet per route when you report the link. After a process-exit notice, repeat the port check before saying the preview is still up.

3. **Choose at most three lanes.** Use a visual and UX lane (browser), a static code lane (read-only repository review), and a backend data lane (API probes). Give each lane its constraints in its own instructions: no edits, no merge, no redeploy, and "if a file is missing, say so." A lane that does not see the parent constraints will edit files.

4. **Model the matrix.** Use buyer states (for example `logged_out`, `unlicensed`, `approved`, or the product's own tiers) by routes (home, listing, product, cart, checkout). Record these fields per cell: `http_first`, `location_first` (redirect target), `final_path`, `surface` (from a fixed set such as Login, Catalog, Product, Cart, Checkout, NotFound), `price_string_count` and `products_href_count`.

5. **Write one runner.** Use a single Python script that imports only the standard library and Playwright. Model the run as data, one row per cell, not as narrated clicks. Create a fresh browser context for each cell so console counts are comparable. Wrap the run in try/except and always write the result file, with partial cells flagged so a rerun can update only what failed. Compute verdicts from the result object, not from variables that exist only inside the browser block. Reuse an existing runner for the same build when one exists, after reading it in full to confirm it covers the matrix.

6. **Load credentials from the environment only.** Pass test credentials through a secret manager's run wrapper or the environment. Never put them on the command line, in the script, or in any output. Record only metadata in results: the length, a short prefix and the domain kind. Never write a full login address.

7. **Set expectations per cell.** Some cells should show leaks and others should not. For example, a buyer approved for wholesale prices should see those prices on catalog and product pages, so label those cells "allowed for approved" and leave them out of the fail count. The same prices on signed-out or unlicensed views are failures. Encode expectations per (state, route), never as one global zero.

8. **Generate the reports from the result file.** `RESULT.md` and any `index.md` come from `RESULT.json` through a script. A hand-written report that differs from the JSON is a second source of truth.

9. **Check before sharing.** Grep the result files and the screenshot inventory for token-shaped strings (`pk_` followed by 20 or more word characters, `Bearer` followed by a token) and for full email addresses. OCR every screenshot for addresses (see Pitfalls). Patterns that match only variable names in prose are false positives: narrow the pattern with value-shaped quantifiers rather than editing the prose.

10. **Hand off.** The top-level `verdict` is PASS only when every cell met its expectation and there was no leak. Each defect carries `{state, route, code, detail, fix_lane}`. Rename stale partial results with their modification time in the name rather than deleting them, because they show that an earlier attempt failed partway.

### Backend gate probe (no browser)

With a storefront publishable key, run these requests in order and record each status:
1. `POST /store/carts`
2. `POST /store/carts/:id/line-items` with an item that needs an eligibility check, and no proof of eligibility
3. `POST /store/carts/:id` with a blocked region on the address
4. `POST /store/shipping-options?cart_id=` (expect no options for a blocked region)
5. `POST /store/payment-collections` (expect a refusal until the gates pass)
6. `POST /store/carts/:id/complete` (expect a refusal)

If step 6 succeeds without the gates passing, report a critical defect. Run step 4 once per product class, because a gate can work for one class and fail for another.

### Persona runs

Run each persona in a fresh browser session with cleared cookies:

| Persona | Path | Expected |
|---|---|---|
| First visit | Home, listing, product, cart, checkout | Gate shown before any restricted catalog |
| Ineligible user | Product, add to cart, direct checkout | Hard block; no payment step |
| Eligible, allowed region | Search, product, switch variant, add, checkout, address, shipping | Shipping options exist; the eligibility step appears; stop there |
| Eligible, blocked region | Same path, blocked address | Clear "cannot ship" message; cart cannot be completed |
| Address flip | Allowed, then blocked, then allowed | Gate state refreshes; totals update; no stale cache |
| Variant integrity | Open several multi-option products and switch every option | Photo, price and attributes change with the selected option |

Take a console check and a screenshot after every navigation and after every address change.

## Pitfalls
- **A UI gate the API ignores is a critical defect.** Prove both layers. A modal or cookie check alone shows nothing about what the server accepts.
- **Gate clicks are allowed only on your own preview, and only as a visitor would make them.** The runner may click the visible age-gate or consent confirm control, once per fresh context, when that control sits outside any form. Record `gate: absent|dismissed|still-shown` for the cell. Do not preset stored gate choices, do not hide gate elements with CSS, and never click on a third-party site. A state picker, a login form, or any control inside a form stays unclicked; record the gate as the state of that cell and name the coverage limit.
- **Untested buyer states are not passes.** If no test account exists for a buyer state, mark that state blocked in the report. Do not run it as a guest and count the result as a pass.
- **A raw GET can be 404 by design.** A checkout route that is reachable only inside the flow returns 404 on a direct request. Record both the raw status and the in-flow status, so a reader does not mistake it for a defect.
- **An in-flow cell has no first-hop status.** Record `200 in-flow` with the final path, not null.
- **Count prices on rendered text.** Framework payloads and product titles can contain `$` tokens that are not prices. If you must scan raw HTML, strip script blocks first and match value-shaped prices only, such as `$12.34` or `$1,234`.
- **Save console text, not only counts.** Keep the first line of each error. A count cannot tell one repeated content-security-policy error from twenty unrelated errors.
- **Console counts depend on context reuse.** A context shared across cells accumulates errors, so a later cell looks worse than it is. Use a fresh context per cell, or label cumulative counts as cumulative.
- **Classify cart state from UI signals, not the word "empty".** A cart holding items can still show an "Empty cart" button. Before adding a test item, clear the cart, record the cleared state and cap the accepted total, so a failed clear fails the run instead of buying the wrong items.
- **Use QA-reserved test products.** Test add-to-cart calls must use reserved test handles, never live inventory.
- **A content-security-policy source with a query string is silently ignored.** Record that as an upstream defect. Do not patch the policy in the QA lane.
- **A runner bug is not a site bug.** If the runner's classifier produced a false FAIL, fix the runner, correct the affected cells with a note saying so, and do not rerun the whole matrix to regenerate numbers the site already answered.
- **Filter NaN before min or max logic.** Geometry checks that take a span across elements turn into NaN when one coordinate is missing. Filter non-finite values first.
- **Match surface headings case-insensitively.** CSS uppercase transforms show up in the rendered text, so a case-sensitive match reports a correct page as a failure.
- **A capture under a broken deploy is one defect, not a matrix of them.** HTTP 200 with an empty body and a client error such as "connection closed" from a shared script bundle means the deploy is broken. Report it once with the stack, the chunk name and the URL, and stop the matrix until the deploy is fixed.
- **Signed-out stills need the assumption stated.** Print the buyer state next to the punchlist (for example "guest session: Sign in expected in header") so a reader does not read the anonymous header as a defect.
- **Payment form checks need a verdict map.** Sample the payment area about every five seconds for about 25 seconds, and record the status text, the test ids present, the iframe count and source, and whether a failure message shows. PASS: the payment iframe is present and the expected prompt is visible. FAIL_LOUD: a visible failure message or failure test id appears, so the user is told. FAIL_STUCK: the form stays in a loading state across every sample with no iframe and no message. Treat a legacy failure sentinel that gives the user no reason as FAIL_STUCK.
- **Report-only means no writes.** Touch a sentinel file before the run, then check that `find <product-tree> -newer <sentinel>` prints nothing. Record the empty output in the result log.
- **Video heroes need a painted frame.** Browsers block autoplay by default, so a screenshot can show a black frame or the poster. Allow autoplay for the test, wait until the video has data and has played past a threshold, then capture. Take every crop from the same full-resolution screenshot, so all crops share one frame.
- **Redact screenshots, not just HTML.** Run OCR over every PNG and flag addresses. Match on the `@` and the domain fragment, because OCR often splits one address across word boxes. Require a PII-shaped match before redacting, because prices and glyphs are misread as `@`. Draw dark boxes over matched word boxes, keep the originals in a backup folder outside the deliverable, and re-run OCR to confirm zero matches. Filter the OCR output itself before it goes into logs or chat, because an unfiltered text dump leaks the address.
- **Do not make deliverable screenshots read-only.** A read-only file breaks the next legitimate overwrite. Keep a separate snapshot folder for finished captures, and confirm sizes and OCR text in a fresh call before handoff.
- **Two sessions can write the same drop folder.** If another session rewrites your artifacts, move your run to a run-specific subfolder and report the conflict instead of fighting over bytes.
- **Verify without a vision model when none is available.** Use OCR with targeted checks: a count for each required label, an absence pattern for each known defect string, and an address scan that must return zero. Record `verified_via: ocr` in the result, so a reader knows the check was text-level, not pixel-level.

## Verification
- The result file validates, and every cell has all required fields or an explicit partial flag.
- `RESULT.md` and the index were regenerated from the current `RESULT.json`, and their counts match it.
- Each FAIL cell has a defect entry with state, route, code, detail and evidence.
- The secret-shaped grep and the OCR address scan both return zero hits before any file is shared.
- The report-only sentinel check prints nothing.

## Attribution

The three-lane QA pattern and the consolidated report layout are adapted from the Eidolon project, a public project by the same publisher. The Store API routes in the backend gate probe are Medusa v2 Store API routes.
