---
name: memory-stack-snapshot
description: Use when snapshotting a Hermes memory stack. It covers profile state, Hindsight native state, the Omega SQLite store, the Graphiti MCP configuration and source, and the Neo4j graph, and restoring is covered too. Verify each layer before relying on the snapshot.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [backup, snapshot, restore, memory, hindsight, graphiti, neo4j]
    category: memory-knowledge
related_skills: [hindsight, triple-threat-memory, graphiti-memory]
---

# Memory Stack Snapshot

## Overview
A memory stack has several layers that each keep state in a different place: the agent profile, a Hindsight daemon's native data, an Omega database (a local semantic index stored in SQLite), a Graphiti server and its configuration, and a Neo4j graph. A snapshot captures all of them in one dated folder, with checksums and a manifest. Use it before risky memory or MCP changes, and copy it off the machine, because a copy on the same disk is only a rollback point.

The snapshot script is not bundled with this library. It is operator-provided, and the steps below describe what a correct snapshot must contain and how to check it.

## When to Use
- Before changing memory infrastructure, MCP configuration, or a Hindsight setting.
- Before moving a profile to another machine.
- After a change, to record a known-good state.
- When restoring a memory stack after a failure.

## Features
- A profile-neutral layout, so the path does not depend on a user name or profile name.
- A capture list covering each memory layer, with a manifest that reports each layer's status.
- Checksums for every archive, plus integrity checks on the Omega database and the Neo4j counts.
- A restore outline that backs up current state first and stops services before replacing live data.
- A verification step that the operator runs before trusting the snapshot.

## Benefits
- Each layer is checked separately, so a failed layer is named.
- A restore starts from a known state, and the current state is kept as a fallback.
- Profile and host details are read from the running environment, not hard-coded.

## Procedure
### 1. Determine the active profile from the environment
Do not hard-code a profile name or a home path in commands. Ask the Hermes CLI where the active configuration and environment files are:
```zsh
hermes config path
hermes config env-path
```
Use the profile name these paths reveal in the snapshot folder name.

### 2. Choose a backup root outside the working disk
Use an external or network volume reserved for backups, for example `<backup-root>`. The snapshot layout is:
```text
<backup-root>/memory-stack/<host>/<profile>/<timestamp>/
```
Keep the timestamp in UTC so that snapshots sort in order.

### 3. Create the snapshot
Run the snapshot script from the profile's Hermes environment, so the configuration paths resolve correctly. Give it the backup root and a label:
```zsh
python3 <snapshot-script> --dest <backup-root> --label memory-stack
```
For a different profile or machine, do not edit the script. Launch it from that profile's environment.

### 4. Confirm the capture list
A complete snapshot contains each of these:
- **Hermes state.** The official quick state archive, the configuration file, the environment file, the agent instruction files and the wrapper scripts.
- **Hindsight native state.** An archive of the profile's Hindsight data folders, when they exist.
- **Omega store.** A SQLite backup made with the database's backup interface, and an integrity-check file whose content must be `ok`.
- **Graphiti.** An archive of the MCP server source and configuration, excluding virtual environments, version-control folders and caches.
- **Neo4j.** Node and relationship count files containing numbers, a logical export, and optionally an archive of the data folder.
- **Metadata.** A `manifest.json` with each layer's status, a `SHA256SUMS.txt`, a restore README, and a verification log with the memory status command output, the MCP test results and an HTTP probe of Neo4j.

### 5. Verify the snapshot before relying on it
```zsh
cd "<snapshot-folder>"
shasum -a 256 -c SHA256SUMS.txt
tar -tzf hermes/hermes-state-snapshot-*.tar.gz >/dev/null
tar -tzf hindsight/hindsight-native-state-*.tar.gz >/dev/null
tar -tzf graphiti/graphiti-mcp-source-config-*.tar.gz >/dev/null
cat omega/integrity_check.txt
cat neo4j/node-count.txt
cat neo4j/relationship-count.txt
```
Pass criteria:
- Every checksum reports OK.
- The Omega integrity check reads `ok`.
- Every archive lists its contents without error.
- The Neo4j count files exist and contain numbers.
- The manifest reports `ok: true` for the Hermes state, the Hindsight state, the Omega database, the Graphiti source and configuration, and the Neo4j export.

### 6. Restore only in this order
1. Back up the current state before restoring anything. A restore that fails halfway must leave a way back.
2. Stop the memory services before replacing live data.
3. Restore the Hermes state using the snapshot ID in `manifest.json`. A quick state snapshot can print its ID instead of writing an archive to the path you gave, so record that ID.
4. Unpack the Hindsight archive into the profile's home folder.
5. Copy the Omega database into the profile's Omega folder.
6. Unpack the Graphiti archive under the same user home, and restore the wrapper scripts if they are needed.
7. Restore Neo4j only while the database is stopped. Use the data archive, or re-import the logical export. Never overwrite the physical data of a running database.
8. Start the services and test each memory layer on its own.

## Pitfalls
- **Full backups can be very large.** A full archive can include backup folders by accident, so do not rely on one unless its archive test passes.
- **A same-disk copy is not disaster recovery.** Copy the snapshot off the machine.
- **Live Neo4j data.** Overwriting the physical files of a running database corrupts them.
- **Assumed paths.** Do not assume a user name or profile name on another machine. The script reads the active profile.
- **Trusting a snapshot without checks.** A snapshot folder that exists is not proof that the archives open or that the counts were captured.

## Verification
- Every checksum in `SHA256SUMS.txt` reports OK, and every archive lists its contents without error.
- The Omega integrity check reads `ok`, and the Neo4j count files contain numbers.
- The manifest reports `ok: true` for each layer.
- A restored stack passes each memory layer's own test. The snapshot check alone does not prove the restore worked.
