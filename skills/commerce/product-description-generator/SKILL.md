---
name: product-description-generator
description: Use when writing or improving product listing copy from specs, competitor pages or manufacturer and distributor sources, including batches of wholesale descriptions from a CSV. Every claim is cited, a two-pass voice audit runs, and facts that cannot be sourced become open questions.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [ecommerce, product-copy, listings, descriptions, wholesale, citations]
    category: commerce
related_skills: [regulated-catalog-content, catalog-publish-safety, catalog-image-sourcing]
---

# Product Description Generator

## Overview

Listing copy should sell only what the product actually is. This skill writes titles, bullets and descriptions for one product, for an existing listing, or for a batch of catalog rows. It writes from the specs the user supplies and from sources it can cite. Anything it cannot cite is left out and listed as an open question. Copy for regulated products also passes a voice audit that removes effect claims and unsupported superlatives.

## When to Use

- Writing a new listing from product specs, optionally with competitor pages.
- Improving an existing listing with a keyword gap check.
- Drafting descriptions for a batch of catalog rows, usually from a CSV, with a fixed word count per row.

Skip it for production writes to a store (use catalog-publish-safety) and for image work (use catalog-image-sourcing).

## Features

- Create and optimise modes for common marketplace and storefront formats, with each format's length limits.
- Keyword scoring from competitor titles and bullets, with tiers for title, bullets, description and backend terms.
- Benefit-led bullets with a feature, advantage, benefit and evidence structure.
- A two-pass audit: a first draft, then removal of unsupported claims and subjective language, then a word-count check.
- Batch output with a fixed row schema, the status set taken from the brief, and a questions file.

## Benefits

- Every fact in the copy traces to a source the reviewer can open.
- Competitor brand names never reach the output.
- Gaps and conflicts show up as questions, not as quiet edits to the copy.

## Procedure

### 1. Set the mode and collect inputs

- **Create:** product name, platform, brand, key features, specs, audience, use cases and tone. If the platform or specs are missing, ask before writing.
- **Optimise:** the current listing text or its URL, plus optional competitor URLs.
- **Batch:** the CSV, the row numbers in scope, and the brief's status words and output schema. Read the CSV header first. Confirm the row numbers, and check that no row is already covered by an earlier batch.

### 2. Gather facts with sources

- Fetch each competitor or manufacturer page, and extract the title, bullets, specs, price and brand. If a fetch fails, search for the product title with the site name, and use only snippets you can cite.
- Rank the references: the manufacturer's own page for the exact model and size; then an authorised distributor's page for the same model; then reviews for usage only.
- Record every fact with the URL it came from. A fact without a URL is dropped.
- Remove competitor brand names from everything you keep.

### 3. Score keywords for marketplace listings

Score each candidate keyword from 1 to 9: frequency in competitor titles (3, 2 or 1), relevance to the product (3, 2 or 1), and how few competitors use it (3, 2 or 1). Use 7 to 9 for the title, 4 to 6 for bullets, 2 to 3 for the description, and 1 for backend terms.

### 4. Write within each format's limits

| Format | Limits and structure |
|---|---|
| Large marketplace | Title up to 200 characters; five bullets of up to 500; description up to 2000; backend keywords up to 250 bytes |
| Auction marketplace | Title up to 80 characters; HTML description with a spec table |
| Mass marketplace | Title up to 75 characters; short description; ten attribute bullets |
| Own storefront | SEO title up to 60; meta description up to 160; headed description |
| Craft marketplace | Title up to 140; description; 13 tags of up to 20 characters |
| Social commerce | Title up to 255; description up to 1000; opens with the problem |

- Write each bullet as a feature, an advantage, a benefit and evidence. Evidence must be a sourced number or spec.
- Lead with the benefit, because buyers purchase outcomes.
- Tone is one of Professional (the default), Friendly, Urgent or Luxury. Choose one and keep it across the listing.

### 5. Run the two-pass audit

**Pass 1, draft.** Write from the verified facts. Aim the first draft near the middle of the word band, because drafts at the top of the band usually overrun it.

**Pass 2, audit.** For each draft:

- Remove effect and health claims for regulated categories. Words that promise an experience or an outcome are claims.
- Remove subjective superlatives such as "premium", "best ever" and "unreal".
- Keep the brand's neutral, sourced positioning, for example "independently tested", as long as the listing states the lab.
- Count the words in the body only. If the count is below the minimum, add a sourced factual line about format, packaging, testing or shipping terms. Never add adjectives to reach the count.
- Check that every fact in the body has a source URL.

Safety and ingredient statements published by the manufacturer are citable copy, not effect claims. If the page says "no added X" or "lab tested for Y", quote it verbatim. The audit targets subjective effect words, not disclosure.

### 6. Produce batch output

- Write one entry per input row to `descriptions.json`. Each entry has the row number taken from the CSV header (not an array index), the identifier shape the brief requires, the title, the description, the reference URLs and the status.
- Use the brief's status words exactly. If the brief names none, use DRAFTED and record the limits in a notes field.
- Write `QUESTIONS.md` listing every unsourced fact, every private-label row, every disagreement between the input title and the reference, and every row that could not be sourced.
- Write `SUMMARY.md` with the method, the references, the word count for each row, and the HTTP result of the probe for each URL.
- Probe every source URL for HTTP 200 before writing it into the file. Replace any URL that fails.
- Check that the row numbers match the expected set exactly, with no gaps and no duplicates.

### 7. Reuse sibling batches

When earlier batches cover the same brands, read their source URLs for each brand and reuse them, with one live check per URL. A fix batch driven by a reviewer's flags must probe every inherited URL again, because a flagged claim often means a link has gone stale.

### Source Rules

These rules come from real failures. Apply them when a source looks right but does not fit.

- **Match the exact product.** A page for another variant, size, model or generation is not a citation for this row. Check the page's title or product name against the exact model before you cite it. A check that matches several model names means the page is a family or comparison page, not a product page.
- **Foreign-language and script-rendered pages.** A page in another language, or a page that returns the site's home page to a plain request, cannot support spec claims. Use it only for what it actually says, and find a distributor page for the specs.
- **Retailer pages.** A retailer counts as authorised only when the brand or the retailer itself states that. A marketplace that carries the brand is not evidence of specs unless it quotes the manufacturer.
- **Family pages and sub-lines.** A family page can support shared hardware specs. A variant sold only in a sub-line needs that sub-line's page.
- **Several fields disagree.** If two or more identity fields (count, strength, variant, format or model) differ between the input and the reference, the row is NO_SOURCE (no usable source for the row). Name each disagreeing field side by side in the body. Do not write a near-match description.
- **One field disagrees.** Use the reference's value, and record the discarded value in `QUESTIONS.md`.
- **Bundle math is not a manufacturer claim.** A distributor's case or bundle total is not published by the manufacturer. Describe the per-unit spec the manufacturer publishes, and list the bundle figure as a question.
- **Per-unit values from a third party only.** Drop them and ask.
- **Category tags need a source.** Do not apply a category or regulated-ingredient tag that no cited source supports. If a source explicitly rejects a category, drop any tag for it.
- **Retired models.** If the manufacturer has retired a model everywhere it publishes, cite an authorised distributor that states its own authorisation, and flag the retirement.
- **Slash-joined identifiers.** Two identifiers joined by a slash on one row are one product. Keep the string as written, and do not split it into two rows.
- **Stylised or sanitised names.** Keep the catalog title verbatim. Use the brand's own spelling in the body, and note the difference.
- **Pack suffixes** such as "5pc", "5ct/bx" or "MF" describe packaging, not a different product. Do not invent a mixed case from them.
- **Model names in slugs.** A short URL slug can still be the right product if the page's title, structured data and body all name the same model. Check that the model name appears in each of them.

### Reviewer Fixes

When a reviewer flags a claim, rewrite the body to match the cited page's wording. Do not keep the claim and add a citation that does not carry it. If no source carries the value, delete the value. Answer each flag in `SUMMARY.md`, showing the old and new wording side by side.

## Pitfalls

- **A first pass that copies a marketing page** trips the audit on effect words almost every time. Always run pass 2.
- **Padding to reach a word count** with adjectives. Pad only with sourced facts.
- **A 404 shipped as a citation.** Probe each URL before writing it.
- **A thin NO_SOURCE body** that says only "no source available". Name each disagreement instead.
- **Inventing a brand, manufacturer, origin or warranty** when the title carries an unknown stamp. Ask instead.
- **Trimming by deleting a cited spec.** Trim repeated prose around the spec.
- **Taking row numbers from an array index.** Use the CSV row numbers.
- **Carrying a citation forward** from an earlier batch without checking that it fits this row.
- **Competitor brand names** left in the output.

## Verification

- Every entry has its identifier, title, description, a status from the brief's set, and at least one source URL unless it is NO_SOURCE.
- Row numbers match the expected set exactly, with no duplicates.
- Every source URL returned HTTP 200 in the probe recorded in `SUMMARY.md`.
- Body word counts fall inside the band the brief sets. NO_SOURCE bodies are counted separately.
- A banned-word scan of description bodies, not titles, returns no hits, or each hit is recorded as a false positive.
- `QUESTIONS.md` lists every unsourced fact, every disagreement and every private-label row.

## Attribution

The create and optimise workflow is adapted from the Nexscope eCommerce Skills (https://github.com/nexscope-ai/eCommerce-Skills). The batch schema, the reference rules and the two-pass audit were written for this library.
