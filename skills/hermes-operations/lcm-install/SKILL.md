---
name: lcm-install
description: Use when installing or repairing a lossless context-engine plugin for Hermes. Covers the three activation steps, registration checks and compaction tuning.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [lcm, context-engine, plugin, compaction, install, lossless-context]
    category: hermes-operations
related_skills: [hermes-architecture-reference, hermes-gateway-ops]
---

# Lossless Context Engine Install

## Overview
A lossless context engine compacts a long conversation into searchable summaries and keeps the originals reachable for
expansion. It is a plugin, and it activates only when three things are all true: the plugin is installed into the same
Python environment the Hermes launcher runs, the context-engine setting names it, and the plugin is enabled. Missing any
one of them fails silently, because Hermes then runs with its stock context engine. This skill gives the install order,
the checks that prove registration, and the tuning steps for a session that cannot compact.

The plugin used in this skill is the open-source `lossless-hermes` project (see Attribution). Check its current install
instructions before you run them, because they can change.

## When to Use
- You want long sessions compacted losslessly, and the plugin is not installed yet.
- The context-engine tools are missing, or the engine seems inactive after a clone.
- A session fails with a "cannot compress further" message, and compaction never runs.

## Features
- Install order that puts the plugin into the launcher's own environment before enabling it.
- Config step through the Hermes command, never by hand edit.
- Registration check in the agent log, with a timestamp after the restart.
- Tool check in a new session.
- Tuning rules for a session that fails to compact, with the trigger point read from the log.

## Benefits
- Activation is proven from the log, not from the success message of an install command.
- A plugin installed into the wrong environment is found before the restart.
- Compaction problems are diagnosed from the real trigger point, not from a status readout alone.

## Procedure
1. Resolve the Hermes home and the interpreter the launcher runs. Do not assume a generic virtual environment path:
   ```bash
   echo "${HERMES_HOME:-$HOME/.hermes}"
   head -1 "$(command -v hermes)"
   ```
   The interpreter named on the first line is the one the plugin must be installed into.

2. Back up the active config file before any change:
   ```bash
   cp <hermes-home>/config.yaml <hermes-home>/config.yaml.bak_$(date +%Y%m%d_%H%M%S)
   ```

3. Install the plugin with the Hermes plugin command. If it does not install into the launcher's environment, install into
   that interpreter explicitly. A Hermes virtual environment can lack a `pip` binary, so use `uv`:
   ```bash
   hermes plugins install <plugin-repo>
   uv pip install --python <launcher-python> -e <plugin-path>
   <launcher-python> -c 'import lossless_hermes; print("ok")'
   ```

4. Set the context engine through the config command, never by hand edit:
   ```bash
   hermes config set context.engine lossless-hermes
   hermes config get context.engine
   ```

5. Enable the plugin after the install, because enabling before the install silently does nothing. Re-run the enable
   command if an earlier attempt ran first:
   ```bash
   hermes plugins enable lossless-hermes
   hermes plugins list
   ```
   If enabling asks for permission to override built-in context tools, stop and report that prompt to the operator. The
   plugin is replacing built-in tooling, so the operator decides whether to grant it.

6. Restart the gateway from an operator shell, not from a session the gateway hosts. The restart is a separate step the
   operator runs. Then start a new session, because a session binds its context engine when it starts, and older
   sessions keep the old one.

7. Verify registration from the log, after the restart:
   ```bash
   grep "context engine" <hermes-home>/logs/agent.log | tail -5
   ```
   The line that proves registration names the plugin and the engine, and it must carry a timestamp after the restart.

8. In the new session, confirm that the context tools are listed, and that the state tool returns without error.

### Tuning a session that cannot compact
- The message "context length exceeded, cannot compress further" usually means the engine has nothing to compact into.
  Check the engine's depth, the number of recent messages it protects, and the size of its leaf chunks. A setting that is
  too conservative for a small window leaves no summary levels to climb.
- Read the actual trigger point from the gateway log, not only from the status tool. The status tool can report a
  threshold from an older configuration. Look for the line that says how many messages and tokens triggered compaction,
  and what threshold it used.
- Change the knobs through the config command, and use the names the installed version documents. Names differ between
  versions, so check the plugin's own help or documentation first. Do not guess a name, because an unknown name is
  silently ignored.
- As an example of the shape of a fix: a trigger at a lower fraction of the window, a smaller number of protected recent
  messages, and one more summary level. Confirm the new trigger point in the log on the next long session.

## Pitfalls
- **Install and runtime Python must match.** A plugin installed into a different interpreter registers nothing.
- **A clone alone registers nothing.** Hermes discovers the plugin through its installed package metadata, not by
  scanning a folder.
- **Never claim the engine is active from the install or enable output.** Only the log line after a restart proves it.
- **Old sessions keep the old engine.** Start a new session after the restart.
- **Do not change model or provider overrides for the engine by default.** The engine should inherit the host agent's
  model and provider unless the operator approves an override.
- **Keep the gateway restart with the operator.** An agent session hosted by the gateway cannot restart it.
- **Redirected home paths can send a write to the wrong file.** When a shell's home directory is redirected, a write to
  the home path can land in another folder, and the real config is unchanged. Write with absolute paths, and check
  that the real file changed.
- **Check the config through the command after any change.** A value set with the command is stored with the right type.
  A hand edit can store a number as text.

## Verification
- The launcher's interpreter imports the plugin package and prints ok.
- `hermes config get context.engine` returns the plugin's engine name.
- `hermes plugins list` shows the plugin as enabled.
- The agent log shows a registration line dated after the restart.
- A new session lists the context tools, and the state tool returns without error.
- On a long session, the compaction trigger in the gateway log matches the configured threshold.

## Attribution
The `lossless-hermes` plugin is an open-source project by its own maintainers, at
https://github.com/mssteuer/lossless-hermes-py. This skill covers only the install order, the registration checks and
the tuning steps.
