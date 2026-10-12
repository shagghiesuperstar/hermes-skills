---
name: regulatory-coa-verification
description: Use when verifying certificates of analysis (COAs). Covers source discovery, identity checks against the document text, status codes, wall hosts and a metadata bind with read-back proof.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [compliance, coa, lab-testing, regulated, verification, catalog, batch-verification]
    category: commerce
related_skills: [regulated-commerce-compliance-gates, catalog-publish-safety, regulated-catalog-content]
---

# Regulatory COA Verification

## Overview

A certificate of analysis (COA) is a legal artifact for many regulated products: it names the lab, the batch or lot, the product form, the strength and the tested analytes. A catalog that shows a COA which belongs to a different variant, size or batch is worse than a catalog with no COA. This skill finds candidate documents from brand and lab sources, verifies each one against its own text, records a status that says exactly how far the verification went, and binds only the verified documents to the product metadata, with a read-back to prove the bind.

## When to Use

- A product's COA link is missing, returns an error, or points at a retired host.
- A new SKU must have a public COA before it is listed.
- A reviewer asks for proof that each published variant has a matching document.

Skip it for products that carry no testing requirement, and for choosing which compliance gate applies (use regulated-commerce-compliance-gates).

## Features

- Pre-search triage that marks categories with no public COA route before any search budget is spent.
- A verify-then-bind ladder: live response, file signature, document text, then identity against the product.
- A closed status vocabulary that counts, sorts and gates reports.
- Wall-host detection for files that cannot be read directly.
- A metadata bind with a read-back at the correct nesting level.

## Benefits

- A bound COA has been read, not just fetched.
- Every unresolved item says why: no public route, a form-gated request, a wall host, or a real mismatch.
- A report's counts are recomputed from the rows they describe.

## Procedure

### 1. Triage before searching

Classify each SKU before any search:

- **Hardware and non-consumables** (devices, batteries, chargers, apparel, display fixtures) need no lab test. Mark them with the terminal status for "no COA required" and cite the vendor page that shows it.
- **Product categories with no public lab index** usually deliver reports on request only. Mark them as blocked-by-request and stop.
- **Brands that cannot be found anywhere** are treated as unknown. Mark them not found, with the note that the brand is not discoverable.
- **Everything else** goes through the search ladder.

Do not spend the search budget on a class that cannot produce a public document.

### 2. Find candidates in order

1. **Brand site first.** Search for the brand with lab reports, COA or certificate of analysis. Look for a dedicated lab-results page on the brand's own domain. Shopify stores can expose their page content as JSON at the page's path with a `.json` suffix, and product JSON lists variant barcodes.
2. **Product-level pages and the batch list.** When a brand index lists batches, match the SKU's batch or lot against the list. A brand index that lists a product family but no batch for the SKU supports only a family-level match.
3. **Manufacturer and authorised distributors.** Search for the manufacturer's name with the product and lab-report terms. A distributor's copy counts only when it matches the same product form and size.
4. **Lab portals.** Search the lab portal by brand name. An empty result is evidence that the brand has no indexed reports, not a search failure.
5. **Broad search for PDFs** with the brand, product and document-type terms.

Record each query exactly as it was run. Count distinct search approaches, not retries of the same query. Stop after the distinct approaches are exhausted.

### 3. Verify each candidate in order

1. **Live response.** The URL must return a success status when requested with redirects followed. A product page or a listing is not a COA.
2. **File signature.** Download the file and confirm it starts with the PDF signature (`%PDF`). A file that starts with an image signature is a scanned image mislabelled as a PDF. Content-type headers alone are not enough, because some hosts send the wrong type.
3. **Document text.** Extract the text layer and require the brand, the product form, the variant or strength, and the batch or lot to appear in the document. Title similarity is never verification.
4. **Identity.** The document must match the product on four points: brand, form (for example tablet against capsule, or powder against liquid), variant, and strength. A document for another variant, size or form is a close-but-wrong match, and the mismatch is recorded.

Judge each fetch on its own bytes. A host that protects its files can return a real file once and a challenge page the next time, so a single good result is not proof of a stable link.

### 4. Name files and cache them safely

Name each download with its URL's own file name. Never overwrite an existing cached copy during re-verification. Two copies of one document in one folder can make a check read the wrong one.

### 5. Recognise wall hosts

Some hosts hide documents behind an interface that cannot be read directly: shared-drive folders, file-sharing viewers, PDF embed frames, and flipbook viewers. A whole brand library behind one of these is a wall. Mark those rows as skipped with the wall host named. Do not record a batch page that only embeds a viewer as the document link.

### 6. Respect access gates

- Age gates and disclaimer pages are a human step. If a gate hides every report link, mark the row as blocked by access. Do not bypass the gate.
- Request forms and login walls are blocked by access too, even when the document probably exists.
- A parked or retired domain does not invalidate a document already known to exist on a file host. Verify that file directly.

### 7. Choose a status from the closed vocabulary

| Status | Use when |
|---|---|
| Verified | The document matches brand, form, variant or strength, and batch where the SKU carries one, and its text was read |
| Candidate, batch unconfirmed | The same product line matches, but the lot cannot be confirmed from the document |
| Candidate, needs map | A sibling variant, another size, a different product line, or a viewer page without a document |
| Not found | No public document exists, the item is hardware, the brand is private label, or every approach is exhausted |
| Blocked | The document sits behind a request form, a login or an age gate |

A verified status needs a real document whose text was read. A candidate status with no document path is not allowed, because a later check will fail on it. When the lab networks cannot cover a product, change the row to not found and record the reason, rather than leaving it pending.

### 8. Bind only verified documents

1. Confirm that the SKU maps to exactly one published product and variant before any write. A token that matches several parents is not identity.
2. Bind the verified document's stable URL to the variant's metadata, and record its source host and the reason it was accepted.
3. Read the field back at the nesting level where the write landed. A null at one response depth can hide a value one level deeper, so read the response shape before concluding that a bind failed.
4. Use an expansion that returns the field. A bare read that returns nothing does not prove the field is empty.
5. Where the environment cannot store uploads, keep the document's public URL, mark the row as an upload failure, and report the environment limit. Do not retry the upload as if it were flaky.

### 9. Build the deliverable

- One result row per SKU, with the status, the public URL, the candidate URL, the byte count and signature check, the four identity checks, the queries run and a note.
- A summary by brand with the counts by status. Derive every count from the rows it describes, and reconcile the total against the input count.
- A list of rows that could not be verified, grouped by reason, for the owner to act on.
- Copy source URLs byte for byte. Do not repair escaped characters, because the repaired link may no longer resolve.

## Pitfalls

- **A link that exists is not a verified link.** Check the document's content, not only its bytes.
- **A document for the right product line but the wrong variant or size** is a close-but-wrong match. Never promote it.
- **The batch date on a lab report is the analysis date,** not the production date. Note the difference instead of guessing.
- **OCR confuses the last digit of batch codes.** Confirm batch codes against the live document, not against a scan.
- **Lot and batch are not always the same thing.** Note the term used on the document when it differs from the catalog.
- **A product page's COA link can point at an old batch.** A brand's central library is more reliable.
- **Retail partner pages can host a brand's document without being the origin.** Trace each document back to the brand or an accredited lab.
- **An unknown lab is a question, not an automatic rejection.** Note the lab's accreditation as an open point.
- **Wayback snapshots are usually HTML,** not documents.
- **Never invent a document URL.** A dead link is a finding to report.
- **Signed download links expire.** Record the stable portal address, not a signed one.
- **Screenshots are not COAs.** An image of a report is a note, even when the product matches.

## Verification

- Every verified row has a document whose signature and text were checked, and whose identity matches on all four points.
- Every candidate row names what is missing.
- Counts in the summary equal the counts recomputed from the rows.
- Each bound URL was read back at the correct nesting level, and the read-back matches the bind.
- No credential, signed link or personal detail appears in the deliverable.
