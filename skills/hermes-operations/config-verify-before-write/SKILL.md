---
name: config-verify-before-write
description: Use when a script is about to write a Hermes config file. Covers the verification ladder that proves a write is needed and correct.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, config, verification, safety, yaml, profiles]
    category: hermes-operations
related_skills: [hermes-architecture-reference, hermes-config-revert-restore]
---

# Verify Before Write: Hermes Config Edit Procedure

## Overview
Config edits fail when verification uses loose checks: a regex over the whole file, a truncated read, or an unverified
CLI result. The script then reports a success that did not happen, or an edit lands in the wrong block. This skill is a
fail-closed ladder: back up, confirm the backup, parse the file structurally, match exact bytes, check the diff, write
atomically, then read back and compare every key. Any failed assertion halts the work and reports the state.

## When to Use
- A script is about to mutate `config.yaml`, a profile `.env`, a persona or instruction file, or any other Hermes state file.
- A CLI write (for example `hermes config set`) returned something ambiguous, such as a list stored as a string.
- You need to add or remove a toolset, MCP server, provider or cron entry in a profile config.
- A previous edit "worked" according to a script, but the live behavior did not change.

## Features
- Nine-step ladder: backup, byte-identity check, structural parse, exact-byte match, scoped diff, atomic write,
  post-write byte check, key-by-key readback, then service restart and re-read.
- Backup names that keep the full original filename and extension.
- Assertions on parsed YAML or JSON structure instead of substring or regex matches.
- Byte-identity comparison for protected blocks.
- Guidance for files that a running daemon holds in memory and for versioned service keys.

## Benefits
- Mistakes are caught before a service reads the file.
- Unintended changes to unrelated top-level keys are detected immediately after the write.
- Every write has a byte-identical backup to roll back to.
- Partial failures are reported as partial, not as "all steps complete."

## Procedure
Run the steps in order. Every `assert` must fail closed: halt, report, and do not patch around it.

1. Back up with a name that keeps the original filename:
   ```python
   import shutil
   from datetime import datetime, timezone
   from pathlib import Path

   CFG = Path.home() / ".hermes/profiles/<profile>/config.yaml"
   TS = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
   BAK = CFG.parent / f"{CFG.name}.bak-<reason>-{TS}"
   shutil.copy2(CFG, BAK)
   assert BAK.exists(), f"FATAL: backup missing at {BAK}"
   print("backup:", BAK)
   ```

2. Confirm the backup is byte-identical to the live file:
   ```python
   import hashlib

   def md5(p: Path) -> str:
       return hashlib.md5(p.read_bytes()).hexdigest()

   md5_pre = md5(CFG)
   assert md5_pre == md5(BAK), "FATAL: backup is not byte-identical to source"
   ```

3. Parse the whole file and assert on the exact key you are changing:
   ```python
   import yaml

   parsed = yaml.safe_load(CFG.read_text(encoding="utf-8"))
   toolsets = parsed.get("toolsets")
   assert isinstance(toolsets, list), "FATAL: top-level toolsets is not a list"
   assert "<item>" not in toolsets, "noop: <item> already present in top-level toolsets"
   ```
   If the change may also touch a nested block (for example a per-platform toolset list), parse that block too.

4. If you patch text, match the exact bytes and require exactly one match:
   ```python
   text = CFG.read_text(encoding="utf-8")
   old_block = "<exact bytes, including indentation and trailing newline>"
   occurrences = text.count(old_block)
   assert occurrences == 1, f"FATAL: old_block matched {occurrences} times, expected 1"
   ```

5. Build the patched text and check that only the intended lines were added:
   ```python
   new_block = "<replacement bytes>"
   patched = text.replace(old_block, new_block, 1)
   original_lines = text.splitlines(keepends=True)
   added = [line for line in patched.splitlines(keepends=True) if line not in original_lines]
   assert added == ["<expected added line>\n"], f"FATAL: unexpected added lines: {added!r}"
   ```

6. Write atomically. A temp file in the same directory followed by a rename is atomic on POSIX:
   ```python
   tmp = CFG.parent / f"{CFG.name}.tmp"
   tmp.write_text(patched, encoding="utf-8")
   tmp.replace(CFG)
   ```

7. Check the bytes after the write:
   ```python
   assert md5(CFG) != md5_pre, "FATAL: live file unchanged after write"
   assert md5(BAK) == md5_pre, "FATAL: backup changed; it must stay the pre-write original"
   ```
   Run this before any next edit in the same script.

8. Read back the parsed structure and confirm only the targeted key changed:
   ```python
   after = yaml.safe_load(CFG.read_text(encoding="utf-8"))
   for key in set(parsed) | set(after):
       if key != "<targeted-key>" and parsed.get(key) != after.get(key):
           raise AssertionError(f"FATAL: unexpected top-level key changed: {key}")
   ```

9. If the setting is held by a running service, stop the service, edit, start it, and re-read the value after the
   restart. Use the service manager for your OS (`launchctl bootout` and `bootstrap` on macOS, `systemctl --user` on
   Linux). A readback before the restart proves only that the file was written.

## Pitfalls
- **Assert on the parsed structure, never on a substring.** A regex for `- kanban` matched a per-platform override
  while the top-level `toolsets:` list did not contain it. The script reported "already present" for an edit that
  never happened.
- **Scope every check to the exact key.** A whole-file match or a truncated `cat` can show a line that belongs to a
  different block. Load the whole file with a parser.
- **Do not build backup names with `with_name(stem + ...)`.** On `SOUL.md` it produces `SOUL.bak-...md`. Append the
  suffix to the full name instead, as in step 1.
- **Compute the timestamp once per workflow.** A multi-file edit split across separate runs gets a new timestamp each
  time, so the second run cannot find the first run's backup. Pass one timestamp through an environment variable, or
  glob for `*.bak-<reason>-*` and take the newest match.
- **Never wrap a write in `try/except` and continue.** A swallowed crash makes the report read "all steps complete" when
  only the first step ran. Let asserts propagate, verify after each atomic write, and report partial state explicitly
  with the path of each backup.
- **Copy before you swap.** `Path.replace()` is a rename, not a copy. Using it to stage a backup moves the live file
  away, and the "new" content can end up overwriting the only original. Back up with `shutil.copy2`, then swap a
  `.tmp` file into place.
- **Do not trust a CLI success message.** `hermes config set` with a list can store a string. Parse the file after every
  CLI write and check the type.
- **Do not edit state that a running daemon holds in memory.** A gateway that flushes session routing state to its
  database on shutdown overwrites a direct edit on the next restart. Stop the daemon first. An agent running inside the
  gateway cannot stop it, so hand the edit to the operator as a one-shot script run from a separate shell.
- **Do not trust `HERMES_HOME` inside Hermes shells.** It can point at the active profile directory rather than the
  Hermes root. Derive the root from `$HOME/.hermes`.
- **Verify versioned service keys against the running binary.** A key copied from a doc or from memory was rejected at
  startup with "Unrecognized setting", and turning off strict validation did not make it load. Ask the running service
  for its config listing (for Neo4j, `CALL dbms.listConfig()`) and use a name it returns. If nothing matches your intent,
  stop. Do not try neighboring keys.
- **When memory and the file disagree, the file wins.** A remembered fix can be recorded as done before it landed, or after it
  was reverted. Check the live state before claiming work is done, and correct the memory entry in the same turn.
- **Match headings against the observed file.** An assertion for `## Section` fails on a file that uses `**Section**`.
  Read the file first, then write the assertion from what you saw.
- **Use byte-identity for protected blocks.** Marker pairs can be asymmetric (an opening `<!-- BEGIN ... -->` with a
  closing marker that lacks its `-->`), so slice-based phrase checks fail even when the block is unchanged. Compare the
  block before and after.
- **Exclude comments and docstrings from absence checks.** A removed key can still appear in help text. Check the parsed
  structure, or match the key with its trailing colon.

## Verification
After the procedure:
```bash
hermes config check
ls -la ~/.hermes/profiles/<profile>/config.yaml.bak-<reason>-<TS>
md5sum ~/.hermes/profiles/<profile>/config.yaml ~/.hermes/profiles/<profile>/config.yaml.bak-<reason>-<TS>
```
Expected: the config check passes, the backup exists, the backup hash equals the pre-write hash, and the live file hash
differs. On macOS use `md5 -q` in place of `md5sum`. For a daemon-held setting, confirm the value again after the
restart, not just before it.
