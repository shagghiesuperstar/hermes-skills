---
name: medusa-agentic-development
description: Use when orchestrating or implementing Medusa.js commerce work with coding agents. Covers harness roles, official docs and agent plugins, a B2C-first monorepo boot, vendored compliance-module wiring and bank-gated payment sequencing.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [medusa, ecommerce, claude-code, codex, mcp, harness, monorepo]
    category: commerce
related_skills: [medusa-admin-data-ops, medusa-docs-first, medusa-api-verification]
---

# Medusa Agentic Development

## Overview

A Medusa storefront project is a monorepo: a backend, one or more storefronts, shared packages and sometimes a vendored compliance module. Coding agents do this work well when each one has a narrow job: an orchestrator that plans and gates, one primary implementer, an independent reviewer, and official documentation as the grounding source. The rules below keep the work small, reviewed and reversible.

## When to Use

- Bootstrapping or changing a Medusa v2 monorepo with coding agents.
- Deciding which agent does which job on a Medusa project.
- Preparing a first boot pull request, a hosted-build fix, or a compliance-module change.
- Planning payment and launch sequencing for a regulated store.

## Features

- A role table for orchestrator, implementer, reviewer and grounding sources.
- Installation of the official Medusa agent plugins and documentation server, with a check that the session can use them.
- A B2C-first boot checklist that comes before any B2B work.
- Lockfile and workspace rules for hosted builds.
- Compliance-module symlink wiring, with the TypeScript resolution rule.
- Payment sequencing behind a stub adapter, so most work proceeds before a processor account exists.

## Benefits

- Each agent has one job, and no agent approves its own change.
- Official documentation and plugins replace guesses about API shapes.
- A smallest-first boot pull request gets reviewed before code is written.
- Launch work continues while a payment account is pending.

## Procedure

1. **Assign roles.**
   - Orchestrator: writes specifications, splits work into tasks, and runs the gates. It does not write application code.
   - Primary implementer: a coding agent with repository access, working in a branch or worktree.
   - Independent reviewer: a second agent or model that reads the proposal and then the final diff.
   - Grounding: the official documentation server and the official agent plugins.
   Use community packages as the main documentation source only when the owner approves them.

2. **Install the coding agent from its official installer,** then confirm it runs and that its login is valid. A person completes any browser login. Never put credentials in tasks, logs or chat.

3. **Install the official Medusa plugins.** Run each install interactively, read the plugin list before you confirm it, and pin a plugin version where the marketplace supports one. Do not script the install with an automatic yes.

   ```bash
   claude plugin marketplace add medusajs/medusa-agent-skills
   claude plugin install medusa-dev@medusa
   claude plugin install ecommerce-storefront@medusa
   claude plugin list
   ```

   The learning plugin is for training and is not needed for production work.

4. **Connect the documentation server over OAuth,** not a personal access token. List the servers with `claude mcp list` before logging in, because a plugin may register the server under a longer name.

5. **Prove the connection before you claim it.** In a headless run, the documentation tool must be explicitly allowed or its calls are blocked. Allow only that tool, never a flag that skips all permissions:

   ```bash
   claude -p "<question>" --allowedTools "<documentation tool name>" --max-turns 12
   ```

   Report a documentation lookup as working only when the session exposed the tool and returned a cited answer. An old, unauthenticated entry for the same server in a project's local settings can shadow the working one. Remove the stale entry and check again.

6. **Propose before implementing.** The implementer writes the smallest pull request it can justify as a plan, without running it. The reviewer checks the plan for unnecessary files, wrong framework patterns, missing tests, exposed secrets, deployment assumptions and scope creep. The owner approves before any code is written.

7. **Boot the storefront before anything else.** The first pull request covers only the local boot path: the storefront environment template, the README steps, and a seed script if the task is broken. Out of scope: other storefronts, public deployment, compliance rule values and unrelated integrations.

8. **Follow the boot order.**
   1. Start the database and create the database named in the backend configuration.
   2. Copy the backend environment template and set real values for the database and secrets.
   3. Run migrations.
   4. Run the seed. It is required, because it creates the regions and the publishable key the storefront needs.
   5. Start the backend and open its admin page.
   6. Set the publishable key in the storefront environment and start the storefront.

9. **Treat the lockfile as the authority.** Trust the package lock over any README that names another package manager. Every workspace under the apps directory must appear in the lock. Do not hand-edit the lockfile. Check a clean install with the same Node and npm versions as the hosted build.

10. **Require a backend build, not only an install.** A clean install does not justify a merge. Run the backend build as well. Passing compliance-module tests does not prove that the runtime wiring works.

11. **Wire a vendored compliance module with symlinks.** Link it into the backend, including the route, the library file and the data file. Relative imports can resolve from a link's own path rather than its target, so check that the resolved paths match, because an incomplete set of links can cause "cannot find module" errors. Commit the links as symbolic links (mode 120000). The gate must never fail open.

12. **Check the prune step.** A monorepo prune for container builds can drop the vendored directory, which leaves links dangling inside the build context. Confirm that the container build includes the vendored files.

13. **Sequence payments around the bank review.** A payment processor often reviews the live site before it issues gateway credentials, so payment stays blocked until the site exists. Build a stub payment adapter behind a common interface, so search, cart and a sandbox checkout can be tested with no credentials. Swap in the live adapter later without changing the checkout tools. Split the work into what can be built now and what waits for credentials, and put the one human go or no-go decision at that boundary.

14. **Split agent-facing commerce by trust.** When an AI agent can search and buy, run two services: a private one with product and checkout tools, and a public one that answers read-only questions only. The public service must have no write or checkout tool at all, and an automated test should confirm its tool list contains no write. Limit its fields to name, handle, category, brand and description, and hold back efficacy or health claims until a legal review.

15. **Put compliance gates upstream.** Every product search and detail response passes the state or age compliance gate before it reaches an agent. The gate fails closed.

16. **Do not count a demo service as live.** A service that passes its tests but serves in-memory demo data is a shell, not a content source. Report it that way.

17. **Roll back a broken production release with a revert.** Fetch the remote first, create a worktree from the current remote main, revert the bad commit, and push. Wait until both the backend and the storefront show the new commit as active, then check a list of pages with curl. A revert still goes through the review gate and the operator's approval. Whether an emergency path skips part of that process is the operator's call, not a default.

18. **Treat hosted-platform rendering changes as deploy gates.** Caching and rendering-mode changes can behave differently on a hosted platform than in the local framework. Test them on a staging deployment with a live page check before merging to production, even when a static review passed.

## Pitfalls

- **A community documentation server as the main source** gives answers no one can check. Use the official one.
- **Reporting a headless session as if its tools were present** when no tool call ran.
- **Blaming a lockfile update for an existing build error.** Check the failing commit before the lockfile.
- **Assuming a submodule is enough.** A submodule that is present but not linked is not wired.
- **Merging on a passing install.** Require the build.
- **Letting the first boot pull request grow** to include public deployment or extra integrations.
- **Letting the orchestrator write application code.** It loses the review boundary.
- **One agent reviewing its own change.**

## Verification

- The coding agent reports a valid login, and the chosen model is confirmed with a one-line probe.
- The official plugins are listed as enabled, and the documentation tool returned a cited answer in a session that exposed it.
- The backend and the storefront both build from a clean install, with the seed run and the publishable key set.
- The compliance module's links are committed as symbolic links, and the build resolves them.
- The public commerce service's tool list contains no write tools.
- After a rollback, the backend and the storefront both run the reverted commit, and the page list returns 200.

## Attribution

The plugin and documentation-server steps follow the Medusa project's official agentic-skills guide (https://docs.medusajs.com/learn/introduction/build-with-llms-ai/agentic-skills) and its documentation-server page (https://docs.medusajs.com/learn/introduction/build-with-llms-ai/mcp-server).
