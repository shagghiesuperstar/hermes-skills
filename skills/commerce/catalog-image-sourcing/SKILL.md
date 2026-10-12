---
name: catalog-image-sourcing
description: Use when a catalog row has a missing, placeholder or wrong product image or description and you must find a real pack shot or manufacturer copy that provably matches that exact SKU. Covers search, live URL checks, vision verification and an honest residual list.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [catalog, product-images, sourcing, vision, ecommerce]
    category: commerce
related_skills: [catalog-publish-safety, catalog-photo-pipeline]
---

# Catalog Image and Copy Sourcing

## Overview

Filling a catalog with real product images and manufacturer copy is a search problem followed by a verification problem. A search result that looks right is not evidence. The image must be fetched from a live, rights-clear source, and a vision check must confirm that it shows the exact brand, model, size and variant on the row. Rows that cannot be confirmed stay on a named residual list. Nothing is invented to fill a gap.

## When to Use

- A catalog import has placeholder, wrong or missing images, or a description that is empty or title-only.
- You must fill many rows and need a repeatable, resumable pipeline with an audit trail.
- A single row needs a pack shot or copy, and an owner has asked for the evidence.

Skip it for photos you took yourself (use catalog-photo-pipeline) and for production writes (use catalog-publish-safety for the preflight).

## Features

- Two-stage pipeline: a search harvest that stores candidate page URLs, then a verify stage that extracts and checks image candidates.
- Fail-fast URL gates before any model call: HTTP 200, an image content type, known placeholder filenames, and a brand or product token in the URL.
- Vision confirmation of the exact product on each candidate, with strict boolean parsing.
- Checkpointed state (one row per SKU with a status and the candidate list) so a run can resume.
- A residual file for rows that stay unconfirmed, with the reason for each.

## Benefits

- Every shipped image and sentence has a live source URL the owner can check.
- A run that stops halfway loses no work and repeats no search.
- Honest residuals show what still needs a human, instead of a silent gap.
- Generic and unbranded items are handled explicitly rather than forced into a match.

## Procedure

1. Validate the input sheet before anything else: the sheet name, and the columns for SKU, item name, brand, current image URL and category. Count rows and flag duplicates.

2. Set up an isolated environment and install the libraries the pipeline uses.

   ```bash
   python3 -m venv .venv && . .venv/bin/activate
   pip install openpyxl==<pinned-version> aiohttp==<pinned-version> tqdm==<pinned-version> pandas==<pinned-version> requests==<pinned-version>
   ```

3. Create a checkpoint table with one row per SKU and the statuses PENDING, CONFIRMED and NEEDS_HUMAN, plus a JSON column for search results. Seed PENDING rows from the rows whose image is a placeholder, missing or failing.

4. Harvest candidates. For each PENDING SKU, run one search built from brand plus item name. Drop the brand from the query for generic or unbranded items. Store the top six result URLs in the row. Respect the search tool's throughput; a fixed per-search delay is normal, and parallel threads often do not help.

5. Verify images in parallel with a small worker pool (six to eight). For each candidate page, extract `og:image` and `<img>` sources, prefer the largest size variant the CDN offers, skip logos, icons, payment badges and known placeholder assets, and rank the remaining candidates by how many product tokens appear in the URL.

6. Run the four gates on each image before any model call:
   - HTTP HEAD returns 200.
   - The content type starts with `image/`.
   - The filename is not a known placeholder.
   - At least one brand or product token appears in the URL. This is a cheap signal, not proof.

7. Confirm with a vision model. Send the image as a base64 data URI, not a bare URL, when the endpoint requires it. Set temperature to zero and ask for a fixed JSON shape. Accept only a real boolean `true` or the exact string `"true"`. Treat any parse failure as a rejection.

   ```python
   messages = [{
       "role": "user",
       "content": [
           {"type": "text", "text": "Does this image show <brand> <model> <size> <variant>? Answer as JSON: {\"match\": true or false, \"reason\": \"...\"}"},
           {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
       ],
   }]
   ```

8. Record the result per row: CONFIRMED with the image URL, the HTTP status, the pixel size and the vision reason; or NEEDS_HUMAN with a specific reason such as `NO_CONFIRMED_MATCH`, `DEAD_URL` or `GENERIC_NO_CANONICAL_PHOTO`.

9. For copy, take facts only from a manufacturer or authorized-distributor page for the exact model and size. Split each draft description into atomic claims, and keep a raw quote from the page for each claim. Drop any claim without a quote. Variant or usage notes that the page does not state are not added.

10. Export three files: the found-image sheet with a final image URL column (verified where found, original otherwise), a residual CSV of NEEDS_HUMAN rows with reasons, and a summary with counts taken from the database, not typed by hand.

11. Hand the residual list to the owner. Do not replace a residual with a related product, a marketplace thumbnail or an image of a different generation of the same line.

### Logo rules (vendor logo hunts)

When the job is brand logos rather than product photos, use these checks:

- Short side of a PNG must be at least 256 px. The short side is `min(width, height)`. SVG passes the size rule.
- A PNG must have a real alpha channel in its pixel data. Check with PIL that the alpha minimum is below 255. A palette image with a transparency entry does not count.
- Prefer, in order: the brand's own site, a verified social profile, then a stock source. Never use a reseller's logo for a brand the reseller does not own.
- Reject favicons, touch icons, footer SVGs, spinners and cookie banners.
- Open every download with PIL. A file starting with `<!doctype` or `<html` is an error page; delete it at once.
- Record each brand as found (with source URL and confidence) or missing (with a reason). Never list a slug in both.

## Pitfalls

- **A URL that returns 200 is not a verified image.** A URL checker proves the file exists. Only the vision check, against the exact product, proves it shows the right thing.
- **A search thumbnail is not the deliverable.** Search thumbnails are often cropped or the wrong SKU. Fetch the page and read the image URL it actually serves.
- **Plain text extraction drops meta tags.** Page-extract tools often remove `<meta>` content, and that is where `og:image` lives. Read the raw HTML with the audit's descriptive User-Agent and parse the tag. If the site refuses that User-Agent, record it as blocked. Match both attribute orders, `property` before `content` and the reverse.
- **An access challenge is a block, not a missing product.** A short "checking your browser" page means automated fetching was challenged. Do not try to get past it with other headers or user agents. Record the site as blocked, use another source, or use a page the owner has confirmed by hand.
- **Some product pages are JavaScript shells.** A page that returns the site's home page byte for byte, with an empty title, has no product content. Do not cite a spec from it.
- **A sized image can be too small.** On many CDNs the path without a size suffix returns the editor's original upload, which can be only 500 to 600 px. Check with `sips -g pixelWidth -g pixelHeight` before citing. A small master is a finding, not a reason to reject siblings in the same batch.
- **A `og:image` can be a site-wide placeholder or missing.** Fall back to the page's product image source set, and mark the row as taken from the page source.
- **A CDN may allow one successful fetch and then challenge.** A URL that returns the image once and a challenge page later is a gate, not a dead asset. Replace the citation from another host in the same run.
- **Pack form factor must match the row.** A single unit is not a multi-pack, and a bundle is not a single unit. Match the form factor word in the row's title to the page's title, slug and image file name before citing.
- **Strength, size and count are identity fields.** A row that differs from the brand's published image on one field is cited with a note. A row that differs on two or more independent fields is not the brand's product and is NO_SOURCE.
- **Vision models can misread stylized brand marks.** Cross-check the brand against the cited page's title, H1 and URL slug, which are set by the editor, not inferred.
- **Category renders are not mockups.** A clean white-background product photo with a faint shadow is the normal style for many categories. Reject the flat, shadowless two-dimensional bag render only when no real product is shown.
- **Packaging photos can show a different variant than the title.** When the title, the brand page and the photo disagree, the physical pack wins: the photo is the product. Retitle the row when two of three sources agree; detach the photo only when all three disagree.
- **A retailer's watermark on a brand's own image is a rights issue.** Re-source from a different authorized host that carries the same image without the burned-in mark.
- **Some vendors publish placeholder descriptions.** Strings such as "description to follow" are not copy. Treat them as empty.
- **The per-turn search budget runs out.** When a per-turn search cap fires mid-batch, stop searching, keep the verified rows, mark the rest NO_SOURCE with the reason, and report the gap. More searches will not change the owner's decision.

## Verification

- Each CONFIRMED row has an `https` image URL that answers 200 with an image content type to a HEAD request that follows redirects, for example `curl -sIL --http1.1 -A "<descriptive-user-agent>" <image-url>`. Read the last response block, not the first.
- Each image's pixel size is recorded with `sips` or PIL. The short side is at least the threshold the batch sets, and 400 px is a reasonable floor for product shots.
- Each CONFIRMED row has a vision result recording the match and a reason. A parse failure is recorded as a rejection.
- Counts in the summary equal the counts the database returns for each status.
- A random sample of four rows is re-checked by hand: open the URL, read the page title and the image, and compare them with the row.
- The residual file lists every NEEDS_HUMAN row with a reason and no row appears in both the found-image sheet and the residual file.
