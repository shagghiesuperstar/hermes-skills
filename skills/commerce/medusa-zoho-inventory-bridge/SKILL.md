---
name: medusa-zoho-inventory-bridge
description: Use when bridging Zoho Inventory and a Medusa store. Includes read-only stock digs against a Zoho dump.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [medusa, zoho, erp, inventory, webhook, workflow, ecommerce]
    category: commerce
related_skills: [medusa-admin-data-ops, medusa-admin-repair, medusa-docs-first]
---

# Medusa and Zoho Inventory Bridge

## Overview

A Zoho Inventory bridge keeps two systems agreeing on what is in stock, what was sold and which customers are approved. Zoho owns item identity and available stock. Medusa owns the storefront catalog, the publication state and the customer accounts. The bridge has to decide which side wins for every field, prevent double counting when both sides adjust stock, and never let a retry or a webhook redelivery change stock twice. This skill covers that design, the build steps, and the read-only stock digs used to check the bridge.

## When to Use

- Designing a Zoho to Medusa inventory or order sync.
- Building a webhook receiver, a stock-sync workflow, an order-push workflow or a reconciliation job for it.
- Importing approved wholesale buyers from Zoho into Medusa.
- Running a read-only stock check against a Zoho item dump.

Skip it for display-only stock badges, which need only the managed-inventory flag and variant metadata, and for payment work, which has its own gate.

## Features

- An identity and authority table that says which system owns each field.
- Cross-system keys stored in Medusa metadata, with a re-run rule after catalog re-imports.
- Webhook verification and idempotency rules.
- Subscribers plus a scheduled reconciliation job, with an absolute-value sync strategy.
- A lock around inventory-level updates.
- A customer import path with its own gates, separate from the inventory bridge.
- A read-only stock-dig procedure with a fixed quantity rule.

## Benefits

- Each field has one owner, so the two systems do not overwrite each other.
- Redelivered webhooks and retried workflows change stock once.
- Wholesale buyers are imported without duplicate accounts, and without exposing their passwords.

## Procedure

### Readiness gate

Do not start the inventory bridge until these hold:

1. Live payment credentials are in place for the backend and the storefront in every environment.
2. The manual payment path is closed.
3. Managed inventory is on for every product that should block overselling. Until then, every stock display is wrong.
4. A checkout funnel shows real orders, so the first three items are proven in use.

The customer import has a separate gate: a verified sender domain, approval of the invitation wording, and an approved send wave. Do not combine the two gates.

### Identity and authority

| Field | Owner | Notes |
|---|---|---|
| Item identity | Zoho | Zoho item ID plus an immutable SKU stored as text, so leading zeros survive |
| Available stock | Zoho | The Zoho available-stock figure already subtracts committed orders |
| Catalog and publication | Medusa | Subject to compliance approval |
| Cost | Zoho, read only | Never sent to storefront clients |
| Price | Derived | Zoho rate times the configured multiplier, computed on the server |
| Stock written to Medusa | Open question | Confirm which field Medusa adjusts for reservations before writing, or the same reservation is subtracted twice |

Store the cross-system keys in Medusa metadata: the Zoho item ID on the inventory item and the Zoho warehouse ID on the location. A Medusa variant or item ID is not stable across catalog re-imports, so re-run the metadata migration after every re-import. Map SKUs as text. Never store a SKU as a number.

Medusa stores the external item ID on the product, but the stock lookup happens at the inventory item. Look up by the inventory item's metadata, not the product's.


1. **Seed the mapping as metadata.** Write one migration that sets the Zoho item ID on each inventory item, matched by barcode from the Zoho export. Make it idempotent so it can run again after every re-import.

2. **Configure the connector.** Pass the bridge settings (schedule, low-stock threshold, retry policy, batch size) as one options object when the plugin is registered. Keep the connector generic, and keep business rules in the store's own repository.

3. **Receive webhooks safely.**
   - Read the event name, the delivery ID and the signature headers.
   - Compute an HMAC-SHA-256 of the timestamp and the raw body with the shared secret. Compare with a constant-time function, never with plain equality.
   - Keep the raw body available to the route, and reject timestamps outside a five-minute window.
   - Acknowledge within the sender's time limit. Do the work in a workflow after the acknowledgement.
   - Use the delivery ID as the idempotency key, with a time-to-live of at least 24 hours to cover the sender's retry window. Where the sender has no delivery ID, hash the body.

4. **Run the stock sync as a workflow.** Use the documented workflow steps, a service module that wraps the Zoho client, and a compensating action for every step that changes state.

5. **Subscribe to inventory events and schedule a safety net.**
   - Inventory-item events carry an ID. Inventory-level events carry an ID and, when an order caused the change, an order ID.
   - Add a subscriber for inventory-level updates for near real-time drift.
   - Add a scheduled reconciliation job every six hours. It reads the absolute stock figure from Zoho and writes it, rather than applying changes from events, so a missed event is corrected on the next run.

6. **Lock every inventory-level update.** The platform's inventory-level workflow has no lock at workflow level. Wrap the call with the locking steps, keyed by inventory item and location, with a short wait and a 30-second lifetime. Never acquire the same lock in a parent and a nested workflow, or the two will deadlock.

7. **Break the echo loop.** If changes flow both ways, mark each outbound push with its origin. The return-path subscriber ignores changes that carry the mark.

8. **Push orders with a rollback.** When an order is placed, push it to Zoho from a subscriber through a workflow. If a later step fails, a compensating action deletes the Zoho order. Store the Zoho order ID on the Medusa order. Allow a manual retry by idempotency key.

9. **Check stock at cart and checkout.** Add validation hooks to both the add-to-cart and the complete-cart workflows. Cache Zoho stock for about 30 seconds. Skip variants with no Zoho ID rather than failing them, and report those separately.

10. **Send the low-stock digest through the existing notification channel.** Do not build new notification infrastructure. The default threshold is 5, and per-item overrides are a decision for the owner.

11. **Import wholesale buyers as pre-approved accounts.** Key each buyer on the Zoho contact ID, never on email, because a shared purchasing inbox can belong to several businesses. Where two contacts share an email, keep the business with the highest revenue as the customer and attach the others as addresses. Create the login with a long random password that is never logged or stored. The buyer then sets their own password through the platform's reset flow, which uses the platform's reset token, not a custom token. Make sure the order path attaches new orders to the existing Zoho contact.

12. **Keep the send path closed until the gates pass.** Every external email fails until the sender domain's DNS records are verified. Send in waves, and halt the next wave when the bounce rate passes a threshold.

13. **Stay inside the Zoho quota.** Zoho limits requests per minute and per day, and the quota is shared by every integration in the organisation. Estimate the calls for any bulk read before running it. Run large reads after business hours, or split them across days. Checkpoint after every page so a restart resumes. Never lower the quota floor that protects the order integrations.

### Read-Only Stock Digs

Use this procedure to check stock for a list of SKUs. Production writes are off during a dig.

1. **Use a local dump first.** If a current dump of the Zoho items exists, analyse it offline and stop there. The dump is a list of item objects from the items endpoint, paginated.

2. **Get a live read only through the official authorisation flow.** Exchange the stored refresh token for an access token. If the refresh is rejected, stop and report it. Do not try other regions or grant types to revive a rejected token, and do not borrow credentials from another tool.

3. **Apply one quantity rule.** Use the available-stock figure, then the available figure, then the on-hand figure. Treat a missing value as zero. When a SKU appears more than once, keep the highest figure.

4. **Count, then report exactly what was asked.** For a SKU list, count found, missing, positive and zero, and list the missing ones. Report only rows present in the dump or the live response, and never invent a SKU, a quantity or a product name.

5. **Match names with explicit include and exclude lists.** Use whole-word or phrase matching. Avoid short generic words that match unrelated products, and list the exclusions in the report. Dedupe by SKU before counting.

6. **Keep secrets out of the output.** Never print tokens, client secrets or key values. Write results to a file with the counts, a sample of SKUs and the origin of the data.

## Pitfalls

- **Medusa's catalog IDs change on re-import.** Re-run the metadata migration every time.
- **The inventory module's service layer fixed some races, but the workflow layer is still unguarded.** Lock the workflow call.
- **A stock field that is already adjusted by Zoho, then adjusted again by Medusa, double counts reservations.** Confirm the field before writing.
- **Webhook secrets pasted into chat break shell commands and leak.** Load them from a protected file.
- **Inventory events fire only inside the running application.** A standalone run emits nothing.
- **Managed inventory is off by default.** Turning it on does not create the inventory item, so create the item and its location level first.
- **A variant without managed inventory always shows in stock,** which hides real shortages.
- **Linking a company to a wholesale group with a one-to-one link lets only one company join.** Check a link's cardinality before assuming it scales.
- **A notification call with a template name that is not a hosted template returns an error,** and every external send fails. Use the inline content shape the platform documents.
- **A bulk read during business hours can exhaust the shared quota** and pause every integration.
- **Medusa Cloud webhooks are a different flow from Zoho webhooks.** The signature pattern is similar, but the secret and the payload differ.

## Verification

- Each field's owner matches the authority table, and the reservation question is answered in writing before the write path is enabled.
- The webhook route rejects a bad signature and an old timestamp, and a redelivered event changes nothing.
- The inventory update runs under its lock, and the lock is released on success and on failure.
- The reconciliation job corrects a deliberately wrong stock figure within one run.
- After an order push and a forced failure, the compensation removes the Zoho order.
- Every variant without a Zoho ID is listed, and none is shown as in stock because of it.
- A stock dig reports counts that match the dump or the live response, with no secret in the output.

## Attribution

The bridge follows the Medusa project's documented ERP recipe and its workflow, webhook and inventory guides (https://docs.medusajs.com).
