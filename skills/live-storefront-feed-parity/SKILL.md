---
name: live-storefront-feed-parity
description: Use when checking live feeds and structured data. Read-only, re-runnable, with a self-test.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [ecommerce, feed, json-ld, parity, structured-data, audit, markdown]
    category: commerce
related_skills: [catalog-data-audit, cro-baseline-audit, storefront-code-audit]
---

# Live Storefront Feed Parity

## Overview

A product record is often published in several places: two feeds, the rendered page, structured data embedded in the page, social-share metadata and a markdown copy for agents. Each copy can drift. A page can show one price while a feed says another, and a structured-data check can pass while the markdown says something else. This skill compares every public surface that carries the same product record, field by field and SKU by SKU, and reports each disagreement. It also checks that the structured data carries the fields that shopping agents and merchant listings need. The check is passive and read-only.

## When to Use

- Checking whether a deploy moved a feed or page away from the others.
- Asked whether the shopper's price, availability and image match what the feed or an agent reads.
- Asked to build a parity checker that runs again after each deploy, with a snapshot report.

Skip it for source-data consistency, such as titles, SKUs and categories inside the repository (use catalog-data-audit). Skip UX and conversion reviews.

## Features

- Sitemap-driven product list, cross-checked against paginated store listings and product sub-sitemaps.
- Four comparison levels: feed to feed, feeds to rendered page, feeds to structured data, and everything to the markdown copy.
- Per-SKU rows for price and availability, and per-product rows for names, images and canonical links.
- Fan-out image checks, so each surface is tested against the feed separately.
- Structured-data readiness checks: exactly one product node, a GTIN where the catalog has one, a currency, an availability URL, an absolute image and a description.
- A selftest against a local fake site with known defects, to prove the checker still catches them.

## Benefits

- The first disagreement is found and named, not discovered by a customer or a merchant feed rejection.
- Every mismatch row names both the first value and the value it was compared with.
- A zero-mismatch check is listed too, so the reader can see what was actually compared.
- The checker is a regression test: the same run after a deploy shows any new drift.

## Procedure

1. **Confirm the host and the surfaces before any check.** Request the two feeds, `products.json` and a catalog feed, and expect 200 with a JSON content type. A host returning HTML on the feed path is a different site. State any inference about which host is meant in the report's first paragraph, and ask the owner to confirm it.

   ```bash
   curl -sI "https://<storefront-host>/products.json"
   curl -sI "https://<storefront-host>/feeds/catalog.json"
   ```

2. **Build the product list from the sitemap.** Read the sitemap, then count product URLs. Check `robots.txt` for every `Sitemap:` line, since product URLs are often only in a sub-sitemap. Cross-check the sitemap list against the paginated store listing. Any URL in one list and not the other is a discovery finding.

3. **Check for a markdown copy of each product.** Request `<product-url>.md` and expect 200 with `text/markdown`. A product with no markdown copy is skipped for the markdown rows and noted in the report. A 200 with HTML content is a separate failure, not a pass.

4. **Read without running scripts or submitting forms.** Use GET requests only. Do not log in, pass an age gate, accept a consent banner, add to a cart or sign up. Read the page HTML as a non-rendering crawler would. If the data only appears after client-side code runs, record that as a finding in its own right.

5. **Throttle to two requests per second or fewer.** Wait at least 550 ms between request starts, across all hosts. Retry a failed request twice with backoff, and count every attempt. Report the total count, the average rate and the highest count in any one-second window.

6. **Compare feed A with feed B first.** For every handle, assert that the two feeds agree on title, SKU set, price per SKU, availability per SKU and main image. A disagreement is its own finding, `FEED_A_VS_FEED_B`. Do not propose a page fix when the feeds disagree, because the page is only one render of them.

7. **Then compare each feed with the rendered page.**
   - The page's `og:image` and `twitter:image` match the feed's main image.
   - The canonical link and `og:url` match the feed's URL.
   - The `<h1>` matches the feed's title.
   - The visible price matches the feed's price for the active size.
   - An out-of-stock message appears only when the feed says every size is unavailable.

8. **Then compare each feed with the structured data in the page.**
   - The product name, URL and description match the feed.
   - The first image matches the feed's main image, and the list of images includes it.
   - The offer SKUs match the feed's SKU set.
   - Each offer's price, currency and availability match the feed for that SKU.

9. **Finally compare everything with the markdown copy.** The title, the canonical line, the SKU table, the per-row price and the description must match the feed. The alternate-link header, if present, must point at the feed's URL with `.md` appended.

10. **Use the right comparison family for each check.**

    | Family | What is compared | Row granularity |
    |---|---|---|
    | coverage | handle present in sitemap and both feeds; counts match; SKU sets match | product |
    | canonical | sitemap URL, feed URL, final page URL, canonical link, `og:url`, structured-data URL, markdown canonical line all agree; page is not `noindex` | product |
    | name | feed title, second feed name, structured-data name, `<h1>`, markdown H1 all agree | product, SKU for size names |
    | price | per SKU: both feeds, structured-data offer price and currency, markdown price table agree; the visible price is one of the feed prices | SKU |
    | availability | per SKU: both feeds and the offer availability agree; product level is in stock when any size is | SKU |
    | image | each surface compared with the feed's main image separately | product |
    | structured data | exactly one product node; required fields present; offer SKUs match the feed | product, SKU |
    | markdown | 200 with `text/markdown`; description and SKU table match the feed | product, SKU |

11. **Treat image checks as fan-out, not consensus.** Test each surface against the feed on its own: `og:image`, `twitter:image`, the first structured-data image, the membership of the image list, and feed A's first image against feed B. A page that uses the same wrong image in two places produces a separate row for each surface. The report shows which surface the page actually agrees with.

12. **Treat a shortened title as information, not a failure.** A page title that is a shortened form of the full name is reported as INFO when the full name is in the `<h1>` and in the structured data. Any other difference is a MISMATCH.

13. **Read structured data fully.** Parse every JSON-LD block. A block may hold one object, a list, or an object with a graph key. Normalise all three before searching for product nodes. Expect exactly one product node per page.

14. **Join split page data before matching.** Some frameworks split one payload across many script tags. Join the pieces into one string before running a pattern on it. A zero-match on a page that visibly shows the value is a sign of a split payload, not of a missing value.

15. **Check structured-data readiness.** For each product, record these checks as PASS or FAIL:
    - Exactly one product node.
    - A name, and a brand with a name.
    - A GTIN (`gtin`, `gtin8`, `gtin12`, `gtin13` or `gtin14`) on the product or on every offer.
    - A SKU on the product or on every offer.
    - Every offer has a numeric price above zero, and a three-letter uppercase currency code.
    - Every offer has a schema.org availability URL.
    - At least one absolute HTTPS image that answers 200 or 206 with an image content type.
    - A canonical link that is an absolute HTTPS URL matching the page URL.
    - A description between 50 and 5000 characters. This length window is the auditor's heuristic for shopping agents, not a schema.org rule, and the report must say so.

    Cite schema.org's Product and Offer definitions for the field checks. Cite the search engine's product-snippet guidance when the target is a merchant listing, since it requires a currency.

16. **Write one CSV row per finding.** Columns, in this order: `severity` (MISMATCH or INFO), `handle`, `area`, `check` (with `[SKU]` for per-SKU rows), `expected_source`, `expected`, `actual_source`, `actual`, `note`. Every row needs both sources named. A row without them is an unsupported finding.

17. **Write the report.** Include, in this order: the run window in UTC, the request count, the average rate and the peak per second; a one-line result per family; a table of every check with its comparison count and mismatch count, including the zero-mismatch checks; every MISMATCH row, truncated to about 80 characters per value; a per-product status table with the HTTP codes; and the limits of the audit. Derive every number from the checker's output, not from memory.

18. **Run the selftest before trusting the checker.** Serve one clean product and one product with known defects from a local fake site: a wrong structured-data price, a wrong availability, two `<h1>` tags, a missing canonical, a mismatched `og:image`, a missing structured-data description and a missing markdown copy. Bind to the loopback address only. The clean product must produce zero mismatches, and each injected defect must be reported on its own product.

## Pitfalls

- **Two feeds is the usual case, not the exception.** Many storefronts publish two feeds. Always compare them before comparing either with the page.
- **Per-SKU, not per-product.** A single size with a wrong price is one per-SKU row. The product-level count hides which size is wrong.
- **Split payloads produce false mismatches.** Join the pieces before matching, or the price will look missing on products whose data crosses a boundary.
- **Image checks need fan-out.** One wrong image on one surface produces several rows, which is correct. The reader needs to see which surface agrees.
- **Shortened titles are not defects.** Report them as INFO when the full name is elsewhere on the page.
- **A markdown copy that returns HTML is a failure.** A 200 response is not a pass unless the content type is markdown.
- **A 403 is a finding.** Record it as a bot wall or a blocked page, fail the fields on that page, and do not change the client identity to get past it.
- **An all-out-of-stock catalog is valid markup.** Report it as an observation to confirm, such as a pre-launch state, not as a field failure.
- **One large image shared by many products is a flag.** When many products use the same stock image, mark it as a flag. Do not fail the image field unless the rule for distinct images is written down.
- **An aggregate offer collapses several offers.** A single offer with a group of prices can hide per-size rules. Record the offer count so the shape is visible.
- **A zero-offer product is a different failure from a missing price.** Report a product with no offers as missing offers, separately.
- **Discovery gaps hide products.** A crawler that reads only the main sitemap misses products listed in a sub-sitemap.
- **Snapshots go stale.** Stock, prices and images change between runs. State the run window in every report.
- **Dedupe against earlier audits.** List earlier reports on the same topic and what this checker does about each one, so the reader knows what was already covered.
- **Keep credentials and private hosts out of the published report.** Use placeholders for any internal host, and check the published files for them before sharing.

## Verification

- Each CSV row has all nine columns filled, with both sources named.
- Running the checker a second time from a clean output folder gives the same per-family counts that the report cites.
- The selftest exits with status 0: the clean product has zero mismatches, and every injected defect is reported.
- The discovery check shows no URLs that are in one product list and missing from the other.
- The equality-check table lists every comparison with its count and mismatch count, including the zero-mismatch checks.
- A random sample of three product URLs, re-fetched by hand, matches the values in the report.

## Attribution

Product and offer fields follow the schema.org definitions (https://schema.org/Product and https://schema.org/Offer).
