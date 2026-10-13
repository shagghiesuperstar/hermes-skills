---
name: medusa-admin-data-ops
description: Use when changing Medusa catalog or inventory data. Covers auth, relation expansion, read-back after every write, safe large reads and the variant-image link rules.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [medusa, admin-api, catalog, inventory, ecommerce, data-repair]
    category: commerce
related_skills: [medusa-docs-first, medusa-admin-repair, medusa-api-verification]
---

# Medusa v2 Admin Data Operations

## Overview

The Medusa v2 Admin API can accept a write and change nothing, hide a field that was never requested, and return a relation as `null` unless it is expanded. Catalog data work needs three habits: read every write back with a fresh request, ask for the fields you need by name, and keep large reads small. The rules here were checked against a live Medusa v2 (2.17-era) backend. Confirm the version you run before you rely on a response shape.

## When to Use

- Creating, repairing or re-linking products, variants, images, categories, price lists, inventory or shipping options through the Admin API.
- Diagnosing an admin page that crashes, or a shopper page that shows the wrong data.
- Checking that a change is visible to shoppers, not only to admins.

Skip it for reads that only need the public Store API, and for schema questions the official docs can answer first (see medusa-docs-first).

## Features

- An auth ladder that is walked in order before a write is called blocked.
- Read-back rules for every write, with the projection that actually shows the change.
- The variant-image link model (general versus exclusive images) and the endpoints that keep it stable.
- Inventory and price-list recipes with check-then-write steps.
- Guards for heavy product reads that can exhaust the backend's memory.

## Benefits

- A "200 OK" is never taken as a finished change.
- A field that was not requested is not mistaken for an empty field.
- Interrupted batches resume without duplicating or erasing data.
- Shoppers see the change, or the gap is reported with the layer that holds it.

## Procedure

1. **Authenticate per host, and keep credentials out of chat.** Store tokens in a mode-600 file. A token minted for one backend is rejected by another, so run `GET /admin/users/me` on the target host before any write. Choose the login path from the variables the project actually has: a password login when an initial-password variable exists, otherwise the platform's OAuth login. Personal access tokens issued to end users do not work on admin routes.

2. **Walk the auth ladder before calling a write blocked.** Try, in order: (a) cached admin tokens for that host, validated with `GET /admin/users/me`; (b) a fresh login through the path in step 1; (c) a project-scoped secret key sent as Basic auth. One failed attempt with a stale key is not evidence that no working credential exists.

3. **Expand relations explicitly.** A relation missing from a response is not an empty relation. Request it with a star prefix, for example `fields=*sales_channels` or `fields=*payment_providers`, and read the field you need back.

4. **Request the fields you will match on.** A lean projection can return variants without their SKU, which makes a real match look absent. Request `variants.sku`, or use the full default payload and scan client-side. To find a SKU that matches no product, query inventory items by SKU.

5. **Read back every write.** Mutating endpoints echo success even when nothing changed. After each write, GET the exact entity and compare it with the intended value. The write is finished when the read-back matches.

6. **Treat a timeout or a 5xx as a possible landed write.** A write can commit after the client has given up. On a timeout or 502, do not repeat the POST. Re-read the entity: if the value is there, log the row as landed and continue. Make every batch check-then-write, so a rerun does nothing when the work is already done.

7. **Know which metadata writes merge and which replace.** Variant metadata POST replaces the whole object, so read it, merge your change locally, send the full object, then diff the keys before and after. Product metadata POST merges, so an omitted key stays, and an empty string deletes a key. Verify either case with a read.

8. **Snapshot before the first write.** Save each affected entity as timestamped JSON with its IDs, and keep the snapshot until the change is verified. A rollback is only possible from a snapshot.

9. **Guard heavy product reads.** Estimate the size before a full read: image count times variant links, plus any metadata repeated on each row. Keep default-field reads of products with large metadata or many images small, use `fields=id` where possible, and never raise the server's memory limit to get a read through. Treat a 502, 503, 504 or status 0 from the backend as a stop: do not retry, and check whether the last write landed.

10. **Link variant images with the image-centric endpoint.** An unlinked product image is general: every variant shows it, and general images render before exclusive ones whatever their gallery rank. Linking an image to a variant makes it exclusive. Use `POST /admin/products/{pid}/images/{img_id}/variants/batch` with `{add: [...], remove: []}`. The variant-centric batch endpoint loses links in remove-then-re-add sequences. Link a variant's own image before the shared images, because link order is insertion order.

11. **Prove image links from the image side.** A product GET with `fields=images.id,images.url,images.variants.id` shows each image's variants, and an image with no variants is general. The variant-side image list returns every product image for every variant, so it cannot prove exclusivity.

12. **A gallery replacement removes the links.** Posting a new `images` list drops existing image-to-variant links. Re-link each remaining image after the replacement, then read back.

13. **Inventory is a three-step change, not a toggle.** A variant with managed inventory on and no inventory item or stock level shows as out of stock. Census first: count the variants that already have an item and a level at the stock location. For each variant, create the item if it is missing, link it to the variant, create the location level with the live quantity, and set managed inventory to true last. Take the quantity from the stock system at write time, not from an earlier export. When no source row exists, leave managed inventory off and report the SKU.

14. **Read stock from the inventory item.** On v2, `variant.inventory_quantity` is null for variants managed through the inventory module. Read `location_levels[].stocked_quantity` for the target location. A proof that compares the variant field produces false failures.

15. **A pilot authorises only its named SKUs.** Expanding managed inventory across a whole category needs its own decision. Rows with zero or negative quantity stay unmanaged and go on a list for the warehouse.

16. **Price lists need explicit payloads.** Create with `title`, `description`, `status` and `type`. Bind customer groups through batch price rules, because separate attach routes may not exist on a given build. Every entry in a batch price update needs `variant_id` and `currency_code`. Page through the whole list until `offset` reaches `count`, since a spot check misses the tail. Derive amounts from a sibling variant on the same backend, because currency units differ between projects.

17. **Keep one category tree.** Fetch the tree before creating a category, because an earlier pass may already have made it. Link a product to its leaf and its parent in one batch, since a leaf-only product does not appear on the parent's page. On some builds a category-set write can fail silently: send the complete intended list rather than a delta, and check that each listing's count moved by exactly one.

18. **Import row by row when the bulk importer fails.** The CSV importer can reject numeric-looking SKUs and handles. Post one product per row, dedupe by handle rather than SKU, log each failure, and treat "already exists" as a probable success that you confirm with a GET. Finish with a product count per sales channel.

19. **Fix titles as data.** A variant's option value baked into a product title appears on the product page. Correct it with an explicit field update on the product, and confirm the variant count did not change.

20. **Check what the shopper sees.** Admin data can be right while the storefront shows something else. Query the Store API with the publishable key bound to the right sales channel: a key with no channels returns an error, and a key bound to the default channel cannot see products in another channel. Then load the rendered page.

21. **Account for caching.** Store query results are cached per request key, and an empty result can persist for a while after a product is republished. Storefront pages can be static until the next build. After a catalog write, trigger a rebuild, wait for the deployment to finish, check the live page, and tell the operator the realistic delay before they report a bug.

22. **Strip internal fields on the server.** A Store API response can carry wholesale prices, pipeline labels or internal IDs, and any visitor can read them in the response. Remove them with an allow-list or deny-list in the backend, not by hiding them in a component. Scan public responses and rendered pages for these keys before each release.

23. **Check shipping options for silent fallbacks.** A calculated option whose provider is disabled or missing credentials can quietly return a flat fallback price. Confirm the provider is enabled and registered in the running backend, and that a calculated quote differs from the flat rate. A calculated option still needs `prices: []` in its payload. Delete in dependency order: options, then service zones, then the fulfillment set, then the stock location.

24. **Check payment providers in two places.** A bare region GET does not show payment providers. Read `fields=*payment_providers`, and read the store's payment-providers endpoint with a publishable key. Remove a manual provider only after the real processor's environment variables are deployed. Environment variables take effect after a redeploy or a build.

25. **Report in plain language.** Lead with the outcome and links to the admin page and the shop page, and give both when asked to look. State any decision the operator must make, then wait for approval.

## Pitfalls

- **An unexpanded relation is not an empty one.** Bare reads have caused false "no providers" and "no channels" conclusions.
- **An admin success is not a shopper success.** Check the store endpoint and the rendered page.
- **Two projects can share a naming pattern.** Confirm the project by its default domain and its version commit before any write.
- **A key from another project returns 401.** Probe the right host with the right key.
- **Delete order matters.** Removing a location before its options and zones leaves dangling records.
- **Shipping province must be the full state name**, not the code, or gate tests can pass for the wrong reason.
- **Some carts and orders need explicit expansion.** Carts may not be a list resource at all on some builds.
- **SKUs are unique across the whole catalog.** Rename the leftover variant before creating a new one with the same SKU.

## Verification

- Every write has a read-back that matches the intended value, using the field names listed above.
- Counts before and after a batch match the plan, and a rerun changes nothing.
- The store-side check with the bound publishable key shows the products, and the rendered page shows the change.
- The snapshot exists before the first write and can restore the previous state.
- No credential appears in logs, chat or committed files.

## Attribution

API shapes were checked against the Medusa v2 documentation (https://docs.medusajs.com).
