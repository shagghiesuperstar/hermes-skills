---
name: spotlight-control
description: Use when Spotlight or model servers strain memory. The memory or disk pressure can come from Spotlight indexing or from two model servers sharing one memory pool. Covers indexing toggles, single-server rules, and diagnosis.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [spotlight, indexing, memory-pressure, metal, apple-silicon, local-models]
    category: fleet-infrastructure
related_skills: [mactop-system-monitor, local-model-deployment, disk-cleanup]
---

# Spotlight Control and Memory Pressure

## Overview
On Apple Silicon the CPU and GPU share one memory pool. Two problems can make a Mac stall for everything at once. The first is Spotlight indexing a large volume of model files while a model is being read. The second is two inference servers loading the same or overlapping weights into the shared pool. Each adds I/O and memory pressure, and together they push the kernel into throttling. This skill covers how to diagnose which of the two is happening, how to pause indexing on model volumes during heavy work, and why running one model server at a time is the safer default.

## When to Use
- The Mac becomes unresponsive during a model load, a build, or a large download.
- The memory pressure figure stays high while the models are idle.
- A large model volume is being indexed during a heavy session.
- You are about to run a second inference server beside one that is already serving.

## Features
- Commands to list, pause, resume, and rebuild Spotlight indexing per volume.
- A diagnosis order that separates indexing pressure from model-server pressure.
- A single-server rule for long sessions, with the steps to stop the second server.
- Guidance on what indexing pauses cost, and how a resumed index catches up.

## Benefits
- Heavy model work keeps its memory and disk bandwidth.
- The cause of a stall is identified from measured pressure, not guessed.
- The fix is reversible: the index keeps its state, and indexing resumes where it stopped.

## Procedure
1. Measure first. Read the memory pressure and the swap activity while the machine is slow:
   ```zsh
   memory_pressure | grep "System-wide memory free"
   vm_stat 1 3
   ```
   Then list which processes hold the most memory:
   ```zsh
   ps -A -o pid,%cpu,%mem,rss,command -m | head -n 16
   ```
   Look for the Spotlight indexing process and for more than one inference server.
2. Check which volumes Spotlight indexes:
   ```zsh
   sudo mdutil -s /
   ```
3. Pause indexing on a model volume during a heavy session. The command needs an administrator, so run it yourself in a terminal, where the password prompt can appear:
   ```zsh
   sudo mdutil -i off <model-volume>
   ```
   Resume it when the session ends:
   ```zsh
   sudo mdutil -i on <model-volume>
   ```
   Do not configure passwordless administrator access for these commands. Pausing indexing does not need it, and a standing exception for it would weaken the system.
4. Keep one inference server loaded at a time for long sessions. Stop the second server through its own service manager, and confirm that its memory is released before you start the work:
   ```zsh
   curl -s --max-time 3 http://127.0.0.1:<port>/health
   ```
   The health endpoint of a model server reports its loaded models and their memory use. Use it to confirm which server is holding the pool.
5. Re-measure after the change. Pressure should fall, and throughput of the remaining server should recover. If it does not, look for another large consumer before blaming the model.

### Caveats
- The index keeps its state while indexing is paused. Turning it back on does not require a rebuild.
- After a long pause, indexing can use a short burst of CPU while it catches up.
- Search on a paused volume returns nothing new until indexing resumes. Plan for that.
- The system volume is harder to pause than an external volume. Pausing an external model volume is the usual fix, and the system volume can report a failure even when the change applied. Check the state afterward.
- Indexing does not need to be paused on volumes that hold no model files.

## Pitfalls
- **Two servers loading the same weights make the pool fight itself.** Shared memory is not counted in the per-process resident size, so a process can look small while the pool is full. Read the server's own health output.
- **A server that reports a pool limit is reporting a real limit.** Adding a second server to a full pool does not add capacity.
- **Killing a server is an operator action.** Stop it through its service manager, and tell the operator which one you stopped.
- **Do not script a standing exception for administrator commands.** Run them interactively.
- **Do not confuse a stall with a crash.** A stalled machine recovers when the pressure drops. Check the logs for crash reports before concluding the process died.

## Verification
- Memory pressure is lower after the change, and the swap activity has stopped growing.
- The remaining server answers its health check with the expected loaded models.
- Indexing state for each volume matches what you intended. Check it with the listing command.
- The paused volume is resumed at the end of the session, and the listing shows it on.
