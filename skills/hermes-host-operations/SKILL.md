---
name: hermes-host-operations
description: Use when operating a Hermes agent host day to day. Covers safe updates, backed-up config edits, provider fallback chains, credential handling, and checking which file a live service reads.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, operations, config, fallback, credentials, updates, host]
    category: fleet-infrastructure
related_skills: [hermes-multi-machine-deployment, multi-mac-fleet-ops, infrastructure-guardian-agent]
---

# Hermes Host Operations

## Overview
A Hermes host runs an agent gateway, one or more profiles, a configuration file per profile, credentials in environment files, and sometimes a local model server. Day-to-day work is mostly small, reversible changes: update the runtime, change a fallback chain, add a provider, rotate a key, check that a change reached the live service. The failure modes are equally small and quiet: an edit that the live process never reads, a key that is present but unused, a fallback chain that points at a provider with no credentials, and a plaintext secret left in a file. This skill sets a consistent discipline for each of those tasks.

## When to Use
- The runtime needs an update, and local changes must survive it.
- A profile's model or fallback chain must change on one host or on all profiles.
- A provider was added, removed, or failed, and the chain needs review.
- A credential must be added, rotated, moved to a secrets manager, or checked.
- A change was made to a file, and you need to confirm the live service actually uses it.

## Features
- A non-interactive update path that keeps local changes, followed by migration and health checks.
- A config-edit procedure: backup, structured edit, re-parse, and a live check.
- A fallback-chain procedure with a pre-flight check of the local model server and a per-profile credential check.
- Credential checks by source name only, never by value.
- Guidance for custom providers, whose presence in a status listing is not proof they work.
- A procedure for finding which configuration file a running process actually loads.

## Benefits
- Updates do not discard local edits, and a broken update is easy to spot.
- Every edit has a backup, a parse check, and a live check.
- Fallback chains only name providers that can actually answer.
- Secrets stay out of configuration files, shell history, and chat.

## Procedure
### Update the runtime
1. Run the update with the operator present, so each prompt is read before it is answered. The update path stashes local changes before pulling and restores them afterward. Then run the configuration migration and the health check, and restart the gateway in a quiet period:
   ```zsh
   hermes update
   hermes config migrate
   hermes doctor
   hermes gateway restart
   ```
   Do not add `--fix` to `hermes doctor` in a default run. Read the findings first, then apply each repair the operator approves.
2. Plan the update for an off-hours window that the operator names. The gateway restart drops messaging for a short time. A scheduled job may only check for and report available updates. Applying an update waits for the operator's go-ahead naming this host and window, and a backup taken before the run. Once approved, run the deterministic steps from a script, not a model call.
3. If the update leaves local changes in conflict, stop and show the conflicts to the operator. Do not choose a side without them.

### Edit configuration safely
4. Back up the file with a timestamp before the first edit:
   ```zsh
   cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak_$(date +%Y%m%d_%H%M%S)
   ```
5. Edit structured files with a parser, not with text substitution. For YAML use a YAML library, and for JSON use a JSON library. Write the file back with the same indentation.
6. Re-parse the file and check the changed keys. Then check the live service: the process should read the new value after its next restart, and the health endpoint should still answer.
7. For an oMLX settings file, use the same discipline: back up, edit with a JSON parser, read back the one entry you changed.

### Set a fallback chain
8. Pre-flight the local model server first. Confirm that it lists its models, and send a one-token chat request to confirm that one of them answers. Do not build a chain around a server that does not answer.
9. Back up every profile's configuration file before you change any of them. Keep the backups in one dated folder, with the profile name in each file name.
10. For each profile, confirm that the credential each chain entry needs is present. Check the profile's environment file and then the host's shared environment file, and report the source name only. A missing credential fails the check loudly.
11. Set the chain as an ordered list. The first entry is tried when the primary fails with a rate limit, a server error, or a connection error. An empty list means the primary only.
12. Remove providers that have no working credential from the chain, rather than leaving them as dead hops.
13. Verify each profile: confirm the chain in the parsed file, and send one request through the primary path and one through a fallback entry where possible.

### Credentials
14. Keep secrets out of configuration files, command lines, shell history, and chat. Read them into environment variables from a secrets manager or from a restricted environment file, and never print the value.
15. Check whether a provider can be used by its configuration block, not by its line in a status listing. The status listing shows only the built-in providers. A custom provider appears in the configuration's provider block and has no row in the listing, so its absence there does not mean it is unusable.
16. After a credential is added to an environment file, restart the gateway so the process environment picks it up. A restart alone does not add a provider entry to the configuration. If the entry is missing, add it, then restart.
17. To move a plaintext key into a secrets manager, check first whether the secret already exists, read the value from the file into a variable without echoing it, create or edit the secret, and read it back to confirm the length or a hash matches. Then, after a backup and the operator's approval, remove the plaintext copy from the file.
18. Rotate a key by adding the new value, checking it with one request, switching the consumers, and only then revoking the old value.

### Local ports and services
19. Keep a list of the local ports each service uses, and check that no two services claim the same port. A port that answers from a different service than the one you expect is a conflict.
20. Check a browser-driven tool's dependencies before relying on it. A browser automation tool needs a browser binary on the host, and its failure message can be generic.

### Second-opinion model lanes
21. Add a second-opinion model for one role, not as the default for everything. Wire it through the role's own configuration, run a smoke call before it is used, and record which role it serves.

### Find the file a live service loads
22. Read the serving process's full command line from the process list, and find the profile flag or configuration path in it. Then confirm in the runtime's documentation or source which file that path resolves to. A file of the same name in the root folder can be inert for a profile-scoped process.
23. A file change is live only after the process that reads it restarts, or after a reload the runtime documents. Check the process start time against the file's modification time.

## Pitfalls
- **Editing a file the live process never reads.** Check the process's command line first.
- **Text substitution on structured files.** It breaks indentation and quoting. Use a parser.
- **A key present in the environment file but unused.** Check the provider block and restart the gateway.
- **A fallback chain with an unreachable provider.** Each dead hop costs a failed request before the next one runs.
- **Trusting the status listing for custom providers.** Check the configuration block.
- **Secrets printed in logs or transcripts.** Use variables, and check output before sharing it.
- **Skipping the backup because the edit is small.** The backup is the only undo.
- **Routing around a network restriction.** If a host cannot reach a source, fetch the artifact through an approved channel, or ask the operator to allow the connection. Do not route around the restriction with a mirror or proxy.
- **A restart during active work.** Restart in a quiet period, and tell the operator when messaging will drop.

## Verification
- Every changed file has a dated backup, and its parsed value matches the intended change.
- The live process was restarted after the change, and its health endpoint answers.
- Each fallback chain names only providers that answered a test request during the change.
- No secret value appears in the files you changed, in the report, or in the transcript.
