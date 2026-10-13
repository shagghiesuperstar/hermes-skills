---
name: storefront-release-publish
description: Use when publishing a Medusa storefront or backend. Pins the approved commit, proves the live build, and runs layered checks before calling the release live.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [medusa, cloud, release, storefront, compliance, publish, production]
    category: devops
related_skills: [medusa-cloud-ops, preview-env-qa, prod-deploy-verification, adversarial-review, minimal-change-operator]
---

# Storefront Release Publish (Medusa Cloud)

## Overview
This skill takes an approved storefront and backend release from approval to live on production, with proof. The readiness signal is end-to-end correctness: the running commit matches the approved one, pages render, the cart shows money, compliance and gating behave, and a visitor sees no placeholder text. A green build proves none of those on its own. Use a how-to for the cloud CLI (see `medusa-cloud-ops`) for plain platform questions, and `preview-env-qa` for a check that stops before production.

## When to Use
- Publishing a merged storefront and backend release to a production cloud environment.
- A release needs a multi-jurisdiction compliance sweep alongside the publish.
- A cloud build failed and needs a local reproduction.

Not for listing deployments, debugging a build with no release in flight, or preview verification on its own.

## Features
- Release metadata recorded before any platform call.
- A pinned merge commit, so the approval attaches to one commit.
- An identity-first preflight: the live version endpoint must report the approved commit.
- Layered live checks: HTTP and header checks, a compliance sweep, a browser walk, and a visitor-eye copy check.
- A windowed error-log check against a baseline.
- A rollback prepared in parallel with the publish.

## Benefits
- Live state is proven against the artifact under review.
- Each check catches a different class of defect, so no check is redundant.
- A bad release has a rollback ready before it is needed.

## Procedure

Before the first step, apply these ground rules to every production deploy: pin each package version, so that no install picks a version at run time; never use an install flag that confirms prompts automatically; require a clean, pushed working tree; and get an explicit operator go-ahead for this deploy. A release script must refuse to run on a dirty tree, and it must never commit dirty files.

1. **Record release metadata before any platform call.** Write the UTC time and the release commit to files. Also record the live commit that the version endpoint reports, at the same moment. Every later probe that asks whether this build is live compares against these records.

2. **Merge to a pinned commit.** Merge only after the operator's go-ahead, from a clean, pushed tree. The approval attaches to one commit SHA, and the merge must end on that SHA. A squash creates a new SHA with the same content, which breaks the link to the approval. Record the post-merge SHA separately if you need to compare the reviewed commit with the published one.

3. **Trigger the build, after the operator's go-ahead, and let it run.** List the platform's deployments and wait for the build to reach deployed. Take the build identifier from the first succeeded row. Do not poll the CLI in a loop.

4. **Run the identity preflight every time.** Read the production backend's version endpoint and assert three things: the commit equals the release commit, the provenance field names the platform's commit variable, and the build timestamp matches the platform's build. Stop if any field disagrees. A green build with a different commit is not the approved release. Treat a storefront version stamp that never changes as informational, never as proof.

5. **Run the live checks in parallel.** Each surface reveals a different defect:
   - *HTTP probe* (GET only): pages return 200, security headers are correct, brand tokens are in the stylesheet, the mandated disclaimer matches its pinned hash, and the key static assets load.
   - *Compliance sweep*: fetch the main pages per jurisdiction in a headless browser, and check for leaks and over-hides against an expected-count oracle. Build the oracle from an admin pull, and check its values against the release's own table first. A cached page can make a sweep read stale data.
   - *Browser walk* (fresh profile, signed out, no cart): check page width against viewport width at desktop and mobile sizes, the order of the gates, and that visual effects behave as specified.
   - *Visitor-eye copy check*: crawl every header link, footer link and category page. Record the business name, the contact details and the disclaimers exactly as shown. Flag placeholder words (lorem, TODO, undefined, NaN, object placeholders) and images that fail to load.

6. **Run the post-publish error-log check over a window.** Query error logs from the release time onward, and compare the count with the pre-publish baseline. The twice-the-baseline threshold is a judgment that treats normal variation as acceptable. A count above it is reported for review as a possible leak, and the report states the threshold and why it was chosen. The owner can set a different threshold. Schedule next-day checks for the coverage and gate counters the release claims.

7. **Pre-stage the rollback.** Prepare the previous release (its commit checked out, its build re-runnable) while the publish runs. The rollback deadline is a hard gate, not a reaction time. Once a failure is discovered, a clean rollback may no longer exist.

## Pitfalls
- **Merge with the release marker in the pull request body.** A bare squash can drop the body, and the build trigger may read the marker from there. The merge step must read the marker back from the commit message and fail if it is missing. Never merge with a bare squash.
- **Poll the live version, not one build identifier.** A build can be superseded or cancelled while its storefront still deploys. Start the next step as soon as the live version or the new route answers, whatever the build status says.
- **Check that the cart shows money.** Pages can return 200 while the cart shows zero and checkout cannot advance. After the version matches, add one item to a reused test cart, check that the subtotal renders, and remove the item. Never place an order. A store-API field list must add fields with an explicit prefix. A bare path replaces the defaults.
- **Version endpoints can be cached for a long time.** A cached version can keep returning an old commit after the new build is live. Cross-check the platform's deployment record for the head commit and its deployed status. The deployment record is authoritative. The version endpoint corroborates it.
- **Check canonical links after a domain change.** A build can bake in the old platform domain. After every build on a moved domain, fetch the canonical link, the og:url and the sitemap locations on the public domain. Any platform domain means rebuild the same commit.
- **Build triggers can bake different values.** A push-triggered build and a manual trigger can read different environment values. While a domain is moving, freeze merges that would trigger a build, and queue the corrected manual trigger in the same turn as any merge you cannot avoid, and only with the operator's go-ahead.
- **Reproduce a cloud build failure locally with the cloud's install.** Use the same lockfile install with exact versions, then the cloud's build script. Peer-dependency ranges that resolve to different versions are the usual cause. Pin the affected versions exactly.
- **A release script must check the live commit before it acts.** Its first step compares the live version with the recorded one, and it exits non-zero on a mismatch. A release that continues on a stale record ships on top of the wrong head.
- **Do not bundle unrelated changes into one release.** Ship the lowest-risk change first, with its own review and merge. Then one regression cannot block the others, and the rollback stays unambiguous.
- **Placeholder text fails the visitor test.** Before you call a new site live, grep the home page and every footer-linked page for placeholder tokens such as TBD, TODO, lorem or a bracketed name. Replace them with empty-state wording a visitor can read, and keep the operator's notes in the readme.
- **Custom fulfilment providers can pass plain tests and fail in the container.** The framework's dependency container can throw on keys it does not register. Read every optional dependency through a guarded lookup, and never throw from a price calculation: return the base price and log a warning. After release, call the live shipping-options write and check for a success response. A succeeded build does not prove the provider runs.
- **Grandfathering existing eligibility records is a compliance decision for the owner.** Until the owner decides, the gate stays closed: existing approved records are blocked at their next checkout, and the release report says so. Do not add a grandfathering value or a migration that marks existing rows as approved without the owner's written decision. When the decision is made, record it in the pull request body and check the approved rows for missing values before the merge.
- **Copy must state only what the document itself shows.** A certificate note that asserts a quantity or a value the document does not state is a finding. Re-read the document and keep only its stated values. Refresh vendor copy from the live document, not from memory.
- **When a deadline is tight, report the head and the impact first.** Give the head SHA and the impact in one sentence, then the next action. Do not wait on a decision that the procedure already settles.

## Verification
- The release metadata files exist before the first platform call.
- The identity preflight matched the release commit on the live version endpoint and on the platform deployment record.
- The cart check rendered a subtotal, and the test item was removed.
- The canonical link and sitemap entries on the public domain carry the public domain.
- The error-log count over the window is within the agreed baseline.
- The rollback has been staged, and its steps are written down.
