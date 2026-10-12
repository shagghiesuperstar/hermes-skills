---
name: hermes-multi-machine-deployment
description: Use when adding a second Mac as a Hermes agent host. Covers private-network SSH, the agent install, profile and bot setup, the gateway service, delegation, and verification.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, deployment, ssh, tailscale, gateway, delegation, multi-host]
    category: fleet-infrastructure
related_skills: [multi-mac-fleet-ops, infrastructure-guardian-agent, macos-remote-access]
---

# Hermes Multi-Machine Deployment

## Overview
A second Mac can run its own Hermes agent, with its own profile, messaging bot, gateway service, and local model server, and can take delegated work from a first machine. The steps are mostly routine, and the failures are predictable: an SSH key that is not authorized, a service bound to an address the other machine cannot reach, a model name that does not match the local server's registry, a bot whose privacy setting hides group messages, and a delegated task that reports success in chat but produced nothing on disk. This skill sets the order and the checks for each phase.

## When to Use
- You want a second machine to run an independent Hermes agent in the same private network.
- You are wiring one agent to delegate missions to another over SSH.
- A remote agent stopped answering after the target machine slept, rebooted, or changed address.

## Features
- Phased deployment with a check at the end of each phase.
- Key-based SSH setup on the private network, with a dedicated key per target.
- Private-network exposure of the local services the remote agent needs, bound to loopback where possible.
- Profile, messaging bot, gateway service, and delegation configuration.
- Verification by session records and deliverables, not by chat messages.
- Recovery steps for address changes, authentication failures, and services that report running while the port is closed.

## Benefits
- Each phase has a pass condition, so a broken step is found before the next one is built on it.
- Delegated work is checked where it actually lands.
- Credentials stay in local environment files and never appear in chat.
- Recovery after a sleep or reboot follows a short, fixed sequence.

## Procedure
### Phase 1: Private-network SSH
1. Confirm both machines are on the same private network, and enable remote login on the target from the system settings. Limit it to the user account the agent will use, if the platform allows it.
2. Read each machine's private address from its network client on the machine itself, not from an address you remember.
3. Create a dedicated key for this target. Use a key that is not used for anything else:
   ```zsh
   ssh-keygen -t ed25519 -f ~/.ssh/<target-name>_ed25519 -N ""
   ```
4. Authorize the public key on the target with the platform's standard tool, then confirm a key-only login works:
   ```zsh
   ssh-copy-id -i ~/.ssh/<target-name>_ed25519.pub <user>@<target-address>
   ssh -o BatchMode=yes -i ~/.ssh/<target-name>_ed25519 <user>@<target-address> 'echo ok'
   ```
   If the target rejects the key, read the target's authentication log before changing anything else.
5. Expose only the local services the remote agent needs, and only on the private network. Keep each service bound to loopback on its own machine, and let the private-network service mapping forward it. Use one mapping per port, and never expose a service to the public internet:
   ```zsh
   tailscale serve --bg --tcp=<port> tcp://localhost:<port>
   ```
6. From the target, confirm each exposed service answers. A health path and a model list are enough:
   ```zsh
   ssh <user>@<target-address> 'curl -sf http://<source-address>:<port>/health'
   ```

### Phase 2: Install the agent on the target
7. Install the agent runtime with the project's official installer. Read the installer before you run it, and verify a published checksum when one exists. Do not pipe an unread script into a shell on a machine that holds credentials.
8. Confirm the version on the target, from a login shell that loads the agent's path:
   ```zsh
   ssh <user>@<target-address> 'zsh -lc "hermes --version"'
   ```

### Phase 3: Create the profile
9. Create a profile named for the agent's role, and confirm its command alias works:
   ```zsh
   ssh <user>@<target-address> 'zsh -lc "hermes profile create <profile-name>"'
   ```

### Phase 4: Messaging bot
10. Create a bot for the agent through the messaging platform's bot-creation service. Give each agent its own bot, with its own token.
11. Turn off the bot's group privacy setting so it can read group messages, then remove and re-add the bot to the group, because the platform can cache the old setting.
12. Read the bot's own identifier from the platform's account-check method, and the group's identifier from an update listing. Put the token in the profile's environment file yourself. Do not paste a token into chat or into a shared document.

### Phase 5: Profile configuration
13. Write the profile's environment file with the bot token, the allowed users, and any API keys. Keep the file readable by your account only.
14. Write the profile's configuration file. The model's provider must point at the local model server, and the model name must match the server's model list exactly, including any vendor prefix the list does not show:
    ```yaml
    model:
      default: <served-model-id>
      provider: custom:<provider-slug>
      base_url: http://127.0.0.1:<port>/v1
    ```
15. Enable the memory integration in the profile's configuration, and check that the memory service answers from the target:
    ```zsh
    ssh <user>@<target-address> 'curl -sf http://<source-address>:<memory-port>/health'
    ```
16. Record configuration changes in version control, so the next change has a baseline to diff against.

### Phase 6: Gateway service
17. Install and start the gateway service through the agent's own commands, then check its status and run its doctor check:
    ```zsh
    ssh <user>@<target-address> 'zsh -lc "<profile-name> gateway install && <profile-name> gateway start"'
    ssh <user>@<target-address> 'zsh -lc "<profile-name> gateway status && <profile-name> doctor"'
    ```
    Use the service manager's own install and start commands. Do not hand-write a background process to keep the gateway alive.

### Phase 7: Delegation
18. Resolve the source machine's live configuration path with the agent's path command, then add a delegation target that names the host, port, the dedicated key, the user, and the profile:
    ```yaml
    delegation:
      targets:
        <target-name>:
          host: <target-address>
          port: 22
          key: ~/.ssh/<target-name>_ed25519
          user: <user>
          profile: <profile-name>
    ```
19. Restart the source gateway from a shell outside the gateway process, then confirm its health.

### Post-Deployment Verification
20. Send a short test message in the group the two bots share. Check the target's gateway log for receipt, and confirm the target replies.
21. Run the agent's doctor check on the source with its full option set, and confirm the delegation target appears as reachable.
22. Confirm the memory service and the local model server answer from the target. Use the health path and the model list.

### Delegated Missions
23. Write a mission that is complete on its own. The target's session starts fresh, with no context from the source session, so the mission must state the goal, the inputs, the output location, and what done looks like.
24. Verify completion where the work lands. The target's final report may be in its session files, not in a chat message. Check the session records and the deliverables on disk, and treat a chat reply as a pointer, not as proof.
25. Give the remote agent a scoped permission allowlist, so routine reads and edits run without prompts and anything outside the allowlist stops for review. A mode that skips every prompt belongs only in a disposable, isolated sandbox or worktree with no credentials or secrets. Never use it on a machine that holds credentials.

### Recovery
26. After a sleep, reboot, or network change, first find the target's current address from the private-network client. Do not reuse an address from an earlier session.
27. If key authentication fails with "too many authentication failures", the agent is offering several keys before the right one. Force the dedicated key with `-o IdentitiesOnly=yes -i <key>`.
28. After the target wakes, check the model server and the gateway. Restart each through its service manager if it is down.
29. A service manager can report a service as running while its port is closed. Check the port and the process. If the port is closed, restart the service and check the port again.
30. If the remote agent's runtime refuses a shell background wrapper, use the service manager's commands. Do not look for another way to launch the same process around the refusal.
31. A bind address that works from the local machine can still refuse the other machine. Check the bound address with the socket listing, then change the bind only as the deployment plan allows.

## Pitfalls
- **A key on the wrong account.** Authorize the key for the account the agent runs under.
- **A bot that cannot see group messages.** Check the privacy setting before debugging the agent.
- **A model name with a vendor prefix that the server does not list.** The requests fail or return empty output. Match the server's list exactly.
- **Credentials in chat.** Tokens belong in the profile's environment file.
- **Chat replies that say "done" with nothing on disk.** Check the deliverables.
- **Services exposed beyond the private network.** Keep every mapping private.
- **A cached address after a network change.** Probe for the current address.

## Verification
- The dedicated key logs in without a password prompt, and the exposed services answer from the target.
- The profile's version check, gateway status, and doctor check all pass on the target.
- The test message in the group gets a reply from the target's bot.
- A delegated mission's deliverable exists at the expected location, and the session record shows the work.
