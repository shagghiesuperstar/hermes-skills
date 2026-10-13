---
name: multi-mac-fleet-ops
description: Use when working across several Macs in one fleet. Covers host identity, live reachability probes, safe cross-host commands, service restarts, and fleet-wide config changes.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [fleet, ssh, tailscale, mdns, gateway, config-change, multi-host]
    category: fleet-infrastructure
related_skills: [tailscale-fleet-macos, macos-remote-access, darkbloom-fleet-ops]
---

# Multi-Mac Fleet Operations

## Overview
A fleet of Macs, each running its own agent runtime, fails in predictable ways. The hosts look alike, so short labels collide. Remembered addresses and usernames go stale. A service reports "running" from a process that no longer serves. A config change lands on one machine and is assumed to be everywhere. This skill sets the order of operations for any cross-host task: confirm which machine you are on, probe the peer live, connect with a non-interactive call, confirm identity, then act and verify each layer separately.

## When to Use
- A task names a machine by role or short label, and you must confirm which host that is.
- A peer host is unreachable, or its service answers in one check and not in another.
- A service on another host needs a restart, or a configuration change must reach several hosts.
- A status report about the fleet is being written and each claim needs a live check.

## Features
- Host identity rules that use full hostnames and a local inventory, not short labels.
- A reachability ladder: name resolution, then the network path, then the login, then the application port.
- Non-interactive SSH with identity confirmation before any action.
- Restart rules that keep the operator's authority and avoid the runtime's own self-restart guard.
- A fleet-wide config change protocol: find, back up, change, verify, report.
- Status claims that name the probe that backs them.

## Benefits
- A command never runs on the wrong machine because a short label matched.
- Stale addresses and remembered state are checked, not trusted.
- A partly reachable peer is reported accurately, instead of being called healthy or down.
- Config changes reach every host, and the report shows exactly what changed.

## Procedure
### Identify the hosts
1. Keep a local inventory that maps each full hostname to its role, network addresses, and login user. Keep it outside shared documentation. Use the full hostname in every command and every message. Short labels such as a model class name collide when several machines share that class.
2. Before any cross-host action, print where you are and confirm the target is not the machine you are on:
   ```zsh
   hostname
   whoami
   ```

### Probe reachability in layers
3. Start with name resolution, not a remembered address. Resolve the full hostname on the local network first, then read the live interface and neighbor table, and only then try the overlay network name:
   ```zsh
   ping -c1 -W2 <full-hostname>.local
   ifconfig | grep "inet "
   arp -an
   tailscale status
   ```
   Treat any address from memory or from an older session as a guess until a live probe confirms it.
4. Check each layer separately, because each can fail on its own:
   - Route: the host answers a ping.
   - Login: a non-interactive SSH call succeeds.
   - Application: the service port answers a short HTTP request.
   A healthy route does not prove the application port is open, and a working login does not prove the model or service is up. Report the layer that failed.

### Connect and confirm identity
5. Connect with a non-interactive call. Batch mode makes a rejected key fail at once instead of hanging on a prompt:
   ```zsh
   ssh -o BatchMode=yes -o ConnectTimeout=6 <user>@<full-hostname> 'hostname; whoami'
   ```
6. If key authentication fails, stop and ask the operator for access. Do not guess other usernames, and do not pass passwords through chat or shell variables. A connection that closes right after the key offer usually means the account is not on the host's remote-login list, so the fix is the operator's to make.
7. Run `hostname` and `whoami` as the first command of every session, so a wrong target shows up before anything changes.

### Restart a service safely
8. Restart from a shell outside the service's own process. Runtimes often refuse to restart themselves from inside, because the restart would kill the shell doing the restart. Use one of these paths:
   - An SSH session to the target, then the restart command there.
   - The in-app restart command, run by the operator on the device.
9. Before a restart, check for in-flight work and note it. After the restart, check the health endpoint and confirm the process ID changed. A health check that answers from the old process is not a restart.

### Change configuration across hosts
10. Find every live reference before you edit anything. Search the live configuration, scheduled-job definitions, instruction files, skill files, and profile files. Skip logs, caches, session history, and backups:
    ```zsh
    grep -rli "<old-value>" <config-dir> <jobs-file> <skills-dir> <profiles-dir> 2>/dev/null
    ```
11. List alias entries that resolve to the old target. An alias is a live route even when its name looks harmless, and a removed provider behind an alias fails only when someone calls it.
12. Back up each file you will change into a dated folder under the runtime's home directory, before the first edit.
13. Make each change with the runtime's own setter where one exists. Edit a file directly only where no setter exists. Do not re-enable a paused job unless someone ordered it.
14. Verify on every host. The old value must return zero matches in the live files, a health probe must pass, and a real request must succeed through each changed route.
15. Report the final routing table, the removal list (file, old value, new value), the backup path, and the health result for each host.

### Make status claims
16. Back each factual claim about a running service or a peer with a live probe taken at claim time. Earlier pings, notes, and memory are history, not current state.
17. Keep three claims separate, and verify each with a different probe:
    - "I wrote the file" is checked on the writing host.
    - "The file is on the peer" is checked on the peer, with a listing or checksum run there.
    - "The sync finished" is checked from an observed transfer result, not from the writer's local state.
    If the peer check cannot run, write "written on <writer>; not verified on <peer>" and name the condition that would unblock it.
18. A model or process is "running" only with a handle: a process ID, a run ID, a log line, or a live response. A name in a status file is not a handle. Before you report a route as active, check the live configuration that routes to it.
19. When a named model cannot be reached, do not silently substitute another one. Name the substitution, the reason, and the handle of the work that ran, and ask whether the named route should be restored.

### Run long builds safely
20. Run a long coding task in its own git worktree, not in the operator's primary checkout. Create the worktree on a new branch, confirm the branch and commit inside it, and tell the operator the path before the run starts.

## Pitfalls
- **Short labels collide.** Two machines of the same model class share most of their names. Always use the full hostname.
- **Cached addresses and usernames go stale.** A host that answered earlier in a session can stop answering on the next probe. Probe again before each action.
- **A ping or a tailnet status line is not an application check.** The network path can be healthy while every application port refuses connections, because of host firewalls or access rules. Probe the port.
- **Guessing usernames wastes turns and can trip lockouts.** Ask for access instead.
- **Passwords do not belong in chat or in shell variables.** Use keys, or ask the operator to provide access through their own tools.
- **One bot token per gateway.** Two agents that share an environment file with the same bot-token key make the last value win, and the wrong bot answers in the shared chat. Give each long-lived agent its own profile, its own environment file, and its own token.
- **Memory and state services are per profile.** A profile-scoped process reads its own copy of config and identity files. A root-level copy of the same name may be inert. Check the profile's copy.
- **Automated echo messages create loops.** When two agents answer each other's status or noise messages, the exchange never ends. A message that needs no answer gets no answer. After two consecutive automated messages with no request, stop replying.
- **Do not use a `timeout` command on macOS.** It is not installed by default, so the command fails with "not found" and an empty result looks like a real negative. Bound a run with a perl alarm instead: `perl -e 'alarm 60; exec @ARGV' <command> <args>`.
- **Use the agent runtime's background-job mode, not a shell `&`.** Some runtimes refuse foreground commands that background themselves.
- **Check what an editable install loads before upgrading.** A forced reinstall can replace a local checkout's install with a published package and drop local changes. Use the project's own sync command after changing the version string.
- **Stop when every probe fails.** Report the failing layer and the unblock condition instead of retrying the same probe.

## Verification
- `hostname` and `whoami` on the target match the inventory entry before any change.
- Each layer has its own recorded probe: route, login, and application port.
- A restart shows a new process ID and a passing health check.
- A configuration change shows zero matches for the old value in the live files, a passing health probe, and one successful request through each changed route.
- The report lists each host, each probe result, and the backup path.
