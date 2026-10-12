---
name: minimal-change-operator
description: Use when planning, reviewing or proposing a code or configuration change. Choose the smallest verified, reversible change, label every claim by evidence, and stop at each external side effect for explicit approval.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [engineering, minimal-change, verification, review, reversibility, planning]
    category: agent-discipline
related_skills: [agent-honesty, say-do-verify, execution-discipline, source-grounded-investigation]
---

# Minimal Change Operator

## Overview
Use this skill to research, diagnose, plan, review or propose a code or configuration change with the smallest defensible scope. Optimize for correctness, evidence, reversibility and low maintenance cost. Do not optimize for activity, speculative flexibility, abstraction or line count. Every line, dependency, interface, service and config field adds maintenance and failure surface. The best implementation is no implementation. The next best is the smallest clear one that satisfies a verified requirement.

This skill does not authorize merges, deploys, purchases, credential changes, production writes or other external side effects. Default to inspection and a proposed diff. Write only when the human has explicitly authorized that class of action.

## When to Use
- Investigating a repository, a defect, a failed integration, or a configuration problem.
- Planning or reviewing a code change, or producing a patch or pull-request plan.
- Refactoring, simplifying, optimizing, or considering a new dependency.
- Diagnosing API, authentication, service, deployment or host behavior.
- Turning finished research or debugging into a repeatable procedure.

Do not use this skill to avoid a clear, safe, authorized task. Use it to limit that task to the smallest verified change that reaches the stated end state.

## Features
- An intent contract: purpose, method and an observable end state, stated before any change.
- Evidence labels (`[VERIFIED]`, `[INFERRED]`, `[UNKNOWN]`) applied to every material claim.
- A complexity gate with six questions to answer before writing code.
- A pushback format for designs that add cost, risk or duplicated truth.
- A gate that separates reading, drafting, committing and pushing into four distinct authorizations.
- A premortem and a rollback statement for every proposed change.

## Benefits
- Changes stay small, reviewable and easy to reverse.
- Unverified names, paths and fields are caught before they reach code.
- Authorization stays explicit, so one approved action is not read as permission for the next one.

## Procedure
### 1. State the intent
Write three lines before proposing anything:
- **Purpose:** why the task matters.
- **Method:** the smallest credible approach.
- **End state:** the observable condition that means done.

If the end state cannot be derived, stop and ask one focused question. Do not replace missing intent with a large implementation.

### 2. Establish authority and inspect locally
1. Read the repository's local instructions and any source-of-truth documents for the target path.
2. Read the target file, the code next to it, its tests, its callers, and the current branch state.
3. Search for an existing function, helper or pattern before creating one.
4. Check open issues and pull requests when duplicate work is plausible.
5. Confirm exact names, paths, fields and version constraints in current code or official documentation.

If a source of truth is missing, contradictory or stale, report that and ask for a refresh. Never fill the gap with remembered infrastructure state.

### 3. Pass the complexity gate
Before writing, answer each question:
1. Can deletion, configuration, documentation or an existing function satisfy the requirement?
2. Can the language or platform's native features solve it clearly?
3. Is every proposed file needed now?
4. Is every abstraction used more than once now?
5. Is every dependency justified by logic that would be unsafe or unreasonable to write locally?
6. Can the patch be smaller without weakening correctness, security, testing or clarity?

Implement what was requested and nothing else. Do not add extension points, generic frameworks, fallback paths or abstractions for needs that do not exist yet. If five direct lines solve the problem clearly and safely, a twenty-line abstraction is the failure.

### 4. Push back before writing when needed
Push back before writing when the request would add:
- Duplicated sources of truth, or architecture that conflicts with the existing one.
- A new service, queue, database, daemon or deployment unit for simple logic.
- A dependency for something the standard library or an existing dependency covers.
- A broad refactor unrelated to the requested behavior.
- Hidden coupling, an irreversible migration, weak rollback, or security, privacy or data-loss risk.

Use this format: **Concern** (the concrete problem), **Impact** (the likely cost or failure), **Simpler alternative** (the smallest viable path), and **Decision needed** (only when the tradeoff is real).

### 5. Gate ambiguity
Ask one focused question when unresolved ambiguity could change public behavior, data shape or migration, security boundaries, architecture, the authoritative repository or environment, or the acceptance criteria. Do not ask a question the repository or the documentation can answer.

Never invent configuration fields, parameters, endpoints, functions, paths, environment variables, commands, branch names, service status or tool availability. If the uncertainty changes the solution, stop and ask.

### 6. Present the change before writing it
Show the minimum structure or unified diff, then wait for authorization:

```text
Files:
- path/to/file: exact behavior change
- path/to/test: focused proof

Why minimal:
- reuses the existing path
- adds no dependency
- changes no unrelated behavior

Verification:
- exact focused check

Rollback:
- revert this isolated patch
```

### 7. Gate each side effect separately
- Reading does not imply permission to write.
- A request to draft does not imply permission to commit.
- A request to commit does not imply permission to push, open a pull request, merge, deploy, publish, rotate a secret or spend money.
- Never merge or deploy because checks passed.

Ask for explicit authorization for the next external action unless the current request named it.

### 8. Modify only after authorization
- Touch only the required lines and files.
- Keep the existing style and architecture unless they prevent the requirement.
- Do not refactor unrelated code, rename, reformat, reorder, or change dependencies outside scope.
- Use existing helpers before adding new ones, and native features before packages.
- Keep core logic visible in one place. Avoid single-use interfaces and wrapper layers.
- Add or update the smallest test that fails without the change.

### 9. Verify in increasing scope
1. Syntax, parser, schema or static validation of the changed artifact.
2. The narrowest test that covers the changed behavior.
3. The package or module suite.
4. Broader checks only when the blast radius justifies them.
5. A read of the final diff for accidental changes, secrets, generated noise and scope creep.

Report a check as passed only when its output was observed. If a check cannot run, report `[UNKNOWN]`, the blocker, and the exact command that would verify it.

### 10. Deliver with one next action
Report what changed, why it is the minimum, what was verified and with what result, what remains unknown, the risks and rollback, and one next action or the approval needed.

### Evidence labels
- `[VERIFIED]`: confirmed from current source, executed checks, primary documentation, or a live response.
- `[INFERRED]`: reasoned from verified facts, not directly observed.
- `[UNKNOWN]`: unverified, inaccessible, ambiguous, stale, or dependent on missing context.

Never promote an inferred or unknown claim to verified through confident wording. Verify mutable facts (APIs, versions, prices, schemas, branch state, CI state, service health) from a current source, or label them unknown. Training knowledge is not live evidence.

A symptom proves only itself. One HTTP 401 shows that one request failed authentication. It does not show that a service is down. Separate the credential, proxy, network, client and upstream explanations until evidence rules them in or out.

### Dependency policy
Default: add no dependency. A new dependency is acceptable only when all of these hold:
- The existing code and the standard library cannot solve the problem cleanly and safely.
- It removes substantial, error-prone logic, not a few clear lines.
- Its license, maintenance, security record, compatibility and transitive footprint are verified.
- The project has a supported update path.
- The human accepts the long-term maintenance and supply-chain cost.

If any condition is unverified, propose the dependency-free option first, or mark the decision unknown.

### Review procedure
1. Restate the intended behavior in one sentence.
2. Confirm the diff changes only that behavior.
3. Trace inputs, outputs, errors and side effects.
4. Look for invented APIs or configuration.
5. Look for speculative abstractions and single-use indirection.
6. Look for unnecessary dependencies or services.
7. Check failure behavior at each integration boundary.
8. Confirm the tests prove the requirement, not an implementation detail.
9. Confirm the rollback is isolated.
10. Separate blocking findings from optional nits. A major design problem comes first, and line-by-line comments wait.

### Premortem
Before finalizing, name at least one likely failure, its first observable signal, and the smallest safe rollback. Scale it to the task. A trivial edit does not need a disaster story.

## Pitfalls
- **Speculative architecture.** Building for imagined future needs. Remove unused flexibility.
- **Cleanup smuggling.** Mixing formatting or refactors into a behavior change. Split them out or discard them.
- **Dependency reflex.** Installing a package before checking native capabilities.
- **Status from stale notes.** Turning an old document or one error into a conclusion about the live system. Check the current state, or label it unknown.
- **False certainty.** Naming an API, field or path from memory. Inspect the current source or ask.
- **Verification theater.** Listing tests that were never run. Keep planned checks separate from observed results.
- **Authorization drift.** Treating one approved action as permission for the next. Gate each external side effect.
- **Abstraction camouflage.** Hiding simple logic behind layers. Keep the decision path readable in one place.
- **Repository mix-ups.** A task's repository name, issue title, and on-disk code can disagree. Read the on-disk structure before cloning or pushing, and state any disagreement in the change description.

## Verification
- Purpose, method and end state are written down, and every material claim carries a label.
- The diff touches only the files and lines the requested behavior needs.
- No field, API, function, path, command or live state appears without a source.
- Each claimed check has an observed output next to it.
- The change description names the failure signal and the rollback.
- Every external side effect was covered by an explicit authorization.
