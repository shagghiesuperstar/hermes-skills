---
name: browser-smoke
description: Use when a live app needs a scripted smoke test. The interactive browser cannot authenticate or capture network evidence. Covers headless runs, request capture, redaction and blockers.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [qa, smoke, playwright, har, storefront, checkout, browser]
    category: web-quality
related_skills: [preview-env-qa, storefront-compliance-sweep, medusa-api-verification]
---

# Browser Smoke Test

## Overview

A smoke test confirms that a core flow works from start to finish and keeps the evidence. This skill covers two modes: a scripted headless run for flows that need a login and a network trace, and a read-only browse of a public storefront. In both, the output is a short result with what was verified, what was blocked, and the artifacts. A gate or a challenge is a blocker to report, not an obstacle to get past.

## When to Use

- A login, cart, checkout-start or account flow must be verified, and the interactive browser cannot sign in or capture the network traffic.
- A public storefront needs a signed-out browse: pages load, the catalog is visible, product variants behave, and the cart reads correctly.

Skip it for checks that need only an HTTP response. Never use it to submit real payment data (see Blockers).

## Features

- A Playwright script with three layers, so a failure points at one of them: capture, sign-in and the flow.
- Gate handling by dismissal through the interface, with the choice recorded.
- Assertions before and after each state change.
- Request-log analysis that confirms the expected write request fired.
- Redacted artifacts with a result file that puts the bottom line first.
- A signed-out storefront checklist with severities.

## Benefits

- Failures are located to one layer.
- A button that looks fine but fails on the server is caught by the request log.
- Evidence can be shared without credentials or personal data.

## Procedure

### Part A: Scripted headless run

1. Launch the browser headless with the Chrome install on the machine. Verify the launch on a trivial page before writing the full script.
2. Supply credentials through a secrets wrapper that places them in environment variables. Never put a secret in a command argument or in the script body.
3. Structure the script in three layers. Capture: record every non-GET request, and the status of each cart and checkout route. Sign-in: fill the named fields and submit, and press Enter in the password field if the submit control cannot be found. Flow: the steps under test.
4. Handle age, consent and region gates before the first click on any protected page. Wait briefly. A full-screen modal intercepts pointer events, so every click retries until it times out. On a site you operate, the operator is the one attesting the age check, so click the visible age or consent confirm control only when the operator asks for that test, exactly as a user would, once per fresh context, and wait for the dialog to close. For a region or state picker, make a selection only when the request names one. Never click a control inside a form, and never hide a gate with CSS or stored values. On any third-party site, stop at the gate and report it.
5. Set quantity and numeric inputs by writing the value through the element's native value setter, then dispatch the input and change events. A locator click followed by a fill often hits the same overlay, and framework-controlled inputs need this form too.
6. Before and after each state-changing click, assert the button's disabled state, its label and the empty-state marker. A button can be enabled and still fail on the server with nothing visible on the page.
7. After the run, parse the capture: list the non-GET requests with method, path and status, and confirm that the expected write request fired. An add-to-cart action that posts only to the page address with a streaming response type is a framework server action. A 500 there means the action failed, and the page may show no error.
8. Redact before sharing. Remove cookie and authorization headers, and replace personal details in request and response bodies. Write a result file in the same folder as the capture, the screenshots and a summary. Put the bottom line first: what was verified, what was blocked, and the list of artifacts. Print summary keys in upper case with an equals sign, so they can be quoted without parsing.
9. Copy the script to a dated backup folder before editing it.

### Part B: Signed-out browse of a public storefront

Use the interactive browser tools where they are available. Stop at the cart boundary. Do not go to checkout, sign-in or account creation, and never enter payment details.

1. **Confirm the host.** Use only the host named in the request. If a redirect leaves that host, stop and report the redirect. Never fall back to a sibling domain.
2. **Dismiss gates through the interface, in order.** On a site you operate, click a visible age or consent confirm control exactly as a visitor would, outside any form, and record which control was clicked. On any third-party site, stop at the age gate and report it. For a region or state gate, choose a location only as the request allows, and record the choice. For marketing dialogs, use the close control. Never preset stored values or hide a dialog with CSS. Record each gate, its button text and any stored flags.
3. **Structural pass on the home page.** Record the title, the first-level heading, the navigation labels, the landmarks, the dialogs, the navigation destinations, which structured data is present or missing, the cookies set, and the console messages.
4. **Catalog pass.** Count the products on the first page and confirm the pagination. For each card, record the name, price, stock indicator and call to action. Check that a card's call to action does not lead to a page where every variant is out of stock.
5. **Variant pass.** For each product with variant selectors, select each variant, wait briefly, and record the call-to-action state, the stock count, the price and the availability in structured data. Record the variant identifier from the address after selection. Where a certificate link exists, it must return a success status and a document type. Mark every variant that was not visited as not checked.
6. **Cart pass, read-only.** Add one in-stock item. Read the cart drawer and the cart page: item, variant, quantity, price, subtotal, shipping copy, tax and total. Shipping shown as calculated at checkout is not a defect, so say so. Check that the remove control has an accessible name. Remove the item and confirm the empty-state text.
7. **Console pass.** Read errors and warnings separately. Real errors rank above deprecation warnings, and application debug logs rank lowest.
8. **Report.** List each finding with its severity, its evidence (address, element and observed text), and one tag: VERIFIED, UNKNOWN or INFERRED.

### Blockers

- A browser challenge page means automated access is blocked. Report the block with its status and the page title. Do not attach a separate browser to the user's session, and do not change the client's identity to get past the challenge.
- A system permission that disables remote automation is a gate for a person to change. State it plainly, and fall back to plain HTTP checks. Note that plain HTTP checks cannot read the console or click controls.
- A flow that stops before the payment step is a result. Record the blocker and stop.
- Never submit real payment details, and never charge a card in a smoke test.

## Pitfalls

- **A click timeout is not proof that a button is broken.** The retry log names the element that intercepts the click, and that overlay is the finding.
- **Separate server errors from flow errors.** A server error on a page post is usually a content problem. A client error from a checkout interface is usually a flow problem. Record the content type and a snippet of the response for both.
- **Probe the live catalog before the flow.** Check which products are published while signed out. A smoke-test product that is unpublished renders as not found after sign-in.
- **Single-page applications return empty bodies to plain requests.** Use a browser for them.
- **Read a cart count twice, a few seconds apart.** Counts can load late, and an early read reports a false defect.
- **Icon-only buttons have no visible text.** Find them by position in the markup, and flag any that lack an accessible name.
- **A background tab may not render.** Bring the tab to the front before reading the layout.
- **Do not infer one variant's state from its neighbours.** Select each one.

## Verification

- The result file lists the verified items, the blocked items and the artifacts, with the bottom line first.
- The capture contains the expected write request with its status, or the failure is reported with its status.
- No credential, cookie, authorization header or personal detail remains in shared artifacts.
- Every gate encountered is recorded with the choice made.
- Each finding has a tag and its evidence.

## Attribution

The signed-out browse checklist is adapted from the Eidolon project's browse-only smoke procedure (a public project by the same publisher).
