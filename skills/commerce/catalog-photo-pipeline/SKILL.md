---
name: catalog-photo-pipeline
description: Use when turning product photos into catalog media. Covers a read-only preflight audit, barcode grouping, OCR, gallery replacement and read-back checks.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [ecommerce, product-photography, ocr, barcode, catalog]
    category: commerce
related_skills: [catalog-publish-safety, catalog-image-sourcing, medusa-docs-first]
---

# Catalog Photo Pipeline

## Overview

A product photo pipeline turns raw shoot folders into catalog media, metadata, prices and live storefront updates. The main risk is that one successful step hides a failure in another: a good upload says nothing about the barcode, a barcode says nothing about the price, and a price says nothing about the certificate link. This skill keeps five systems separately verified and treats each as its own evidence.

## When to Use

- A batch of photos with barcodes, labels or QR codes must become catalog media.
- A destructive gallery replacement is planned for shared, multi-variant products.
- A new folder is presented as new products and you must first check whether its barcodes already exist.

Skip it for one-off image edits with no catalog identity or commerce write.

## Features

- Read-only preflight audit: scope, extension casing, duplicates, readability, orientation and barcode grouping, with reconciled totals.
- Barcode-first grouping in capture-time order, with quarantine for conflicts.
- Per-frame OCR and QR decoding that enriches a listing but never establishes identity.
- Fail-closed allowlist that matches every decoded code to one live product before any write.
- Product-by-product gallery replacement with a recovery manifest and read-back checks.

## Benefits

- Every photo is accounted for once, so no frame is silently dropped or double-counted.
- A replacement can be rolled back, because the old image IDs are saved first.
- Products do not disappear because one shoot is missing; their status follows the stock source instead.
- Shoppers see a verified, on-domain certificate link or a clearly marked draft, never a dead button.

## Procedure

### Operating principles

1. **Identity:** decode barcodes and EAN or UPC codes deterministically. Nothing else sets identity.
2. **Media:** the photographer's original files are the publish files. Do not change pixels unless an owner explicitly orders it for a batch.
3. **Enrichment:** OCR and QR-derived text adds facts to a listing. It never starts or changes a group.
4. **Certificates:** a certificate link points to a document on your own domain. A product with no on-domain certificate is a draft.
5. **Commerce:** matching, pricing, replacement and read-back are checked against the live admin and storefront.

### 1. Preflight audit (read-only)

1. Write the scope before running anything: source folder, whether the scope is the top level only, accepted extensions, the grouping time gap, the interpreter and the grouping entry point, and the protected output trees.
2. Count every supported image. Match extensions case-insensitively and report the counts for each casing. Exclude fixtures and sample folders explicitly. Hash every file to find exact duplicates across folders.
3. Check each file for readability and dimensions. For JPEG, verify with PIL, then reopen and load the pixels so truncated data is caught. Record the EXIF orientation and the display orientation (EXIF tags 5 to 8 swap width and height).
4. When nested folders could change the grouper's mode, build a temporary folder of symlinks to the top-level files only. Confirm the symlink count equals the inventory count. Delete only that temporary folder afterwards.
5. Run the repository's own grouping command with the same interpreter it documents, in dry-run mode. A generic system Python can silently turn every barcode into "unknown" when the barcode library lives in the project's environment.
6. Snapshot the original and protected output trees before and after the run. Compare file counts and a digest of filename, byte size and timestamp. A dry run can still print an output path, so the snapshot is the proof that nothing was written.
7. Reconcile the totals: the sum of group sizes plus the quarantine count equals the number of eligible files. A mismatch blocks the run.
8. Classify barcode starts separately: a repeated group key that is not contiguous, a repeated code inside a group (usually harmless), a start frame with several codes (quarantine), and a group with no identity start (report its bounds).

### 2. Barcode-first grouping

- Sort a flat shoot by capture time, using EXIF time before file modification time.
- A decoded retail barcode starts a group or changes it. QR URLs and OCR digits never start a group.
- Quarantine unknown or conflicting groups instead of inventing a product.
- Account for every input photo exactly once.

### 3. Media and OCR

- Process from the raw originals. Do not use derived or compressed copies as the origin of a QR or label.
- Background removal and white compositing are a default you should not apply. When an owner orders a standard background for a named batch, process from the raw files, check every output frame visually for damage to the label or code, and verify the served file after upload. Say in the report that the object edges are feathered by the technique.
- Decode QR codes on every frame. Compression can remove a code, so decode from the originals first.
- Run OCR on every relevant frame and keep the per-frame text. Batch OCR functions often take a list; passing one path can fail quietly and mark every image as unassigned. Re-read the output on disk before trusting a completion message.
- Parse ingredients, warnings, label directions, nutrition, net weight, manufacturer, batch or lot, expiry and contact URLs. Keep OCR merge-only and gate it by confidence.

### 4. Classify image roles per frame

- Use per-frame OCR and decode results plus the frame's geometry. Never give every frame the group's combined text.
- Each publishable item needs at least one complete full-pack hero.
- Barcode, QR, lot, warning, nutrition and compliance frames are never thumbnails. Order heroes first, then compliance, then detail.
- Clear generated role files before a rerun.
- Verify that the original-photo count equals the publish count and the OCR frame count.

### 5. Fail-closed allowlist before any write

For every decoded code, read the live catalog and pricing without writing. Record the exact IDs, the match tier, sibling variants, categories and channels, existing media, the authoritative price, the photo count and whether a hero exists.

For destructive replacement, require that the identity is unique, the category and channel are valid, and every variant that has photos has a hero. A variant with no photos is not a reason to remove the variant. Draft versus published is decided at product level by the stock source, not by the photo folder.

When a live product photo shows the wrong strength or a placeholder image, flag it with the product ID and both admin and shop URLs. Do not invent a replacement image, and do not hide the product.

### 6. Replace galleries product by product

1. Group all records by parent product before any write.
2. Upload and verify the complete new image set first.
3. Save a recovery manifest of the old image IDs, URLs, thumbnails and associations.
4. Replace the parent gallery once.
5. Rebuild each variant's associations from its own images only.
6. Set thumbnails from the exact hero IDs.
7. Merge metadata without blanking trusted values.
8. Read back immediately. Stop on any mismatch.

Never replace a shared gallery one variant at a time. The last variant write erases its siblings' images.

Some admin pickers reject files above about one megabyte, while API uploads accept the multi-megabyte originals. Upload the originals through the API rather than asking the operator to compress them.

### 7. Gallery order on the storefront

- The product page should open on the variant thumbnail or the product thumbnail, not on the first image. A first image that is a barcode close-up is a gallery-order bug, not a missing photo.
- Keep barcode frames in the gallery. Only the order changes.
- Live variant metadata is often null. Do not claim that label text appears on the page until a write-back confirms it.

### 8. Certificates of analysis

- A certificate link must go to a document on your own domain. A vendor-hosted PDF is the origin you copy from, not the link you show. Upload it to your own storage, check its hash, and point the record at your copy.
- Link each product to the certificate for its exact variant and size. A sibling product's certificate is a guess. Do not send a shopper to a brand index page when a per-variant document exists.
- Mirror lab documents through a temporary path, assert the file starts with `%PDF`, and only then move it into place. Extract the text layer first; run OCR only when the text is below a declared threshold, and record which method was used.
- Keep lot identifiers separate from lab sample IDs, and store the lab name next to every lab identifier.
- Record only the test panels that are present in the document, as numbers.
- Retire out-of-date certificates in one pass: back up the records with a timestamp, replace each one with the newest document for the same variant, or remove it and flag the product. Never leave a dead link. Finish with a check that no old dates remain and no map points at a deleted document.
- Do not bypass an access control to reach a lab portal. A browser-verification page is a blocked state, and the run must say so.

### 9. Dead links and recovery

- A 404 on one host is not proof the document is gone. Check the brand's other owned hosts and its lab page before declaring it missing.
- A lab hub page can list documents under new paths. Match on lot codes and file-name fragments, not on the old full path.
- A cloud-drive share link returns HTML on a HEAD request even when it is live. Mark it as needing a host check unless a probe confirms a PDF.
- A distributor's document counts as a found source only when it matches both the product and the size. A document for another size is ambiguous and fails closed.
- A dead domain routed to unrelated pages is NO_CANDIDATE (no usable candidate was found), not a match.
- Run candidate checks in a scripted parallel loop, accept only status 200 with a document signature, and record the status of every row.

### 10. Dry-run the exact live command

Run the same allowlist, flags, limits and multiplier that production will use. Inspect the plan for counts, ordering, category and channel preservation, prices and parent completeness before anything is written.

### 11. Verify three surfaces

Check the admin API, the store API and the rendered storefront. A successful write response is not enough. After a full replacement, assert that no old image ID or URL remains, that no prohibited background appears, and that an identical rerun does not grow the gallery.

### Concurrency and overnight runs

- Serialize agents that edit code in one working tree.
- Do not publish while outputs are still being written.
- Pause redundant schedulers before a manual live run.
- A scheduled job that has a next-run time but no last-run time has not run. Check the log, not the schedule.
- Prefer resumable, idempotent stages with timestamped reports.

### Preflight audit gotchas

- A rich-text CLI can truncate file names. Keep the log, but take membership from a structured report.
- Group order is not file-name order. Take the first and last names from the grouper's returned order.
- Symlinks keep access to the target's EXIF and metadata, which the grouper needs. Confirm the grouper follows symlinks before relying on that.
- "The metadata exists in the catalog API" and "the metadata renders on the storefront" are two checks. Record both.

## Pitfalls

- **Derived copies lose codes.** Decode QR and barcodes from the original files.
- **Grouping mode can change silently.** A recursive grouper switches behaviour when nested folders exist. Use a flat input view.
- **Interpreter mismatch hides barcodes.** Run the report with the same interpreter as the grouping command.
- **Decoded identity is not permission to replace.** Resolve the parent product and its siblings first.
- **A second dated folder is not automatically new products.** Run a live barcode diff first. An existing barcode gets a photo replacement, not a new product.
- **Missing photos are not a removal reason.** A sibling absent from this folder may be in an older tree. Search before concluding anything.
- **Compliance frames get dropped.** Rembg-style cleanup removes small codes and text. Keep the untouched originals for compliance.
- **A stock-sheet colour beats folder contents.** A product's draft or publish state follows the stock source.
- **A rip from a vendor site looks different.** Generated file names, uniform low resolution and watermarks are signs of a rip. Visual review must cover these, because code review does not see pixels.
- **Pack print beats the title.** Read the printed size and count on the pack before retitling or searching for a new photo.
- **URLs must match the corrected title.** When a product is renamed, fix its slug everywhere it appears: admin, sitemap, tests and certificate links. Keep the wrong size out of the URL.
- **An admin record is not a live page.** A 200 from the store API does not prove the product page renders.
- **Browser caches keep old images.** After a swap, check the served files directly, then clear caches before judging the result.
- **Wholesale formats are not consumer formats.** A bundle or case size the brand does not publish on its own page has no per-format photo. Escalate rather than substituting a related size.

## Verification

- Tests and smoke checks pass, and the diff is clean.
- Every source file is accounted for once, and corrupt or duplicate files are resolved.
- Every publishable group has a hero and an allowed image path.
- The sum of group sizes plus quarantine equals the eligible file count.
- OCR and QR evidence is kept per frame and matched to identity.
- Prices come only from the authoritative source and multiplier.
- A recovery manifest exists before any destructive replacement.
- Admin, store API and storefront read-back agree after the write.
- Each certificate link resolves on your own domain and its document starts with `%PDF`.
