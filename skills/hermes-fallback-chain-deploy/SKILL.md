---
name: hermes-fallback-chain-deploy
description: Use when rolling out or auditing Hermes fallback chains. The chains span several profiles. Covers the chain rules, credential gaps, verified writes, watching for silent fallbacks and rollback.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, fallback, deployment, fleet, config, observability, cost-control]
    category: hermes-operations
related_skills: [config-verify-before-write, hermes-baseline-dump]
---

# Hermes Fallback Chain Deployment

## Overview
A fallback chain is the ordered list of providers a profile tries after its primary model fails. Hermes switches
silently by default. The notice is logged, but in some chat clients it is shown for a second and then replaced, so an
operator can pay for an expensive tier for hours without seeing a switch. This skill covers two jobs: rolling a
standard chain out to many profiles with verified writes and a credential audit, and watching fallback events from
outside the chat so that switches and their costs are visible.

## When to Use
- A fleet-wide change needs the same chain on every profile, such as a provider sunset or a cost-control mandate.
- A single operator-requested change touches several profiles at once.
- A provider is being removed, and every profile that still lists it must be found and fixed.
- You need to know whether a profile's fallbacks are real, meaning which provider actually served recent turns.
- A worker dies at a regular interval, and you suspect the fallback chain ran out.

For a single profile's chain, use the Hermes fallback commands directly. For a change to the primary model only, use
the model command.

## Features
- Preflight checks on the CLI verbs and on any endpoint a tier depends on.
- Credential audit that marks each profile that cannot use a tier, without stopping the rollout.
- Chain rules: skip a tier that duplicates the primary, omit retired providers, and check each tier's credentials first.
- Two write paths, the CLI and an atomic structured edit, each followed by a read-back.
- An out-of-band watchdog that scans logs for fallback and auth events and alerts only when something new appears.
- Procedures for checking the live chain and for finding the cause of a worker that dies early.

## Benefits
- A chain is never applied to a profile that lacks the credentials for it.
- Retired providers and duplicate tiers are removed, not carried forward.
- Each profile's final chain is confirmed from the runtime, not assumed from the file.
- Silent fallbacks and their cost show up within minutes.
- A rollback path exists for every profile that was changed.

## Procedure
1. Preflight. Confirm the verbs you plan to use exist, and identify every profile in scope:
   ```bash
   hermes fallback --help
   hermes config set --help
   PROFILE_ROOT="$HOME/.hermes/profiles"
   profiles=($(ls -1 "$PROFILE_ROOT" 2>/dev/null) default)
   ```
   Probe any local endpoint a tier depends on. Record the HTTP status. A 200 with an empty model list means the server is
   up but has nothing loaded. Send one real completion request before you call the tier live:
   ```bash
   curl -s -o /dev/null -w '%{http_code}\n' -m 5 http://127.0.0.1:<port>/v1/models
   ```

2. Audit credentials. For each profile, check whether the provider for each tier has a key in the profile's env file
   or in a configured secret source. Print presence only, never the value. Record each gap as
   `GAP profile=<name> missing=<KEY_NAME>`. A gap is a finding for the operator, not a reason to stop the rollout.

3. Back up every profile's config before any write. Keep the profile name in the file name and a date or reason tag in
   the folder name:
   ```bash
   TAG="<reason>-$(date -u +%Y%m%d)"
   mkdir -p "$HOME/.hermes/backups/$TAG/fallback"
   for p in "${profiles[@]}"; do
     src="$PROFILE_ROOT/$p/config.yaml"; [ "$p" = default ] && src="$HOME/.hermes/config.yaml"
     [ -f "$src" ] && cp -p "$src" "$HOME/.hermes/backups/$TAG/fallback/${p}-config.yaml"
   done
   ls -l "$HOME/.hermes/backups/$TAG/fallback/"
   ```

4. Build the chain for each profile as an ordered list of `{provider, model}` entries. Apply these rules:
   - Omit a tier that duplicates the profile's primary. A duplicate tries the same model twice.
   - Put a tier in only if its credential exists for that profile. Otherwise record a gap.
   - Remove every entry for a provider that the operator has retired.
   - Add a custom endpoint only with its `base_url` and only after the probe in step 1 succeeds.

5. Apply the chain. Use the CLI when the terminal is interactive, and the structured edit otherwise:
   ```bash
   hermes -p <profile> config set fallback_providers '[{"provider":"<p1>","model":"<m1>"},{"provider":"<p2>","model":"<m2>"}]'
   ```
   Single quotes around the whole JSON argument avoid escaping mistakes. Stop on any profile that fails, fix it, and
   then continue. Do not skip a failed profile silently.

   The structured edit replaces only the `fallback_providers` key. Back up the file, parse it, change the key, write to a
   temp file in the same folder, rename it over the original, then parse it again and compare the new list with the
   intended one. The `hermes fallback add` verb needs an interactive picker and cannot run from a script.

6. Verify each profile from the runtime, not from the file:
   ```bash
   hermes -p <profile> fallback list
   hermes -p <profile> fallback list 2>&1 | grep -ci 'retired-provider-name'
   ```
   The list must show the intended order and no retired entries. The count must be 0.

7. Report one row per profile: primary, the chain set, the credential source or the gap, the probe result for any local
   tier, whether retired providers were removed, and the backup path. End with a single summary line with real counts.

### Watching Fallback Events
A built-in fallback notice can be missed in a streaming chat, and a stale session pin can keep a profile on a tier
the config does not name. Watch from outside the chat:

1. Check the config intent and the live session together. Report both, along with the last model that actually served a turn:
   ```bash
   hermes --profile <profile> config path
   hermes --profile <profile> fallback list
   rg "Fallback activated|API call failed|HTTP 40[0-9]|HTTP 429|HTTP 5[0-9][0-9]" <hermes-home>/profiles/<profile>/logs/agent.log | tail -40
   ```

2. Schedule a no-agent script job every five minutes. Its standard output is the alert. An empty output sends nothing.
   Register it with the scheduler's script option, bare file name only, and check the registration:
   ```bash
   hermes cron create --help
   hermes cron list
   ```

3. Give the script a byte-offset cursor per log, so each run reads only new bytes. Reset the cursor when a log shrinks
   after rotation. Keep the pattern set short, and cap the lines per log:
   ```bash
   #!/usr/bin/env bash
   LOG_DIR="${1:?log dir}"; STATE_DIR="${2:?state dir}"
   PATTERN='Fallback activated|API call failed|HTTP (401|402|403|429|5[0-9][0-9])|rate limit|spending limit|PermissionDenied'
   mkdir -p "$STATE_DIR"
   for log in "$LOG_DIR"/*.log; do
     [ -f "$log" ] || continue
     name=$(basename "$log"); size=$(wc -c < "$log" | tr -d ' ')
     cur="$STATE_DIR/$name.offset"; last=$(cat "$cur" 2>/dev/null || echo 0)
     [ "$size" -lt "$last" ] && last=0
     hits=$(tail -c +"$((last + 1))" "$log" | grep -E "$PATTERN" | head -n 5)
     echo "$size" > "$cur"
     [ -n "$hits" ] && printf '== %s\n%s\n' "$name" "$hits"
   done
   ```
   The first run reads the whole backlog. That is intended, because it shows problems that were already happening.

4. Add the same pattern for other cost signals if they matter: an auth-expired message, a platform rate limit, or a
   daily token total above a threshold. Each signal gets its own script and its own cursor.

### Editing a Chain Safely
- The fallback verbs are `add`, `list`, `remove` and `clear`. None of them inserts at a position. `add` appends.
- To change the order, either clear and re-add in the new order, or use the structured edit in step 5.
- Each entry needs both `provider` and `model`. Check both after each add.
- A chain is tried in list order, and position is priority.
- Confirm the live config path with `hermes --profile <profile> config path` before any edit. A file in the wrong
  folder is never read.

### Diagnosing a Worker That Dies Early
When a worker stops at a steady wall time, do not assume a timeout. Read its own log around the failed runs and map each
status to a distinct fix:
```bash
rg "429|401|403|PII|invalid_json_after_redaction|Fallback activated" <hermes-home>/profiles/<worker>/logs/agent.log
```
- A 429 means a credential pool is exhausted, so wait or add a key.
- A 401 means the key is wrong, so repair it.
- A content-filter rejection means the payload type needs a different model or a different tier.
- A chain with no tier left means the config must add a local tier that can always answer.

A varying death time disproves a fixed timeout. Search the config for the timeout key before you assume it exists.

### Rollback
1. Stop or let finish any job that uses the affected profile.
2. Restore each profile from its backup, one file at a time. Restore only the file you backed up for that profile.
3. Confirm with `hermes -p <profile> fallback list`.
4. Note the reason, the time and the backup path in the report.

Backups remain usable after a delay, so keep the folder path with the report.

## Pitfalls
- **A built-in switch notice is not proof anyone saw it.** Watch the logs out of band.
- **A session pin can override the config primary.** Report the config, the pin and the last model that served a turn as three separate facts.
- **Fallback tiers can be expensive.** A tier that bills per token keeps running after the primary has been restored.
  Alert on repeated rejections from the primary, and cap the tiers that can bill.
- **Do not trust a memory note about the chain.** It goes stale after every edit. When a note disagrees with the runtime,
  the runtime wins, and you correct the note in the same turn.
- **A duplicate tier wastes a call.** Skip any tier that matches the primary.
- **A missing credential does not fail the rollout, but it does leave the tier unusable.** Report it every time.
- **A connectivity check is not a health check.** Send one real completion request before you call a local tier live.
- **Bash 3.2 has no associative arrays.** Keep watchdog scripts portable across the shells cron uses.
- **Give scheduled script jobs the script name the scheduler accepts.** Check the job definition after you create it.
- **Quote JSON once.** Single quotes around the whole argument avoid escaping mistakes.
- **Do not change the primary model as part of a chain rollout.** That is a separate change with its own approval.

## Verification
- Every profile in scope lists the intended chain from `fallback list`, with no retired entries.
- Each reported credential gap matches what the credential audit found.
- The backup folder holds one file per profile in scope.
- The watchdog prints nothing on a clean run, and prints one block when a line matching its pattern is appended to a test log.
