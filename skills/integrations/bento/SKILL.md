---
name: bento
description: Use when operating the Bento email platform through its API, MCP server or dashboard. Covers keys and site scoping, which surface to use, safe-send rules and common pitfalls.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [bento, email, marketing, mcp, api, deliverability, automation]
    category: integrations
related_skills: [n8n-cloud-integration, mcp-client-setup]
---

# Bento Email Operations

## Overview
Bento is an email and automation platform. Work in it goes through three surfaces: a REST API, an MCP server for agents,
and the dashboard. Each surface can do different things, and some actions, such as sending a broadcast or editing a live
automation, are safe only when a person reviews them. Most mistakes come from the wrong site, a missing identifier, or a
send that bypasses a recipient's unsubscribe state. This skill covers the account model, which surface to use, the
send-safety rules, and the pitfalls that cause the most damage.

Check every endpoint and limit in this skill against Bento's current public API documentation before you rely on it.

## When to Use
- You need to look up a person, a tag, a field, a sequence or a workflow's statistics in Bento.
- You need to track an event that starts a workflow, or import contacts.
- You need to create an email draft, or change a sequence or template.
- A send failed or was accepted, and you need to know whether the recipient got it.
- You are connecting a new brand or a new site to an automation tool.

## Features
- Account model: teams, sites, people, events, fields, tags, flows, sequences and broadcasts.
- Surface chooser: which job belongs to the API, the MCP server, the dashboard or a person.
- Authentication rules: the publishable and secret key pair, the site identifier, and the user-agent header.
- Read-before-write checklist for any change.
- Send-safety rules for broadcasts, transactional mail and unsubscribes.
- Pitfall list with the reason behind each rule.

## Benefits
- A change lands on the right site, and it never reaches another brand's audience.
- Drafts stay drafts until a person reviews them.
- Unsubscribed people stay unsubscribed.
- Failures are read from the right signal, not from a queue count.

## Procedure
1. Confirm the site before any write. Map the brand to its site identifier out loud, and check the keys against the API
   settings in the dashboard. Then make one read-only request from Bento's API reference, with the site identifier as the
   `site_uuid` query parameter.
   A 200 means the keys and the site identifier are right. A 401 usually means the wrong identifier,
   not wrong keys. The dashboard's site slug is not the API identifier. The API identifier is the 32-character value
   shown under the API key settings.

2. Pick the surface for the job:

   | Job | Use |
   |---|---|
   | Look up a person, list tags, fields, sequences, workflows, broadcasts, site or workflow statistics | MCP read tools |
   | Create a broadcast draft, add or patch a sequence email, patch a template | MCP tools, then a person reviews and sends in the dashboard |
   | Track one event that should start a workflow | REST events endpoint |
   | Sync attributes, tags or fields in bulk | REST subscribers endpoint, which does not start workflows |
   | Send order receipts or account mail | REST emails endpoint, a workflow step, or the SMTP relay |
   | Create or edit workflows, segments, forms, sender identities, DNS, billing | Dashboard, or the vendor's assistant if available |

3. Keep one credential set per brand and per site. A key pair can reach every site its owner belongs to, so select the site
   with the site identifier on each request. Use a service owner for automation, so that a departing team member does not
   break the keys.

4. Preview before any send. Check the sender identity, the audience (explicit tags or a segment), the hourly batch
   size, the preview text, and a human sign-off. Warm an audience with engaged people first, then widen it in steps.

5. Verify after a change. Read the object back, and report exactly what changed and where.

### Send-safety rules
- **A draft is a draft.** A broadcast created through the MCP tools is a draft. Report it as "draft created, needs
  review in the dashboard", and never say it was sent.
- **Every marketing body carries the unsubscribe link.** Put the unsubscribe placeholder in the visible HTML of each
  broadcast, sequence email, workflow email and non-transactional send, and include the postal address the law requires.
- **The transactional flag is for true order and account mail only.** It bypasses unsubscribe state. Never use it for
  promotions, win-backs or newsletters. The default is off.
- **Editing a template or sequence email changes live automations immediately.** Diff the change, keep the HTML in
  version control, and never test on a live workflow with real subscribers.
- **Test on a staging site with seed addresses.** Tag test people so that they are easy to find, and do not fire test
  events for real customers.
- **Do not re-add people who unsubscribed.** Do not use a subscribe command on them, do not import unsubscribers as active,
  and do not let a sync from another system bring them back. Prefer unsubscribing to deleting. Delete only after you pause
  the upstream syncs and save the consent state.
- **Never send to purchased, scraped or appended lists.** This also violates the platform's acceptable-use terms.
- **Respect the rate limits in the documentation.** Retry only rate-limit and server errors, with increasing waits. Do not
  retry an email send or a broadcast creation without an idempotency check, or the recipient gets duplicates.
- **Watch complaints and bounces.** Slow down when they rise, and stop when they cross the thresholds your provider and your
  policy set.

## Pitfalls
- **Always send a real user-agent.** Requests without one can be blocked by the edge network with an HTML error page.
- **Always send the site identifier, from the same site as the keys.** A mismatch looks like a bad key.
- **Use the events endpoint for anything that must start a workflow, and the subscribers endpoint for syncs.** Imports and
  commands do not start workflows.
- **Send purchases with a real order identifier as the unique key.** Without it, retries double-count revenue, and the
  client may generate a random key that defeats deduplication.
- **Keep event fields flat.** Nested values belong in the details object, or validation fails.
- **Pass tags as comma-separated strings where the endpoint expects them.** An array can fail validation.
- **Definition endpoints create definitions only.** Creating a tag or a field does not tag or set a value for anyone.
- **Asynchronous commands return a count, not a result.** Do not read back right after a command. Check later.
- **Imports can take minutes to appear.** Do not retry in a loop. Check the person afterwards.
- **The sender must be a verified identity.** A send from an unverified sender fails, which is the most common send error.
- **A send response is a queue acceptance, not delivery.** Suppressed, unsubscribed and bounced recipients are dropped
  quietly. Use the delivery view for proof.
- **Keep transactional mail plain.** Emojis, link shorteners, user-controlled names and attachments trigger throttling.
- **List drafts explicitly.** A broadcast list can default to sent items, so a draft will not appear unless you ask.
- **Tags, fields and event names are case-sensitive and free-form.** One typo creates a new tag. Use one naming
  convention. A text match that means "contains" can match the wrong event, so use exact matches.
- **Do not decide on open rates.** Privacy features in mail clients distort opens. Use clicks, purchases and conversions.

## Verification
- A read request with the site identifier and the user-agent returns 200 for each site in use.
- A test event or send reaches only the seed addresses on the staging site.
- A broadcast draft appears in the draft list, and nothing in the send history shows it as sent.
- Each marketing body contains the unsubscribe placeholder, checked in the rendered HTML.
- A purchase event carries the order identifier, and a second identical event does not change revenue totals.
