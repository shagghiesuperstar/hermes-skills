---
name: regulated-commerce-compliance-gates
description: Use when adding state, age or license gates to a store. Covers one legal blocklist, fail-closed checks, cache-stable pages, a dark-launch arming sequence and verification by hash.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [compliance, state-gate, age-gate, license-gate, checkout, medusa, regulated]
    category: commerce
related_skills: [catalog-publish-safety, regulated-catalog-content, medusa-docs-first]
---

# Regulated Commerce Compliance Gates

## Overview

A regulated store can be sold in some places, to some buyers, under some conditions, and not others. Three gates decide that: a state gate (which jurisdictions may receive a product), an age gate (whether an extra age acknowledgement is required) and a license gate (whether the buyer's company holds the license for a product class). Each gate can break a store's legal position or cost revenue when it is wrong, so the design keeps one legal artifact as the authority, makes every check fail closed, keeps server pages identical for every visitor, and arms each gate only after it has been tested against the live provider.

## When to Use

- Adding a state, age or license restriction to a product class.
- Changing the shipping blocklist, the product metadata that drives it, or the storefront that displays it.
- Wiring a hosted age-verification provider into the checkout sequence.
- Auditing an existing gate before arming it.

Skip it for stores with no jurisdiction-specific rules, and for the content side of compliance (use regulated-catalog-content).

## Features

- Three separate gate axes, each with its own product field, so a rule for one axis never silently changes another.
- A single blocklist file, mirrored byte for byte to the storefront and checked by hash.
- A backend enforcement point at cart completion and before payment, with storefront filtering as display only.
- A pre-paint attribute pattern that keeps server HTML identical for every visitor.
- A dark-launch sequence for age-verification providers, with a matrix test run immediately after each arm.

## Benefits

- The legal decision is made in one place, and every copy of it is checked by hash.
- A visitor never sees a product the backend would refuse, and the backend refuses what the storefront shows.
- A misconfigured provider fails closed, so the gate blocks the sale instead of letting it through.

## Procedure

### 1. Keep the three axes separate

- **State restriction:** a product class maps to a list of blocked jurisdictions. A cart whose shipping state is on that list cannot use the product.
- **Age restriction:** some classes require an extra acknowledgement beyond the store-wide minimum age. Each class has its own stored acknowledgement.
- **License restriction:** the buyer's company must hold the license for the class. This check belongs to the buyer account, not the product, and the gate design touches it only where the checks are combined.

Never combine the three into one flag. A product can be legal in a state and still need an extra age step, and one combined flag forces a wrong answer for one of them.

### 2. Apply the invariants to every change

1. **One blocklist.** The shipping blocklist in the backend data folder is the legal artifact. Every storefront copy must be byte-identical to it. After every change that touches either file, compare the SHA-256 digests of both files. They must match. Check by hash, not by reading the contents.
2. **Legal backbone and display are separate.** The backend middleware and the cart-completion hook enforce the rule. The storefront only filters what it shows, and it reads the same blocklist and product metadata. Never add a storefront-only rule that the backend cannot reproduce. Never change the backend blocklist to make a storefront display work.
3. **Cache-stable server HTML.** Public pages use the same cache headers for every visitor, and server-rendered HTML must be byte-identical for every visitor. No server component branches on shopper state, no redirect depends on local storage, and no response varies by cookie. All per-shopper filtering runs in the browser after the first paint.
4. **Absent data means block.** A product with no gate value does not ship anywhere until the owner approves a different default. A missing value is a gap to fill, not a reason to show the product.
5. **Combine gates with AND.** A product is hidden only when every gate that covers it blocks it.

### 3. Build the pre-paint pattern

For each gate that reads shopper state:

1. Give the stored acknowledgement a stable key with a version suffix, one key per class, so each acknowledgement can be cleared on its own.
2. Add a small inline script to the root layout. It copies the stored values onto attributes on the document element before hydration. Reuse the shape of the existing age-gate script in the same repository.
3. Write a synchronous reader. It reads the attribute first, falls back to the stored value, and returns a stable value for the initial render state.
4. Filter the product lists, product pages, cart lines and any downloadable documents after mount. The server HTML stays unchanged.

When a component mounts before the script runs, its first render can flicker. Confirm by comparing the server HTML with the hydrated page in the browser's developer tools. A flicker means the script ran too late.

### 4. Extend the blocklist only under the cadence rule

Adding a new class to the blocklist is a separate change that the legal owner approves on a fixed cadence.

1. The legal owner updates the external matrix and supplies the new class definition and its blocked jurisdictions.
2. The approved change updates the backend blocklist.
3. A follow-up copies the file to every storefront location, checks the SHA-256 digests, and commits.
4. A metadata change tags the affected products. Write product metadata through the admin endpoint for that product, one product at a time. Do not use a bulk product import for metadata, because a bulk import can recreate variants.

A storefront-only change must never add a class to the blocklist. If a product needs a class the blocklist lacks, stop and ask for the change to go through the cadence process.

### 5. Keep the metadata vocabulary fixed

Two product keys drive product-level gating: one for the state class and one for the extra age class. Use only the values the owner has approved. Adding a value is a decision for the owner, not for the person writing the change.

### 6. Split file ownership when several people work on one gate

Give each file one owner. The only file several changes may touch is the blocklist, and only the legal-owner change touches it. Keep the layout file to one mount line from one change, and keep product-list rendering and the cart in their own owners. Two changes that edit the same layout or product module will conflict, so check ownership before work starts.

### 7. Verify after every change

1. Compare the SHA-256 digests of the backend blocklist and each storefront copy.
2. Confirm that no protected file changed. Compare the enforcement middleware, the cart-completion hook and the storefront against the base branch.
3. Request one product page twice with different user-agent headers. The two bodies must have the same length and the same digest. A difference means a server component branched on shopper state.
4. Run the existing test suites for the state, age and ship gates.
5. Test with three products: one with only a state class, one with only an extra age class, and one with neither. Change the test state to a blocked jurisdiction and confirm the displayed products and the checkout refusal match the matrix.
6. End each verification with a sentence on what it cannot detect. For example, a matching hash does not detect a parallel branch with a different blocklist.

### Age-verification provider integration

Hosted age-verification providers are easy to wire wrongly, so the integration follows strict rules.

- **Fail closed.** Only a successful server-to-server decision counts as a pass. An error, a timeout or a parse failure is a refusal.
- **The redirect and the webhook are hints.** The browser redirect and any webhook body are unsigned. The webhook only tells the server to ask for the decision again.
- **Evidence is signed and bound.** Evidence carries a signature, is bound to the cart and the email, and is checked against the current age threshold configuration.
- **Ship dark.** The provider is enabled only when its flag is exactly the string `true`. Other values such as `1` or `yes` leave it off, and a unit test should assert this.
- **Register the data module.** Any custom data module used by a route must be registered in the backend configuration. A route can compile and pass unit tests and still fail at runtime when the module is missing, so the live environment test is the third gate.
- **Add a migration.** A custom module needs its own migration file, or its table never exists in the hosted environment.
- **Keep the raw body.** Signature checks need the raw request body. Enable the raw-body option for the webhook route, or the check silently does nothing.
- **Trigger a build after every environment change.** Environment variables on a hosted platform do not take effect until a build runs.

### Arming sequence

1. Create the verification workflow through the provider's API and record its ID.
2. Create the webhook destination and store its shared secret.
3. Stage the environment variables in staging first, never in production first.
4. After the operator's go-ahead, on a clean, pushed tree, trigger the build and wait until it is active.
5. Run the matrix: the provider flag reads on, a session starts, a pending status is reported, a decision poll returns, an unsigned webhook is rejected, and payment is refused while the buyer is unverified.
6. A person completes the hosted flow on a phone. Only then does the decision change and payment unlock.
7. Arm the next environment only after the previous one passes.

An armed gate with broken keys blocks every checkout, so run the matrix immediately after arming.

### Provider rules that prevent incidents

- Identity-scoped evidence binds to the authenticated actor, not to the cart's customer ID, because the cart's customer ID can be set from an unauthenticated email lookup.
- A route that turns verification into a reusable credential requires a server-minted proof that the caller holds the cart. A cart ID alone must never be enough.
- Changing a provider's workflow does not change which workflow the store selects. Check the deployed configuration and a session result.
- A simulated approve or decline in a sandbox proves only the provider's sandbox behaviour. It does not prove the callback, the webhook, the cart binding or payment.
- Redirect targets must be deployed routes that render without the desktop cart cookie, because a mobile device may complete the flow.

## Pitfalls

- **A nav category as the only gate** hides products by category but cannot separate two products in one category with different classes. Keep the category filter and add the per-product gate on top of it.
- **Cloning a product to work around a missing field** creates duplicate content and cart problems. Set the field or block the product.
- **Adding a class silently** invents compliance rules. The owner decides.
- **Hiding a hydration warning** with a suppression flag hides the cause, which is server HTML that branches on shopper state.
- **A bypass for a subset of products** is a new feature with its own review, not a configuration change.
- **Dark launches** must stay dark until tested. A flag that defaults to on, or a missing secret that leaves a route dormant without an error, is an incident waiting to happen.

## Verification

- The SHA-256 digests of the backend blocklist and every storefront copy are equal, and the result is recorded.
- Protected enforcement files show no change against the base branch.
- Two requests with different user agents return identical server HTML.
- The matrix results for the three test products match the rules.
- The provider's matrix passes in each environment after its build, and the arming decision is recorded with the person who approved it.

## Attribution

The age-verification integration follows the provider's public API documentation for workflows, sessions and webhooks. Check the provider's current documentation before relying on any endpoint shape.
