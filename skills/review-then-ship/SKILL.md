---
name: review-then-ship
description: Use when preparing a commit or PR for production code. Pause after the first working draft, verify the external symbols, trim the scope, then ship.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [pr, review, verification, scope, production, upstream]
    category: devops
related_skills: [pr-evidence-verification, adversarial-review, github-issue-to-pr]
---

# Review-Then-Ship Discipline

## Overview
A first draft that compiles and passes basic tests feels ready. A review pass before the change leaves its author's hands catches three common failures: an over-scoped first attempt, unverified assumptions (wrong signatures, missing symbols), and missed edge cases. The discipline is draft, verify, trim, ship. Never skip the verify and trim steps for work that an outside reviewer or a production deploy will see.

## When to Use
- The work ends in a pull request, commit or patch that someone other than the author will review.
- The change touches C, C++, Rust or another language with opaque headers, where the compiler is not the only check.
- The change affects a live service, where a bad patch means a restart loop or broken production.
- The draft is described as "it compiles and the tests pass, ready to commit".

Skip for throwaway spikes, local scripts that never leave the machine, and comment-only or documentation-only changes.

## Features
- A header and dependency check for every new external symbol.
- A scope trim, with three questions for each new line.
- A one-sentence justification test before the final commit.
- A verification checklist, including a live request against the real binary for HTTP changes.
- A commit-message-first step.

## Benefits
- Upstream reviewers see the minimal change rather than the speculative one.
- Wrong signatures are found before a reviewer finds them.
- A change that alters output a downstream consumer parses is caught before it breaks that consumer.

## Procedure

1. **Verify every external symbol.** List each function, type, field and endpoint the change introduces. Grep the headers and the implementation for each one, and confirm it exists with the signature you use. If a symbol is missing or different, fix it now. A successful compile can have used a stale object or another header path.

2. **Trim the scope.** For each new line, ask three questions. Is it required for the stated goal? Does it add a new contract the maintainer must review, and if so, is that justified? Would a smaller version still solve the immediate problem? If the third answer is yes, ship the smaller version. A trimmed change is smaller, easier to review, and has fewer new dependencies.

3. **Write a one-sentence justification.** Answer: why must this exist in the upstream project and not only in the consumer? If you cannot answer in under twenty words, the change is too large, or it belongs somewhere else.

4. **Run the checks.** Build with warnings enabled (`-Wall -Wextra` or your toolchain's equivalent). Run the relevant test target. For HTTP changes, exercise the real binary with curl, because unit tests can pass while the dispatch order is wrong.

5. **Check the public routes that did not change.** Confirm that they still behave the same.

6. **Check downstream consumers.** If a dashboard, a tool or a service parses the program's output (its help text, telemetry or error format), restart that consumer against the new binary and check its status endpoint.

7. **Write the commit message first,** to a file, then commit with that file.

## Pitfalls
- **"It compiled, ship it."** The first build can hide wrong signatures that no code path has called yet. Grep the headers.
- **"I'll add it now and remove it later if they object."** Reviewers reject extra surface area. Trim before the first review, not after.
- **The editor's language server is not the verifier.** It catches syntax and some type errors. It does not catch a field that takes its value from the wrong place, or an endpoint name that will collide with a future route.
- **A benign change to output can break a parser.** A reformatted help text or telemetry line can crash a consumer that parses it on its next refresh. Fix the consumer or keep the format, and know that you are creating the work.
- **Wait for the maintainer before proposing follow-up work.** While an upstream pull request is open, do not suggest next steps or fallbacks. A reply that anticipates objections reads as presumptuous. A reply to feedback reads as responsive.
- **Opened is not shipped.** An open pull request is not done. Done means merged, with the merge commit confirmed and any required checks green. Re-check the pull request's state before you report it complete.
- **After each squash merge, recheck the next pull request.** Sequential merges often mark the next branch as conflicting until the base has the earlier change.

## Verification
- [ ] Every new external symbol was found in the headers or implementation with the expected signature.
- [ ] Every added field or endpoint has a one-sentence justification.
- [ ] The build is clean with warnings enabled.
- [ ] The relevant test target passes, and any HTTP change was exercised against the real binary.
- [ ] Public routes that did not change still behave the same.
- [ ] Downstream consumers were restarted, and their status endpoints answer.
- [ ] The commit message was written before the commit.
