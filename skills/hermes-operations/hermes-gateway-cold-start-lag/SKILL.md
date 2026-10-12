---
name: hermes-gateway-cold-start-lag
description: Use when a Hermes gateway's first model call is slow. It takes about 30 seconds after a restart. Covers the cold-path cause, how to measure it and when a fix is worth it.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, gateway, latency, cold-start, diagnostics, telegram]
    category: hermes-operations
related_skills: [hermes-gateway-ops, hermes-profile-config-yaml-debug]
---

# Hermes Gateway Cold-Start Lag

## Overview
After a gateway restart, the first model call can take about 30 seconds. Later calls finish in under 2 seconds. The delay
is a one-time cold path: the gateway performs an authentication token exchange on the first request, and the chat
platform's polling loop may still be inside a long poll when the first message arrives. The cost is paid once per
process start. This skill covers how to confirm that pattern in the logs, how to tell it apart from a real fault, and
when a fix is worth the risk.

## When to Use
- A user reports that the first message or the first model-picker action after a restart is slow, and later ones are fast.
- A callback button in a chat client shows a "query is too old" error after a long wait.
- You need to decide whether a slow first call is a fault or the normal cold path.

## Features
- Symptom profile: which calls are slow, and what the second call looks like.
- Evidence checklist: auth exchange timing, poll timing and the gap since the last activity.
- Reliable process lookup that uses the gateway lock file and not a name search.
- End-to-end timing from a real turn, using the agent log's model and latency fields.
- A decision rule for when to leave the cold path alone and when to act.

## Benefits
- A cold-start delay is confirmed in minutes, so no one edits gateway code for it.
- A real fault, such as a broken config file or a wrong model, is not mistaken for the cold path.
- Restarts are not used as a "fix" that resets the warm path again.

## Procedure
1. Confirm the symptom pattern: the first call after a restart or long idle period is slow, and the second is fast.
   Note the gap since the last activity. A gap of several minutes makes the cold path more likely.

2. Find the gateway process from its lock file, not from a name search:
   ```bash
   cat <hermes-home>/profiles/<profile>/gateway.lock
   ps -p <pid> -o pid,ppid,etime,command=
   launchctl list | grep <gateway-label>
   ```
   The PID in the lock file must match the service manager's entry. A process started by the service manager has a
   parent PID of 1. Use the elapsed time to see how long the process has been up.

3. Look for the cold-path lines in the agent log. Auth-exchange lines and a poll cycle that ran long are the signatures:
   ```bash
   grep -E "auth|polling|getUpdates" <hermes-home>/profiles/<profile>/logs/agent.log | tail -20
   ```
   Compare the timestamps. A first call with a multi-second auth exchange, followed by a fast second call, matches the
   pattern.

4. Measure with a real turn. A synthetic request can differ from what the gateway does. After a real message arrives,
   read the conversation record from the agent log:
   ```bash
   grep "agent.conversation_loop" <hermes-home>/profiles/<profile>/logs/agent.log | tail -4
   ```
   The record names the model, the provider, the platform, and the latency of each model call. Confirm the model and
   provider are the configured ones before you read the latency.

5. Decide with this rule:
   - First call over 10 seconds and second call under 2 seconds: the cold path. No action unless restarts are frequent.
   - Both calls over 10 seconds: a different problem. Go to the configuration and provider checks.
   - A callback timeout with no slow model call in the log: check the chat platform's callback timing, not the model.

6. If the operator wants a fix anyway, present the options with their costs. Each option changes startup code or polling
   behavior, so it needs approval first:
   - Warm the authentication exchange at startup with a no-op request.
   - Warm the whole model client at startup. This is larger, with more risk.
   - Shorten the chat platform's poll timeout. This can raise the number of API calls.

## Pitfalls
- **Do not edit gateway code for a one-time cost without approval.** The fix is invasive and the cost is small.
- **Do not restart the gateway to test the lag.** A restart resets the warm path, so the next call is slow again.
- **A callback timeout is a symptom.** The cause is the slow first call, so fix the cause, not the timeout.
- **A slow first call is not a YAML problem.** A config parse error shows up in the gateway's log as a load failure, not
  as a slow model call.
- **The launchd output log can lag minutes behind.** Its modification time may not move while the gateway is active.
  Read the agent log for live activity.
- **A name search for processes can return ghosts.** A short one-shot CLI command can match a search and exit before you
  act on it. Confirm each candidate PID exists, and that it matches the lock file.
- **A name search can miss a module-launched process.** When the gateway runs as a Python module, the search pattern must
  match the full command line. Use a bracketed pattern so the search does not match itself:
  `ps aux | grep "[h]ermes_cli.*gateway"`.
- **The first chat click is the slow one.** A picker that loads at startup is fast when warm, but its first action after
  a cold start takes the full cold path.

## Verification
- The lock-file PID, the service manager entry and the process table all agree on one gateway process.
- A real turn appears in the agent log with the configured model and provider, and its latency is recorded.
- Two consecutive calls show the expected pattern: a slow first call and a fast second call.
- No configuration or code was changed as part of the diagnosis, unless the operator approved a fix.
