---
name: macos-remote-access
description: Use when restoring Screen Sharing or VNC access to a Mac. Covers mode conflicts, socket-activated listeners, authentication isolation, private-network access, and verification.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [macos, remote-access, vnc, screen-sharing, ard, tailscale, ssh]
    category: fleet-infrastructure
related_skills: [multi-mac-fleet-ops, tailscale-fleet-macos, aperture]
---

# macOS Remote Access

## Overview
Remote control of a Mac runs through several layers: the private network path, a listener on the Screen Sharing port, a service mode (ordinary Screen Sharing or Remote Management), user authorization, and the client's own credentials. Each layer can fail separately, and an open port does not mean a login will work. Recovery goes layer by layer: inspect live state, make one bounded change, and verify that layer before touching the next one.

## When to Use
- Screen Sharing or a VNC client cannot connect to a Mac, or the port is closed.
- The Mac accepts a connection but rejects every login, or the client forces a username that does not work.
- Remote Management and ordinary Screen Sharing conflict on the same Mac.
- A Mac that was removed from a private network needs to rejoin it.
- A private-network SSH or file-serving route is blocked, and you need to diagnose which layer is at fault.

## Features
- A layered diagnosis: network path, listener, service mode, user authorization, client authentication.
- Recognition of socket-activated listeners, so an absent daemon process is not read as "down".
- Authorization repair for Remote Management users, configured without restarting the live listener.
- Per-mapping repair for private-network file and port forwards, without a node-wide reset.
- Tailnet-lock rejoin guidance for a node that was deleted from the admin console.
- A verification contract that separates "transport restored" from "login verified".

## Benefits
- Each change is tied to one failing layer, so a fix is never mistaken for a coincidence.
- A working remote session is not disturbed during recovery.
- Credentials stay with the operator. The skill never asks for or stores a password.
- A partial recovery is labeled as partial, so nobody assumes control works when only the port answers.

## Procedure
### Stay within safe limits
1. Keep the working transport. If a private-network SSH path works, do not change it while repairing Screen Sharing.
2. Never request, receive, store, or type a login or VNC password. The operator enters credentials locally or through their own secure terminal. Do not change the Mac's login password to repair VNC authentication.
3. Do not expose the Screen Sharing port publicly. Use a private network only.
4. Do not stop every process that owns the port. Socket activation can make the port owner appear as the launch daemon, PID 1. Target the owning service instead.
5. Do not repeatedly boot out protected system services to force a state. Use the supported service controls and the system settings panes.
6. Once remote access works, stop changing things. Do not toggle Remote Management or switch services during an active session. Schedule cleanup for a maintenance window.

### Identify the machine and the intended mode
7. Name the machine from live facts before any change: the computer name, the local host name, the chip string, the serial number, the private-network name, and the client version. Match screenshots on host name, address, version, and last-seen time, not on a marketing chip name.
8. Decide the intended mode. Ordinary Screen Sharing authenticates the Mac user. Remote Management (Apple Remote Desktop) grants management privileges and can change how authorization works. The two share components and conflict when only part of one is configured.

### Check each layer in order
9. Network path: confirm both devices are on the same private network and probe the Mac's private address with a bounded check:
   ```zsh
   nc -G 2 -zv <private-address> 5900
   ```
10. Listener: check the port on loopback and on the private address. Treat a closed loopback port with a live process as a configuration fault, not a network fault.
11. Processes: check whether the Remote Management agent and the Screen Sharing daemon are running. The Screen Sharing daemon can be socket-activated and absent while idle. A successful connection can start it, so absence alone is not proof of an outage.
12. Service mode: read the unified log for lines showing that Remote Management is active and which mode owns authorization:
    ```zsh
    log show --last 10m --predicate 'process == "screensharingd"' | tail -n 50
    ```
13. Authorization: check both the Screen Sharing access group and, when Remote Management is active, the user's privilege record:
    ```zsh
    dscl . -read <user-record-path> naprivs
    id <short-name>
    # <user-record-path> is the account's directory record: the users folder plus the short name
    ```
14. Authentication evidence: the server log distinguishes transport from credentials. A failed-authentication line with the correct user name and client address proves the connection reached the Mac, so the fault is in authorization or in the password.
15. Change one layer, then repeat the probes for that layer and the layers above it.

### Repair authorization for Remote Management users
16. When Remote Management is active and a user lacks a privilege record, grant access to that one user without activating or restarting the agent. Run this only with the operator's approval, and record which user was granted:
    ```zsh
    sudo /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart \
      -configure -allowAccessFor -specifiedUsers
    sudo /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart \
      -configure -access -on -users <short-name> -privs -all
    ```
    A successful run ends with `Done.`. Verify the record and the port before asking for another connection attempt. Avoid adding a restart option during recovery: a restart that hangs can leave the listener unstable, and the configure-only path writes the authorization without touching the live listener.

### Handle the launch-daemon details
17. Inspect the actual launch plist and its label before any enable, bootstrap, or kickstart. Do not guess a label from a process name. A successful enable or bootstrap often prints nothing, so verify afterward.
18. If the label is enabled but not loaded, bootstrap the system plist first, then check the listener. The ordinary Screen Sharing daemon is commonly described by a plist in the system launch-daemon folder. Confirm on the live host rather than assuming the path.
19. A TCP success proves only transport. It does not prove that credentials will succeed.

### Classify the failure
20. Use this order:
    1. Connection refused or timed out: listener, firewall, route, or a service that is not loaded.
    2. The protocol handshake reaches the Mac, but credentials are denied: transport works. Check the active mode, allowed users, and the authorization record.
    3. Remote Management is active when ordinary Screen Sharing is expected: resolve the mode through supported settings. Stopping one agent alone is not durable, because its job can start it again.
    4. The client forces a user name: it is using Mac-user authentication. A separate legacy VNC password does not match the Mac account password.

### Rejoin a removed node to a locked private network
21. If the operator deleted this machine from the admin console, a fresh login creates a new node entry with a new address. Do not try to refresh the old node. Log the machine in again with the same account.
22. The new node appears as locked out until a signing node signs it. Use a signing node that is online. An offline signing node cannot sign, and a status command that reports the lock as not enabled on a logged-out machine proves nothing.
23. Keep the old node only when the admin console still lists it and a profile exists on the machine. In that case, switch to the profile and re-authenticate.
24. Login and signing are operator tasks. Do not paste login links into shared channels.

### Serve files or ports over the private network
25. File serving through the private-network service works only on the standalone build of the client app. The sandboxed store build cannot serve files or directories. Confirm the build before promising file serving.
26. Repair one mapping at a time. Never run a reset of the serve configuration to fix one mapping, because a reset removes every mapping on the node. Remove a single mapping with its own off form, then re-add the missing one with its exact original target and port, so clients and their addresses keep working.
27. Probe both layers in any health check: the raw port on loopback and on the private address, and the mapping line in the serve status. A port can fail while its row still appears, and a row can disappear while an old handler still answers. Those are different faults.

### Diagnose a blocked private-network SSH route
28. Work up the ladder: confirm the data path, probe the port with `nc`, check name resolution, try alternate ports only if the operator allows them, then check whether the node's control API answers. If the control API answers but the SSH port filters, the cause is usually the host firewall or the remote-login setting. Hand the operator the unblock steps, and verify with one `nc` probe after they finish.
29. When a required host cannot be read over SSH, report the probe evidence and mark every unread field as unverified. Do not infer what the logs contain.

## Pitfalls
- **An open port is not working authentication.** A socket can accept connections while every login is rejected.
- **Killing every port owner can kill the launch daemon.** Target the service, not the process list.
- **Silence is not proof.** A command that prints nothing may still have failed. Verify each change with a probe.
- **Remote Management and ordinary Screen Sharing can fight.** Partial configuration of one leaves the other in a confusing state.
- **A reset of a serve configuration removes every mapping.** Use per-mapping off forms only.
- **Guessing labels and usernames wastes turns.** Read the live plist and the account list instead.
- **Deleted nodes do not come back by refreshing.** A new login creates a new node entry.
- **A locked network needs an online signing node.** Offline signing nodes cannot sign.
- **Credentials do not belong in the chat.** The operator enters them locally or in their own secure terminal.

## Verification
Do not declare recovery until every applicable check passes:
- The intended service mode is known from the live host.
- No stale setup command is still running.
- The port answers on loopback.
- The port answers over the private route.
- The intended client authenticates with the intended user.
- The operator can view and control the desktop.

If only the transport works, label the result **transport restored, authentication unverified**.

## Attribution
- Apple Screen Sharing and Remote Management are Apple features; the commands above use the tools that ship with macOS.
