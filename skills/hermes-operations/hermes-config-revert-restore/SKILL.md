---
name: hermes-config-revert-restore
description: Use when reverting a Hermes profile's primary model to a backup without losing later changes. Covers snapshot, block-only restore, verification and reporting.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, config, revert, restore, backup, rollback]
    category: hermes-operations
related_skills: [config-verify-before-write, hermes-fallback-chain-deploy]
---

# Hermes Config Revert and Restore

## Overview
When a primary model was changed without authorization, or a verification run changed models it should not have,
the fix is a rollback to the snapshot taken before the change. The obvious method is to copy the whole backup file back
over the live one. That also restores every other key, so any legitimate change made after the snapshot, such as an
updated fallback chain, is silently lost. This skill restores only the block that changed, checks that the rest of the
file is intact, and reports the result with before and after evidence.

## When to Use
- An operator-authorized request asks for a rollback to a named backup snapshot.
- A profile's primary model changed without approval and must return to its pre-change value.
- Several profiles changed, and only one block (such as `model:`) should be restored in each.
- A failure traces back to a config change that should not have happened.

Not for routine edits (use `config-verify-before-write`), for multi-file changes that belong to one atomic change, or for
rollback of files unrelated to Hermes state (use version control or the standard backup tools).

## Features
- Inventory of the snapshot and the live configs before anything changes.
- A "before" snapshot of the live state, taken so the revert itself can be audited and undone.
- Comparison of one named block per profile, parsed as YAML.
- Block-only replacement, written atomically.
- Verification of the restored block and of the fallback chain that must not change.
- A summary that reports the before, now and after state for each profile.

## Benefits
- Later changes to other keys survive the rollback.
- A failed revert leaves a recoverable state, because the pre-revert snapshot exists.
- Success is claimed only when the checks pass.

## Procedure
1. Confirm the authorization and the snapshot. Stop unless the request names both the backup set and the profiles:
   ```bash
   ls -la <backup-dir>/<snapshot-set>/
   ```
   Every profile in scope needs a backup file in that set. If one is missing, stop and report it.

2. Snapshot the live state before any change. Keep the copy with its timestamps:
   ```bash
   mkdir -p <backup-dir>/<revert-set>
   # Print the default config path with `hermes config path`, then copy that file:
   cp -p <default-config-path> <backup-dir>/<revert-set>/default-config.yaml
   # Print each profile's config path with `hermes -p <profile> config path`, then copy that file:
   cp -p <profile-config-path> <backup-dir>/<revert-set>/<profile>-config.yaml
   ```

3. Compare the target block, parsed as YAML, for each profile. Profiles whose block already matches need no action:
   ```python
   import yaml
   from pathlib import Path

   def model_block(path: Path):
       return yaml.safe_load(path.read_text(encoding="utf-8")).get("model")

   snapshot = Path("<backup-dir>/<snapshot-set>")
   live_configs = {"<profile-a>": Path("<profile-a-config-path>"), "<profile-b>": Path("<profile-b-config-path>")}
   for profile in ["<profile-a>", "<profile-b>"]:
       before = model_block(snapshot / f"{profile}-config.yaml")
       now = model_block(live_configs[profile])
       print(profile, "unchanged" if before == now else "NEEDS REVERT")
   ```
   Before you restore a profile, confirm the difference is a real change to the model and not formatting or comments.

4. Replace only that block in the live file, leaving every other line alone. Write the result to a temp file in the same
   directory and rename it over the original, so a crash cannot leave a half-written config:
   ```python
   import os
   from pathlib import Path

   def block_span(lines, key):
       start = next(i for i, l in enumerate(lines) if l.rstrip() == f"{key}:")
       end = next((i for i in range(start + 1, len(lines))
                   if lines[i].strip() and lines[i][0] not in " \t#"), len(lines))
       return start, end

   def replace_block(config: Path, new_block: str, key="model"):
       lines = config.read_text(encoding="utf-8").splitlines(keepends=True)
       start, end = block_span(lines, key)
       updated = "".join(lines[:start]) + new_block + "".join(lines[end:])
       tmp = config.parent / f"{config.name}.tmp"
       tmp.write_text(updated, encoding="utf-8")
       os.replace(tmp, config)
   ```
   Take `new_block` from the snapshot file with the same span function, so indentation and newlines match exactly.
   If the operator's order does not authorize a direct file edit, restore each key through the Hermes CLI instead, and
   read each value back.

5. Verify the block immediately after each write. A mismatch means the revert has a defect. Halt, and do not check the
   other profiles until the defect is explained:
   ```python
   assert model_block(live_configs[profile]) == before, f"FATAL: {profile} model block differs after revert"
   ```

6. Verify that the fallback chains were not changed by the revert:
   ```bash
   for p in <profile-a> <profile-b>; do
     echo "== $p"
     hermes -p "$p" fallback list 2>&1 | head -9
   done
   ```
   Compare the output with the chain you expect. If a chain is missing or different, the revert is not clean.

7. Report the result per profile: the model before the change, the model now, and the model after the revert. Include
   the fallback output. End with one line in this form, with real counts:
   `REVERT host=<host> profiles_checked=<n> primaries_restored=<m> fallback_untouched=yes`
   Claim success only when every check passed and the counts match the request.

## Pitfalls
- **Never copy a whole backup file over a live config to undo one change.** It also restores every other key, including
  fallback chains and other settings that changed after the snapshot.
- **Snapshot the live state before you change it.** The snapshot is the "before" for the audit trail and the way back
  if the revert fails.
- **Parse the block; do not grep for it.** A grep can match a similar line in another section, such as a per-platform
  override.
- **Verify right after each write.** Deferring the check to the end hides which write broke the file.
- **A failed block check stops the run.** Do not continue to the fallback check or to other profiles with a defect
  unexplained.
- **Write atomically.** A temp file and a rename survive a crash. An in-place edit does not.
- **Re-check the snapshot before you rely on it.** Confirm it is the snapshot the order names, and that its
  timestamps are the expected ones.
- **Do not claim a revert succeeded from the command exit code alone.** Read the block back, and read the chains back.
- **Authorization covers the named profiles only.** Do not widen the revert to other profiles that look similar.
- **Log the cause, not only the fix.** Record which change was unauthorized and where it came from, so the same path is
  closed.

## Verification
- Each reverted profile's `model` block parses to the same value as its snapshot.
- Each profile's fallback chain prints the same entries as before the revert.
- The pre-revert snapshot directory exists and holds one file per profile in scope.
- The summary line reports the expected profile and restore counts, and `fallback_untouched=yes`.
