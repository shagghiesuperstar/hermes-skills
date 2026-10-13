---
name: disk-cleanup
description: Use when a Mac's disk or memory is under pressure. Covers a read-only audit, safe cleanup order, halt conditions for local model servers, and reporting reclaimed space.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [disk, cleanup, memory, macos, docker, time-machine]
    category: fleet-infrastructure
related_skills: [mactop-system-monitor, multi-mac-fleet-ops]
---

# Disk and Memory Cleanup on macOS

## Overview
A Mac that runs local model servers, containers, and long-lived daemons fills its disk with caches, model copies, container images, and local snapshots. Cleanup is safe only in a fixed order: read-only audit first, reversible caches next, and destructive steps last, each gated by a check. Report what was reclaimed, step by step, so the next run has a baseline.

## When to Use
- The data volume is above roughly 70 percent full, or a write fails for lack of space.
- A scheduled hygiene run comes due (for example every two weeks).
- Memory is creeping upward after new long-lived daemons were added.
- The operator asks what is using storage.

## Features
- A read-only pre-flight audit of memory, disk, containers, model-server ports, mounted volumes, and local snapshots.
- A fixed cleanup sequence ordered from lowest to highest blast radius.
- Halt conditions that stop cleanup when a model server or container is in use.
- Real-size auditing that avoids trusting `du` on a nearly full filesystem.
- A memory review that restarts nothing unless a threshold or the operator says so.

## Benefits
- Cleanup never removes data that a running server is reading.
- Each step is reversible or explicitly approved, and the report says which is which.
- Reclaimed space is measured before and after, not estimated.
- Duplicate model copies and oversized backup archives are found without guesswork.

## Procedure
1. Run the read-only audit first. None of these commands changes anything:
   ```zsh
   memory_pressure | grep "System-wide memory free"
   df -h /System/Volumes/Data | tail -1
   docker ps -a --format '{{.Names}} {{.Status}}' | head -10
   curl -sS --max-time 2 http://127.0.0.1:<model-port>/v1/models 2>&1 | head -3
   ls /Volumes/
   tmutil listlocalsnapshots / | wc -l
   ```
2. Stop and ask the operator before continuing if any of these hold:
   - A container is running. Stop it first, or skip the container prune.
   - A local model server answers on its port. Cache deletion under a live server can break it.
   - An external drive is being written to by another job.
3. Clear reversible caches, after the operator approves the exact directory list. Browser automation, updater, and language-tool caches are rebuilt on demand:
   ```zsh
   rm -rf ~/Library/Caches/<cache-directory-name>
   brew cleanup -s
   ```
   Delete only the named cache directories, not whole parents.
4. Prune unused container images only when no container is running, and only after the operator approves the prune by name. Run the prune interactively so you read its confirmation summary:
   ```zsh
   docker system prune -a
   ```
   Volumes hold data. Do not add `--volumes` unless the operator approves that removal separately.
   Container runtimes often shrink their virtual disk only after the app is restarted or its data is purged from the app's own troubleshooting menu. The CLI alone frees the contents, not the disk image.
5. Clear a model-server cache only when that server is confirmed not serving, only after the audit showed its port closed, and only after the operator approves the exact cache list.
6. Treat user-owned content as off limits without an explicit instruction. Screen recordings, documents, and photos are reported with their sizes and left alone unless the user approves their deletion by name.
7. Remove stale project clones and build artifacts after verifying nothing references them, and only after the operator approves the exact list:
   ```zsh
   pgrep -fl "<project-name>"
   lsof -nP -iTCP:<dev-port> -sTCP:LISTEN
   ```
8. Unmount stale network shares that are no longer in use. Leave local external drives alone.
9. Thin local Time Machine snapshots, after the operator approves the byte target and urgency. These are purgeable space, not backups. Never run the thinning command on a real backup volume, which is a separate store:
   ```zsh
   tmutil thinlocalsnapshots / <bytes> <urgency>
   ```
10. Remove old configuration backups, after the operator approves the list, that you have confirmed are not referenced by any running service.

### Memory review (read-only)
Look at the largest resident processes first:
```zsh
ps -A -o pid,user,%cpu,%mem,rss,etime,command -m | sort -k5 -nr | head -16
```
Do not restart a long-lived daemon unless free memory is below the agreed threshold, one process is using more than the agreed resident size, or the operator asks.

## Pitfalls
- **A recursive prune with volumes is destructive.** On a machine with no containers it removes little data, but always read the confirmation step rather than piping an answer into the command.
- **Stopping a model server breaks clients.** Check the port before any cache removal, and check it again after.
- **Time Machine local snapshots are purgeable.** They are safe to thin, but thinning a real backup volume is not.
- **Some caches refill immediately.** Browser and mail caches can be rebuilt by their apps. The space is still reclaimed for a while, so the net gain is positive.
- **Screen recordings refill while an app is recording.** Check for an active recording before you delete the folder.
- **`du` can overstate sizes on a nearly full filesystem.** Verify with a byte-count sum over the files. Where `find -printf` is available, print each file's size. Where it is not, read each size with `stat -f %z`:
  ```zsh
  find <dir> -type f -exec stat -f %z {} + | awk '{sum+=$1; n++} END{printf "%d bytes in %d files\n", sum, n}'
  ```
- **Model copies can be duplicates.** When the same model exists in a tool's home folder and an external models volume, check whether they are the same file (`stat -f %i` on both) before deleting either. Convert duplicates to a symlink only after you confirm the content.
- **Large backup archives sit at the top level.** Files over 100 MB in a home or project folder are the usual culprits. Confirm each one before deleting it.
- **Scheduled cleanup reports instead of guessing.** When a pre-flight check fails, the scheduled run should write its findings and skip the destructive steps.

## Verification
```zsh
df -h /System/Volumes/Data | tail -1
du -sh ~/Library/Caches
tmutil listlocalsnapshots / | wc -l
```
Report reclaimed space for each action, and the totals before and after.
