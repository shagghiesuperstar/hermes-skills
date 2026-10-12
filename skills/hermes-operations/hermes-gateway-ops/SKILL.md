---
name: hermes-gateway-ops
description: Use when a Hermes gateway stops responding. It also applies when Telegram polling fails. Covers service identity, logs, restart discipline, failure signatures and health checks.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, gateway, telegram, launchd, diagnostics, operations]
    category: hermes-operations
related_skills: [hermes-gateway-cold-start-lag, hermes-fallback-chain-deploy]
---

# Hermes Gateway Operations

## Overview
The messaging gateway is the long-running process that polls chat platforms, runs the agent loop for each inbound
message, and sends replies. It is not an HTTP server by default, so a failed port probe does not mean it is down. It is
supervised by the service manager, and it reads a config that depends on which profile it was started for. Most
gateway problems come from one of four things: the wrong profile or config is live, a restart was assumed to have
happened, two processes are polling the same bot token, or the network path to the chat platform is broken. This skill
gives the order in which to check those.

## When to Use
- Messages are not answered, or answered only after a long delay.
- A health or status command says the service is not loaded, or two gateway entries exist.
- The chat platform reports a polling conflict, a network error, or a crash loop.
- A config change was made and you need to confirm the running gateway picked it up.
- A Hermes update was installed, and the running process may still be the old code.

## Features
- Identify the live gateway by its service label, command line, lock file and environment, not by a name search.
- Liveness check from logs and launchd state, not from a port probe.
- Read-only Telegram probe through the public Bot API, with the token kept out of output.
- Restart procedure that pairs bootout with bootstrap and confirms the new process.
- Failure-signature table for the common messaging and polling faults.
- Update check that compares the local install with the real upstream.
- No-agent health watchdog pattern with silent healthy runs.

## Benefits
- The right profile, config and log files are checked the first time.
- A gateway is not declared down because of a probe that never applied to it.
- Config changes are reported as live only after a restart that is confirmed.
- Duplicate pollers and stale service definitions are found before they cause message loss.

## Procedure
### 1. Identify the live gateway
```bash
hermes gateway status
launchctl list | grep -i hermes
ps aux | grep "[h]ermes" | grep gateway
```
Confirm three things for the process that is actually running:
- the service label, which is often profile-specific;
- the command line, which should include the expected `--profile` flag;
- the environment the service exports, especially the Hermes home directory.

If the service is profile-scoped, the config that matters is that profile's config file, not the root config. Compare
both files, but treat the profile file as the one the running gateway reads.

### 2. Check liveness with logs and launchd, not a port
Read the agent log for recent inbound messages and recent sends. If an inbound message from today appears, and a send
follows it, the gateway is alive:
```bash
grep "inbound message" <hermes-home>/profiles/<profile>/logs/agent.log | tail -5
grep "Sending response" <hermes-home>/profiles/<profile>/logs/gateway.log | tail -3
```
A non-zero launchd PID confirms that the service manager has the process. A failed `curl` to a port the gateway never
opened says nothing about health.

### 3. Find the log files
Log paths are not obvious. They are open on the gateway process. List them from the process, and use the absolute paths
the list prints:
```bash
lsof -p <gateway-pid> | grep -E "gateway\.log|agent\.log|errors\.log|gateway\.error\.log"
```
- `agent.log` is written synchronously and is the best source for live activity.
- `gateway.log` from the service manager's standard output can lag minutes behind.
- `errors.log` and `gateway.error.log` hold failures from the agent and the gateway respectively.

### 4. Probe the chat platform without printing secrets
For Telegram, load the bot token from the profile's env file inside the probe, then call the read-only Bot API methods.
Print only the username, the ID and the webhook fields:
```bash
# inside a script, with the token read from the env file and never printed
#   getMe                -> username and id only
#   getWebhookInfo       -> url should be empty for polling; read pending_update_count and last_error_message
```
A webhook URL set on a bot that should poll is a conflict to fix before anything else.

### 5. Restart discipline
- A gateway cannot restart itself from inside a turn it is hosting. The restart attempt stops the turn and the safety
  checks refuse it. When that happens, do not try other verbs to get around the check. Write the change to disk, verify
  it, and give the operator the one command to run from an external shell.
- Report a config change as "on disk, not live" until a restart is confirmed.
- Restart by pairing bootout and bootstrap. A single kickstart may not reload a changed service definition:
  ```bash
  launchctl bootout gui/$(id -u)/<gateway-label>
  sleep 1
  launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/<gateway-label>.plist
  sleep 3
  launchctl list | grep <gateway-label>
  ```
  A new PID confirms the restart. A status of `-15` means the process was killed by SIGTERM.
- Move old service files into a dated quarantine folder. Do not delete them, so you can roll back.

### 6. Match the symptom to a signature

| Log or status signature | Cause | Fix |
|---|---|---|
| `Conflict: terminated by other getUpdates request` | Two processes poll the same bot token | Find the duplicate instance and stop it, or rotate the token |
| `not loaded` in the gateway status, or two launchd entries for one gateway | A stale service definition, or two competing services | Disable the stale plist, then do a bootout and bootstrap cycle |
| `PID file race lost` repeating after a reboot | Two launchd entries start instances that block each other | Remove the stale entry, and use a start wrapper that clears the old PID file |
| `Bootstrap failed: 5: Input/output error` | A half-loaded service | Bootout, wait, then bootstrap |
| `HTTP 401` on a provider call | Missing or stale key | Check the key with the auth tools, not by printing it |
| `HTTP 404` on a model call | Wrong model name or a retired model | Update the model name, or check provider availability |
| A server in the config fails its initial connection on every session | A dead MCP entry | Remove it from the config |
| `Symlink loop` on the kanban database | Two profile paths point at each other | Restore one canonical file, and remove the other link |
| Group messages ignored, direct messages work | Mention gating is on | Test with an explicit mention, and do not treat it as a crash |
| Home-channel ID disagrees with the operations group ID after a group migration | Config drift | Align the IDs with the current group |
| Repeated retries of the same message every few seconds | Unclosed client sessions, or flood-control retries stacked on a loop | Check for repeated stream-delivery lines, then restart from the operator shell |

**Network crash loop.** When the chat platform's name resolves badly, the polling client retries, and a fallback address
that was cached at startup can be dead. The gateway exits with an error and the service manager restarts it into the
same failure. Check DNS resolution for the platform's host, probe the cached fallback address with a short timeout, and
restart once DNS works. Throttling the service restart interval gives DNS time to recover. If the client never
re-discovers fallback addresses during reconnect, file an upstream issue. Do not patch the installed code.

### 7. Check updates against the real upstream
Compare the install with the upstream remote, not with the remote the update command tracks:
```bash
cd <hermes-clone>
git fetch <upstream-remote> main
git fetch origin
git rev-list --count HEAD..<upstream-remote>/main
git merge-base --is-ancestor HEAD <upstream-remote>/main && echo "fast-forward possible"
```
If the install is an ancestor of upstream, fast-forward only. After a code update, the running process keeps the old code
until it is restarted. Use the update command's plan mode to see which services would be affected before running it.

### 8. Set up a health watchdog
Use a no-agent script on a schedule set away from the top of the hour. It writes a short table of checks every run, and
prints to standard output only when a check is red. An empty output sends nothing.
- Gateway process present, and its last inbound and outbound lines are recent.
- Disk use on the volume that holds the Hermes home is below 90 percent. Read the percentage column only.
- The chat platform's bot API answers `getMe`.
- Any local model server the profile depends on answers its models endpoint.

Register it with the scheduler's script option and a bare file name, then confirm it in the job list.

## Pitfalls
- **A failed port probe is not a down gateway.** Read the logs and the launchd state first.
- **Check which profile is live before you change any config.** A root config and a profile config can disagree, and the
  running gateway reads only one of them.
- **Write a change to disk, then say it is not live.** Never claim a platform picked up a flag before a confirmed restart.
- **Do not retry a failed send blindly.** The message may already have been delivered, and a retry creates a duplicate
  or hits flood control. Retry once after a short delay at most. If the operator confirms receipt, stop. If the send
  really failed, write the message to a durable local file, so the content survives.
- **Keep the bot token out of output.** Read it inside the probe and print only the fields you need.
- **Do not use `pgrep` alone to identify the gateway.** It can match a short-lived one-shot command. Confirm each PID with
  the process table, and confirm it against the lock file.
- **A name search can miss a process started as a Python module.** Match the full command line, and use a bracketed
  pattern so the search does not match itself.
- **A single kickstart can leave the old definition loaded.** Pair bootout with bootstrap.
- **Quarantine old service files instead of deleting them.**
- **Confirm liveness against the process table and the lock file.** A PID written in a file proves nothing by itself.
- **Packaged desktop apps are a separate process tree.** Check their own logs before you blame the messaging gateway.

## Verification
- The service manager lists one gateway entry for the profile, with a live PID that matches the lock file.
- A real inbound message appears in the agent log, followed by a send.
- The bot API probe returns the expected username, and the webhook URL is empty for a polling bot.
- After a confirmed restart, the new PID is listed and the first new message is answered.
- The watchdog prints nothing on a healthy run, and prints one block when a check is red.
