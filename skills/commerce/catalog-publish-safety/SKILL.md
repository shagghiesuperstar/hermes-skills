---
name: catalog-publish-safety
description: Use when preflighting catalog writes, price changes, media replacement or new catalog items. Proves identity, sibling coverage, sell-unit pricing and compliance gates before any write, then requires a read-back check.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [commerce, catalog, preflight, pricing, media, safety]
    category: commerce
related_skills: [catalog-photo-pipeline, medusa-admin-data-ops, storefront-compliance-sweep]
---

# Catalog Publish Safety

## Overview

Catalog writes are hard to undo. A wrong price, a gallery replaced one variant at a time, or a product published without its compliance document can reach shoppers before anyone notices. This skill sets the order of work for any catalog write: read everything first, prove each identity and price, decide each product's status from explicit gates, and only then write, followed by a fresh read-back. It is platform-neutral. Use the project's own clients and policy code rather than inventing request shapes.

## When to Use

- Before catalog creates, variant updates, price changes or full-media replacement.
- When products share a parent gallery or sibling variants, so that partial coverage could damage live listings.
- When identity, categories, channels, existing media and external prices must all be proven before a write.

## Features

- Deterministic identity matching in a fixed order, with ambiguity treated as a blocker.
- Full parent context for every match: variants, categories, collection, channels, gallery and variant-image links.
- Price resolution that checks the sell unit against the product photo, not only the identity.
- Decision labels (`SAFE_FULL_REPLACE`, `FAIL_CLOSED`) with exact reasons.
- Processed-media acceptance gate: one output per angle, a hero for every variant, and QR evidence kept apart from OCR.
- A recovery manifest and a read-back check for any destructive replacement.

## Benefits

- A write only happens after every identity, price and relationship has been proven.
- A missing photo on one variant does not hide or remove a variant that is otherwise ready.
- Wrong-unit and wrong-product errors are caught before they reach a shopper.
- Every destructive step can be rolled back from the saved manifest.

## Procedure

1. **Check standing rulings before any hide, draft or unpublish.** Search the project's decision log for a ruling on the product class. When a ruling exists, follow it and correct only false copy. Raise a question to the owner only when new evidence contradicts the ruling. Never draft first and ask second.

2. **Run a read-only preflight first.** Use only authenticated GET or read endpoints and project-owned clients. Do not write, upload or edit tracked files during this step. Do not print credentials.

3. **Parse the whole batch before querying production.** Build one row per decoded identity with its source and photo count. Assert the expected row count, that each identity is unique, and that the totals add up.

4. **Match in a fixed order.** Use the exact variant barcode, EAN or UPC first, then the exact SKU, then the product's external ID. Normalise only UPC-A and EAN forms that are explicitly equivalent. Never match by title.

5. **Treat ambiguity as a blocker.** If a tier returns more than one product or variant, stop that identity. Do not accept the first result.

6. **Read the full parent for each match.** Retrieve variants, categories, collection, sales channels, gallery images and variant-image links. Count shared gallery media once per parent.

7. **Resolve prices from the authorised source, and check the sell unit.**
   - Require an exact identity match on the matching item, record the exact selling-price field and value, apply the configured multiplier, and compute minor units with integer arithmetic.
   - Never use purchase cost or a fuzzy candidate.
   - An exact identity match does not prove the unit. A source rate can be for a wholesale case while the listing sells the inner retail unit. Read the matching item's unit field and any count suffix in its name, and compare them with the printed count or net weight on the hero photo.
   - When they differ, the retail price is the case rate divided by the inner count, times the multiplier, and the title must be changed to the retail unit. A correct multiplier on the wrong unit is a silent error that read-back checks will not catch.

8. **Gate at product level, then apply the stock sheet, then the compliance overlay.**
   - Missing photos on one variant are not a reason to hide or delete that variant. Ready variants stay listed.
   - A stock sheet marks a product as draft (for example, banded or out of stock). Follow the sheet rather than the photo folder.
   - Most platforms have no per-variant draft flag. Do not delete ready variants to imitate one.
   - A product with no on-domain compliance document page is a draft, even when the stock sheet is green.

9. **Fail closed for new items.** An unmatched code needs a deterministic category mapping and a human review before creation. A resolved price alone is not permission to create. Never infer a category from a title, OCR text, an image or similarity.

10. **Snapshot relationships before any write.** Record category IDs, collection, status and channel IDs. After the write, read them back and assert that they are unchanged.

11. **Write the audit artifact.** Group output by product ID, with every per-identity field from the list below and every blocker stated exactly. Save it outside the repository or in a verified ignored path.

12. **Run the processed-media gate before any upload.** Check the media and metadata separately from the identity and price checks (see the next section).

13. **Write only after every gate passes**, then read the result back from the admin API, the store API and the rendered page (see Verification).

### Required per-identity fields

- Source identity and photo count
- Exact match yes or no, match tier, ambiguity count
- Product ID, title and status
- Variant ID, title, SKU and barcode
- Category IDs, names and validity
- Collection
- Sales channels and validity
- Parent gallery image count
- Current variant-image link count
- Every sibling variant with its barcode, SKU and media state
- Coverage of all siblings, and coverage of siblings that have media
- Exact pricing-source identity and selling price
- Configured multiplier and target minor units
- Blockers

### Decision labels

- `SAFE_FULL_REPLACE`: every strict gate passes for the whole parent.
- `FAIL_CLOSED`: the reasons are listed exactly. A missing sibling, category, channel, identity or price is never downgraded to a warning.

### Processed-media acceptance gate

A passing identity and price check does not make the media safe to upload. Before any upload, check the processed media and metadata on their own:

1. **One output per intended angle.** Match each output to its source frame by a stable provenance key. Use the project's canonical filename parser, not a loose wildcard, because role suffixes can follow the plate marker.
2. **Classify each frame on its own evidence.** Use that frame's geometry, its decoded codes and its own text. Never give the group's combined text to every frame's classifier, because one ingredients panel would then label the whole group.
3. **Every publishable variant needs a hero.** A hero is a complete, uncropped frame with no code, label panel or compliance text as its main subject. Zero valid heroes is a hard blocker.
4. **Compliance frames go last.** Order complete heroes first, then ordinary detail frames, then barcode, QR, lot, nutrition, warning and ingredient frames. Confirm that the live thumbnail resolves to a hero.
5. **Keep OCR evidence complete.** Process every relevant frame, keep the per-frame text and source file names, and merge parsed sections without losing any. Rank candidate sections by completeness and confidence, not by first appearance. Stop each section at a clear label boundary. Never read a nutrient-table quantity as a product strength unless the product's strength is stated.
6. **Keep QR evidence apart from OCR.** Decode every frame. OCR digits and URLs never establish product identity. A frame that carries a decoded code is not eligible as a hero or thumbnail.
7. **Clear stale outputs on rerun.** Old role-suffixed files for the same group must not sit beside corrected ones.

### Full shared-gallery replacement

Use this mode only when the owner explicitly authorises replacing all existing media. Do not treat normal pipeline replacement as permission for it.

1. Group the whole plan by parent product ID before any image change.
2. Require identity, category, channel and price gates. Replace media on the variants that have photos, and leave the others listed.
3. Save a recovery manifest: old image IDs and URLs, their order, the thumbnail, and each image's variant links.
4. Upload and verify the complete new image set for every sibling before removing any old image.
5. Replace the parent gallery once. Replacing it one variant at a time means the last variant write erases its siblings' images.
6. Rebuild each variant's links from its own images only, then set the thumbnail from the verified hero.
7. Read back with bounded requests: the parent gallery with only ID, thumbnail and images, then each variant's images, price, thumbnail and required metadata. Assert that every old image is gone, every new image appears exactly once, the links are exact, and no non-white or gradient image is attached.
8. Treat a successful write response as provisional. Confirm with a fresh read that the change happened. If the endpoint says it succeeded but the state did not change, stop. Do not retry the same request in a loop, and do not invent a different call.
9. Record the real IDs and the result for each product: success, skipped, failed verification or error. An upload that succeeded is not a replacement that succeeded.
10. Keep storage deletion separate from storefront removal. Do not claim old files were deleted unless the storage API was called and the deletion checked. The storefront requirement is that no old image is attached or visible.

### Attaching operator-sourced media

When media arrives from an operator or an outside feed, attach it without changing the product's publish state, so it stays draft or held.

1. Check the file's signature, not its extension: `FF D8 FF` for JPEG, `%PDF` for PDF. A file with the wrong content fails partway through a batch.
2. Make each run idempotent. Before uploading, check the live product. Skip the upload when the thumbnail and at least one gallery image are already there.
3. Save metadata even when images are missing. Metadata can be staged on a draft while images are still pending.
4. Tag writes often replace the whole list. Read the current tags, merge in the new one, and send the full list.
5. Metadata writes are often a full replacement of the object. Read the product, merge your keys into the existing object, then send the whole object.
6. Verify with a separate read pass. Do not rely on the writer's own counts. Run the script a second time and check for zero changes.

## Pitfalls

- **Counting gallery images once per code inflates old-media totals.** Count once per unique parent.
- **"Every sibling with media is represented" is not "every sibling is represented".** Track both measures.
- **A search filter can return a near match.** Check the returned SKU, UPC, EAN or ISBN exactly before accepting a price.
- **A published, channel-linked product can still be unsafe to replace** if one sibling is missing its photos.
- **Concurrent workers change the repository state.** Snapshot it before the preflight, so that earlier changes are not blamed on the preflight.
- **Destructive whole-gallery mode needs its own association rules.** If the new set includes detail shots, each one must still be linked to the variant that owns it.
- **Price and metadata writes count as mutations.** Incomplete photo coverage blocks the whole parent group, not only the image step.
- **A metadata allow-list drops new fields silently.** Collect every non-empty field and deny only identity and error fields, and test both variant and product metadata.
- **Section headers need anchors.** A line that begins with "contains" is not an allergen declaration unless it has the declaration form. Text that mentions calories, daily values or carbohydrates with no allergen word is nutrition text, not allergen text.
- **Publishing in the admin does not change a pre-rendered storefront.** A rebuild or deploy has to run first. Check the live page, and grep the listing for the real link before calling a page missing.
- **Pack size on an item name is not proof of the sell unit.** Read the printed volume or count on the hero photo and the brand's own page before setting the title.
- **Off-domain document links must not appear in shopper-visible text.** Sweep the description and any structured metadata for vendor hosts before publishing, then check the live page.
- **Marketing copy comes first, and label text is secondary.** Label facts belong in structured fields. They should not be repeated in the description, the details and the product information.
- **Effect words are a denylist, not a hint.** Any word that implies an effect on the consumer is a hard failure in the description.
- **Compliance review reads the words.** A filter that catches one category of claim but misses a synonym lets the same claim ship.
- **A `.pdf` link is not a PDF.** Check the `%PDF` signature after download. A vendor link can serve an error or consent page.
- **Environment defaults go stale.** Pass the live backend URL explicitly when a client is built for a specific region. Otherwise you get connection or authentication errors that look like a credentials problem.
- **Warehouse-retired codes never publish.** Keep a list of retired codes and fail the plan on any hit.
- **A bulk allow-list or deny-list change is one job.** Run the preflight with a hard cap on rows and a fail-closed rule for off-class products, then the apply step, then an independent review. Run allow-list and deny-list changes on the same axis as one job, because the second can undo the first.

## Verification

Before calling the work complete, check these in code:

- The expected identity count equals the number of rows in the report.
- Every identity appears exactly once.
- No write, upload or tracked-file change happened during the preflight.
- Every resolved price has exact identity evidence and integer minor units.
- Every `SAFE_FULL_REPLACE` parent has full sibling coverage.
- Every product with a compliance requirement has its document on the owner's own domain, and the document opens as a PDF or a valid image.
- After the write: the admin read, the store read and the rendered product page all show the expected state, and the old media is no longer attached or visible.
- Report hashes or stable file paths are recorded for handoff.
