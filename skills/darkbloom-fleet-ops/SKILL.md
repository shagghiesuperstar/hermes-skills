---
name: darkbloom-fleet-ops
description: Use when running or re-modeling Darkbloom provider Macs. Covers update recovery over SSH, stale PID fixes, revenue-driven model selection, safe model switches, and a controller-agent pattern.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [darkbloom, provider-node, launchd, model-selection, fleet-ops]
    category: local-inference
related_skills: [darkbloom-provider, multi-mac-fleet-ops]
---

# Darkbloom Fleet Operations

## Overview
Darkbloom pays provider nodes for serving inference from a consumer account. Running several Macs as providers creates three recurring problems: a daemon that cannot be restarted from a remote shell, an earnings record that a poller can silently lose, and model slots that keep earning nothing after the plan was set. This skill covers the recovery steps, the revenue loop that drives model choice, and a controller-agent pattern that watches the other nodes.

## When to Use
- A provider daemon stays down after an update that ran over SSH.
- A node refuses to start with a PID-file error after a reboot.
- You are choosing or re-checking which models each node serves.
- You are setting up one always-on agent to monitor and update the provider nodes.

## Features
- Restart recovery for a provider daemon whose launchd agent failed to bootstrap in an SSH session.
- Stale PID file cleanup and launchd re-registration through the provider CLI.
- Earnings ledger collection from the account API, deduplicated by job id, with gap reporting.
- Per-model ranking by revenue per active provider-day, plus a dead-weight alert for secondary models.
- A model-swap sequence that drains jobs instead of cancelling them.
- Controller routines: a status pulse, a daily digest, a one-node-at-a-time update window, and a balance check.

## Benefits
- A node that fails to restart after an update returns in minutes without a physical visit.
- Model decisions rest on recorded revenue, not on last month's plan.
- Gaps in the earnings record show up in the digest instead of making the numbers quietly wrong.
- Updates never take the whole fleet offline at once.

## Procedure
1. Read each node's state and version. `auto_update = true` in the provider config is an option the operator can choose, not a default. A scheduled check reports the version, and an update waits for the operator's go-ahead:
   ```zsh
   darkbloom status
   ```
   Expect `Daemon: running`, and an enabled-model filter that matches the plan.
2. After the operator's go-ahead for each node, update one node at a time, with the wait for success before the next node:
   ```zsh
   darkbloom update --timeout 600
   ```
3. If the update leaves the daemon down with `launchctl bootstrap failed: 5: Input/output error`, the SSH session is outside the user's GUI launchd domain. Bootstrap the provider agent from that domain, then confirm:
   ```zsh
   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/<provider-plist>
   darkbloom status
   ```
4. If startup fails with "a live process owns the provider PID file", confirm the recorded PID is dead with `kill -0 <pid>`. Back up the PID file, then start with the intended model. The start command clears the stale file and re-registers the agent:
   ```zsh
   cp <provider-pid-file> <provider-pid-file>.bak
   darkbloom start --model <model-id>
   ```
5. If launchd refuses to load the agent because its label is disabled, check who disabled it before enabling it:
   ```zsh
   launchctl print-disabled gui/$(id -u)
   launchctl enable gui/$(id -u)/<label>
   ```
6. Collect earnings on one host only. Poll the account earnings endpoint with the account token read from a file, dedupe on job id, and append to a local JSONL ledger. Run the collector with a Python that has a current CA bundle (see Pitfalls).
7. Rank models by trailing 7-day revenue per active provider-day. For a model with no ledger history, a rough heuristic ranks it as `(0.3 × input_price + 0.7 × output_price) / sqrt(providers)`. Treat that score as a heuristic only, and replace it with ledger data as soon as the ledger has it.
8. Swap models in this order:
   ```zsh
   cp ~/.config/darkbloom/provider.toml ~/.config/darkbloom/provider.toml.bak
   darkbloom models download <model-id>
   darkbloom switch --model <model-a> --model <model-b> --timeout 600
   darkbloom status
   ```
   `switch` drains in-flight jobs and keeps the coordinator session, and it needs no launchd, so it works over SSH.
9. Run the ROI check weekly. Alert on any enabled model that earns under 10 % of the host's best model per provider-day, and deliver the alert to a place someone reads.

### Controller-agent pattern
Use one agent on an always-on machine that has no inference role. Its own inference can come from the fleet with a frontier fallback for hard reasoning.

- Address nodes by tailnet hostname, not by raw IP.
- **Status pulse every 15 minutes.** Ask each node for one JSON status line. A node that does not answer gets a line with `reachable: false`. Never stop the loop for one node.
- **Daily digest at a fixed time.** One table: node, uptime, served models, thermal events, failed checks, actions taken. Bottom line first.
- **Update window once a week, one node at a time, after the operator's go-ahead.** Run the node's maintenance routine, wait for success, then move on. A failed check opens a task, and no further node is updated until the operator approves.
- **Laptops serve only on AC power.** A battery-powered node stops serving until it is plugged in.
- **Thermal limits.** Sustained throttling over two consecutive pulses goes to the operator. Do not unload models on your own.
- **Version drift.** A node more than one minor version behind the newest node is reported the same day, and updated after the operator's go-ahead.
- **Model changes need approval.** A download and reload costs earning time, so propose new models with prices and memory needs, and wait for a yes.
- **Stale is stale.** A node counts as up only if the latest pulse says so.

## Pitfalls
- **Bootstrap the agent from the GUI launchd domain.** An SSH session can swap the binary but cannot bootstrap the agent. Use `gui/$(id -u)` from a logged-in session or the recovery in step 3.
- **Poll faster than the endpoint's window.** If an endpoint returns only the newest N records and ignores paging, any collector outage longer than the time those N records cover leaves a permanent gap. Poll at least that often, and report gaps in the digest instead of averaging across them.
- **Use an interpreter with a current CA store for the collector.** An old system Python can fail TLS verification, so the collector fails before it reads any data. Pick an interpreter whose TLS verification works against the API.
- **Never key data on a provider id.** The provider id rotated on every daemon restart. Attribute earnings by model and time window, or by the change in the served-request counter, and never assign a host from a stale mapping.
- **Check every enabled model, not only the top one.** A check that tests only the top model hides a secondary slot that earns almost nothing. Alert on any slot that falls under the earning threshold.
- **Give Hermes its own local port.** If an agent calls the provider locally, bind a dedicated loopback port for the provider endpoint and change only the base URL of that provider entry. Never bulk-replace the URL of the existing model server.
- **Check other tools before deleting weights.** Model caches in a shared hub directory can serve more than one tool. Confirm no other consumer needs a model before removing it.
- **Leave a node off when the operator switched it off.** The operator turned it off for noise or heat. Do not re-enable it without asking.
- **Never print the account token or any local API key.** Keep them in files with restricted permissions and out of logs, task bodies, and comments.

## Verification
- `darkbloom status` shows `Daemon: running` and an enabled-model filter that matches the plan.
- After a switch, the warm-model list matches the plan once in-flight jobs finish.
- The earnings ledger has one row per job id and any day with missing data is listed in the digest.
- The latest pulse has one line per node, with the reachable flag set on every line.
