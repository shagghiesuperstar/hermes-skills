---
name: hermes-webui-remote-access
description: Use when a Hermes web UI must be reachable from a phone over a private network. Covers a private-address bind, the daemon start, a debug ladder and separate SSH checks.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes-webui, remote-access, mobile, tailscale, daemon, private-network]
    category: hermes-operations
related_skills: [hermes-gateway-ops]
---

# Hermes Web UI Remote Access

## Overview
A Hermes web UI can be driven from a phone through a companion server. The companion server is an open-source project
(see Attribution). By default it listens on loopback only, so a phone cannot reach it. Making it reachable widens who
can reach the login, so the bind address should be the private network address and nothing wider. This skill covers
starting the server as a daemon, a short ladder for a "server refused access" report, and the separate question of
whether SSH is reachable on the same machine.

## When to Use
- You want to operate Hermes from a phone or another device on your private network.
- A mobile client reports that the server refused access, or cannot connect at all.
- A server restart has logged out every mobile session.
- You need to know whether a remote shell is reachable, separately from the web UI.

## Features
- Daemon start with a bind address you choose, and a status check that shows the bound address.
- Reachability check against the private network address, not localhost.
- Debug ladder that reads the server's request log by client address.
- Separate checks for the web UI and for SSH.
- Warnings about what a restart does to signed-in sessions.

## Benefits
- The login is exposed only on the private network, not on the whole local network.
- A refused-access report is traced to one of three causes in a few steps.
- Remote-shell problems are not confused with web-UI problems.

## Procedure
### 1. Start the server as a daemon on the private address
```bash
cd <webui-checkout>
HERMES_WEBUI_HOST=<private-network-address> ./ctl.sh start
./ctl.sh status
```
- The default bind is loopback. A phone cannot reach loopback, so a non-loopback bind is required for phone access.
- Use the private network address printed by `tailscale ip -4`. Binding to all interfaces also exposes the login on the
  local network. Use that wider bind only when the operator approves it, and only with a strong password.
- The server is not restarted by a reboot. Start it again after a reboot, or install a supervised service definition.
- Check reachability from the server itself, against the private address:
  ```bash
  curl -s http://<private-network-address>:<port>/health
  ```

### 2. Debug a "server refused access" report
1. Run `./ctl.sh status`. Confirm the server is running and bound to the address you chose.
2. Read the server's request log, filtering by the phone's private address. Use the log file the server writes, or the output of the terminal where it runs:
   ```bash
   tail -50 <webui-log-file> | grep <phone-private-address>
   ```
   - A successful login followed by a refused chat start points to a stale session token. A restart of the server
     invalidates signed-in sessions, so the fix is to sign out, reconnect and sign in again. The server does not need a
     change.
   - A burst of connection-level errors with no method usually comes from a client retrying a broken connection. It is
     often harmless.
3. Only if the health check fails from another device, check the private network link: both ends must be on the same
   private network, and the status command shows it. Then check the bind address.

### 3. Check the remote shell separately
Reachability of the web UI and reachability of SSH are independent. If the phone is already on the private network,
the network path is confirmed. Check only the server side:
```bash
tailscale status --self
lsof -nP -iTCP:22 -sTCP:LISTEN
```
If no listener is on port 22, the remote login setting is off. Turning it on is an administrator action. On macOS the
command is `sudo systemsetup -setremotelogin on`. The operator must approve it and enter their own administrator
password. Never collect, store or type that password. Connect with `ssh <user>@<private-network-address>` afterwards.

Some sandboxed client builds do not support the network's SSH feature. That does not mean the network is broken. Use the
operating system's remote login setting over the private address instead.

Do not enable port forwarding, a public tunnel, or any other exposure to the public internet for this.

## Pitfalls
- **A restart logs out every mobile session.** Warn the user to sign in again after any server restart.
- **A healthy web UI does not prove that SSH works.** Verify each transport on its own port.
- **Do not bind to all interfaces by default.** Use the private address unless the operator has approved a wider bind.
- **Do not re-explain a network setup the user has already completed.** Confirm what works, then check the one remaining
  server-side item.
- **Do not handle an administrator password.** The operator approves and types it.

## Verification
- `./ctl.sh status` shows the server running and bound to the private address you chose.
- The health check returns an ok status from the private address.
- A test login from the phone succeeds, and the request log shows it with the phone's private address.
- The SSH listener check shows the expected state, and a remote login from another device works if it was requested.

## Attribution
The companion web server is the open-source hermes-webui project. The mobile
client is a separate app; this skill covers only the server side and the private network path.
