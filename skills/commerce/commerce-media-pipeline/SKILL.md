---
name: commerce-media-pipeline
description: Use when batch-processing storefront product photos or 3D assets, pruning a shoot folder to hero shots, or watching a shared photo folder, with a visual operator gate before anything reaches the catalog.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [commerce, media, catalog, photo-pipeline, 3d-assets, compression, operator-gate]
    category: commerce
related_skills: [catalog-photo-pipeline, catalog-image-sourcing, catalog-publish-safety, storefront-visual-acceptance]
---

# Commerce Media Pipeline

## Overview

Storefront media goes through several steps before it reaches shoppers: a batch template or compression pass, a set of pruned hero shots, a copy that is uploaded and mapped to products, and an intake monitor that notices new files. Each step can fail quietly. A batch can stop halfway, a template can change the label on a regulated product, and a worker can report "all done" when a third of the files were never touched. This skill sets the coverage checks, the classifiers, the operator visual gate and the upload rules that catch those failures.

## When to Use

- An operator asks for one template or compression setting to be applied to every product photo.
- A shoot folder with many products needs pruning to a few keepers per product, with the rest set aside.
- A 3D asset must be compressed and checked by eye before it ships.
- A shared folder receives new photos that should trigger a downstream job.

## Features

- Coverage scan of the full source tree before any run, so partial work is visible.
- Deterministic classifier for whole-product shots versus close-ups, measured on the output.
- Two output sets for regulated products: template-only (packaging untouched) and enhanced.
- Series segmentation of a shoot by barcode payload, with validation and a stricter re-check for suspicious series.
- Read-only intake monitor for a shared folder, with per-file deduplication and a failure threshold.
- GLB compression that inspects first, changes the minimum, and keeps node and material names.

## Benefits

- A report of "all processed" is checked against the file count before it is believed.
- Regulated text on a label is not silently changed by an enhancement step.
- Nothing is deleted. Rejected photos move to a holding folder, and the manifest records every decision.
- Every upload is verified by reading it back, and the second run shows zero changes.

## Procedure

### 1. Inventory and coverage (every run)

1. Walk the live source tree and count every asset in scope. Do not use a staging copy left by an earlier worker. Count extensions case-insensitively, and check upper and lower case separately.
2. Record the total in the run log. A subset is an explicit scope, never an unlisted "leftover". If N of M were processed before, this run owns the other M minus N items by name.
3. Before any API-costing batch, check the remaining credit or quota on the provider's dashboard and log the value with a timestamp. A value relayed from an earlier report is not evidence. Budget at least 1.5 times the asset count.

### 2. Classify each asset before any call

Use a deterministic rule, not a judgement call:

- **Whole product** (a template cutout applies): the subject does not touch two or more edges of the frame, and at least 85 percent of a thin border band is background-coloured. Check the band's colour against the corner samples, with a colour difference of 12 or less.
- **Close-up** (label, panel, barcode or a crop that fills the frame): either rule above fails, or the central area is label paper. Compress the original; do not cut it out.
- **Broken cutout**, checked after the call: alpha coverage below 8 percent or above 92 percent, or the largest opaque region under half of the total alpha. Fall back to the compressed original. Never ship a broken cutout.

For 3D assets, sort them into texture-heavy (resize and convert to WebP) or geometry-heavy (Draco or Meshopt), and check whether the loader already supports the codec.

### 3. Run the smallest variant first, then measure

- Photo template: run one frame with enhancement off. Check that the subject is intact and the label text is unchanged. Then turn enhancement on for the batch.
- Do not start a full run until a proof sheet has been approved by the operator.
- For a regulated product, run OCR on the result and on the original, and compare every numeric field (strength, count, serving, net weight). Any difference means a rerun without enhancement, or a note to the operator with both texts side by side.

### 4. Two outputs for regulated packaging

An enhancement step re-draws the image. On regulated packaging it can change the cap colour, the label layout or the silhouette while the main words still pass OCR. A reviewer holding the real pack will notice. For every regulated cutout, produce:

1. A template-only output with the packaging untouched. This is the safe set, and it ships even when enhancement fails on a frame.
2. An enhanced output from the combined call. It may differ from the original. Never show it as the default.

The manifest gets one row per product with both file names and both statuses. The proof sheet shows the two outputs side by side with file sizes. If an enhanced output has changed the packaging, the recommendation is the template-only output. Rerunning the enhancer will change it again, because the model is generative.

### 5. Operator visual gate (before any catalog write)

- Build a side-by-side page of source and result, served on a local address that the operator's device can reach. Serve the page on a private network for the review window only, confirm it answers with HTTP 200 from the reviewer's device, and stop the server afterwards.
- Nothing is written to the catalog until the operator approves in writing. Silence is not approval.
- Record the approval text in the run log next to the batch it covers.

### 6. Shoot-folder pruning (keep the hero, set the rest aside)

Use this for a folder that holds a series of photos per product, where each series starts with its barcode shot.

1. Confirm the series boundaries and the rotation policy before starting. If the boundary convention is missing, say which assumption you made.
2. Make thumbnails for the whole folder. Assert that the thumbnail count equals the original count.
3. Check orientation from the EXIF tag or the aspect ratio. Fix rotation only after checking one sample by eye.
4. Decode the linear barcodes in each frame. Split series when the payload changes, not when a barcode appears. Ignore QR codes for splitting, because one QR link can be shared by several products. Files with no barcode join the current series. Flag series with fewer than two or more than about twenty photos. Assert full coverage.
5. Give each series to a vision reviewer. Each reviewer views every frame and returns, for each file, one of: keep or prune; the hero; any rotated frames; and a note. Keep the first frame of each series. Keep every frame that carries unique product information. Among near-duplicates, keep the sharpest. Keep three to five per series. A series of three or fewer keeps all.
6. Check the output. Normalise file names against the series list, because reviewers drop extensions. Assert that keep and prune together equal the file list with no overlap, the barcode frame is kept, and the hero is among the keepers. Send a stricter re-review only for series that kept more than 90 percent of more than three frames. Some series really do need every face kept, such as multi-packs; accept that verdict when the reviewer gives a reason for each photo.
7. Apply. Rename keepers with `-barcode` and `-hero` suffixes, move pruned files into a `_pruned/` folder, and never delete anything. Write a manifest recording each file's series, barcode, action, new name and flags. Assert that the kept and pruned counts add up to the original count, and that there is one barcode suffix and one hero suffix per series.

Make sure that no information found only on a pruned frame (weight, strength, ingredients, lot, expiry, a QR or certificate link, warnings) is lost. Keep the set of frames that carries all of that text.

### 7. Upload and map to products

- A typical admin upload API needs the file bytes. It does not fetch a URL. Download and stage the file first, then send the bytes.
- Name every staged file with its product code and role, for example `<code>_<role>_<index>.webp`, and keep a manifest of file name, product code and role. The upload response gives back only an ID and a URL, so the manifest is the only link back to the product.
- Write the returned ID and URL into the manifest immediately, keyed by product code.
- Product-level images are set on the product. Variant-level images are set through the variant's metadata or a separate link, depending on what the platform supports. Check the platform's documentation for which one exists before you choose.
- Metadata writes often replace the nested object. Read the current value first, merge your change, and send the whole object.
- Re-host any third-party image into your own storage before publishing. Retailer and brand URLs go missing or change without notice.

### 8. 3D assets (GLB) compression

1. Inspect first and save the output. Record the bytes by category (geometry against textures), texture sizes and formats, and vertex counts. The next worker should not have to repeat this.
2. Texture-heavy meshes: resize textures to 2048 or smaller (only when textures dominate), remove duplicate and unused data, and convert to WebP. This often meets the target.
3. Draco or Meshopt: add a geometry codec only if the existing loader already includes its decoder. Adding a new decoder is a separate change for approval, not part of a compression change.
4. Simplify geometry only as a last resort. Accept it only when the kept-triangle ratio is at least 0.75 and the error is at most 0.001. Do not weld vertices in a way that collapses hard creases on character meshes.
5. Keep node and material names unchanged, so downstream code finds the same IDs.
6. Compare the original and the compressed asset side by side with the same render code. Use fixed camera angles and save stills at a fixed size. The mean absolute pixel difference per pair should be below 1 percent. Print the file sizes and load times beside each.
7. Commit only the asset. Leave the comparison page out of the repository, and check the status to confirm.

### 9. Intake monitor for a shared photo folder

Use this only for a folder you are authorised to read. Keep the monitor read-only and separate from any processing step.

- Poll every two minutes. List only the direct children of the folder that are images and not in the trash.
- Deduplicate by the platform's file ID, never by file name.
- On the first run, record the existing IDs as a baseline without alerting.
- For later new files, send one grouped alert per poll with the metadata and the folder link. Do not download or send the image bytes through the alert channel.
- A single API failure is silent. Alert only after three failures in a row. An expired credential stops automated processing until the owner re-authorises it.
- Request only the read-only access scope. Do not add mail, calendar, contacts or document scopes for this job.
- Treat the state file as valuable. Deleting it re-baselines every file and sends a flood of alerts. Back it up and get approval before any reset.
- Put any later processing step in its own job. It reads file IDs from the monitor's state, writes under its own work folder, keeps an append-only ledger with retry and dead-letter handling, and never changes the original files.

## Pitfalls

- **"All done" needs a count.** Compare the original tree with the processed tree before believing a worker's report. A large gap is the warning sign.
- **A template can change regulated text.** Run OCR on the result and check the numbers. A label that reads the same to OCR can still look different from the pack.
- **A soft "is this a whole product" check breaks close-ups.** Use the measured edge and border rules, then check the output alpha.
- **A batch that started under an old specification keeps running on it.** When the spec changes, stop the batch, then rerun it. Report the credits you spent on the first attempt.
- **A window bound only to the loopback address is invisible to the operator's device.** Serve it on the private network for the review window and test from the device.
- **A harness script is not a process supervisor.** A server started inside a script that exits stops with it. Start long-lived servers as background processes, then check the port again.
- **Rejected files are moved, not deleted.** Keep them in a holding folder and record each move in the manifest.
- **Segmenting on "has a barcode" splits series badly.** Barcodes appear in many frames. Split on a change of payload.
- **Reviewers drop extensions and mix case.** Normalise names against the authoritative file list before any check, and glob both upper and lower case.
- **Rotation from EXIF is not always right.** Check one sample by eye before applying a rotation to the batch.
- **A one-photo series can be real.** Flag it, keep it, and give it both suffixes.
- **A multi-pack can need every face photographed.** Accept a keep-all verdict when the reviewer names what is unique in each photo.
- **A metadata allow-list drops new fields.** Collect every non-empty value and deny only identifiers and errors.
- **Browser caches keep old images.** After a swap, read the served files directly before judging the result.
- **Admin pickers can reject large originals.** Upload originals through the API. Do not ask the operator to compress them.
- **Cropped labels fail as heroes.** A close-up of a label, code or panel is never the hero or thumbnail.

## Verification

For a photo template run:

- The original-tree count equals the processed-tree count within the declared scope.
- The list of close-ups that skipped the template is in the report.
- OCR shows no change in any strength, count, serving or net-weight field on regulated products.
- The proof sheet was approved in writing before the full run.
- Broken cutouts were reclassified and went to the compressed-original path.
- The catalog write happened once, after approval, with the counts before and after.

For a shoot-folder prune:

- Thumbnail count equals source count.
- Keep and prune sets together equal the file list, with no overlap.
- Each series has one barcode frame and one hero, and the hero is one of the kept frames.
- Kept plus pruned equals the original count, and nothing was deleted.
- The manifest matches the files on disk.

For a 3D compression run:

- The inspection output is on disk.
- The loader code is unchanged, or the decoder change has its own approval.
- The side-by-side page answers with HTTP 200 from another device.
- The mean absolute pixel difference is under 1 percent for each pair.
- `git status` shows only the asset change.

For an upload:

- Each file's signature matches its type before upload.
- Each returned ID and URL is written to the manifest.
- A fresh read shows the expected images on each product and variant, and a second run changes nothing.
