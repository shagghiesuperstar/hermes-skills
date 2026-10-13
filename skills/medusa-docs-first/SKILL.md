---
name: medusa-docs-first
description: Use when writing or changing Medusa code and API calls. Requires the installed version, a cited official page or the installed types for each version-sensitive shape, and a stop with one exact question when the docs are silent.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [medusa, docs, cloud, cli, verification, no-guessing]
    category: commerce
related_skills: [medusa-agentic-development, medusa-admin-data-ops]
---

# Medusa Docs-First

## Overview

Medusa APIs, workflow hooks and hosting commands change between minor versions. A shape that looks right from memory can fail at runtime while unit tests pass against a stub, and a field the platform rejects can take a live store down. The rule for this work: confirm the installed version, cite the official page or the installed type for each version-sensitive shape, and stop with one precise question when neither answers it. Guessing is not an option.

## When to Use

- Writing or changing a Medusa route, workflow, module, notification, hook, subscriber or scheduled job.
- Calling the Admin or Store API, or the hosting CLI, from code or a script.
- Saying a feature is "not built in" or "needs a custom build".
- Debugging a Medusa build, deploy, migration or runtime error.

## Features

- A version check against the latest release and the project's pinned version, with a stated reason for any difference.
- A fixed source order for each shape: installed types, then the official page for that version, then a stop.
- A search of the official examples and of the team's own repositories before a feature is called missing.
- Gate rules: a real production build, live proof for user-facing work, and hook and metadata rules that prevent silent failures.
- A template for the one question to ask when the docs are silent.

## Benefits

- Shapes come from the installed version, so a wrong field is caught before a customer sees it.
- "Built in" claims are checked against the examples and the codebase first.
- A documentation gap becomes one specific question for the platform's documentation assistant, not a shipped guess.

## Procedure

1. **Check the version.** Read the installed `@medusajs` packages in the project and compare them with the latest release. State both in the task. If the project is pinned behind latest, confirm the documented behaviour applies to the installed version by reading its release notes, or flag the difference. Do not change a pin without the owner's approval.

2. **Read the installed types first.** The type definitions in the project's dependencies, and the generated types the framework writes to its output folder, reflect the exact version in use. They outrank any web page.

3. **Cite the official page for anything the types leave open.** Fetch the current page for the API, workflow, module, notification or cloud feature. Quote the line or example the implementation follows, and use the documented shape exactly. Do not add fields "because they might help".

4. **Use the CLI's own help.** Compare the hosting CLI's version with the latest and upgrade it if it is behind. Read `--help` for every flag. Never assume a flag exists.

5. **Search before claiming something is missing.** Look in the official examples repository and the documentation recipes. Then search the team's repositories for an existing implementation, and read each hit, because text search matches substrings. Only then state the build effort, and name the example or repository path you would reuse.

6. **Stop when the docs are silent.** Write one exact, self-contained question the owner can paste into the platform's documentation assistant, with the concrete conditions included. For example: "If a notification is created with both a template name and inline HTML, does the hosted service look up the template and fail when it is missing?" Do not ship on a guess.

7. **Vet third-party plugins before use.** A plugin's version range is not compatibility. Check its peer dependencies against the installed core packages, and its major versions of shared libraries. Boot the backend with the plugin installed on the same version. Review a community plugin's public store endpoints before exposing them. Prefer a native module to a forced dependency override.

8. **Build with the real build command.** A type check with no output does not generate the types that query-graph links depend on, so it can pass while the real build fails. Run the project's production build and keep its tail in the task record. After a merge, read the hosting platform's build log.

9. **Require live proof for user-facing work.** For email, done means a delivery record with status delivered, not merged code. For a storefront change, done means the live page shows the change.

### Rules That Prevent Silent Failures

- **One handler per workflow hook.** Two features that each register a validator on the same hook pass alone and fail together. Keep one registry file per hook, and check for duplicates before merging.
- **A hook receives a narrow field set.** The cart a checkout hook receives contains only the fields the platform lists for it. A validator that reads any other field silently does nothing. Load other data by ID with the query graph, and test the hook with a cart that carries only the fields it receives.
- **An empty metadata value deletes the key.** Store negative state as a real value such as a timestamp. An empty string makes the state disappear, and later code reads "never set".
- **The validated body is the one that persists.** The route's validation middleware makes a sealed copy of the request body, and that copy is what gets saved. Stripping the raw body in a later middleware changes nothing that is stored. Reject on the validated copy, and test by composing the real middleware array in order.
- **Relations need explicit expansion.** A field missing from a response is not an empty field. Request the field with its expansion and check the result.

### Three-Label Truth Taxonomy for Research Notes

When writing an architecture brief or a research note, label every claim:

- **Officially supported:** a documentation page states the capability directly. An inference from a related page does not count.
- **Workaround:** a page describes the pattern but says it needs custom code or a custom platform layer.
- **Not documented:** no page confirms or denies it. Write "not documented" and stop. Do not add speculation.

Cite the page URL for each point, and keep the citations in their own table. Fetch each page rather than citing a search snippet. Use individual pages rather than a gated full-text file. Count words with a tool, and keep the brief below its cap with a margin.

## Pitfalls

- **Calling a feature missing without searching the examples and the codebase.** It may already exist.
- **Trusting a passing type check as proof.** Run the real build.
- **Citing a URL you never fetched.** That is invented citation.
- **Speculating after "not documented".** Stop at the label.
- **Presenting community documentation as official.** Label partner or third-party material as such.
- **Guessing a field on a version newer than the one you read.**

## Verification

- The installed version and the latest version are both stated.
- Every version-sensitive shape is backed by the installed types or a cited page.
- The production build passes, and its tail is in the task record.
- Every claim in a research note has one of the three labels and a source URL.

## Attribution

Recipes and examples come from the Medusa project: its official documentation (https://docs.medusajs.com) and its examples repository (https://github.com/medusajs/examples).
