---
name: deterministic-discovery-doctrine
description: Use when answering questions about configuration, keys, vendors, UI, how-to steps or architecture. Load an authoritative source before answering or acting, because a guessed answer on these topics is a hard failure.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [discovery, documentation, grounding, configuration, vendors, accuracy]
    category: agent-discipline
related_skills: [source-grounded-investigation, vendor-identity-verification, agent-honesty]
---

# Deterministic Discovery Doctrine

## Overview
Some questions have one correct answer that lives in a document, a schema, a config file, a live API or a user interface that can be clicked. Answering them from memory produces confident fabrications: header names, token formats, authentication methods and button labels that sound right and are wrong. Each fabrication costs the operator time and trust. This doctrine sets a rule for six topic classes: load an authoritative source before answering or acting, quote what it said, and say plainly when no source is available.

## When to Use
- The question concerns configuration: environment variables, settings, or deployment configuration.
- The question concerns keys or secrets: formats, scopes, headers, or authentication methods.
- The question concerns a third-party vendor: service behavior, API shape, pricing, or schemas.
- The question concerns a user interface: buttons, navigation, panel names, or form fields.
- The question is a how-to: an operational procedure or a click path.
- The question concerns architecture: system design, request flow, or an authentication chain.

Outside these six classes, use ordinary judgment. General knowledge, arithmetic and common tool usage do not need a lookup.

## Features
- A six-class trigger list that decides when the doctrine applies.
- A source-selection ladder: local skills or documentation, then vendor documentation, then a connected domain tool, then the operator.
- A citation rule: the reply names the path or URL beside each claim.
- A list of forbidden inferences, such as guessed header names and token parsing by prefix.
- A fallback rule: when no source exists, say so and ask.

## Benefits
- Claims about authentication, headers and UI can be checked by following the citation.
- Wrong guesses about vendor APIs are caught before they reach code or configuration.
- The operator can tell a sourced answer from a guess at a glance.

## Procedure
### 1. Name the topic class
Decide which of the six classes the question belongs to. If it spans more than one, apply the doctrine to each part.

### 2. Pick the authoritative source
1. For first-party software, search the local skills directory for a skill with a matching name, and read it.
2. For vendor behavior, fetch the official documentation with a web extract tool, or search for it first. Keep the URL.
3. For a connected domain service, query that service directly, such as a documentation server or a platform API.
4. For a user interface, ask the operator for the screen, or drive the interface yourself with a browser or desktop tool and read what is there.

### 3. Quote the source in the reply
Put the file path or URL beside the claim. A memory of the source is not a citation.

### 4. When no source is available
Say so in one sentence, name the sources you tried, and ask the operator for the missing input. Do not fill the gap with a likely answer.

### 5. Treat live evidence as current state only
A request that returned a status code, or a log line that shows a call, proves the current state. It does not reveal undocumented behavior. Use live evidence to confirm a documented claim, not to infer a new one.

### Forbidden inferences
- Guessing an authentication header name, such as "it might be a bearer token" or "try an organization header".
- Inferring a token's type or scope from its prefix string.
- Reciting an API pattern from memory when the documentation is one fetch away.
- Naming a button, menu or field without having seen it.
- Probing with request variants one after another when one documentation lookup would answer the question.

## Pitfalls
- **Fetching for trivial questions.** The doctrine costs a lookup. Apply it to the six classes, not to every sentence.
- **Explicit requests for a guess.** When the operator says a rough idea is fine, answer, and label the answer as a guess.
- **Stale documentation.** If the live system disagrees with the documentation, report both, and check the version.
- **Search results as sources.** A search hit is a pointer. Fetch the page before quoting it.
- **Absence claims without probes.** "The feature does not exist" needs the places you searched listed beside it. Without that list, say the feature was not found.

## Verification
- Each answer in the six classes names the source it came from, with a path or URL.
- No header name, token format, button label or endpoint appears in a reply without a source beside it.
- When no source was found, the reply says so, names the sources tried, and asks for the missing input.
