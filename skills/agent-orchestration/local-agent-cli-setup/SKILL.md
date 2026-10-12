---
name: local-agent-cli-setup
description: Use when installing, authenticating, updating, or verifying a local AI agent CLI that works inside a project directory. Ends with a live model response, not an install command.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [agent-cli, installation, authentication, verification, updates]
    category: agent-orchestration
related_skills: [cursor-agent-cli, codex-cli-integration, grok-build, claude-cli-model-switching]
---

# Local Agent CLI Setup

## Overview
A local agent CLI runs a coding or analysis agent inside a project directory. A usable setup is not an installed binary. It is a binary that resolves on the path, reports the expected product, is signed in through the tool's own flow, and returns a real model response from inside the project. This skill covers each stage in order, the checks that prove each one, and the traps that make a setup look finished when it is not.

## When to Use
- Installing a new agent CLI on a machine, or moving one to a new machine.
- Signing in an installed CLI, or repairing a sign-in that stopped working.
- Updating one or more installed CLIs, and checking that the update took effect.
- Preparing a CLI for a headless run that a scheduler or worker will start.

Do not use this skill to write a new CLI application, or to delegate a coding task to a CLI that is already configured.

## Features
- A pre-install check of the existing command, its version, the platform, and the project directory.
- A validated installer path: download, inspect, record a checksum, then run.
- A verification chain from binary to sign-in to a sentinel reply inside the project.
- An update procedure with a fixed order, a before-and-after version check, and a shadow-install check.
- Rules for headless runs, delegated edits, and secrets handling.

## Benefits
- Setups are proven by a live response, so a broken sign-in is found before a real task depends on it.
- A downloaded installer is read before it runs, which catches unexpected install paths and profile edits.
- Host configuration is snapshotted before an installer changes it, so a change can be reviewed and reversed.
- Shadowed installs, which are a common cause of "the update did not take," are caught by checking the path.
- Secrets never appear in a status report or a verification transcript.

## Procedure
1. Check what already exists, without changing anything:
   ```bash
   command -v "<cli>"
   "<cli>" --version
   uname -sm
   ls -d "<project-dir>"
   ```
   Note whether the command exists, its version, the platform, and whether the project directory exists. Read the CLI's own status command for the sign-in state, and do not open any credential file.
2. Install from the vendor's documented HTTPS endpoint. When the vendor offers a shell-script installer, do not pipe it straight into a shell. Save it to a temporary file, record its size and checksum, read it, and check its download hosts, install paths, profile edits, and how it handles credentials. Run the saved file only after its behavior matches the scope you were given.
   ```bash
   curl -fsSL "<vendor-install-url>" -o "<tmp-dir>/installer.sh"
   shasum -a 256 "<tmp-dir>/installer.sh"
   ```
3. Snapshot every host configuration file the installer may change before you run it. Copy each file to a dated backup folder. After installation, compare the live files with the snapshot, and do not rely on memory for the claim that nothing else changed.
4. Verify the install with actual commands:
   - the command resolves on the path in a fresh shell;
   - the version command exits successfully;
   - the help output names the expected product;
   - the vendor's own diagnostic command passes. Separate blocking failures from optional warnings, such as an unavailable voice feature.
5. Sign in through the tool's supported flow. Check the sign-in state with a harmless command, such as listing models or reading account status. If the state is signed out, start the vendor's login flow. Let the user complete any browser step. Keep the login process running until its callback finishes, then check the sign-in state again.
6. Verify inside the target project, using two non-destructive checks:
   - inspection: confirm the working directory, the repository root, the trust status, and any project instruction files the tool discovers;
   - a bounded smoke test: one headless turn that forbids file inspection, file changes, and tool calls, and asks for an exact sentinel reply.
   ```bash
   "<cli>" --cwd "<project-dir>" --max-turns 1 -p "Reply with exactly AGENT_CLI_READY. Do not inspect or modify files, and do not run tools."
   ```
   The setup is complete only when the binary, the sign-in, the project discovery, and the sentinel reply all pass.
7. For a headless run from a scheduler or a worker, use the tool's explicit one-shot flag rather than a positional prompt, which can open the full-screen interface. Run in the foreground with a generous timeout. Preserve the exit status and the complete output. Leave code changes uncommitted, so the parent can read the diff before anything is committed.
8. After any delegated edit, check the diff, the tests, and the generated artifacts yourself. Then have a fresh-context reviewer read the result before a consequential step, and fix and review again if the reviewer rejects it.
9. Update installed CLIs only when the operator asks for it, in a fixed order, and check each one afterward. Pin a version whenever the tool allows it, and do not accept an update prompt on the operator's behalf:
   - use the tool's own update command where it has one, for example `claude update` or `cursor-agent update`;
   - where a package manager installs the tool, update it to a pinned version with that manager, for example `npm install -g <package>@<pinned-version>`;
   - skip any CLI that is busy with a running process, and report it as skipped;
   - for a deprecated CLI, report it as deprecated and do not update or rely on it.
   Compare the version before and after each update, and run `command -v` to confirm the path that now resolves.
10. Expose the CLI to the agent platform as a provider only when the goal requires it. Bind any local shim to the loopback address only. Never make the shim the default model, and never add it to a fallback chain, unless the operator explicitly asks for that.

## Pitfalls
- **A successful version check is not a sign-in.** Confirm the sign-in with the status command, then with a live reply.
- **A headless smoke test can pass while the surrounding integration is broken.** When a hook or plugin is involved, check the full chain: the hook fired for the right session, the reply reflects the expected content, and any stored record exists. A hook that fires while the model sign-in is broken proves only the hook.
- **Do not print credential fields when you verify a configuration file.** Drop the credential fields before any output. Otherwise the verification transcript itself leaks the credential.
- **Do not source an environment file just to test whether a key exists.** Ask the tool's status command instead.
- **Do not download and run an installer in one step.** Save it, read it, and then run it.
- **A shadowed install makes an update look like it failed.** Two installs on the path can both be real, and the one that runs is the one that resolves first. Check `command -v` after the update.
- **Some vendor flags differ by product.** An option that makes an installer skip its launch step is named differently in each tool. Read the help output before you use it.
- **An unattended installer that waits for a terminal or a browser strands the run.** Choose the non-interactive option the help text lists, and stop if none exists.
- **Harness restarts belong to the operator.** A new tool integration usually appears only after the session restarts, so tell the operator when a restart is needed.
- **A tool that discovers its servers at startup will not show a server added mid-session.** Say so in the report.
- **Some diagnostics need a real terminal.** When a command refuses to run without one, give the operator the one-line command to run themselves, and do not report the setup as blocked.
- **Do not run two editing agents in one working tree.** Confirm the earlier process has stopped before a retry.
- **Re-test a model before you trust a note about its quota.** A stale quota note can quietly downgrade every later model choice.

## Verification
- `command -v "<cli>"` resolves to the expected path in a fresh shell, and the version command succeeds.
- The sign-in status command reports signed in, with no account identifiers printed.
- The sentinel reply appears exactly, from inside the target project.
- The host configuration diff against the snapshot shows only the changes the installer was expected to make.
- After each update, the version is newer, and the resolved path is the one that was updated.
- The setup report lists the version, the binary path, the sign-in result without secrets, the project status, the smoke-test output, and any optional warnings separately.
