---
name: medusa-admin-repair
description: Use when a Medusa admin page crashes on orphaned rows. Covers diagnosis, a fail-closed SQL repair with backups and tested sync patterns.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [medusa, admin-repair, inventory, sync, database, medusa-cloud]
    category: commerce
related_skills: [medusa-admin-data-ops, medusa-docs-first]
---

# Medusa Admin Repair and Inventory Sync

## Overview

An admin page can crash on data the API hides. The usual cause is a link row that points at a record that was deleted, or was never written correctly. The API returns the missing side as `null`, and the dashboard's list code fails on it. This skill covers how to find the exact bad row, remove it in one checked transaction with backups on both sides, and which external sync patterns are worth testing against Medusa v2.

## When to Use

- An admin list or detail page shows a generic error, a blank screen, or a not-found page that the API does not reproduce.
- An API response shows `null` inside a list of relations.
- An external inventory or order system must be synced into Medusa.

## Features

- Diagnosis that replays the failing page's own field list and looks for `null` entries.
- A read-only check of the link table through a direct database connection.
- A repair transaction that asserts each count, returns the rows it removed, and rolls back on any mismatch.
- Backups before and after every direct database write.
- A deletion order that leaves no dangling records.

## Benefits

- The repair removes only the orphan rows, never live links.
- Each change can be reversed from a dump taken the same day.
- The diagnosis names the real row, so the repair is not aimed at a guessed cause.

## Procedure

1. **Reproduce with the page's own query.** Copy the field list the failing page requests, call the API with it, and walk the JSON for `null` values inside relation arrays. A `null` where a related record should be is the signal.

2. **Read the rows before naming a cause.** Query the link table for the affected location or product, and compare each row's target ID with the live records. A truncated or mistyped ID looks exactly like a deleted record until you read the row.

3. **Check whether the API can fix it.** A removal call that names the dead ID cannot work when the API returns that ID as `null`, and the admin API may not expose deleted records at all. If the API cannot remove the row, a direct repair is the only route. Confirm this in the platform's documentation before touching the database.

4. **Use the platform's own control for direct database access.** Some hosts offer a time-limited write connection string that must be switched on in the dashboard and switched off afterwards. Store it in a protected file, never in chat or a log. Check that the file has content before reading it, and delete it when the repair is finished.

5. **Take a dump before the write.** Export a custom-format dump with `pg_dump -Fc`, record its checksum, and keep it in a backup folder rather than a downloads folder.

6. **Get the operator's go-ahead for the exact repair.** Before the repair transaction, show the operator the exact link rows to be deleted, listed by table and ID, and the checksum of the dump from step 5. Proceed only on the operator's explicit go-ahead for that list. Any change to the list needs a new go-ahead.
7. **Run the repair as one transaction with assertions.** Count the orphans and expect the number you saw in step 2. Delete only rows that are scoped to the affected records and whose target does not exist, with `RETURNING` so the removed rows are listed. Count again and expect zero. Confirm the live links still exist. Commit only when every assertion matches; otherwise roll back.

   ```sql
   delete from <link_table> l
   where l.<scope_column> = any(%s)
     and not exists (select 1 from <target_table> t where t.id = l.<target_column>)
   returning l.id, l.<target_column>, l.<scope_column>;
   ```

   The table and column names are placeholders. Link tables often have no foreign keys, so a wrong `WHERE` clause can reach rows you did not mean to change.

8. **Watch for soft deletes.** A link row whose target is soft-deleted still exists, so a `LEFT JOIN ... IS NULL` query can report zero orphans while the crash continues. Check `deleted_at` on both sides of the link.

9. **Dump after, read back, then turn access off.** Confirm the API read-back and the page, then switch the write connection off.

10. **Get the operator's go-ahead for the deletes.** Before any deletion in dependency order, show the operator the exact shipping options, service zones, fulfillment sets and stock locations to be deleted, listed by ID, with the dump checksum. Proceed only on the operator's explicit go-ahead for that list.
11. **Delete records in dependency order.** Remove shipping options first, then service zones, then the fulfillment set, then the stock location. The stock location's removal workflow cleans up its own link rows, so the order is what prevents new orphans.

### Inventory and Order Sync Patterns

These patterns are unverified advice from a documentation assistant, dated 2026-09-08. Probe each one with a read-only check before you rely on it.

1. **Webhook handling:** hash the payload, cache the hash with a time-to-live to drop duplicates, run the work in a workflow, and return success quickly. Do not do the work inside the handler.
2. **ID mapping:** store the external item ID and the external location ID in the variant and location metadata, and query by that metadata.
3. **Two sync paths:** an inventory-change subscriber for near real-time updates, plus a scheduled reconciliation job as a safety net.
4. **Order push with rollback:** push each new order from an event subscriber through a workflow whose step has a compensating action. If a later step fails, the compensation deletes the external order. Store the external order ID on the Medusa order.
5. **Stock checks at cart and checkout:** add validation hooks to both the add-to-cart and complete-cart workflows. Cache external stock for a short time. Skip variants with no external ID rather than failing them.
6. **Concurrency:** the inventory-level update workflow has no built-in lock. Wrap it in a keyed lock per item and location.
7. **Managed inventory:** a variant without managed inventory is always shown as in stock, and validation hooks apply only when the flag is on. Turning the flag on does not create the inventory item, so create the item and its location level first.

## Pitfalls

- **Read the rows before blaming the feature.** A stored ID that is truncated can look like a feature fault, so check the stored values first.
- **A documentation assistant's first answer is a hypothesis.** Test any route or table name against a live response before using it. Feed it your evidence and check its second answer.
- **Dump first and dump after.** Platform daily backups are a third safety net, not a replacement.
- **A 200 is not verification; a row list is.** Use `RETURNING`, then read back.
- **Turn the write connection off when you finish.** It stays live until someone switches it off.
- **A 401 with a key from another project** almost always means the key belongs to a different project.
- **A write that returns 502 may have committed.** Read the row before any retry.
- **A new host may have no admin user.** Admin routes need a user created by a first login. A token with an empty actor ID cannot create one.
- **Publishable keys are bound to sales channels.** A key bound to the starter channel does not see products in your channel. Relink keys by their channel link, not by a hard-coded ID, and never delete products during a migration without a written list of what to keep.

## Verification

- The orphan count is zero after the repair, and the live link count equals the number the transaction expected.
- The admin page loads, and the API read-back shows the expected relations.
- Dumps exist before and after the write, each with a recorded checksum, and sit outside the downloads folder.
- The write connection is off, and no connection string remains on disk.
- A rollback leaves the orphan count unchanged.

## Attribution

API and dashboard behaviour was checked against the Medusa v2 documentation (https://docs.medusajs.com).
