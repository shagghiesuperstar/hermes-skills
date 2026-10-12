---
name: storefront-visual-acceptance
description: Use when accepting storefront visual changes. Covers fixed-canvas heroes over CSS backdrops, scroll-driven entrances, product grids and commit-pinned preview evidence.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [visual-acceptance, storefront, screenshots, animation, preview]
    category: web-quality
related_skills: [preview-env-qa, ui-sibling-symmetry, storefront-accessibility-audit]
---

# Storefront Visual Acceptance

## Overview
Visual acceptance decides whether a storefront change looks right on a real render, not whether it deployed. HTTP 200 and a matching string in the HTML do not show that a hero paints, a heading wraps cleanly or a product image is cropped. Acceptance needs a rendered capture at the agreed viewports, measured values for the claims that can be measured, and one explicit verdict per item with its evidence.

## When to Use
- A change touches a hero, a product grid, a product page, the navigation or the footer.
- A change adds scroll-driven entrance animations or a fixed WebGL or canvas layer.
- Someone asks for live proof that a deployed preview shows a change.
- A review needs a verdict on a visual change, with evidence attached.

## Features
- A design rule set for storefront surfaces, with the reason for each rule.
- An acceptance workflow that requires a real render with real catalog data.
- Screenshot and measurement recipes: first viewport, first long scroll, and pixel checks.
- A paired A/B probe for a canvas layer over a CSS backdrop.
- Checks for scroll entrances that do not stay hidden in captures.
- A verdict format that ties every criterion to a measured value or a file and line.

## Benefits
- A visual change is judged on what a visitor sees, not on the CSS that was written.
- Claims come with a number, so a reviewer can re-check them.
- Decorative layers are checked against the content they must never cover.
- Captures are named and kept in a way that keeps the full-viewport evidence intact.

## Procedure

1. **Require a real render.** Check the change on the branch's own storefront with real catalog content. A compiled CSS demo, a static mock or a synthetic tile fixture is not proof of the storefront layout.

2. **Confirm the served build first.** Before you capture anything, run the four checks in `preview-env-qa`: the listening process, its working directory, the build identifier, and the marker strings in the served HTML. Capture only after all four match the change under review.

3. **Capture at the agreed viewports.** The default pair is 1440 x 900 and 390 x 844. Responsive changes add 360 x 780 and 430 x 932. For each page, capture the first viewport and the first long scroll. Set small widths through device-metrics emulation, not window size.

4. **Drive scroll animations to completion before capturing.** Scroll in fixed steps through the full page height, return to the top, and wait until the entrance has finished. A capture taken mid-animation or before any scroll is not evidence of the final state.

5. **Check each design rule that applies** (see the list below) against the captures and the DOM.

6. **Measure what can be measured.** Read computed opacity, bounding boxes, text content, and the fraction of non-black pixels in each section. Quote the measured values in the verdict.

7. **Keep captures without overwriting.** Store per-fix before and after captures in the drop folder under new names. Save crops under new names too, so the full-viewport evidence stays intact.

8. **Write the verdict.** Use one of three forms: `AGREE`; `DISAGREE` with the file and line or the measured value that disagrees; or a discussion note, which is not a verdict. A review with no measured proof for a hero, a story section, a ticker, a header or a product-page redesign is a self-approval, and should be returned as DISAGREE.

9. **For a stills-only order, deliver stills only.** Deliver the named PNGs at the requested path, and a numbered PASS or N/A line for each named item with its evidence value (video time, geometry measure, OCR text) and the stated session assumption (for example "guest session, sign-in expected"). Do not add critique that was not requested.

### Design rules

- **No dangling words in headings.** A two-sentence display heading breaks after the first sentence, so the second sentence starts its own line. Use a real line break in the string and `whitespace-pre-line` at each render site. Check at 390 and 1280. The DOM proof is a line break in the heading's text.
- **Products win.** Decorative artwork never covers product images, names, prices, copy, buttons or navigation.
- **Use the approved brand asset.** Do not regenerate or overwrite an approved logotype. A large decorative logotype sits in its own reserved strip, behind commerce content, not floating over it.
- **Keep lighting subtle.** A CSS drop shadow is not scene lighting in a 3D scene. Light a 3D model with the scene's own light.
- **Reserve the gutter by breakpoint.** Above a chosen width (for example 1280 px), reserve a gutter for decoration. Below it, hide the decoration and collapse the gutter. Keep the masthead logo at every width.
- **One type scale for sibling navigation.** A category rail and its homepage jump list use the same classes, label and face. A second type scale on one of them is a defect.
- **Masthead and rail share a face and weight.** Use the display face's own weight. Do not apply a synthesised bold to a condensed display face.
- **Align footers to visible artwork.** Match the left edge of a logotype's visible glyph, not the container edge, because SVG whitespace shifts the box. Check desktop and mobile.
- **Short product-card names.** Use the family or form and the essential size, count or strength. Drop redundant brand prefixes. Display cleanup never changes the canonical catalog title, identifiers, prices, stock or compliance data.
- **Show stock only from the data.** If the backend tracks inventory, show the count on the product page. Confirm the label in the client bundle, because an HTML-only check can miss it.
- **Show one of two options that encode one choice.** If two option groups map one-to-one to the same SKU, show only the one that selects the SKU. Keep the other in the data, and apply the rule to every product with that pair.
- **Open the gallery on the hero photo.** The default image is the head-on product shot, not a close-up of a barcode. Reorder the gallery; do not delete the close-up frames.
- **Never render an empty accordion.** If product metadata is missing, say so and offer a catalog write. Do not fill the panel with invented content.
- **Scroll the two product columns independently on desktop.** Give each column a maximum height of the viewport minus the masthead, with its own overflow. Mobile keeps normal page scroll.
- **Anonymous chrome must match anonymous state.** On a wholesale or account-gated storefront, any sign-out state that shows an account link is a defect.

### Scroll-driven entrances

- Do not start a load-bearing entrance at opacity 0. A small translate from a visible start is safer, because a capture or crawler that does not scroll still sees the content. Reserve opacity fades for ambient layers.
- Verify the entrance fired in the capture, not only that the rule exists. After scrolling to the bottom and back, check that the computed opacity of every entrance target is 1.
- Prove the bands are painted. For each section's bounding box in a full-page capture, measure the fraction of non-black pixels. A section below about 5 to 10 percent is still at its start frame.
- Gate the animation behind `prefers-reduced-motion: no-preference` and `@supports (animation-timeline: view())`, so reduced-motion users and unsupported browsers see the content at once.

### Canvas over a CSS backdrop

- A fixed backdrop changes what a pixel mask reads. Hide every backdrop layer by its exact selector when you measure the canvas alone, and say that you did.
- Report two metrics. Canvas-only is the regression gate, because it does not depend on backdrop alpha. A paired A/B probe is the perception gate: capture with the backdrop hidden, restore it, wait briefly, capture again on the same pixel mask, and report both differences. Either alone is incomplete.
- When tuning one number (light intensity, fog density, blur), sweep at least five values that bracket the current baseline, with at least three frames per value. Pick the smallest value whose median clears the target band, and report the whole curve.
- Reduced motion can stop a WebGL canvas in headless browsers. Use the no-preference setting for paired captures; reduced motion is fine for static reads.
- To show a before state for a CSS-only fix, inject the old rules into the current build and capture it as `before_sim`. Do not check out an old commit, because that changes the working tree and undoes unrelated work.
- Opaque cards cover the backdrop in some scroll positions. Count them per route and width, and leave them out of the brightness-minimum check. The probe must tell "the backdrop painted nothing" apart from "a card covered it".

### Video heroes

- Autoplay is blocked by default. Wait until the video reports data and has played past a threshold before capturing. If the video is stuck at its first frame after a dialog closes, seek to a later time and play, without reloading the page.
- Keep a poster or a moving layer for the hero at every width. Do not remove a hero video on a device class to save bytes. Defer its load instead: show the poster first and start playback when the hero is in view.
- If lower sections keep their media, the hero keeps its media too.

### Preview-stills proof without a vision model

- Open the page in a named, isolated browser session, and confirm the URL again before each capture.
- On a preview you operate, click a visible age or consent confirm control exactly as a visitor would: outside any form, once per fresh browser session. Record that the click happened, then capture. Leave region pickers and any control inside a form unclicked, and capture with the dialog showing, saying so in the proof.
- Never preset stored choices or hide a modal with CSS, because that changes what the proof shows. Never click any control on a third-party site.
- Copy each capture to the drop folder in the same call that makes it. Browser tools often write to their own scratch area.
- Verify with OCR for the expected strings (presence only, since OCR misreads letters) and a pixel-bucket histogram that confirms the layer painted. Take layout facts from DOM rectangles and text, not from OCR.

## Pitfalls
- **Do not overwrite full-viewport evidence with crops.** Name crops with a suffix such as `-nav-crop.png`, so the full capture stays available.
- **Do not make deliverable stills read-only.** A read-only file breaks the next legitimate overwrite. Keep a `locked/` snapshot folder for finished captures and leave working files writable.
- **Check the drop folder after any capture error.** A capture that ends in a script error can still write files. List and size-check the folder before you report paths.
- **OCR is noisy.** A brand name may come back with a digit in place of a letter. Use OCR for presence of expected strings only.
- **A dev server can serve a stale layout on some routes.** After a layout-level change, check every route family for the new marker, not one route. Touching the framework config file restarts the dev server's child process, which fixes a stale cache on some builds.
- **A sitewide fixed overlay breaks pixel samplers.** Samplers that look for low-saturation surface pixels read the overlay, not the 3D model. Hide the overlay for lighting checks, and report both numbers.
- **Window size is not viewport size.** The operating system clamps small windows, so a 390 window flag can measure a wider viewport. Use device-metrics emulation and assert the client width.
- **Routes can differ in chrome.** The same preview can serve a listing page with one heading style and a category page with another. Reproduce the exact route the reviewer named before you claim a fix.
- **A local-only bind is not an operator-facing preview.** If the server listens only on the loopback address, name it as an internal preview that other devices cannot reach.
- **A hung preview server needs a restart, not an argument.** Restart it on the same port. Bind it to a private-network address only with the operator's approval, and state what that exposes. Then verify the local address before reporting it.
- **An exit notice invalidates the old URL.** Before saying the preview is up, check the port again. A process that exited with code -9 or 1 is not evidence about the current one.

## Verification
- Each claim has a capture at the stated viewport, with a file name that says what it shows.
- Each measured claim quotes its value (opacity, bounding box, pixel fraction, video time) with the command or script that produced it.
- The served build was confirmed by the four checks in the same turn as the capture.
- Every verdict line is `AGREE`, `DISAGREE` with evidence, or a discussion note, and nothing else.
- Before any capture is handed off, the drop folder's file names, sizes and OCR presence checks were re-run in a fresh call.
