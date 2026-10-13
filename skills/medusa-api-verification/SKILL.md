---
name: medusa-api-verification
description: Use when verifying a Medusa backend over HTTP. Covers token classes, read-only probes, publishable-key discovery, product counts and deploy-SHA gates, without admin keys or test passwords.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [medusa, store-api, audit, read-only, publishable-key, verification]
    category: commerce
related_skills: [medusa-admin-data-ops, medusa-docs-first, catalog-data-audit]
---

# Medusa API Verification Without Admin Credentials

## Overview

Read-only verification of a Medusa project's backend, storefront and catalog, using only what a session can reach over HTTP. Without an admin key or a test password, most existence questions cannot be answered, so the job is to say which questions are answerable, answer them with the cheapest correct probe, and report the wall for the rest. Never infer an admin-only fact from a public response.

## When to Use

- Checking which backend is live, and whether it runs the commit you expect, before trusting any data.
- Counting published products, categories or stock-visible rows through the public Store API.
- Checking that a publishable key or a customer login works, without writing anything.
- Auditing a storefront's public surface when no admin access exists.

## Features

- A host check that matches the live commit before any data question.
- A token-class table that prevents using the wrong credential on the wrong route.
- Probes that separate "not found" from "wrong channel", "wrong key" and "empty catalog".
- A publishable-key discovery path that does not depend on scraping the page.
- A deploy gate that checks the merged commit against the live commit.

## Benefits

- A wrong host or a stale deployment is caught before a count is reported.
- Each claim is tied to the probe that produced it, with its HTTP status.
- Missing access is named as a wall, so nobody mistakes it for an empty result.

## Procedure

1. **Identify the live host first.** Request `GET /version` on each candidate backend. It needs no authentication and returns the commit SHA and build time. Compare the SHA with the expected commit. Preview environments often run older commits, and a wrong host means querying the wrong database while believing it is production.

2. **Classify each token by its prefix before using it.** A publishable key (`pk_`) is for storefront reads. A secret admin key (`sk_`) is for admin routes. An end-user token is for customer flows only and returns 401 on admin routes. Keys are issued per project, so a key that works on one host returns a bare 401 on another. Match the credential class to the route.

3. **Admin existence checks need an admin credential.** Customers and companies sit behind admin routes. A publishable key always fails there. Without an admin credential, existence cannot be verified, so report the wall and do not infer.

4. **Do not use login as an existence test.** A customer login returns the same 401 for an unknown email and a wrong password, so the response gives no information about existence. A dummy-password probe only confirms that the route is live.

5. **Do not use registration as an existence probe.** A duplicate-email error is evidence that the account exists, but a successful registration creates a new customer. That is an accidental write.

6. **When the store says a valid publishable key is required, check the key's class first.** A wrong class looks like a missing key. The real key is held by the platform dashboard or the storefront's server environment. The key is supplied at build or run time, and a storefront often ships the public key in its client chunks. Scan the served HTML and chunks, record where the key appears, and treat its presence in a browser bundle as expected, not as a leak. Stop scraping for the private key.

### Storefront Probes

- Cookie-gated storefronts can redirect to the same URL until a cache cookie is set. Use a cookie jar (`curl -sL -c jar -b jar <url>`), and judge the page by its title and body length, not the first status line.
- A logged-out storefront may redirect product pages to a login wall. That is the wall, not a missing product. Confirm the product through the Store API.
- A store product request can return HTTP 200 with an empty list. Treat that as not found, a wrong channel, or a wrong key. Record the list length, because the status alone is misleading.
- Plus-addressed emails are stored exactly as typed, including the `+` tag. A bare address does not match an alias account. Compare test-buyer addresses byte for byte before blaming a password.

### Counting Published Products Without Admin Access

1. Request `GET /store/products?limit=1` and read the `count` field. That count is the published total. `products.length` is only the page.
2. Check channel membership by repeating the request with `sales_channel_id[]=<id>`. If the count is unchanged, the key is bound to that channel.
3. Status filters such as `status[]=draft` are rejected by the Store API. Draft counts need admin access, so name that gap and stop.
4. The category count from the Store API is a lower bound: it counts only categories with published products in the active channel.
5. Never derive counts from a summed per-category file alone. Such sums can exceed the Store count because they include unlinked or unpublished rows. Report the Store count as the published figure and name any gap.

### Reusing Earlier Evidence

When the operator accepts earlier data only if it is recent, check each file's timestamp against the freshness limit before using it. Label every reused number with its source and time, for example "snapshot from the earlier run, timestamp taken from the file". Re-probe when anything publishable could have changed since then: prices, status, new SKUs, channel membership.

### Stock Visibility

- Catalog variants often run without managed inventory by design, and the Store API then returns a null quantity. That is expected. It does not mean out of stock.
- Find stock in the system of record for the catalog. Query the Store API for visible state and the admin API only when you have an admin credential.
- Do not infer stock for a product from its title.

### Probing a Publishable Key and a Storefront Read

When a read-only script needs the storefront's publishable key, and the task forbids pulling it from the environment, git history or a sibling file:

1. Scan the served HTML for the key pattern on several storefront routes, and the first few script chunks as well. Record where the public key appears. A healthy storefront may show hits in client chunks, because the public key ships to browsers, so a hit is expected and not a leak. Look for secret-shaped keys separately.
2. Request `GET {backend}/store/products?limit=1` without a key. An HTTP 400 that says a publishable key is required is positive proof that the backend is reachable and that the key is the only missing input.
3. Accept the key from an environment variable that the operator supplies, and fall back to the HTML scan only when the variable is missing.
4. If the key is still missing, report the three probe results and stop. Do not open a pull request with a placeholder audit.

Keep the read rate at two requests per second or fewer, and set field lists explicitly. Do not request every field on every product, because that pulls prices and weights the task did not ask for.

### Deploy Gate for Write-After-Merge Work

1. Confirm the merge with the repository host, and take the merge commit SHA as the target.
2. Compare the SHA from `/version` with the target. Use only the SHA as the gate; the status words can lag.
3. If the SHAs differ, the new route is not live. Do not probe it or guess request shapes against an older build.
4. Record the deployed SHA in the report, so later disputes about timing can be settled.

### Credential Sweep Before Declaring a Write Blocked

Check these in order, and mask every value in output:

1. The session environment, noting which host each key was minted for. One cheap probe against the target host settles whether a key works there.
2. The secret manager's list of key names only, never the values.
3. Repository documentation and operations notes for a stored token or login.
4. Only then report the write as blocked. Name the missing credential class and the evidence, for example the 401 response and the list searched.

Never fall back to a customer login to perform admin writes.

## Pitfalls

- **A wrong host gives confident wrong answers.** Check `/version` first.
- **Status alone lies.** Check list lengths and body sizes.
- **A 307 on a product page is a login wall,** not a missing product.
- **A count from a summed file is not the published count.**
- **A key from another project returns 401.** This is almost always a wrong key, not a rotation.

## Verification

- The `/version` commit for each host is recorded before any data is reported.
- Each count is tied to the request that produced it, with its HTTP status and the field used.
- Every blocked item names the missing credential class and the evidence for it.
- No token, key or password appears in the output.

## Attribution

Endpoint behaviour was checked against the Medusa v2 documentation (https://docs.medusajs.com).
