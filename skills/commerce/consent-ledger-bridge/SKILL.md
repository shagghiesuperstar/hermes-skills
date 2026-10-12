---
name: consent-ledger-bridge
description: Use when wiring commerce opt-in and opt-out events to an email or contact-list service so that an opt-out always wins, including out-of-order and duplicate events. Covers a durable suppression ledger, event-time ordering and a five-case test matrix.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [consent, email, opt-out, suppression, compliance, webhook]
    category: commerce
related_skills: []
---

# Consent Ledger Bridge (Commerce to Email Service)

## Overview

A bridge that forwards one-way events (customer created, order placed, opt-in, opt-out) from a commerce system to an email or contact-list service looks simple, but the destination cannot be the authority for who may be contacted. An opt-out must survive a crash, a retry, a race with a queued opt-in and an out-of-order delivery. This skill builds a durable local suppression record first, orders decisions by event time, and proves each case against a real sandbox before the bridge is switched on.

## When to Use

- Wiring any one-way event webhook from a commerce platform to a mailing list, for any event name.
- Reviewing an existing bridge that might acknowledge an event before its opt-out is stored, or that trusts arrival order.

Skip it for integrations with no contact list, such as a store-to-warehouse sync, and for send-only flows where the email service already owns the list.

## Features

- Durable suppression table keyed by a hash of the lower-cased address and the brand.
- Ordering by the event's own timestamp, never by arrival time.
- Opt-ins that clear a suppression only when strictly newer than it.
- A five-case test matrix run against a real sandbox destination.
- A switch that keeps the bridge inactive until every case passes and the owner approves sends.

## Benefits

- An opt-out cannot be lost to a crash, because the commerce platform only clears its retry after the record is stored.
- A queued opt-in from before an opt-out cannot re-subscribe the person.
- No raw email address sits in the local ledger, so a backup or log leak exposes only hashes.
- The audit trail shows every dropped event.

## Procedure

1. **Read the destination's event model from its API reference.** Subscribe, unsubscribe, list-attach and profile-update calls each have their own idempotency and sync rules. Treat the request schema as the truth and the README as a hint.

2. **Create the suppression table before any event handling.** Use one row per address and brand, with these columns: `email_hash`, `brand`, `event_ts`, `source_event_id`, `state` (opted-out or opted-in). The key is the SHA-256 of the lower-cased, trimmed address, combined with the brand. The composite key makes the cases below atomic.

   ```python
   import hashlib
   email_hash = hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()
   ```

3. **Order each event by its own timestamp.** Read the `ts` or `created_at` field from the payload before any routing. Never use the time the workflow received the event. Pass the timestamp along as the value that decides order.

4. **Short-circuit redeliveries.** When an event with the same `event_id` and an older or equal timestamp arrives again, stop there and return success. Do this before reading the suppression row.

5. **Write the suppression row first.** Before any call to the destination, record the opt-out or opt-in in the suppression table. The destination's own duplicate handling covers retries; the local row is the record of the decision.

6. **Apply the decision rules.**
   - An opt-out always writes a suppression row, whether or not the contact exists at the destination. If the contact exists, also unsubscribe it there.
   - An opt-in clears a suppression only when its timestamp is strictly greater than the suppression's timestamp. An equal or older opt-in is dropped and logged.
   - A duplicate event with the same `event_id` and timestamp changes nothing.

7. **Acknowledge the event only after the suppression write commits.** The commerce platform removes its retry as soon as it gets a success response. Wait for the store's confirmation before replying.

8. **Test the five cases against a sandbox destination.**
   - (a) An opt-out for an unknown contact writes a suppression row and makes no destination call.
   - (b) An opt-out followed by an older opt-in, queued from before the opt-out, is dropped.
   - (c) An opt-out followed by a strictly newer opt-in clears the suppression and subscribes the contact.
   - (d) A duplicate `event_id` is idempotent and writes nothing twice.
   - (e) A concurrent opt-in and opt-out for the same address leave the state set by the newer timestamp.
   Run every case with real HTTP calls. Use a sandbox account, never real contacts.

9. **Activate in two steps.** Turn the workflow on only after all five cases pass. Check it with one test contact per case, sending no real email. Then turn it off again until the owner approves sends. Wiring the bridge and approving sends are separate decisions.

## Pitfalls

- **An acknowledgement before the write loses opt-outs.** A bridge that subscribes the contact and then crashes before saving the opt-out has told the platform the event is handled. The platform deletes its retry, and the opt-out is gone.
- **Arrival order is not event order.** Parallel workers, webhook retries and queue backlogs reorder events. An opt-in that happened first can arrive after an opt-out. Compare event timestamps only.
- **A stored raw address is a leak waiting to happen.** Keep only the hash in the local table. The destination holds the raw address, and nothing else should.
- **The destination's own deduplication is not suppression.** The destination may ignore a repeated subscribe, but it will not remember an opt-out that your bridge lost. The local ledger is the record; the destination is a cache.
- **A dropped event must be dropped, not retried.** Retrying an older opt-in after the opt-out has landed re-subscribes someone who already lost the race. Log every drop so an audit can see it.
- **Mocks do not reproduce real behaviour.** Mocks miss the destination's rate limits, its retry rules, its eventual consistency and its response to a malformed address. Only a sandbox run proves the cases.
- **Green unit tests are not the proof.** Unit tests cover the bridge's own code. The five-case run against a real destination shows that the round trip works.
- **Logs must redact addresses.** Scrub any address from logs and error messages, not only from stored tables.
- **Keep secrets out of chat and logs.** Load credentials from a protected file or the platform's secret store.

## Verification

- After each of the five cases, the suppression table holds the expected row, or no row where none was expected.
- All five cases pass against a real sandbox destination, with the HTTP responses recorded.
- The table contains no raw email address, and a search of the logs finds none either.
- The workflow is inactive until the owner approves sends, and that approval is recorded.
- A duplicate event, replayed once more, produces no new destination call and no new row.
