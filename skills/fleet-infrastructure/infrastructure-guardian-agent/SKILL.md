---
name: infrastructure-guardian-agent
description: Use when a scheduled agent should watch critical services on two or more Macs, report config drift, and flag upstream releases without changing operator-owned config.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [infrastructure, monitoring, parity, drift, release-watch, alerts, multi-host]
    category: fleet-infrastructure
related_skills: [multi-mac-fleet-ops, legacy-infrastructure-cleanup, mactop-system-monitor]
---

# Infrastructure Guardian Agent

## Overview
A guardian agent is a scheduled watcher for a small fleet. It checks that critical services are up on each host, compares the configuration of the hosts that should match, notices stale files and new upstream releases, and reports what it finds. It acts only where the change is a process-level restart with a backup taken first, and it never rewrites configuration that the operator owns. Keep the deterministic checks in scripts, so the agent is only needed to summarize and to decide what to escalate.

## When to Use
- Two or more Macs run the same agent stack, and their settings should stay aligned.
- Critical services (the agent gateway, a local model server, a memory service, the private network) must be watched on a schedule.
- You want a daily report that also says which upstream releases of those services are worth reading.

Do not use it to make configuration decisions. It proposes changes, and the operator approves and applies them.

## Features
- A scope list that names the critical services and the things that are out of scope.
- A master and replica model: one host's configuration is the reference, and the other hosts are compared against it.
- A parity check that reads the remote configuration over key-based SSH and reports only the differences that matter.
- Separate health checks for each messaging channel and each session type, so a healthy direct channel is not mistaken for a healthy group channel.
- Alert thresholds by severity, with an action for each level.
- A daily report with a fixed set of sections, and an evidence rule for any claim that ranks one option above another.

## Benefits
- Drift between hosts is found before it causes an outage.
- Process restarts are automatic only where they are safe, and each one is logged.
- Upstream releases are reviewed on a schedule, with a go or no-go recommendation for the operator.
- Operator-owned configuration is never changed silently.

## Procedure
### Set the scope and ownership
1. Write the scope as two lists. In scope: each critical service on each host, the parity-relevant configuration, the scheduled jobs and their definitions, the private network, the messaging channels, and the release watch for the stack's components. Out of scope: anything that is not infrastructure, such as trading or market analysis.
2. Name one host as the reference for configuration. The other hosts are replicas and are compared against it. Record which configuration file is the live one on each host, and resolve it with the runtime's own path command, not by assuming a profile name:
   ```zsh
   hermes config path
   ```
3. Write the ownership rule into the agent's instructions: the operator owns the configuration file on every host. The agent reports drift and proposes the change. It does not write the file, even on a replica host, unless the operator asks in the current session.

### Check service health
4. Check each critical service on each host. Use the health endpoint or the process check that the service provides, and record the result with a timestamp. A service that answers on its own host but not from another host is a reachability finding, not a health finding.
5. For a process-level failure of a service the agent is allowed to restart, back up the relevant state first, restart the process from a shell that is not the process itself, and check the health endpoint again. Record the restart in the log.

### Check configuration parity
6. Read the replica's configuration over key-based SSH. Use a non-interactive connection (batch mode), so a rejected key fails at once instead of waiting for a password. Do not put passwords in commands or in scripts:
   ```zsh
   ssh -o BatchMode=yes -o ConnectTimeout=6 <user>@<replica-host> "cat \"\$(hermes config path)\"" > <tmp-dir>/replica-config.yaml
   diff <tmp-dir>/reference-config.yaml <tmp-dir>/replica-config.yaml > <tmp-dir>/config-diff.txt
   ```
7. Compare only the sections that matter for operation: model and provider routing, gateway binding, ports, and service endpoints. Report differences. Do not edit either file.
8. Treat differences in a messaging channel's settings separately. Check the bot's account name against the name the operator expects, the mention rule, the allowed chats and users, and whether the group and the direct session use the same model. A healthy direct channel does not prove the group channel works, because sessions can keep separate state.

### Check the network and resources
9. Check name resolution and outbound access for the messaging service's host. If warnings about failed name resolution pile up in a short window, report the DNS check, the outbound port check, and any static hosts entry that the operator would need to add.
10. Check the file-descriptor limit when the log shows "too many open files". Report the current limit and the value the operator would need to raise it to. Raising it is an operator change.
11. Snapshot resource use on each host. Report, do not act, unless a service is down.

### Check releases and stale files
12. For each component in the stack, check its release page and its open issue list at the frequency the operator set. Report the new version, the changes that matter for this stack, the open issues that touch it, and a go or no-go recommendation.
13. Compare the architecture or topology document with the live state. If a service has changed port, host, or provider, and the document does not say so, report it as stale. Do not rewrite the document unless the operator asks.
14. Flag any instruction or skill file that has not been reviewed for more than the set number of days.

### Alert and report
15. Apply the alert thresholds below. Send an immediate alert for critical findings. Put everything else in the daily report.

| Severity | Condition | Action |
|---|---|---|
| Critical | A critical service is down on any host | Alert now; attempt a process-level restart with a backup |
| Critical | The model server or the agent gateway is unreachable from another host | Alert now; report the bind address |
| High | Configuration parity is broken | Log it; report it within the hour |
| High | Messaging group health differs from direct health | Inspect session state and model resolution; report the cause; ask for a human test |
| High | Remote access to a replica fails | Alert now |
| Medium | A stale instruction file | Log it; report it |
| Medium | A missing service definition | Log it; report it |
| Low | Resource use above the set threshold | Include it in the daily report |

16. Write the daily report with these sections: service health per host, configuration parity, stale file list, release summary with go or no-go recommendations, architecture document staleness, remediations performed, resource highlights, and blockers that need the operator.

### Evidence Rule
Never make an unqualified claim that one option is better than another. A ranking claim needs four parts: the metric (such as throughput, accuracy, context length, or adoption), the set of options compared (at least three named options), the measured numbers, and the source of the numbers. If no measurement exists, state the specifications only and say that the claim is unvalidated.

## Pitfalls
- **Replica drift is a finding, not an edit.** Even when the fix looks obvious, the operator owns the configuration.
- **Do not put passwords in commands.** Use key-based access, and ask for access changes rather than working around a failed key.
- **A healthy service on one host says nothing about another host.** Check reachability from each side.
- **Sessions keep separate state.** A direct channel and a group channel can use different models, so check both.
- **A process-level restart is the only automatic action.** Anything that changes configuration, routing, or ports needs the operator.
- **Scheduled runs should call scripts for the deterministic checks.** Use the agent to summarize and decide what to escalate, not to re-derive each check.
- **Remote configuration files can be large.** Read only the sections that matter, and never print credentials from them.
- **A release watch is a recommendation, not an upgrade.** Upgrades wait for the operator's go.

## Verification
- Each critical service has a dated health result from every host it runs on.
- The configuration diff shows only the sections that matter, and no file on any host changed during the run.
- Every automatic restart has a backup, a restart line in the log, and a passing health check afterward.
- The daily report contains every section, and each unverified item is marked as unverified.
