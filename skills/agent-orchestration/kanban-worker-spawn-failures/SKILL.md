---
name: kanban-worker-spawn-failures
description: Use when a kanban worker crashes or gives up within about two minutes of starting. Matches the failure to a cause before any repair runs.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [kanban, dispatch, spawn-failure, triage, stdlib-shadowing]
    category: agent-orchestration
related_skills: [dispatch-proof, kanban-orchestration, kanban-card-lifecycle]
---

# Kanban Worker Spawn Failure Triage

## Overview
A kanban worker that dies within the first two minutes has one of a small set of causes. The right fix depends on which cause it is, and the broad repair commands can make a different failure worse. This skill matches the symptom in the worker's own output to a cause, applies the targeted fix, and records the diagnosis on the task so the next person can find it. The default first read is the worker's output for the failed run, never a summary written from memory.

## When to Use
- A task moves to a crashed or gave-up state within about 120 seconds of starting.
- The worker log is empty, or the process disappeared about 60 seconds after launch.
- The log names a missing file under the working directory, or a line that suggests running a repair command.
- The orchestrator reports repeated spawn failures, but the task body does not explain the crash.

Do not use this skill for a worker that ran for minutes and then died. That is a real defect in the worker, so use the debugging and incident-review skills instead. A worker that exited through its normal completion or block call is a clean lifecycle event, not a spawn failure.

## Features
- A ranked table that maps each log symptom to a cause and a targeted fix.
- A check for a stray script in the working directory that shadows a standard-library module.
- Rules that stop repair commands from running for causes they do not fix.
- A check for a mass crash, where many workers fail in one interval.
- A recovery order for orphaned workers that still hold a branch.

## Benefits
- Each failure gets the one fix that addresses its cause, which saves retries and avoids damage.
- Repair commands run only for the cause they fix, so a half-finished update is not re-pinned by mistake.
- A mass crash is recognized as one board-wide event, so cards are not triaged one by one.
- An orphaned worker that still writes to a branch is found before it causes a conflict.
- The written diagnosis on the task lets the next person skip the same investigation.

## Procedure
1. Read the failed run's own output first. Use the task viewer on the board.
   ```bash
   hermes kanban --board <board> show <task-id>
   ```
   Look at the run records and their worker output. Ignore the operator's summary until you have checked this.
2. Match the output against the cause table below, from top to bottom. The first row whose symptom fits is usually the cause.

   | Symptom in the output | Likely cause | Targeted fix |
   |---|---|---|
   | Process gone about 60 seconds after launch, output empty | The worker's launcher died before it started the worker process, often after a fork on macOS | Retry on a different host, or launch from a shell that is not the gateway's child. Avoid background launch on the failing host. |
   | A "no such file" error naming a file in the working directory, usually followed by a suggestion to run a repair command | A stray script at the top of the working directory shadows a standard-library module, and the launcher loads the wrong file | Move the stray script into a scratch subfolder, remove the bytecode cache next to it, confirm the module now resolves to the standard library, then unblock the task. |
   | An import error from inside the platform's own bootstrap code | A dependency is missing because an update stopped partway | Check the install's git log and status first. Then run the documented repair command. |
   | An authentication or quota message printed right after the model starts, with no tool calls | A provider gate, not a spawn bug | Block the task for the authentication fix, or switch the provider and reassign for a quota limit. Do not loop on unblock. |
   | A real traceback from inside the worker's own tool call | A defect in the worker's code | Re-dispatch a fix task. The spawn path is fine. |

3. Apply only the fix for the matched row. Verify it with a check you can run now, such as the module resolution, the login status, or the process list.
4. Record the cause on the task before you unblock it. The comment should name the row, the fix, and the evidence.
   ```bash
   hermes kanban --board <board> unblock <task-id>
   ```
5. Confirm the new worker is alive about a minute after the restart. Check the process identifier and its elapsed time.

### Mass crash in one interval
1. Count the crash events by minute in the task's event history. If many land in the same few seconds, treat it as a board-wide event, not as separate spawn failures.
2. Do not conclude an outage from one message. Repeated "source update could not be finished" lines printed once per command call are noise, not the crash.
3. Check whether new workers are healthy before you declare an outage. Respawns that happen seconds later may be fine.
4. After a mass reclaim, check each old process identifier. A process whose elapsed time is shorter than the time since its crash is a reused number, not the old worker. An old worker still running under the card's profile is an orphan that may write to the same branch. Let the newer run finish, then stop the orphan by its process identifier. Do not signal a process group.
5. For each affected task that has a pull request, compare the pull request's head commit with the commit the final run reported. A mismatch means two writers touched the branch, so block the task and re-review.
6. Check the machine's load before you add more work. When the load is very high, cap the number of concurrent workers first. After a reboot, check the boot time, and recover in one pass: confirm no old worker survives, comment on each task with the cause, unblock them together, and check the new process identifiers about a minute later.

## Pitfalls
- **Run a repair command only for the cause it fixes.** Repair commands for one cause can damage a different one. Pick the cause first.
- **An empty log is a fork failure more often than a timeout.** Look at the system's crash reports and the launcher log for the same second, not at the worker's log.
- **A stray script in the working directory shadows the standard library.** Only the files at the top of the directory can shadow a module, so list them with a non-recursive listing before you re-dispatch a task into a directory that already holds files.
- **Two writers in one directory can each cause the same crash.** A leftover script from an earlier worker breaks the next worker too. Clear the directory before you dispatch.
- **Per-task model overrides outlive a profile change.** A crashed worker keeps its original provider even after the profile is repointed. Set the model on the task again before you retry.
- **Do not update the platform from a worker or from a chat session.** An update restarts the process that runs the session, so run it only from the operator's own environment, and check your local changes afterward.
- **An orphaned worker can keep writing after its replacement starts.** Two writers on one branch produce a mix of both sets of changes, so stop the orphan before the replacement pushes.
- **Do not state a cause from timing alone.** Check the data first. A plausible hypothesis from timing has been wrong more than once.
- **Credentials can break in the middle of a write.** A login that reports as not logged in with a token still present may need a fresh login from the operator. Check the login status without printing token values, and never edit credential stores by hand.

## Verification
- The diagnosis comment on each affected task names the matched row and the evidence.
- The worker's process identifier is alive, and its elapsed time is shorter than the time since the restart.
- For a stray-script cause, the module name resolves to the standard library from inside the working directory.
- For a mass crash, the count of crashed tasks per minute shows one burst, and no old process identifier remains running.
- Every pull request on an affected task has a head commit that matches the commit the final run reported.
