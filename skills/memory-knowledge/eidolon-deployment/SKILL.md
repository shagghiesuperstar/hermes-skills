---
name: eidolon-deployment
description: Use when deploying the Eidolon layer on Hermes. Its scope covers the SOUL.md identity file, the dream-cycle handler, the integrity watchdog, scheduled reports, and the operator-policy rules that govern its changes.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [eidolon, soul, dream-cycle, integrity-watchdog, self-improvement, deployment]
    category: memory-knowledge
related_skills: [eidolon-hermes-ground-truth, hindsight, hermes-profiles, hermes-gateway-ops]
---

# Eidolon Deployment on Hermes Agent

## Overview
Eidolon is a public, drop-in self-improvement layer for Hermes Agent. It adds three parts: a `SOUL.md` identity contract loaded every session, a dream-cycle handler that reflects on sessions and produces risk-gated lesson candidates, and an integrity watchdog that detects drift in skills, scheduled jobs and hooks.

The layer produces candidates. It does not make the agent better by itself. A candidate counts only when it becomes a file the agent loads next session: a skill edit, a SOUL change or a config change. Pipeline counters, a passing health check and a clean watchdog report are infrastructure evidence, not evidence that the agent improved. Report the change in plain terms: which files changed, and what the agent does differently next time.

A cycle ingests recent episodes from the configured memory backend, clusters them by kind, extracts lessons, and proposes candidates. Each candidate is gated by risk. Low-risk changes apply with a ledger entry, and the rest are held. A last-known-good snapshot supports rollback, and the integrity watchdog runs before the cycle exits.

## When to Use
- Installing Eidolon on a Hermes instance for the first time.
- Changing its hooks, schedules, memory backend or policy settings.
- Verifying a deployment, or diagnosing why its reports are green but nothing changed.
- Preparing the public repository for release, and keeping operator data out of it.

## Features
- A session-end hook and scheduled runs, both driven by one handler.
- A risk gate: only low-risk change kinds apply automatically, and unknown kinds fail closed.
- A transactional outbox that captures lessons locally, then flushes them to the memory backend.
- A monitor contract that records structural state, not only exit codes.
- Operator-policy rules that force upstream verification and CLI-based changes.

## Benefits
- Lessons leave a durable local trace even when the memory backend is down.
- Each change is either applied with an audit record or held for an operator decision.
- Upstream fixes are checked before a workaround is written.

## Procedure
### 1. Clone the public repository
```bash
git clone https://github.com/shagghiesuperstar/Eidolon-Soul-For-Hermes-Agent-Universal eidolon
cd eidolon
```

### 2. Copy the skills and the identity file
```bash
mkdir -p ~/.hermes/skills
cp -r skills/dream-cycle ~/.hermes/skills/
cp -r skills/integrity-watchdog ~/.hermes/skills/
cp SOUL.md ~/.hermes/
```

### 3. Wire the session-end hook through the Hermes CLI
Use the CLI, not a direct edit to the configuration file. Direct writes to that file are blocked by the safety guard.
```bash
hermes config set hooks.on_session_end '[{"command": "python3 ~/.hermes/skills/dream-cycle/handler.py --mode sessionend", "timeout": 180}]'
```

### 4. Add the scheduled jobs
Check the existing crontab first. Entries left by an earlier install often use the wrong interpreter (`python` instead of `python3`) or a stale path, and those duplicate runs.
```bash
crontab -l
(crontab -l 2>/dev/null; echo '0 * * * * python3 ~/.hermes/skills/dream-cycle/handler.py --mode scheduled') | crontab -
(crontab -l 2>/dev/null; echo '*/15 * * * * python3 ~/.hermes/skills/integrity-watchdog/handler.py') | crontab -
```

### 5. Validate before relying on the layer
```bash
python3 tests/adversarial.py                                  # sandboxed, no side effects
python3 ~/.hermes/skills/dream-cycle/handler.py --mode sessionend
python3 ~/.hermes/skills/integrity-watchdog/handler.py
ls -l ~/.hermes/state/
```
The adversarial suite must pass in full. The handlers must exit cleanly in both modes, and the state directory must contain the files the handlers write.

### 6. Install the overnight monitor and its capture contract
Copy the monitor from the repository's scripts folder, and schedule it hourly through the Hermes cron tool:
```bash
cp <repo>/scripts/<monitor>.py ~/.hermes/skills/
hermes cron create --name "eidolon-hourly-monitor" \
  --schedule "0 * * * *" \
  --script "<monitor>.py" \
  --deliver local
```
Without the following captures, weekly audits produce impressions, not evidence. Each monitor run must record:
1. Dream-cycle structure: total runs, runs by mode, whether proposals exist, whether any were applied, whether any were rolled back, and the last known-good snapshot.
2. Lessons file state: whether it exists, its line count, and its last modification time.
3. Memory backend reachability, probed with the API that matches the active backend type.
4. Watchdog structure: status, open incident count and incident keys.
5. Drift signals: short strings that name each structural problem observed.
6. Hermes-side health: scheduled job count, job states, last errors, skill count, and whether the identity file carries its expected section.
7. Cadence: median gap between runs, and the gaps that were too long.

### 7. Schedule the reports with pinned model and provider
Every scheduled job that calls a model must pin both the model and the provider. An unpinned job fails in a fresh session with "No inference provider configured". Use provider names from the host's provider cache file, not free-form strings.
```bash
hermes cron create --name "eidolon-daily-report" \
  --schedule "0 8 * * *" \
  --prompt "Read the latest report in ~/.hermes/eidolon-reports/ and deliver it verbatim." \
  --skill terminal --skill file \
  --deliver origin \
  --model "<model-id>" \
  --provider "<provider-name>"
```
A weekly deep audit follows the same pattern, on a Sunday schedule, and it must cross-reference every Hermes-level finding against upstream (see step 9).

### 8. Install the upstream cross-reference skill
Copy the ground-truth skill into the active profile's skills folder, then run its self-test:
```bash
mkdir -p ~/.hermes/skills/devops/
cp -r <repo>/skills/eidolon-hermes-ground-truth ~/.hermes/skills/devops/
python3 ~/.hermes/skills/devops/eidolon-hermes-ground-truth/scripts/hermes_ground_truth.py --self-test
```

### 9. Apply the operator-policy rules
These rules bind any Eidolon deployment. A deployment that breaks one is broken.

**Rule 1: check upstream before reporting a Hermes-level finding.** Never report a Hermes bug from inference alone. Before a finding reaches a report or an operator message, check it against the upstream repository (`NousResearch/hermes-agent`) with the ground-truth skill. Cite its verdict:
- `fixed_upstream: true`: propose a Hermes update in the report, and do not file a new bug.
- `fixed_upstream: false, still reproducible`: file a bug, or work around it in Eidolon, and say which.
- `local_only_quirk`: probably configuration drift. Propose the Hermes doctor's repair command.
- `unverifiable`: report it as needing a human, and never auto-report it.

A local clone that is far behind upstream cannot show whether a bug is already fixed. Check upstream first.

**Rule 2: update Hermes before any core configuration change.** The order is fixed:
1. `hermes update`
2. `hermes config migrate`
3. `hermes doctor --fix`
4. `hermes auth list`
5. `hermes gateway restart`

Track the number of commits behind upstream as a drift signal, and propose an update in the weekly report when it passes 50.

**Rule 3: change Hermes through its CLI, not its files.** Apply actions must emit CLI invocations such as `hermes config set`, `hermes auth add`, `hermes cron edit`, `hermes model`, `hermes mcp add` and `hermes skills install`. The CLI validates against the current schema, so a bad provider name fails when it is set, not at the next run.
- Low-risk changes apply automatically: a configuration key set through the CLI, or a credential rotation.
- High-risk changes need operator approval: anything that touches the identity file's identity or security sections, skills the operator curates, and the model provider chain.
- Every CLI call appends a record to an audit file: timestamp, command, exit code, and the state before and after.

**Rule 4: update with `hermes update`, never `git pull`.** The update command stashes local changes, fetches, and restores them. A raw pull leaves commits behind while the version check still reports the install as behind.

### 10. Capture lessons through an outbox
A lesson that is captured only when the agent remembers to capture it is lost on the day the agent forgets. Use a transactional outbox:
1. **Capture** runs at session end. It reads user messages from the local session store, looks for correction phrases such as "you assumed", "stop guessing" or "remember:", and appends each match to a local outbox file. It makes no network calls, tracks a cursor, and skips duplicates by hash.
2. **Flush** drains pending entries to the memory backend. An entry is marked as retained only after the backend confirms the write. If the backend is down, entries stay pending and are retried.
3. **Exit codes** separate the outcomes: 0 for success, and 2 for degraded but captured. A degraded run is loud. It is never silent.

### 11. Keep the public repository separate
- Use a dedicated profile whose only job is public repository maintenance. Its identity file must forbid personal, network, device, path and account data.
- Do not mix local development work, personal state or real metrics into public changes.
- Before a public commit, scrub the repository. Search for IP addresses, host names, absolute paths under the home folder, account names and cluster names, and replace each one with a generic description:
  ```bash
  grep -rnE '(10\.10\.|192\.168\.|username)' . --exclude-dir=.git
  find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
  ```
- Check the README, the changelog, handler comments and skill files. Handler comments that name a real endpoint are a common leak.

## Pitfalls
- **Dream counters are not self-improvement.** Ingest counts, flush counts and a passing doctor are infrastructure proof. Answer "does the agent improve" with the files that changed.
- **Soft lessons with no action.** A lesson written into the memory file without a file change, a SOUL change or a config change changes nothing the agent does. Turn each lesson into a file, then remove it from the inbox.
- **A missing memory backend is a structural failure.** The handler can exit 0 with no durable output, so the monitor must probe reachability on every snapshot.
- **A green watchdog is not a working system.** The watchdog checks skills, scheduled jobs, hooks and state. It does not check the memory backend.
- **An integrity hash on the identity file.** A seal on the identity file raises false tamper alerts whenever an operator edits it on purpose. Compliance should come from the file's content, not its hash.
- **Rollback disabled by an empty snapshot.** If the last-known-good snapshot is never set, the rollback path does nothing. Set it on the first successful run, and check it in the monitor.
- **Unknown change kinds.** A change kind not on the low-risk list is treated as high risk, which blocks it. A kind added to the code but not to the list never applies. Add each new kind to the list in the same change.
- **Hard-coded endpoints.** A handler that reads a fixed address while the host's configuration names another one runs for days against the wrong machine and still reports success. Read the live configuration on every run, accept more than one schema version, and report the configured address and the probe result in each drift signal.
- **Guessed configuration for a Hermes subsystem.** Install and configure a Hermes-native subsystem from its canonical plugin README in the upstream repository, not from a summary page. Check install method, mode names, environment variable names, version constraints and daemon lifecycle against that README.
- **Idle-stopping local daemons.** A local memory daemon can stop after an idle timeout (the timeout is set in the daemon's configuration). A closed port during idle is normal. Send a small recall request to wake it, then probe. Otherwise every morning report reads "unreachable".
- **Retain versus recall.** A backend can serve recall from its local index while retain fails because its model endpoint is down. A retain error with working recall points at the model endpoint, not the daemon.
- **Claims about running services.** Probe the port or the health endpoint at claim time. A value copied from a log line or an earlier session is not a current fact.
- **Append-only adapters.** If the memory adapter appends every write and never raises on duplicates, a skip path that waits for a duplicate error can never run. Detect duplicates before capture.
- **Hard-coded tool counts in tests.** Adding a tool to a registry breaks any test that asserts the old count or the exact name list. Update those assertions in the same change.
- **Silent browser failures.** A dashboard served from another port fails with no visible error when the server sends no cross-origin headers, while the same endpoint works from curl. Add the headers, and add a preflight response. Check it with an OPTIONS request.
- **Port collisions.** A dashboard on the port a local model server already uses fails at start. Pick a free port and record it.
- **Stale cron entries.** Remove entries that use the wrong interpreter or a stale path before adding new ones.
- **Naming collisions.** The local lesson file in the Eidolon home is not the host's memory bank. Do not claim the agent recalled an Eidolon entry until the real provider path has shown it.
- **Bare interpreters.** A system `python3` may be older than the package needs, and the failure reads as "not importable" while the cron wrapper works. Probe with the same interpreter the scheduled job uses.
- **Repeated blockers.** When an operator decision blocks progress, state the blocker once with the recommended default, then stop. Repeating the same question each turn is the spinning the operator asked to avoid.
- **Executable bit in version control.** An installer script tracked without its executable mode fails the continuous-integration installer test. Set the mode in the index, and verify it with a listing of the tracked file.
- **Squash merges from a stale ref.** Fetch the exact branch head, compare it with the pull request head, and run the full unit suite on the squash result.

## Verification
- The adversarial suite passes in full, and both handler modes exit cleanly.
- The watchdog reports `ok` with no open incidents.
- The state directory holds the files the handlers write, and the session-end hook is in the configuration.
- Each scheduled job lists its pinned model and provider.
- The monitor captures all seven fields, and its daily report arrives on schedule.
- The upstream cross-reference self-test passes.
- The repository scan finds no addresses, host names, home paths or account names.
- The report names the files that changed, and the change in agent behavior each one causes.

## Attribution
Eidolon is a public project: https://github.com/shagghiesuperstar/Eidolon-Soul-For-Hermes-Agent-Universal. Its design draws on public work whose names are given here without links: CavemanLLM (load-bearing-token prompt compression), PromptQuine (pruned prompts that match or beat verbose originals, ICML 2025), the Meta-Skill doctrine by yaojingang, and the soul-document pattern attributed to the Fable 5 work. Concepts from the other projects were adapted in prose.
