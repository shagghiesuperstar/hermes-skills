---
name: delegated-artifact-spotcheck
description: Use when a delegated worker's output must be checked. An orchestrator confirms it is real work, not a stub. Reads files on disk and returns a REAL, STUB, or SUSPECT verdict.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [verification, delegation, artifacts, stub-detection, audit]
    category: agent-orchestration
related_skills: [adversarial-review, ar-verify-findings, data-artifact-adversarial-review]
---

# Delegated Artifact Spot-Check

## Overview
A delegated worker is supposed to leave a set of output files: a summary, a results table, and a claim or shard record. A stub worker can leave the same files with invented contents. This skill is a quiet, read-only check that decides whether a worker's artifact reflects real work. It reads the files, compares rows against the input, reads the write order from timestamps, and confirms every path the worker cited. It never re-runs the worker's probes and never fills a gap with invented evidence. The output is one verdict, REAL, STUB, or SUSPECT, in a note written next to the artifact.

## When to Use
- A worker reports that a batch is finished, and the orchestrator must confirm the output before it is used.
- An operator asks for an overnight or wave check of a worker's result files.
- A worker's results claim a count, such as "25 of 25 not found," and the count must be proven.
- A worker's output is a summary, a results table, and a claim file, and each one must be checked against the others.

Do not use this skill to produce the worker's artifact, to review mission or queue state, or to probe live services. Those are separate tasks.

## Features
- A fixed procedure: locate the artifact, snapshot paths, sizes, and times, check row counts and key sets, reconstruct the write order, verify cited evidence, and write the verdict.
- Set comparison of the input keys against the results keys, which catches phantom and missing rows that a line count misses.
- A write-order check that uses file timestamps to separate a real run from a batch written in one step.
- A verdict note placed beside the artifact, with an evidence table for every claim.
- A reply format that gives the operator the verdict, one rationale line, and the note's path.

## Benefits
- Stub output is caught before it reaches a downstream step.
- A line count alone cannot pass a results file with wrong keys, because the key comparison catches them.
- Every claim in the verdict cites a file path, so the operator can check the reasoning.
- The check is cheap and read-only, so it can run during an overnight window without side effects.
- An honest SUSPECT verdict is kept when evidence is missing, rather than being softened into a pass.

## Procedure
1. Locate the artifact. Look in the known drop directory first. Use a bounded search only if that fails.
   ```bash
   ls -d "<drop-dir>"
   find "<home>" -maxdepth 8 -type f -name "SUMMARY-*.md"
   ```
   There should be exactly one canonical drop. If there are two, the older one is stale. A summary that appears in two drops is a SUSPECT signal, not a pass.
2. Snapshot every file in the set: absolute path, byte count, and modification time. Take the snapshot from the disk at check time, never from an earlier read.
   ```bash
   wc -c "<file>"
   stat -f "%Sm" "<file>"
   ```
3. Compare the row sets. Count the lines, the status distribution, and the verdict distribution, and diff the sorted keys of the input against the sorted keys of the results.
   ```bash
   awk 'END{print NR" total lines"}' "<results.csv>"
   diff <(awk -F, 'NR>1 {print $1}' "<input.csv>" | sort) <(awk -F, 'NR>1 {print $1}' "<results.csv>" | sort)
   ```
   The diff must be empty. Rows that appear only in the results are phantoms. Rows that appear only in the input are missing verdicts.
4. Reconstruct the write order from the modification times. The input should be staged first, then the results, then the summary, then the claim file. A summary written before the results is a stub signal. Identical times across all files are SUSPECT, not an automatic STUB, because a fast run can produce them. Decide with the row count.
5. Check the evidence the worker cites. For each claimed corpus directory, check the file count. For each claimed entry, check that it exists. For each claimed link map, check that it exists. If a result row says "not found," confirm that its candidate field is empty. Do not re-probe any live source. This step is a disk check only.
6. Check cleanup notes. If the summary says a bad key was replaced, confirm that the bad key has zero rows in the results and that the replacement has a row. A cleanup note with no on-disk confirmation is SUSPECT.
7. Write the verdict note next to the summary, named `SPOTCHECK-<summary-filename>.md`. Include the sections for artifact paths, row counts, timing, evidence checks, verdict, and notes. Each claim cites the path it came from.
8. Reply to the operator with a short message: the verdict, one line of rationale, and the absolute path of the note. If the verdict is STUB or SUSPECT, add one line that names the next decision, such as a re-run or an operator review.

## Pitfalls
- **Identical timestamps are a signal, not a verdict.** Batch-written stub files often share a timestamp. A fast legitimate run can do the same. Decide with the row count and the content, not the timestamp alone.
- **`wc -l` misses wrong keys.** A results file can have the right number of lines and the wrong keys. Always run the sorted key diff.
- **Do not re-run the worker's probes.** Re-running a search or a fetch changes rate limits, logs, and caches, and the worker is the only source of truth for its own probes. If its evidence is missing from disk, mark SUSPECT and stop.
- **Do not invent counter-evidence.** A SUSPECT verdict stays SUSPECT when a cited path is missing, even if the operator expects a pass. Write "cannot confirm claim X at the cited path." Do not soften it to "appears to exist."
- **Keep the verdict note focused.** Prior context, the worker's own recap, and the operator's request belong in the reply only when they help interpret a specific row.
- **Put the note beside the artifact.** A note in a separate audit directory makes the operator open two places to read one verdict.
- **Bound every search.** An unbounded search of a home directory can exceed the command timeout and then look like "not found." Cap the depth and check the known path first.
- **Check the cleanup notes.** A "this supersedes" note in a summary is a claim. Confirm it against the results file.

## Verification
- The verdict note exists beside the summary, and it names every file that was snapshotted.
- The key diff printed no output, or the note lists each phantom and missing key by name.
- Each evidence line in the note cites an absolute path and an observed count.
- The verdict matches the strongest evidence in the note: a row-key mismatch or a missing cited path cannot yield REAL.
- The reply has the verdict, the rationale, and the path, and nothing else.
