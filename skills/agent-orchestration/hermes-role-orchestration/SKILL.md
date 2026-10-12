---
name: hermes-role-orchestration
description: Use when designing or maintaining role routing. Covers runnable agent profiles, identity documents, and provider fallback chains for a multi-agent Hermes fleet.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, profiles, roles, routing, fallback, orchestration]
    category: agent-orchestration
related_skills: [kanban-orchestration, harness-task-prompting, claude-cli-model-switching]
---

# Hermes Role Orchestration

## Overview
A multi-agent Hermes fleet has several surfaces that describe which model each role uses, and they drift apart unless one of them is the source of truth. This skill sets the ownership rules: the live configuration is the only place that names models and providers, identity and roster documents point to it, and a role is a runnable profile only when it has its own working configuration. It also covers the routing defaults, the cost rules for council-style model use, and the checks that a role can actually receive and finish work.

## When to Use
- Creating a role-named profile, or deciding whether a role needs a new profile or only a routing label.
- Maintaining the routing document, the live configuration, identity documents, or the roster.
- Setting provider and fallback chains for a role.
- Retiring or merging legacy profiles.
- Deciding whether a council of models is worth its cost for a task.

## Features
- A map of the four source-of-truth surfaces, with the owner of each.
- A rule that identity and roster documents carry no model names, only pointers to the live configuration.
- Routing defaults: a provider router, throughput sorting, data-collection denial, and slug verification against the live catalog.
- A cost rule for council-style multi-model use, with the model matched to the function of each step.
- A readiness floor for any profile that accepts kanban work, and a test for a runnable profile.
- A profile retirement procedure that preserves operational facts before deletion.

## Benefits
- A model change happens in one place, so no document keeps a stale model name.
- A profile that looks ready is checked against a real configuration, not a directory listing.
- Council cost is spent only on planning and open-ended design, not on mechanical edits.
- Retiring a profile does not lose the hosts, endpoints, or scheduled jobs that depended on it.
- A broken profile is replaced by a working external harness, so the work keeps moving.

## Procedure
1. Name the owner of each fact before you write it down:
   - The routing document holds the role-to-model map, primary and fallback choices, and dispatch notes.
   - The live configuration holds the provider, default model, routing block, fallback providers, auxiliary routes, and provider authentication. It is the only file that actually runs.
   - The identity document holds role, scope, non-goals, delegation targets, and workflow gates. It holds no model names, versions, or fallback chains. It may point to a section of the live configuration.
   - The roster document describes the roster and dispatch behavior. It matches what the dispatch code does, and it also holds no model pins.
2. Before you create a new role-named profile, inventory the existing profiles and their identity documents. Check whether the role already exists under an older name. Prefer a routing label when a tuned profile already covers the role.
3. Create a new runnable profile only when it has a distinct provider, authentication, licence, or lifecycle need. Give it a working configuration with a provider, a default model, and authentication. A directory that holds only an identity document is a dead stub, not a profile.
4. Check the profile before you call it created. Run the configuration check and require it to pass.
   ```bash
   hermes --profile "<profile>" config check
   ```
5. Verify every model slug against the live catalog before you write it. Use exact set membership on the catalog's identifiers. Do not use a substring search, and do not trust a catalog read that was cut off partway, because it can look like a missing model. If two reads disagree, re-run the clean read.
6. Set the routing defaults for a provider router: throughput sorting, data-collection denial, and a model-specific quality floor where the router supports one. Keep those keys at the top level of the routing block.
7. Choose the council (multi-model) mode per task. Use a council for planning, strategy, and hard design. For mechanical work, such as file edits, configuration patches, commits, and deterministic checks, use a single model. When the remaining work is mechanical, recommend switching to a single model.
8. Match each model to the function it serves. Structured extraction and schema work suit fast models that enforce schemas. Reasoning steps suit frontier models. Embeddings suit a local model. Spend frontier budget on planning, then hand the written plan to a mid-tier model for implementation.
9. Make a profile able to receive kanban work. It needs a valid configuration with a model and a provider, the kanban toolset, the terminal and file toolsets for any coding or operations role, and an identity document that ends every run with a completion or block call.
10. When a profile is broken, route coding work to an external coding harness that is working, under the orchestrator's ownership. Smoke-test that harness before dispatching to it.
11. To retire a profile, first record any operational facts that only it holds: host addresses, endpoints, and key names that other profiles share. Then check the scheduled jobs and the task board for references to the profile, and update or reassign them. Only then delete the profile.
12. Read the final state from disk, and confirm every check passes before you report the work as complete.

## Pitfalls
- **Model names in an identity or roster document drift.** Within two generations an identity document can describe models that the live configuration no longer runs, and it misleads whoever diagnoses a fault. Keep model pins out of those documents.
- **A directory with only an identity document is not a profile.** Dispatch to it fails, and the failure looks like a lost task.
- **A profile that claims to be ready needs a toolset check.** Listing the profiles is not enough. A profile without the kanban toolset can exit without completing or blocking, and it then crash-loops.
- **Do not let the router use an unverified slug.** A phantom slug fails partway through a council run, and the failure is hard to trace.
- **Council runs can corrupt.** A reference model's stream can degrade into repeated output. Treat a garbled reference as a reason to drop the council for that task, and never base a configuration change on a garbled read.
- **Use the platform's own configuration commands for guarded files.** Some editing tools refuse to write an existing configuration file. Do not work around that refusal with a different tool. Make the change through the configuration command, or ask the operator.
- **Some local servers reject common parameter values.** Check the exact accepted values for a local server's parameters before you set them, because a value that looks equivalent may be refused.
- **A per-profile override may not be supported.** If the platform does not scope a routing option to one profile, keep the route on a concrete model and write a note that records the intended behavior.
- **Honest disagreement is part of the job.** If the operator proposes a model choice you think is wrong, say so with the evidence. If the operator brings newer information that changes the answer, update the recommendation.
- **Do not delete a profile that a scheduled job still names.** A job that points at a deleted profile fails silently until someone notices.
- **Remove nested cache directories in a second pass if the first removal fails.** The directory handles are often released after the first attempt.

## Verification
- The live configuration parses, and the configuration check passes.
- The routing document has a row for every role that was requested, and each row was read back from disk.
- Every model slug in the configuration appears in an exact-match check against the live catalog.
- Identity and roster documents contain no model names, versions, or fallback chains. A search for model-name patterns in those files returns nothing.
- Every profile that accepts kanban work has the kanban toolset, a model, and a provider.
- A retired profile has no remaining references in scheduled jobs or on the task board.
