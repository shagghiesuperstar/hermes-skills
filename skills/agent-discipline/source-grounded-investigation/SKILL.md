---
name: source-grounded-investigation
description: Use when asked what an installed tool does, where it writes, or how to remove it. Read the upstream installer source first, list the install footprint and its reseed sources, then ship a dry-run removal that backs up before it deletes.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [investigation, installers, uninstall, footprint, dry-run, provenance]
    category: agent-discipline
related_skills: [read-only-discovery, vendor-identity-verification, agent-honesty]
---

# Source-Grounded Investigation

## Overview
When the question is what an installed thing does, where it came from, or how to get rid of it, read the upstream source before inferring from local files. Local files are residue from installation. Folders get renamed, configs get merged or left partial, and paths go stale. The installer's source is the ground truth.

The common failure is matching a folder name to a conclusion. A folder named after a system looks like that system's runtime configuration, and deleting it looks safe. The folder can instead be the user's own data, linked from the install location. The folder name matched the system. The conclusion did not. The investigation should have read the installer first.

## When to Use
- "How does X work?" where X is an installed tool, framework, plugin or hook.
- "Where does X write?" or "where is X's data?"
- "How do I uninstall, remove or undo X?"
- "Why is this folder, file or config key here?"
- "A file I deleted came back. What is recreating it?"
- "Which installer placed these files?"
- "Show me the install surface so I can audit it."

### Do not use
- Debugging your own code. Use a debugging workflow on your own source files.
- Reading your own source files. Open them directly.
- Vendor support or ticket escalation.
- Rebuilding a tool from its source as a replacement for using it.

## Features
- A search for the installer in a public repository, a package manifest, a service definition or the vendor's uninstall documentation.
- A table that maps each installer action to the inverse action that undoes it.
- A distinction between additive merges and overwrites, read from the installer's own header comment.
- Two named traps: a link from the install location to user data, and an installer that only adds what is missing.
- A reseed check: the removal must also disable whatever runs the installer again.

## Benefits
- The removal list comes from the installer, not from a guess about folder names.
- User data is preserved by construction, because the data home is identified before any deletion.
- A dry run shows the plan, and the backup makes the change reversible.

## Procedure
### 1. Name the system and find its installer
Establish the real name of the system, then find its installer or deployment code.
- **Public open-source:** the repository's install script, setup file, binary directory, Makefile install target, package scripts, or Dockerfile. Fetch the raw file from the repository's default branch, or from the tagged version the user installed.
- **Packaged software:** the package's help output, the vendor's uninstall documentation, and the manifest of files the package claims to own (for example, the package manager's file-list command).
- **macOS launch agents and daemons:** list the agent and daemon folders, then read each property list to find the executable it runs.
- **Language packages:** the package's manifest lists install-time files, and its readme often describes removal.

For a system built locally, the repository the user installed from is the ground truth. Find it with a listing of likely locations.

### 2. List what the installer writes
Search the installer source for every filesystem change. Each one is a target that the removal must handle:

| Pattern in the installer | What it does | Removal target |
|---|---|---|
| Copy commands | Copies files or folders | Each source-to-destination pair |
| File write or append | Creates or extends a file | Each file path |
| Directory creation | Creates folders | Each folder |
| Symbolic link creation | Links one path to another | The link, with its target noted |
| Configuration merge | Adds keys to an existing file | Each key added |
| Background service install | Registers a launch agent or service | Each unit file |
| Dependency install | Adds packages | Each package and where it landed |

The result is a complete inventory of files, folders, configuration keys, service units and dependencies that the installer owns.

### 3. Read the header for the merge contract
Installers differ in how they treat existing content:
- **Additive merge:** adds missing keys and never overwrites a populated value. Removing the install location is often undone by nothing, because the next run finds nothing missing.
- **Overwrite:** replaces the target. The next run may reinstall the same files.

The contract is usually stated in a header comment. Read it. It tells you what the removal must keep: keys the user set, files the user added, and backup files the installer created, which are part of the install footprint.

Two traps to check for:
- **Symlink to user data.** The install location links to a data folder that belongs to the user. Remove the link and the runtime. Keep the data folder. Removing it destroys data.
- **Copy-missing semantics.** The installer copies only what is missing. Deleting the runtime and rerunning the installer then installs nothing, so the removal must not assume the installer will restore it.

### 4. Build the inverse map
For each forward action from step 2, write its inverse:
- A copy becomes a removal of the copied files that are known to belong to the installer, not the user's additions.
- A created folder becomes its removal, only when it is empty or contains only installer folders.
- A symbolic link becomes the link's removal, with the target preserved.
- A merged key becomes its removal from the configuration file, written back atomically.
- A launch agent becomes an unload followed by the removal of its property list.
- A dependency becomes its removal from the parent manifest, where that is appropriate.

If the installer ships its own uninstall command, use it, and check it against the inventory.

### 5. Ship one script that dry-runs by default
Write a single script that:
1. Prints the plan without changing anything, and applies only when given an explicit apply flag.
2. Copies everything it intends to change into a timestamped backup folder under a cache location in the user's home directory.
3. Probes the state before each step, rather than trusting a memory of it.
4. Refuses to delete an ambiguous path. If the installer code does not show whether a path is the installer's or the user's, ask first. Treat every symbolic link target as the user's until proven otherwise.
5. Verifies each step with a real probe, such as a check that the path is gone or a count of the removed key.
6. Prints a final list of changes: files removed, keys stripped, services unloaded.

Write the script to a file and run it from there. Do not pass a long script inline.

### 6. Check whether the removal will be reseeded
After removal, ask whether the thing will come back. The reseed source is separate from the install footprint:
- A scheduled job, a launch agent with keep-alive, or a repository hook that runs the installer.
- Another tool, plugin or service that calls the installer during its own setup.
- A bootstrap step that the parent tool runs when it starts or is onboarded.

If a reseed source exists, the removal must disable it too. Otherwise the user will find it back the next day.

### 7. Verify the removal
- Every installer-written path from step 2 is gone, shown by a path test.
- Every merged configuration key from step 3 is removed, shown by a count.
- The data home still exists, shown by a path test that also shows whether it is a link.
- No service from the install is running, shown by listing the service manager.
- The reseed source is disabled, and the next start of the parent tool does not run the installer.
- A final list of changes is in the reply.

### Anti-patterns
- "This folder is named after the system, so it must be its runtime configuration, and I'll remove it." The folder may be the user's data.
- "The error says a module is missing, so I'll install it." The better fix may be removing the hook that asks for it.
- "I'll search for the name and delete every match." Matching strings appear in unrelated paths.
- "I'll ask the user what to remove." The user already asked for the removal. Derive the surface from the installer code, and ask only about ambiguous paths.
- "I'll use the package manager's removal and trust it." The package manager may not know about files the user added.
- "The installer won't overwrite, so I'll delete the runtime and rerun it." Another source may rerun it without asking.

## Pitfalls
- **Folder name is not ownership.** Check what the installer actually points at before deciding a folder is runtime configuration.
- **Case matters in paths.** An installer may deploy to one capitalization and read another. Check both spellings.
- **Deletion is permanent.** Dry-run first, back up, probe the state, and never delete a path that holds the user's data.
- **The header comment is the contract.** Statements such as "never overwrites" or "data home is linked" say exactly what the removal must keep.
- **Closed-source footprints can be incomplete.** Their documented removal steps may miss files. Remove through the package manager first, then clean up what remains, checking each path.
- **The reseed source may be hidden.** A plugin that runs the installer on startup will not look like an installer in a plugin folder listing. Search its code for shell commands that fetch and run scripts.

## Verification
- The inventory from step 2 is complete, with each item tied to a line in the installer source.
- The data home was identified, and it is intact after the removal.
- The dry run was reviewed before the apply step, and the backup folder exists.
- Every probe result is in the reply, with the path, the count or the service state.
- The reseed question was answered with a source line, not a guess.
