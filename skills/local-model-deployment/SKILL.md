---
name: local-model-deployment
description: Use when running, debugging, or retiring LLM servers. They run locally on a Mac. Covers port coexistence, single-model residency, auth and bind rules, memory-guard errors, client routing, and safe model decommissioning.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [local-inference, mlops, macos, ds4, omlx, local-llm, troubleshooting]
    category: local-inference
related_skills: [ds4-system-health, omlx-model-management, omlx-per-model-tuning, mlx-inference, darkbloom-provider]
---

# Local Model Deployment on macOS

## Overview
A Mac can host more than one local inference server, but the servers share one unified-memory pool and one GPU. Most production problems come from that sharing and from configuration that looks correct: a server that is listening but has the wrong model resident, a client that routes to a model the server does not have, a memory guard that rejects a prompt because of other tenants, or a deleted default that silently promotes some other model. This skill covers how to check what is really running, how the servers coexist, how to bind and authenticate them, how to debug the common failures, and how to retire a model without leaving dangling references.

## When to Use
- A local model request fails with a 4xx, a memory-guard error, an end-of-sequence token, or a silent empty reply.
- You are bringing a second inference server up next to an existing one.
- A peer machine cannot reach a server on this Mac.
- You are removing, replacing, or promoting a local model.

## Features
- Live residency checks: which ports are open, which models the server lists, and which model is actually loaded.
- A coexistence map covering shared memory, single-resident-model limits, and provider modes that change what gets loaded.
- Authentication and bind rules for loopback, LAN, and tunnel access.
- A decision table for memory-guard, context-length, and empty-output failures.
- A five-surface decommission audit before any model is unpinned or deleted.
- Routing guidance for agent clients, including auxiliary model slots.

## Benefits
- Diagnosis starts from what the server reports now, not from what a config file says.
- Two servers do not silently starve each other.
- A removed model cannot leave a default vacant or keep a pin that holds memory for nothing.
- Unexplained failures are sorted by symptom into a short list of likely causes.

## Procedure
1. Check what is live before reading any config. Probe the expected ports first, then ask the open server for its model list:
   ```zsh
   for p in <port-a> <port-b>; do nc -z -w 2 127.0.0.1 $p && echo "$p open" || echo "$p closed"; done
   curl -s --max-time 3 -H "Authorization: Bearer <key>" http://127.0.0.1:<port>/v1/models
   ```
   Report the models the server lists as available. Listing a model does not mean it is resident. Most MLX servers keep one large model in GPU memory at a time, and switching takes tens of seconds.
2. Confirm the server is running the process and configuration you think it is. Compare the running arguments and the base directory the process opened files from with the intended configuration:
   ```zsh
   ps -o pid,args -p $(pgrep -f <server-process-pattern> | head -1)
   lsof -p $(pgrep -f <server-process-pattern> | head -1) | grep -i "<config-dir-name>"
   ```
3. Plan memory before loading a model. A model that loads alone can fail when another model is resident. Add up the resident sizes, the cache budget, and the context the request needs, and compare with the ceiling the server reports. Measure the real footprint with `vm_stat` or `memory_pressure`, because the resident-set figure from `ps` can hide memory mapped from disk.
4. Probe with a short completion through the exact client path. A listed model can still fail, and a one-token request separates "server is down" from "model cannot generate".

### Coexistence
- **Share the pool deliberately.** Two servers on one machine cost each other bandwidth and memory. Run one large server at a time for benchmarks, and keep the second server for light work.
- **A provider mode can change what loads.** Some local-endpoint modes load a model for the network and for loopback clients at once. Check the mode before starting a second service.
- **Ports must be distinct.** Give each server its own port and set it explicitly. A server that defaults to a port another server uses can start, log success, and still lose the port.
- **Do not swap the resident model for someone else's pinned model.** Changing the model that another client depends on needs that client's owner to agree.
- **Do not put two roles on one server by default.** An interactive session and a background job competing for one resident model make each other stall. Give the background job its own server, or route the interactive session to a cloud provider.
- **Stop what you do not need before a large start.** Killing a competing server frees its memory, but only if the start is planned around it.

### Authentication and Binding
- **Bind to loopback by default.** A server on `127.0.0.1` answers only the local machine. To reach it from a peer, bind to a specific address or to all interfaces, and accept that the whole network can then reach it. Restrict that with a firewall or an SSH tunnel.
- **Verify the bind before blaming the client.** `lsof -nP -iTCP:<port> -sTCP:LISTEN` shows whether the server listens on loopback or on all interfaces. A peer's "connection refused" usually means loopback-only.
- **Never expose a model server publicly.** Do not enable a public tunnel or funnel for an inference port.
- **Use the bearer token the server validates.** Some clients send their key in a different header. A key sent in the wrong header returns 401 even when the key is right.
- **Expect the key to change after an upgrade.** Some versions regenerate the secret on first start, which invalidates older keys. Read the current key from the server's settings and update each client. Keep key verification on, even on localhost.
- **Keep keys out of notes and logs.** Store them in a secret store or a restricted environment file, and pass them to child processes through their environment, not through shell strings.

### Failure Decision Table
| Symptom | Likely cause | First check |
|---|---|---|
| 422 about a `system` role in messages | Client sends a role the server rejects | Route the request through a shim that moves system text to the top-level field |
| 401 invalid key | Key in the wrong header, or key regenerated | Compare the header name the client sends with the one the server reads |
| 400 with a memory-guard message | Dynamic memory pressure from other tenants | Re-send the same prompt on a quiet machine; if it passes, the guard is reacting to contention, not to the model |
| Client hangs with no output | Thinking output consuming the token budget | Turn thinking off for tool-calling clients, or raise the budget |
| Empty or end-of-sequence reply, no error | Configured model name not in the server's list | Compare the client's model name with the live list; fix the name, not the server |
| Context rejected below a minimum | Context length resolved from a stale or wrong field | Set the context length at the provider or root level, and clear stale cache entries |
| Fallback hop fails | Fallback endpoint not listening | Probe the port; a dead fallback is a dead hop, so say so instead of starting the server |

### Thinking Models
- Use the server's native reasoning controls, not extra instructions in the agent's prompt. Set the thinking switch, the chat-template argument, the reasoning parser, and a thinking budget in the per-model settings.
- A thinking model with a small token budget will show a reasoning preamble and end on the length limit. That is the model working as designed. Raise the budget, or send a longer test prompt, before concluding the model is broken.
- Clients should read both the answer field and the reasoning field. Dropping the reasoning field, or stripping it with a regex, hides real failures.
- Keep thinking off for models used only as fast tool-calling workers, and make sure those models still emit structured tool calls when thinking is off.

### Model Lifecycle
Before unpinning, unloading, or deleting any local model, audit five surfaces:
1. **Server pin and default state.** A pinned model is loaded at every start, even if nothing uses it. A default is used whenever a request names no model.
2. **Client fallback chains.** Search every client's configuration for the model name and each alias or variant spelling.
3. **Scheduled jobs.** Search each job file for the name in both its current and any snapshot field.
4. **Auxiliary routing.** Check the auxiliary slots for vision, compression, titles, and similar tasks.
5. **Live server truth.** Compare the live model list with the configuration, and grep the server log for both names, because the list shows aliases, not raw keys.

Only after all five are clean, and the operator approves: unpin the model with a backed-up settings edit, restart, and then remove the weights.

If a removed model was the default, the server can silently make whatever model sorts first the new default. After any removal, set a new default explicitly and restart. Never leave the default vacant.

Stale references to a removed model are low urgency when the chain has other working rungs. Batch the cleanup with the next planned change so the configuration is written once.

### Client Routing
- **Register the exact served ID.** Use the name the server lists. Aliases can resolve in the server but not in a client's own model map.
- **Set one canonical definition per provider.** The same provider defined in two places can disagree on port, key, or model. Keep one definition.
- **Make every auxiliary slot explicit.** A slot set to automatic falls back to the main provider and then down a catalog chain, which can reach a provider the machine has no key for. Give each slot its own provider, model, and base URL, and check that the provider matches the base URL.
- **Use the provider name the client expects.** Some clients need a namespace prefix for providers defined in a secondary list. A wrong prefix looks like an unknown provider.
- **Probe the live list before rejecting a model.** A cached picker list is a snapshot. Query the provider's current model list before concluding a model is missing.
- **Restart the gateway from an outside shell.** A gateway cannot reliably restart itself from inside one of its own sessions. The running session keeps the old model until the gateway restarts.
- **Set context length explicitly.** Clients that check a minimum context reject a model whose resolved value is small. Set the length at the root or provider level. Check the resolution order: explicit override, then cache, then live server query, then defaults.

## Pitfalls
- **Silent default promotion.** A missing default model does not raise an error. The first model in the list becomes the default.
- **Orphaned pins hold memory.** A pinned model preloads and occupies memory even when no client calls it.
- **Duplicate app installs share one launch agent.** Two copies of the same app launched from one agent start twice, and the menu bar shows two icons.
- **Models in a scanned folder load at startup.** Keep unused models in a folder outside the scanned path, not hidden inside it.
- **Copying a neighbor's full settings entry breaks the settings UI.** Build each per-model entry from the schema for the installed version. Fields that a variant does not support can make the UI hide most of the settings.
- **A stale size estimate can refuse a model that fits.** The estimate can count shard files that the current index no longer references. Compare the referenced shard set with what is on disk before lowering any guard.
- **Remote-session processes accumulate.** Clean up stray processes after remote diagnostic sessions.
- **Stopping a provider that is stalled can disable its auto-start.** Re-enable auto-start before leaving the machine, or the server will not come back after a reboot.
- **Some apps wedge after long uptime.** A server that has run for days under swap pressure can slow to a crawl. Measure throughput and swap before assuming a model problem, and restart the server cleanly if throughput has collapsed.
- **macOS privacy controls block launch-agent file access on external volumes.** A process started by a launch agent can hang in its first file open with no error, when the model or the binary lives on an external or network volume. Keep binaries and weights on the internal disk. Cache directories on external volumes are usually fine.
- **Forensic claims need evidence.** When investigating a corrupted configuration, report only what file metadata, the file's own contents, or timestamped logs show. Say plainly when the evidence is missing.
- **A 426 from a free tier means the client is too old.** Update the client, or remove that fallback. The primary provider keeps working.

## Verification
- The live model list matches the intended set, and the server reports the intended model as resident.
- A one-token completion and a short tool-call test pass through the exact client path.
- The bind address matches the intended exposure, and no port is open publicly.
- After a decommission, the five-surface audit is clean and the server's default is an explicitly chosen model.
- A peer machine, if one is in scope, gets a completion over the intended network path.

## Attribution
- DS4 inference engine by antirez: https://github.com/antirez/ds4
- oMLX model server by jundot: https://github.com/jundot/omlx
