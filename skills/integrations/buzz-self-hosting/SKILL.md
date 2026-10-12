---
name: buzz-self-hosting
description: Use when setting up or debugging a self-hosted Buzz relay with Docker Compose. Covers the hostname rules, membership roster, domain changes, layered agent debugging and backups.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [buzz, self-hosting, relay, docker, compose, nostr, troubleshooting, backups]
    category: integrations
related_skills: [hermes-in-buzz, hermes-gateway-ops]
---

# Buzz Self-Hosting

## Overview
Buzz is a chat system whose relay routes each connection to a community by the hostname it was addressed with. A
self-hosted relay runs as a Docker Compose stack: the relay, a Postgres database for events and memberships, an object
store for media, and a Redis instance for live fan-out. Most failures come from a few traps: a hostname the relay does
not route, a membership roster that is missing an agent, or a domain change that starts a new empty community. This
skill covers the setup order, those traps, a layer-by-layer way to debug an agent that does not respond, and backups.

Guide the operator through steps that change state: give them the exact commands and let them run those. Run read-only
checks yourself, such as log reads and roster listings.

## When to Use
- You are standing up a Buzz relay for a person or a team, with Docker Compose.
- A client or an agent reports "relay down", a 404 on connect, or an agent that never answers.
- You are changing the public domain of an existing relay.
- You need to back up or migrate a relay.

## Features
- Setup order for the environment file, the URL block, the start command and the liveness check.
- Membership roster rules for humans and agents on a closed relay.
- Hostname rule for local deployments, with a direct routing test.
- Layered debugging table for agents, from connection to model authentication.
- Verification queries that prove data is stored locally.
- Backup steps for the database, the object store, and the environment file.

## Benefits
- A relay that routes wrongly is found by a single handshake test, not by guesswork.
- Agents stop sitting idle, because each layer is checked in order.
- A domain change is treated as the new-community event it is, before anyone loses channel data.
- Backups include the environment file, so restored data is usable.

## Procedure
1. Prepare the environment file from the example file. Generate every secret locally with a random generator. Do not
   copy a secret from another deployment. Set the owner's public key in the variable the stack expects, with the exact
   name, because similar names are easy to mix up. Back up the environment file, because the relay's identity key and
   the signing secret live there.

2. Pin the image to a release tag for any long-lived deployment. A moving tag changes under you.

3. Set the URL values from one host choice: the relay domain, the client connection URL, the media base URL, the media
   domain and the allowed browser origins. Choose the host before you start, because a later change re-keys the
   community (see Pitfalls).

4. Validate the configuration, then start the stack. Use the TLS option only for a public domain:
   ```bash
   ./run.sh config
   ./run.sh start
   curl -fsS http://127.0.0.1:<port>/_liveness
   ```

5. Register every human and every agent on a closed relay. Add a short pause between adds, because two roster events in
   the same second can collide. Confirm the roster:
   ```bash
   ./run.sh add-member <pubkey>
   ./run.sh list-members
   ```

6. Connect the client with the exact connection URL from step 3. Create channels, add the agents to them, and mention
   them to test.

### Debugging Agents That Do Not Respond
Check the layers in this order. Read the newest agent run log, because an old error banner in the client can describe a
failure that has already been fixed.

| Log symptom | Layer | Fix |
|---|---|---|
| Connection refused with a 404 on connect | Hostname routing | Use `127.0.0.1` everywhere, and recheck the routing test |
| Connected, but the agent is missing from the roster | Relay membership | Add the agent to the roster |
| Zero channels discovered | Channel membership | Add the agent to a channel, confirm the membership event arrives, and re-add the community if the client disagrees with the relay |
| Channels discovered and subscribed, but mentions are ignored | Response rule | The default response rule may answer only the owner. Check the agent's rule |
| Wakes up, then errors instead of replying | Model authentication | Check the runtime's own credentials. The relay plumbing is fine |

A healthy sequence in an agent log runs: connected to the relay, discovered channels, subscribed to each channel. New
channel additions appear as subscription notices.

### Shell Notes
- A script written for bash must run under bash. In a PowerShell session it opens in an editor instead of running. Use a
  bash shell, or run the script with `bash`.
- Some Git Bash installs rewrite container paths into host paths, and the container command then fails. Set the path-conversion
  switch off for that command, or run container commands from PowerShell.
- On Windows, file-name extensions may be hidden, so an environment file can look nameless. Turn extensions on to see it.
- If the desktop client will not launch, check for hung instances and stop them before you retry.

### Backups
The database and object-store volumes live inside the container runtime's disk, so a plain file backup does not reach
them. Dump them to real files, and keep the environment file alongside:
```bash
cp .env <backup-dir>/env-backup.txt
chmod 600 <backup-dir>/env-backup.txt
docker compose --env-file .env -f compose.yml exec -T postgres pg_dump -U <db-user> <db-name> > <backup-dir>/db.sql
```
Archive the object-store and git volumes the same way, with a throwaway container that mounts each volume and the backup
folder. Restoring the data without the environment file restores nothing, because the keys live there.

### Migrating From a Hosted Community
There is no export tool. A person's identity key moves with them. Agent definitions are local files. Git repositories can be
cloned from the hosted community and pushed to the new relay. Channel history, direct messages, media and canvases do not
move. A new relay starts empty, so set that expectation before anyone removes the hosted community.

## Pitfalls
- **Use `127.0.0.1` everywhere for a local relay, not `localhost`.** The client rewrites loopback names to the numeric
  address before it starts an agent, but the relay routes by the literal domain. A domain of `localhost` then returns 404
  to every agent, while the client connects fine.
- **A connection with the wrong hostname gets a 404 on the upgrade request.** It looks like "relay down", but the relay is up.
  Test the routing with a WebSocket upgrade request to the host you intend. A status of 101 means good, and 404 means wrong host.
- **Changing the domain starts a new, empty community.** The relay keys its community to the domain. After a change, the
  client may keep showing the old channels and members from its cache, and messages may still send. Channel and membership
  records do not exist on the relay. Remove the community in the client and add it again, then create channels afresh.
- **Check server-side events, not the client screen.** Creating a channel and adding a member should produce matching
  events in the relay log. If the client says a change happened but the log shows no matching event, the client state is stale.
- **Protect agent key files.** An agent directory may hold plaintext private keys in its runtime records. Treat those files
  as secrets, and never paste them into chat.
- **Expose admin surfaces only on a private machine.** A development overlay can publish the database and cache ports.
  Turn it on only where that exposure is acceptable.
- **Keep the database and object store as the record.** The cache is disposable.

## Verification
- The liveness endpoint answers, and the routing test returns 101 on the intended host.
- The roster lists every human and every agent that should connect.
- A test message in a channel appears in the database query for recent messages.
- An agent's log shows the connected, discovered and subscribed sequence after a restart.
- A backup dump file exists, is not empty, and is restored to a scratch environment before you rely on it.
