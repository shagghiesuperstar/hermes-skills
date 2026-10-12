---
name: technical-documentation-distillation
description: Use when distilling large official docs. The references keep exact endpoints, headers, signatures, imports, paths and commands. Search first, read bounded regions, and verify every file and the final response.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [documentation, distillation, apis, reference, offline, fidelity]
    category: memory-knowledge
related_skills: [source-grounded-investigation, read-only-discovery, deterministic-discovery-doctrine]
---

# Technical Documentation Distillation

## Overview
A large official documentation set is too big to load into an agent's context at once, and a loose summary of it loses the exact tokens that matter: endpoint paths, header names, import lines, signatures and config keys. This skill turns a documentation corpus into compact, task-oriented reference files. It keeps exact technical tokens verbatim, synthesizes the explanation around them, and treats the file set, its size bounds and any response schema as separate checks.

## When to Use
- Building compact offline references for an agent skill from a large local or downloaded set of official docs.
- Splitting framework documentation into API, architecture, module, interface or operations notes.
- Preserving exact endpoints, headers, imports, signatures, paths, names and decision rules.

Do not use this for a free-form summary where source fidelity does not matter.

## Features
- A manifest step that turns the request into checkable constraints before any writing.
- Search-first reading, with bounded regions instead of whole-file loads.
- A split between exact tokens, which must match the source, and synthesized guidance.
- A source map in each file, naming the sections actually used.
- Validation of line counts, headings, hidden control characters and placeholders.

## Benefits
- Each reference is small enough to load, and its exact tokens can be checked against the source.
- Requested file sets, size bounds and response schemas are each verified on their own.
- Invented APIs are caught before they reach a skill.

## Procedure
### 1. Build the manifest
Write down the output paths, the topic scope, the tokens that must stay exact, the size bounds, whether a source map is required, and the final response contract. Every explicit constraint must appear once in the manifest.

### 2. Search the corpus, then read bounded regions
Use a search tool to find chapter headings and high-signal terms. Read only the regions around each match, and widen the region when context crosses a chunk boundary. Each output topic should have at least two source anchors: its official chapter titles or section names.

### 3. Normalize the text
Strip zero-width and bidirectional control characters from extracted text. Keep punctuation and code tokens. A reference with hidden formatting controls fails the check in step 7.

### 4. Separate exact tokens from synthesized guidance
- **Exact tokens:** endpoint patterns, HTTP headers, authentication flows, SDK signatures, imports, module names, file paths, commands and configuration keys. Copy them exactly, with source spelling, capitalization, path parameters, package scopes and argument order.
- **Synthesized guidance:** responsibilities, interactions, sequencing, caveats and decision rules. Write these in your own words.

Never infer an endpoint, method, import, header, config key or signature from a naming convention. If the source does not show it, leave it out.

### 5. Draft for retrieval
Organize the notes by task, not by source order. Use short headings, decision rules as bullets, and links between related concepts. Consolidate repeated bullets rather than deleting exact tokens. Do not copy long passages.

Keep the file structure simple: one H1 title, then H2 and H3 headings, and one fact, rule or interaction per bullet. Put an example in a code block only when the syntax needs it.

### 6. Add a short source map
Name the official documents or chapter titles that the file used. The map is a navigation aid, not a bibliography.

### 7. Write each file and validate it
For each file, check that it exists, that its line count is inside the requested range, that its expected headings are present, that it has no hidden control characters, and that it has no placeholder text left in it.

### 8. Validate the final response from the artifacts
If the task supplies a JSON schema, the final response is one JSON value. Serialize exactly that value and parse it with a standard parser before sending it, and check the required fields. Do not add prose before or after it, and do not wrap it in a code fence unless the task accepts one.

### Fidelity rules
- Never infer an endpoint, method, import, header, configuration key or SDK signature from naming conventions.
- Separate public or storefront credentials from privileged or admin credentials, and label each.
- Keep version-sensitive claims qualified when the documentation does not state a stable contract.
- Prefer a few representative API patterns over a generated catalog of every endpoint, unless the task asks for the catalog.
- Describe cross-module behavior as orchestration and ownership boundaries. Do not describe direct database coupling unless the documentation states it.

## Pitfalls
- **Loading the whole corpus.** It overflows context and lowers fidelity. Search first, and read bounded regions.
- **Copying prose.** Bulky copies defeat the purpose. Keep the tokens, and write the explanation yourself.
- **A file that exists is not a file that passes.** Scope, line bounds and hidden characters are separate checks.
- **A valid file set can still fail delivery.** If the final response breaks its machine contract, the whole task fails.
- **JSON-only contracts.** Return exactly one object, with no prose, no second object and no trailing summary.
- **Summary requests versus schemas.** If the task asks for a human summary and also supplies a schema, the schema controls the envelope. Fit the summary inside the allowed fields.

## Verification
- Every requested output path exists.
- Each file's line count is inside the requested range.
- A scan of each file finds no zero-width or bidirectional control characters.
- Each file has a source map and covers its requested subject areas.
- Spot-check each endpoint pattern, header, signature, import and path against the source text.
- The final response parses with a standard JSON parser, and its required fields are present.
