---
name: hermes-baseline-dump
description: Use when auditing a Hermes profile config snapshot. The snapshot is read-only. Covers the fields to capture, what empty fallbacks mean and how to cross-check auth.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, audit, diagnostics, snapshot, configuration, read-only]
    category: hermes-operations
related_skills: [hermes-fallback-chain-deploy, hermes-gateway-ops, config-verify-before-write]
---

# Hermes Baseline Configuration Snapshot

## Overview
A baseline is a frozen record of every Hermes profile's routing, fallback chain, memory provider and gateway topology at
one moment. It answers "what was the configuration when this failed?" and "do profiles match the known-good shape?" It
is a read-only operation. It prints names, providers, models and URLs, and never key values. Capture the timestamp
with every snapshot, because a baseline only proves what was true at the time it was taken.

## When to Use
- An operator asks for a config snapshot or an audit before and after a change.
- A profile's model routing changed, and you need to confirm what it routes to now.
- An incident post-mortem needs the configuration from before a failure.
- A provider call fails with 401 or 429, and you need to know which credential path the profile uses.
- You are comparing several profiles against a known-good shape.

## Features
- One record per profile: primary provider and model, ordered fallback chain, memory provider and its mode.
- Gateway topology check: whether a gateway serves one profile or all of them.
- Cross-check of each provider against its credential state, without printing the credential.
- Findings matrix that maps a snapshot pattern to its implication and its next step.
- Integrity check for any snapshot script copied in from elsewhere.

## Benefits
- Routing problems show up as concrete facts, not guesses from memory.
- Empty fallback chains and dead providers are found before the primary fails.
- Secrets never reach the snapshot output.
- A timestamped snapshot supports a post-mortem with a defensible timeline.

## Procedure
1. Set the snapshot up as a read-only step. Record the capture time before you start:
   ```bash
   date -u +%Y-%m-%dT%H:%M:%SZ
   hermes config path
   ```

2. If you copy in a snapshot script from another source, verify its SHA-256 before you run it. Compare it with the hash
   the publisher listed, and stop if the two differ:
   ```bash
   shasum -a 256 <snapshot-script>
   ```
   A mismatch means the file was changed or corrupted. Report it. Do not run it.

3. Run the snapshot with the Python interpreter the Hermes command uses. Its shebang line names that interpreter. Use
   system Python only if that one lacks the YAML parser:
   ```bash
   PY="$(head -1 "$(command -v hermes)" | cut -c3-)"
   "$PY" <snapshot-script> 2>&1
   ```
   Give the snapshot run up to two minutes. For a longer run, start it in the background and poll for its exit. Never
   interrupt it partway.

4. Capture each profile's record as one JSON line. Keep every line verbatim, with the profile name, host name, primary,
   fallback chain and memory fields. Do not summarize or reformat it.

5. Cross-check each provider in a failing chain against its auth state. Print names and status only:
   ```bash
   hermes -p <profile> auth list <provider>
   ```

6. Check gateway topology with `hermes gateway status`. Note whether the gateway is standalone (one profile) or serves
   several.

7. Remove any temporary copy of the snapshot script, then write the report with the capture time, the hash you
   verified, the profiles covered and the findings.

### Findings and what they mean

| Snapshot pattern | Implication | Next step |
|---|---|---|
| Empty fallback chain `[]` | A primary failure has no safety net | Propose adding a fallback with the fallback command |
| Primary `provider: null` and `model: null` | The profile is unconfigured, or runs on fallbacks only | Check whether the profile is meant to be empty |
| A provider in the chain has no credentials | Routing wastes time on it or fails on it | Remove the entry, or add its credential |
| Memory fields set but `provider: null` | The memory settings exist, but the provider is not selected | Check the config and the memory provider's own config file |
| Auth list shows `401` for a provider | The credential was rejected, or rotated on the provider side | Re-authenticate through the auth command |
| Auth list shows no credential for a provider | The key is not in the expected env file or secret source | Check the profile's env file and the export |

## Pitfalls
- **A snapshot proves only what was true when it was taken.** Claim a change caused a failure only if the snapshot was
  taken after the change and before the failure. Record the capture time every time.
- **Quote provider slugs exactly.** A slug such as `custom:<name>` is the routing key in config. It is not a display
  name. Do not abbreviate it in a report.
- **An empty chain and an unconfigured primary are different problems.** An empty chain means a primary exists with no
  fallback. A null primary means the profile is unconfigured.
- **A 401 does not always mean the key is wrong.** It can also mean the wrong header format, an account mismatch, or an
  endpoint that expects other auth. Test the key directly before you call it stale.
- **Gateway topology warnings are advisory.** A standalone gateway is the right shape for a single profile. Changing it
  is an operator decision.
- **Two profiles that hold the same bot token conflict.** Only the first to claim the token answers messages. Fix this
  by giving one profile its own token, removing the token from one profile, or routing chats through the primary.
- **The snapshot prints names, not values.** Do not patch it to print environment values or key contents.
- **Keep the snapshot read-only.** Any fix is a separate step with its own approval and its own backup.

## Verification
- The capture time, the hash check result and the profile count all appear in the report.
- Each profile line parses as JSON, and the count matches the number of profile directories under the Hermes home's
  profiles folder.
- Each finding in the report can be reproduced by re-running the auth list or the gateway status command.
- The temporary copy of the snapshot script no longer exists after the run.
