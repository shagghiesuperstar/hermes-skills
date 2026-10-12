---
name: tailscale-fleet-macos
description: Use when a Tailscale node on a Mac fleet needs recovery. Covers key expiry, Tailnet Lock signing, ACL reachability, node removal, variant choice, and MagicDNS rules.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [tailscale, tailnet-lock, acl, magicdns, macos, fleet, key-expiry]
    category: fleet-infrastructure
related_skills: [multi-mac-fleet-ops, macos-remote-access, aperture]
---

# Tailscale on a macOS Fleet

## Overview
A private network across several Macs fails in a few predictable ways. A node key expires and the node drops off the network. A signing node is locked out of the trust list. An access rule blocks one port while ping still works. A VPN overrides name resolution. A stale machine registration keeps a name from rejoining. This skill covers the checks and the order of recovery for each, plus the standing rules that prevent a single bad command from locking the whole fleet out.

## When to Use
- A node is unreachable, or its agent service answers on the node but not from other nodes.
- A node's key is near or past expiry, or a re-authentication is needed.
- Tailnet Lock needs a signing node added, rotated, or checked.
- Two machines can ping each other, but a specific port fails.
- A machine must be removed from the admin console before it can rejoin.

## Features
- Client-variant detection, so the right command set is used for the installed client.
- Key-expiry recovery with the operator's console step separated from the local steps.
- Signing-node checks, with the difference between the node key and the lock key spelled out.
- Stale-node removal through the admin console, with an API fallback and its error meanings.
- A reachability ladder that separates a route problem from an access-rule problem.
- Standing rules that prevent lockouts.

## Benefits
- Recovery starts from live state, not from a remembered address.
- The operator keeps the steps that need the admin console or a human login.
- Signing authority stays with trusted nodes, so a lockout does not happen by accident.
- Port failures are diagnosed as access rules or as node faults, not guessed at.

## Procedure
### Identify the client variant
1. Detect which client is installed before running any command. Two variants can be present, and they must not run at the same time on one node:
   ```zsh
   ls /Applications/Tailscale.app/Contents/MacOS/Tailscale 2>/dev/null && echo "GUI app present"
   which tailscale
   tailscale version 2>&1 | head -3
   ```
2. Know what each variant allows. The standalone variant supports the system extension controls and the full feature set. The App Store variant uses a network extension and does not support Tailscale SSH or serving files. The open-source daemon is command-line only and has no system extension. Pick one variant per node and record it in that node's notes.
3. Control the system extension only on the standalone variant:
   ```zsh
   tailscale configure sysext status
   ```

### Check the node before any change
4. Read the state of the node and the network:
   ```zsh
   tailscale status
   tailscale lock status
   tailscale netcheck
   ```
   Run `tailscale lock status` only on a node that can sign. Record the peers, their online state, and the node's own key status before you change anything.
5. Probe the peer by its MagicDNS name, not by a stored address:
   ```zsh
   tailscale ping <node>.<tailnet>.ts.net
   ```
   Addresses change after sleep and network changes. Treat any stored address as a guess until a fresh status shows it again.

### Recover an expired key
6. If a node's key has expired, the node cannot reach the network, and its services time out from other nodes. The operator extends the key in the admin console (the device's menu, then the temporary key extension). This step needs a human in the console.
7. Re-authenticate the node from a path that does not depend on the network you are fixing. A console login or a local session is safest. Then run:
   ```zsh
   sudo tailscale up --force-reauth
   ```
   A signing node signs its new key automatically in the normal case, so no manual re-signing is needed.
8. Verify the node as a signing node, and check that its signing key appears in the trusted list:
   ```zsh
   tailscale lock status
   ```
   If the key is missing, add it from another trusted signing node, using the signing key rather than the node key. The two keys have different prefixes, and removal commands need the signing key.
9. Prevent the next expiry. Turn off key expiry for signing nodes in the admin console, and track the expiry dates of the other nodes.

### Remove a stale node
10. Remove a stale registration from the admin console, if the console allows it. The user needs an owner, admin, or IT-admin role. A node that was shared into the tailnet from another account cannot be deleted with the normal controls.
11. If the console's remove control is unavailable, an API key from the admin settings can delete the device. Store the key in a secrets store, not in shell history or notes. The operator names the device to delete before you run the call:
    ```zsh
    curl -X DELETE "https://api.tailscale.com/api/v2/device/<device-id>" -K <restricted-curl-config>
    ```
    The config file holds one line, `user = "<api-key>:"`. Make it readable only by your account (`chmod 600`), so curl reads the key from the file and it stays off the command line.
    Read the status code. A 403 means the key lacks the role, a 404 means the device id is wrong or already removed, a 400 means the device is an external share, and a 5xx means a transient service fault to retry later.
12. After removal, confirm the node is gone from `tailscale status`, then re-authenticate it as a new node.
13. A stale signing registration must be removed from the lock's trusted list before the same name can rejoin. Remove it only with the operator's direction.

### Diagnose reachability
14. Separate the layers. Ping uses the network path. A TCP connect to a port uses the access rules. A node can answer ping while every TCP port is refused by the access rules, so ping alone does not prove a service is reachable.
15. When a node is reachable by UDP but a TCP port fails, check the access rules first, then the node:
    ```zsh
    tailscale ping <node>.<tailnet>.ts.net
    tailscale netcheck
    ```
    If `netcheck` shows the port blocked end to end, the cause is the rule, not the node. The fix belongs to whoever administers the access rules.
16. Use a fixed health definition for each node. A node is green when ping succeeds and each service port answers. It is red when ping fails and the service ports time out. Anything between is amber and needs a note.

### Access rules and naming
17. Keep the access rules default-deny. Grant each cross-node path explicitly, with the minimum ports the service needs. Re-verify any path that was broken before.
18. Address fleet nodes by MagicDNS name, never by raw address. Treat a stored address as suspect when it differs from a fresh status.
19. A VPN that overrides name resolution can break MagicDNS. Connect the other VPN before the mesh client, and check the mesh client's DNS state after the VPN connects:
    ```zsh
    tailscale dns status
    ```

### Standing Rules
- Never run two Tailscale client variants on one node.
- Never edit the client's configuration with text substitution. Use the client's own commands or the admin console.
- Never paste login codes or auth keys into chat. Take a key from the admin console or a secrets store, and pass it to `tailscale up --authkey "$(cat <restricted-key-file>)"` only in a session you control. The key is visible in the process list while the command runs, so tell the operator before you run it.
- Do not call recovery successful until the status, the lock state, and a real ping all agree.
- Do not log out a signing node unless a second signing node is still trusted. Otherwise the tailnet can lock you out.
- Do not bring the client down on a machine you are reaching only through the network it provides.
- Escalate to the operator for any change that needs the admin console, a human login, or removal of a trusted signer.

### Quick Reference
```zsh
tailscale status                        # peers, addresses, online state
tailscale ping <node>.<tailnet>.ts.net  # end-to-end reachability
tailscale netcheck                      # path, relays, blocked ports
tailscale version                       # client and daemon versions
sudo tailscale up --force-reauth        # rotate the node key
tailscale lock status                   # trusted signing nodes
tailscale lock add tlpub:<signing-key>  # add a trusted signer
tailscale dns status                    # resolver state
```

## Pitfalls
- **Trusting a stored address.** Addresses shift after sleep and network changes.
- **Confusing the node key with the signing key.** Removal commands need the signing key.
- **Treating a ping as a service check.** Access rules can refuse the port while ping succeeds.
- **Deleting a signer during a lockout.** Keep at least one other trusted signer before any removal.
- **A VPN started after the mesh client.** It can override DNS and break name resolution.
- **A key pasted into chat.** Treat any exposed key as compromised and rotate it.

## Verification
- `tailscale status` shows the node online with the expected name, and `tailscale lock status` lists its signing key.
- A ping by name succeeds, and each required service port answers from another node.
- The node's service answers its health check from a second node, not only from itself.
- The admin console shows the node with the expected key expiry, and the lock list has no stale entries.

## Attribution
- Tailscale: https://tailscale.com
