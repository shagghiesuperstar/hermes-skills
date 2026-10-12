---
name: regulated-catalog-content
description: Use when drafting buyer-facing content for a regulated online store (hemp-derived products, alcohol, prescription-adjacent, gambling, supplements or firearms) from its live catalog and a few fetched pages. Output is one draft pull request, never merged, with a compliance lint that must report zero hits.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [content, compliance, catalog, drafts, seo, regulated, marketing]
    category: commerce
related_skills: [medusa-admin-data-ops, catalog-data-audit, storefront-compliance-sweep]
---

# Regulated-Catalog Content Drafts

## Overview

Content for a regulated store is only useful if every claim in it can be traced to a live product record or a fetched page, and only if it passes the store's own claim rules. The work produces draft files in one pull request for a human to review. Nothing is merged or published by the drafting process. Numbers come from the live feed, not from memory. Rules that block a product class stop the work, and the drafter reports the conflict rather than working around it.

## When to Use

- Writing buyer-query articles, product FAQs, category introductions or sell sheets for a regulated catalog.
- Writing outreach or partner material for a regulated product class, which needs an explicit compliance check first.

Skip it for unregulated copy, which does not need the lint and gate steps below, and for copy that a human writes from scratch.

## Features

- Three pre-flight reads that gate every draft: the live host, the store's claim rules, and any standing prohibition on promoting the product class.
- Observed search queries only. Each target query records where and when it was observed.
- A single build script that generates every draft, so the shared facts cannot drift between files.
- Numeric claims checked against the live feed at build time.
- A compliance lint with a negative control, so the zero-hit result is known to mean something.
- A draft pull request that is read back to confirm it is a draft with the expected files.

## Benefits

- A reviewer can check every number and every link against the live data.
- The copy stays inside the store's claim rules, and the lint result is evidence the reviewer can rerun.
- A standing prohibition is found before writing, not after review.

## Procedure

### 1. Run the pre-flight reads

1. **Catalog host.** Request the store's published product feed. If it returns 200, that host is the snapshot source. If not, try the other published hostnames for the store and use the one that answers. Record the host. Use relative product links in drafts so they resolve on whichever host publishes.
2. **Claim rules.** Find the repository's claim test and its content rules. Load them. The claim test is the minimum. Add a stricter list of effect-style words that the test does not cover.
3. **Standing prohibitions.** Before drafting anything that promotes a product class, search the repository and its decision records for explicit prohibitions. Affiliate or referral programs, paid placement and loyalty-to-cash are common examples. If a rule blocks the work, stop, name the file and line that blocks it, and ask the owner to decide. Do not draft around it.

Do not start drafting until all three reads are complete.

### 2. Observe each target query

Each draft names a target query and the page where it was observed, in its front matter. Get queries from:

- Public search suggestion endpoints, recorded with the seed that returned each one. Keep the raw responses out of the pull request.
- Public forum threads that a search engine surfaces, read and cited with the date read.
- Rendered results pages, if the question asks for "people also ask" questions. Without a rendered page, mark that field as not captured. Do not invent questions.

A query that was not observed is a guess. Ask for an observed one, or observe one before drafting.

### 3. Build every draft from one script

Write one build script with one function for the shared front matter and one body function per article. Pass per-article facts through data structures. Use one campaign name and one naming rule for tracked links, so the links are uniform. When a new article is requested, add a function to the script. Do not hand-write a new file beside the generated ones.

### 4. Cite every number

- The build script reads the live feed, checks that each number it writes matches the feed, and then writes. If the feed says ten of ten are in stock, the article says ten of ten.
- Arithmetic such as price per milligram or per-serving estimates is labelled as arithmetic, with the assumption stated. It is never presented as a label claim.
- When a number the article needs is not published, write UNKNOWN and name the page that was checked.
- A bigger total in a bigger container is not a stronger single serving. State which figure is per container and which is per serving.

### 5. Lint before opening the pull request

Run a lint script over the rendered drafts. It must report zero hits before the pull request is opened. It checks:

- The front matter has the title, slug, status (draft), audience, target query, query source, catalog snapshot time and sources.
- The target query appears in the body.
- Every tracked link's content tag matches the file's slug.
- The minimum number of distinct products are linked.
- The body word count is inside the range the task names. Count the body only, after removing front matter.
- Every claim-test hit is classified as one of: a real claim to rewrite, a false positive in a mandated footer or catalog quote, or a false positive in data or a filename. Rewrite real claims. Do not change the mandated footer. Narrow a rule only with the owner's approval.

Run a negative control before trusting the result: insert one banned phrase into a copy of a draft, confirm the lint catches it, and discard the copy. Record that in the pull request.

Scan only the draft bodies. Do not scan the README, the build script or the data files.

### 6. Open one draft pull request

Branch from the base branch. Make one commit with a clear message. Push, and open the pull request as a draft. Read it back and confirm it is a draft with exactly the expected files. Do not merge it, and do not change the store.

### 7. Check the four done conditions

1. The number of drafts in the pull request matches the task.
2. Every claim cites live catalog data or a fetched page, and the snapshot time is in the body.
3. The lint reports zero hits, with the negative control recorded.
4. Each article names its target query in the front matter and in the body.

### Extensions

- **Category introductions.** Discover category pages from the product sitemap, not only from the navigation, because some sub-aisles are reachable only from a parent page. For each category, check that the page's canonical link points to the expected handle. Alias pages that canonicalise elsewhere produce duplicate copy, so publish only one of each pair. Keep a per-category build assertion: the page answers 200, the product count matches the copy, and every cited product appears on the page.
- **Sell sheets for the top brands.** Rank brands from the wholesale catalog, not from a smaller consumer catalog that shares name prefixes. Record the ranking method and the count of records behind it, and name the brands just outside the cut. Mark wholesale fields such as case pack and case price as UNKNOWN when the listing does not state them.
- **Per-product fields.** Generate one field value per live product only from product-level facts. Record a view basis for every value that describes a photo, and mark a view as unknown when the page does not state it.
- **Outreach and partner material.** Mark the material as "no send, draft only" on its first line. Leave every recipient-specific value in brackets, to be filled by a person from the recipient's own page. Name every unknown in the terms (tracking, payouts, tax forms, legal review of the disclosure, card-network rules) as UNKNOWN. Propose no vendor.

## Pitfalls

- **The public host and the feed host can differ.** Use whichever host answers for the path you need.
- **A wholesale catalog and a consumer catalog can share names.** Verify which catalog a ranking came from before publishing it.
- **A claim test is a floor, not a ceiling.** It misses many effect-style words. Use the stricter list too.
- **"We" and "us" read as brand statements.** Write in the third person about the store.
- **A lint scanning its own README or its script produces false hits.** Scan only draft bodies.
- **Synonyms chosen to avoid a lint hit hide the problem.** Fix a real claim. Classify a false positive, and narrow the rule only with approval.
- **Mandated disclaimers must appear verbatim.** Do not swap them to pass a lint. If the wording conflicts with a rule, report the conflict.
- **A status word in the header can match the lint.** Keep the front-matter status flag, which stops automatic import, and reword the header line.
- **Word counts include links and front matter.** Count the body only, the same way the lint does.
- **Over-generated Q&A.** Regenerate from the build script to the specified count, rather than editing a worker's output in place.
- **Docs-only pull requests have no build to catch wrong numbers.** The reviewer must check every number against the repository, not against the drafter's report.
- **A worktree needs its own commit identity.** Set it before the first commit, and use the store's configured author for content work.
- **Never print live credentials, payment keys or raw catalog exports into a pull request.**

## Verification

- The pull request is a draft, contains exactly the expected files, and has not been merged.
- The lint reports zero hits on the bodies, and the negative control was recorded.
- Every number in the bodies appears in the live feed or is labelled as arithmetic or UNKNOWN.
- Every target query was observed and is recorded with its source.
- No mandated disclaimer was altered, and no credential appears in the pull request.

### Reviewer Checks

A reviewer re-runs the lint, re-counts the body words, checks each numeric claim against the repository and the live feed, confirms every cited path exists at its exact name, and confirms that each category grouping matches the category map in the build script. The reviewer returns changes whenever one check fails.
