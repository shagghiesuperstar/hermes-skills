---
name: ecommerce-readiness-rollout
description: Use when turning lessons from past e-commerce launches into one reusable readiness checker that runs against any storefront URL. Covers the lesson record format, portable checks, consolidation timing and checking a new site against known incidents.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [ecommerce, readiness, checklist, regression, cross-site, rollout]
    category: commerce
related_skills: [catalog-publish-safety, commerce-media-pipeline]
---

# E-commerce Readiness Rollout

## Overview

Every launch teaches the same lessons again: an age gate that blocks the cart, a price shown without tax, a checkout that charges before the cart state is re-read, an order that never reaches the back office. When each lesson stays inside one site's incident report, the next site repeats it. This skill turns each catch into a short record with a portable check, then consolidates those records into one checker that takes any storefront URL and a test account as inputs.

## When to Use

- Asked to build a reusable readiness checker or to gather every lesson from past launches into one list.
- Asked to run a readiness pass against a new site that did not produce the original catches.
- A dogfood run, a catalog preflight or a review round has produced a new catch that should join the shared list.

Skip it for a single-site test pass, a single catalog write (use catalog-publish-safety), a single storefront build, or a single media job (use commerce-media-pipeline).

## Features

- A fixed record shape for every catch: surface, symptom, root cause, portable check and evidence reference.
- One list per surface, such as checkout, payments, catalog, email consent, speed or search files.
- A check rule that takes the storefront URL and test account as inputs, with no site name in the code.
- A self-test step that proves the checker finds the known catches on a site where they are known to exist.
- A consolidation timing rule that keeps the work from competing with live launches.

## Benefits

- A new site gets the full history of known failures without anyone re-deriving them.
- Each check can be re-run and gives the same answer, so a regression shows up as a failed check.
- A FAIL points to the earlier incident that it matches, which is faster to triage than a fresh bug.

## Procedure

1. **Write each catch as one record.** Use this shape, one record per catch:

   ```text
   surface: <auth-age-gate | catalog-pdp | cart | checkout-state | payments | orders-erp | email-consent | speed | seo-agent-files | release-ops>
   symptom: <what the operator or tester saw>
   root_cause: <the mechanism, in one clause>
   check: <the deterministic check that would have caught it earlier>
   evidence_ref: <task ID, review file or section of a runbook>
   ```

   The check is the part that carries across sites. Symptoms and causes are local to one store.

2. **Require a portable check.** A check must be a single command, a single function or a single assertion that can be re-run. A check that says "review by hand" is not a check. If a catch arrives without one, derive one before adding the record.

3. **Deduplicate.** Before adding a record, search the list for the same `evidence_ref`. A catch already present gets no second record.

4. **Keep the per-site report as it is.** The incident report is the audit trail for one site. The shared list is the regression list for all of them. Both exist side by side, and neither replaces the other.

5. **Make every check parameterised.** Take the storefront URL and the test account as inputs. Search the checker's code for any site or store name before you finish; a name in the code is a per-site check dressed up as a general one.

6. **Avoid checks that depend on one platform's internals.** A check that reads a particular framework's internal module fails on any other stack. Describe the behaviour instead: "a checkout that retries after a network drop must re-read the cart before charging". Then implement that behaviour test for the platform in use.

7. **Self-test the checker.** Run it against one staging site where the known catches exist. A checker that reports nothing on such a site is broken. A checker that reports exactly those catches is working.

8. **Run it against a new site.** Pass the URL and the test account, save the report, and list every FAIL with its evidence reference. The check is read-only: it places no orders, makes no real payment and changes no account data, and it runs only after the owner approves the test account. A FAIL means "this site has the same shape as an earlier incident; investigate before the next release". Deciding whether to block a release belongs to the owner.

9. **Consolidate only when no launch is in flight.** Reviewing the whole history of reports is a large job that competes with live launches for the same budget. Run it between launches, and check the budget first. If a launch is active, record the consolidation as deferred, with the reason and the condition for resuming.

10. **Re-check deferred work each time.** A deferred consolidation is still pending. Check its resume condition at the start of each session that touches e-commerce work, and raise it with the owner when the condition is met.

## Pitfalls

- **"Consolidated everything" needs a count.** Compare the number of incident reports with the number of records in the list, per surface. A very large gap means the pass is partial. Report the per-surface numbers, not one total.
- **A check that hardcodes a host is a per-site check.** Grep the checker for every host and store name from the original launches before calling it general.
- **A check tied to one platform's internals fails on another stack.** Describe the behaviour, then implement it per platform.
- **Asking the same deferred question again wastes a turn.** Record the decision and the resume condition once. Ask only whether the condition is now met.
- **A parked item is not a dead one.** Deferred work loses value when nobody checks its resume condition.
- **A FAIL is not an automatic block.** The checker shows where a site resembles a past incident. The owner decides what to do about it.
- **Records without evidence drift.** A record that cites no task, review or runbook section cannot be checked later. Reject it until it has one.

## Verification

- Every record has all five fields filled, and its check is a single runnable step.
- Searching the checker's code for any site, host or store name finds none.
- The self-test on the known-incident staging site reports exactly the known catches, and nothing else.
- The per-surface record count matches the count of incident reports that were consolidated, and the gap is explained.
- A run against a new site produces a report in which every FAIL names its evidence reference.
