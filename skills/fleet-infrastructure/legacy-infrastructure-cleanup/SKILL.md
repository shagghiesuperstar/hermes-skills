---
name: legacy-infrastructure-cleanup
description: Use when an infrastructure cutover left stale host, address, or endpoint references behind. Covers live-versus-evidence triage, backups, a re-scan gate, and reporting.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [infrastructure, cutover, stale-references, verification, network-migration]
    category: fleet-infrastructure
related_skills: [multi-mac-fleet-ops, macos-remote-access]
---

# Legacy Infrastructure Cleanup

## Overview
After a cutover (a network removed, a provider moved, a host relocated), old addresses and endpoints survive in configuration, memory notes, instruction files, and evidence logs. Live configuration that still points at a dead address fails silently, while evidence files that record the removal are supposed to mention it. This skill separates the two. It finds every stale reference, classifies each hit as live or evidence, fixes only the live ones after a backup, and gates completion on a clean re-scan.

## When to Use
- A network or provider cutover is done, and the old addresses should no longer be referenced by anything the agents read.
- A scan or a review shows stale references, and you need to know which ones are live.
- A host was moved or retired, and its old name still appears in configuration.

## Features
- A small, dependency-free scanner that counts matches in live files and in evidence folders separately.
- A fixed triage order: live configuration first, then instruction and memory files, then evidence folders.
- Backup before every live edit, with a dated folder.
- A re-scan gate: the cleanup is done only when the live count is zero.
- A profile-warning check that reports informational guardrails separately from broken configuration.

## Benefits
- Live configuration stops pointing at dead addresses, and the agents stop failing against them.
- Evidence of the removal stays intact, so the audit trail survives.
- Every change is reversible, because the backup holds the exact pre-change file.
- The final report shows counts before and after, so the result is checkable.

## Procedure
1. Define the dead patterns and the live replacements before you scan. Write the dead addresses, host names, and endpoint paths as one regular expression, and list the live replacement for each one.
2. Run the scanner over the directories that agents read. Keep the scanner in a location you control, and check its contents before running it. The scanner's behavior matters more than its name:
   ```zsh
   python3 <scanner-dir>/stale_ref_scan.py '<dead-pattern-regex>' <config-dir> <instructions-dir> <memory-dir>
   ```
   Expect a line per live hit and one summary line. `GREEN` means no live hits remain. `RED` means at least one live file still references a dead address.
3. Check profile directories separately. Profiles often carry deliberate warnings such as "do not use this address", which name the dead address on purpose. Count those warnings, report them as guardrails, and leave them unchanged.
4. Classify each live hit:
   - Configuration or instructions the agent reads at runtime: fix it.
   - A memory note stating a past fact: rephrase it so the fact stays true without the dead address.
   - A record of the removal: it is evidence. Do not fix it. Archive it in step 6.
   - A skill file you do not own, or a bundled file: do not edit it. Record it as an unmanaged hit in the report.
5. Back up each live file before you change it, into a dated folder, and confirm the backup landed:
   ```zsh
   mkdir -p <backup-dir>/<date>/legacy
   cp <live-file> <backup-dir>/<date>/legacy/<file-name>.bak
   ls -la <backup-dir>/<date>/legacy/<file-name>.bak
   ```
   Then edit the live file: remove the dead reference, replace it with the live address or name, or rephrase a fact. Use a structured edit for structured files.
6. Move evidence files, such as closure logs and audit records, into the backup folder. Make sure the scanner's ignore list covers the destination. Check it before you move anything, so the evidence does not keep counting as a live hit.
7. Re-scan after all edits, not after each one. Expect `GREEN`. If a hit remains, decide whether it is a false positive (add a rule for it), a new live problem (fix it and repeat), or an intentional guardrail (leave it and report it).
8. Report the result for each host: the scan counts before and after, the backup folder, the live files changed with what changed, the evidence files moved, the profile warnings left in place, and any unmanaged hits.

### Scanner
This is the whole scanner. It walks the given directories, skips version-control and dependency folders, and counts a file as ignored when its path includes a backup, archive, or evidence folder:

```python
#!/usr/bin/env python3
"""Count stale references in live files vs evidence folders. Usage: stale_ref_scan.py REGEX DIR [DIR...]"""
import os, re, sys

pattern = re.compile(sys.argv[1])
IGNORED_PARTS = {"backups", "archive", "evidence"}
real, ignored = [], []
for root in sys.argv[2:]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules"}]
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                text = open(path, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            if pattern.search(text):
                parts = set(path.split(os.sep))
                (ignored if parts & IGNORED_PARTS else real).append(path)
for path in real:
    print("REAL", path)
print(f"{'RED' if real else 'GREEN'} real={len(real)} ignored={len(ignored)}")
```

## Pitfalls
- **Evidence and live configuration look alike.** A closure log and a live config can both contain the dead address. Triage by where the file sits and what reads it, not by the match.
- **A warning is not a broken setting.** A profile that says "do not use the old address" is a guardrail. Leave it.
- **Editing evidence wastes effort and loses history.** Archive it instead of rewriting it.
- **Rephrasing a memory note can change its meaning.** Keep the fact and drop only the dead address.
- **The archive location must be in the ignore list.** A folder the scanner does not ignore keeps the evidence counted as a live hit.
- **Verify backups before editing.** A mistyped destination can create a different file name and leave no backup of the original.
- **A remote profile is not scanned from another host.** A profile that lives on a different machine needs a scan on that machine.
- **Do not call it done on a partial scan.** Completion means the final scan on every host reads `GREEN`.
- **Check the scanner before running it.** Confirm its contents and its checksum against the copy you expect, and do not run an unexpected copy.

## Verification
- The final scan on each host reads `GREEN` with `real=0`.
- Each changed live file has a backup in the dated folder, and the backup contains the pre-change text.
- Evidence files sit in the backup folder, and their count matches the report.
- Profile warnings are counted and listed as guardrails.
- The report lists every unmanaged hit, with the reason it was not edited.
