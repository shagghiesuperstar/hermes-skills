---
name: security-gate-review
description: Use when a change touches a compliance gate. The question is whether a fail-closed gate still blocks, such as a restriction at checkout, an age check, or a blocklist. Covers a read-only review, transpiled probes, data reconciliation, surface scans, and a verdict file.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [security, gate, compliance, regulatory, fail-closed, review, probes]
    category: security
related_skills: [adversarial-review, independent-static-review, read-only-discovery, catalog-publish-safety]
---

# Security Gate Review

## Overview
A compliance gate is a check that must fail closed. A shopper, client, or unauthenticated caller must not be able to get past a restriction such as an age check, a jurisdiction block, a payment-method block, or a product-class block. This review asks one question: does the gate still fail closed, and does the data it reads still keep it that way. It is a read-only review. It finds problems, and a separate builder fixes them. The core method is to run the gate's own code on crafted inputs, not to trust the unit tests or the change description.

## When to Use
- A change adds or edits a fail-closed rule, a blocklist, or the data that feeds one.
- A change adds a new category that opens or closes an access path.
- A pull request includes a data file that will be applied to live records, and that file changes a gate's inputs.

Use a general code review for correctness questions, and a static review for money-path questions. This review is for whether a gate can be bypassed.

## Features
- A static read of each enforcement point and each helper it calls, pinned to a commit.
- A transpile of the gate's modules into a scratch folder, so probes run without touching live systems.
- A probe matrix of at least 17 cases, covering precedence, spoofed inputs, case tricks, unknown values, and empty lists.
- A reconciliation of any data file against the live records.
- Scans for supply-chain changes, changes outside the application source, and secret or personal-data shapes.
- A verdict file with a fixed last line.

## Benefits
- Probes catch bypasses that unit tests did not cover, such as fallback values and input normalization.
- The review cannot change live data, because it works on frozen copies.
- Findings are ranked, so the most serious ones are fixed first.
- The verdict is tied to one commit, so a later push cannot inherit an old approval.

## Procedure
### Hard rules
- Read-only. Do not post comments, approve, merge, push, or edit tracked files. Do not call write endpoints or administrative endpoints. Run probes against transpiled scratch copies.
- Pin the commit. Create a detached worktree at the reviewed commit, and check that its HEAD equals the review target. Stop if it does not.
- Clean up at the end. Remove the worktree and prune it. Confirm the parent checkout has no tracked changes.
- The verdict file is the deliverable. Name it `SECURITY.md`, and place it beside the pull request description. Its last line must be `SECURITY: PASS`, `SECURITY: CONDITIONAL: <condition>`, or `SECURITY: FAIL: <reason>`.
- A brief that grants write or merge authority makes the reviewer the builder. Refuse it. Fixes are separate builder tasks.
- The builder, the verifier, and the reviewer each run in their own session with their own worktree.

### Step 1: Read the gate
Read every enforcement point and every helper it calls:
- The route guard or middleware.
- The validation hook that runs at checkout or submission.
- The decision function.
- The function that extracts the state or the attributes the decision uses, such as a shipping region or a date of birth.
- The loader and validator for the data file that lists the restricted classes.
- The metadata reader, including how any hash is computed and what a missing field falls back to.
- Both the user interface's copy of the logic and the backend's. Confirm the backend is the authority.

Cite file and line for each criterion, from the pinned commit, for example with `git show <commit>:<path>`.

### Step 2: Transpile and probe
Read the repository's TypeScript version from its package file. Transpile the gate's modules into a scratch folder:
```zsh
cd <scratch-dir>/apps/backend
python3 -c "import json;print(json.load(open('package.json'))['devDependencies']['typescript'])"
npx -p typescript@<version> tsc \
  --target es2022 --module commonjs --moduleResolution node \
  --esModuleInterop --skipLibCheck --strict \
  --outDir <scratch-dir>/gate \
  <gate-source-glob>
```
Load the output from a short script and run at least 17 probes. Record the input, the expected result, and the actual result for each one.

Use this matrix as the default for a fail-closed gate. Replace the example classes with the classes in the code under review. The example classes are unrelated regulated categories, chosen so the matrix is not tied to any one catalog:

| # | Probe | Expected | Pass criterion |
|---|---|---|---|
| 1 | Product class A, variant class B (a mixed pair) | Block at the product value | Gate blocks |
| 2 | Product value blank, variant class B | Blank must not fall through to a permissive default | Gate blocks |
| 3 | Variant class B, product value null | Record the behavior | Flag if it relaxes the gate |
| 4 | Customer-supplied line-item attributes that claim a class | Ignored | Gate reads only the catalog's attributes |
| 5 | Customer-supplied cart-level attributes | Ignored | Gate reads only the catalog's attributes |
| 6 | Case changes, trailing spaces, zero-width characters | Exact match | Unknown class blocks |
| 7 | Keys such as `__proto__` and `constructor` | Blocked | Unknown class blocks |
| 8 | Arrays, objects, and numbers in place of strings | Blocked | Unknown class blocks |
| 9 | Mixed carts: all blocked, all allowed, one blocked among allowed | Strictest result wins | A relaxed item does not relax the others |
| 10 | Region spellings: abbreviations, padded names, full names, and codes with prefixes | Resolve to the canonical region | Garbage returns nothing, and blocks |
| 11 | Regions outside the permitted list | Block | Block, even for the most permissive class |
| 12 | A bad region code alongside a valid name | Block | The bad value wins |
| 13 | An unknown class handle | Block | The lookup misses |
| 14 | An empty allow-list for a class that is normally restricted | Parses, and blocks everywhere it should | The gate does not default to a permissive class |
| 15 | A new class with an empty block-list | Allowed everywhere | Allowed everywhere, and documented as the only relaxation path |
| 16 | A data file with a misspelled key | Throws at load | Throws |
| 17 | Two writes to the same record at once | Record the outcome | Flag if the gate has more than one writer without a guard |

For an age gate, replace the region probes with date-of-birth probes. For a payment-method gate, replace them with instrument-list probes.

### Step 3: Reconcile the data
When the pull request includes a data file that will be applied to live records:
1. Parse the file from the pull request description. Record the hash of the raw block.
2. Recompute each row's hash with the repository's own hashing rules.
3. Fetch the live records into a separate raw file. Do not reuse the pull request's own snapshot.
4. Recompute each row's current class and hash from the live records. Every row should match the table in the description.
5. Check that the table and the file agree on row count, identifiers, classes, and order.
6. Check that every new class is a known handle in the data file.
7. Flag any row that loosens a restriction, unless the description names it and explains it.
8. For any empty allow-list, check that the description says so and shows the arithmetic for the affected rows.

### Step 4: Scan the surface
Run three scans, and record each result:

| Scan | Method | Pass criterion |
|---|---|---|
| Supply chain | List changed files, and filter to dependency manifests, lock files, build settings, workflow files, container files, and environment files | Zero changes |
| Outside the application source | List changed files, and filter to paths outside the application's source folder | Zero files |
| Secrets and personal data | Search the diff and the description for key prefixes, bearer headers, password and token assignments, private key blocks, cloud and code-host token shapes, database connection strings, email addresses, phone numbers, and identifier shapes | Zero hits. The only URL allowed is the public backend host |

Scan the supply chain even when the diff is small. Lock files and workflow files are often one or two lines, and they are the most dangerous changes in a diff.

### Step 5: Check structural claims in the code
Confirm each claim in the description against the code at the pinned commit:
- The change does not touch any enforcement-point file.
- Every class handle the description names exists in the data file.
- Any class arithmetic in the description matches what the code computes.
- An empty allow-list is actually empty, not a list that matches everything minus something.
- No row for a strictly restricted class changes unless the description says so.
- Any date that moves is a warning only, never a gate.

### Step 6: Classify the findings
- **CRITICAL.** The gate is weakened, or a new bypass path exists. A new class opens a restricted region with no justification in the description.
- **HIGH.** The apply tooling accepts an unknown class, a loosening change, or a row that is not in the list.
- **MEDIUM.** A gap that already existed in the apply tooling, and that this change makes more dangerous. The change loosens only the newest class.
- **LOW.** A time-of-check gap, a fallback that applies only to admin users, a test that accepts an empty list for any class, or an incorrect claim in the description.
- **INFO.** Exposure of a hash in public client code, provenance metadata, or a user interface that does not hide an unclassed item.

A finding against a gap that existed before this change is MEDIUM, not HIGH, unless this change is the first to add a class that opens more than it closes. Score it against the worst legitimate error the tooling allows, not against a typo.

### Verdict file
Build the file in this order:
1. The stage, the commit, the base, the worktree path, and the parent commit at the end of the pass.
2. A diff-fidelity line with the byte count, the file count, and the hash comparison with the description's diff, if one was given.
3. The probe table with the count of probes and the count of unexpected results.
4. The data reconciliation table.
5. The three scan results.
6. Findings in order: CRITICAL, HIGH, MEDIUM, LOW, INFO.
7. Controls to apply at deploy time, for any MEDIUM or HIGH finding that needs no code change.
8. A "what this review cannot detect" list. Include legal correctness, live drift after the review, runtime behavior in production, and writers outside the application source folder.

End with the verdict line, exactly as shown above.

## Pitfalls
- **Trusting passing tests as evidence.** Unit tests cover only what their authors wrote. Probes against the transpiled gate catch variant fallbacks, mixed-cart precedence, case tricks, and region spellings.
- **Skipping the empty-list probe.** A new class with an empty block-list is a legitimate way to open a region. A mistyped empty list on the wrong class is a silent loosening. Probe every existing class as well as the new one.
- **Reviewing the description instead of the code.** The description is prose. The code at the pinned commit is the thing under review.
- **Reusing the pull request's own snapshot.** Fetch the live records again and recompute.
- **Accepting a block as a pass without checking the lookup.** A lookup must be an exact match. A substring or pattern match lets a mistyped class resolve.
- **Stopping at a static read.** A correct decision function can still leak through the code that extracts its inputs, such as spelling or fallback order. Only the probes catch this.
- **Leaving the worktree up.** Remove the worktree, prune it, and confirm the parent checkout still has no tracked changes.
- **Printing probe inputs that look like secrets.** Redact the value, and keep the file path.

## Verification
- The verdict file's last line is one of the three allowed forms.
- The probe table has at least 17 rows, and every unexpected result is listed as a finding.
- Every row of the data file was reconciled against the live records, or the gap is listed.
- All three scans are recorded, and the worktree is removed.
- The findings are ordered by severity, and each one names the evidence it rests on.
