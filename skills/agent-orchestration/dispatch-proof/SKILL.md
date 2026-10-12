---
name: dispatch-proof
description: Use when claiming a background job is running or finished. Requires a process ID, a fresh process check, and read output before any status report.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [verification, background-processes, orchestration, status-reporting]
    category: agent-orchestration
related_skills: [say-do-verify, delegated-artifact-spotcheck, kanban-card-lifecycle, kanban-orchestration, external-coding-agent-orchestration]
---

# Dispatch-Proof: Verify Background Jobs Before Claiming Them

## Overview

A background job is only as real as the live process identifier that backs it. This skill
requires every "running", "still working", "launching", "almost done", "finished", or
"stopped" claim to carry its evidence in the same message: a process ID, a fresh process
check, and the output the job wrote.

The failure it prevents is narration that sounds confident and hangs together but is false,
such as a job that died at launch, never started, or finished long ago. The fix has the same
shape as checking a citation: require an artifact you can re-check, not a remembered launch.

### Why narration fails

- A background launch that returns without error means the shell forked. It does not mean the job is still alive a second later.
- Memory from an earlier turn or an earlier session records a claim. It is not a current state and must be re-verified when the work matters.
- A worker's report of success is a self-report until its artifact is found on disk.

## When to Use

- Any job started in the background: a background terminal launch, a delegated worker in background mode, a detached child process, or a shell wrapper around `nohup` or `disown`.
- Any "still running", "almost done", or "in flight" update between turn boundaries.
- Any scheduled job described as "runs" or "ticks" without a last-run timestamp and status. A listed schedule is configuration, not a live process.
- Any "I'll come back to that" promise. Work that continues after the turn ends needs a mechanism: a scheduled job, a board card, or a verified PID.
- Any claim about state held elsewhere: a merge, a deploy, a board status, a live preview, a subagent's output, or the model a live session is bound to.
- Not needed for a foreground command that already returned in this turn. Its printed output is the proof.

## Features

- Requires a process ID and a fresh `ps` line in the same message as any running claim.
- Reports a dead process with no result as a hard failure, in plain words.
- Requires reading a finished job's output before calling it complete.
- Applies the same evidence rule to subagents, board state, merges, deploys, and previews.
- Gives a stop procedure that enumerates every live lane and ends at a verified zero count.
- Uses one labeled status line per workstream, each carrying its own evidence.

## Benefits

- Every status line carries evidence from the same turn, so the operator never has to re-check it.
- A dead or stalled worker is reported in the turn it dies, not after a long stretch of narration.
- Duplicate writers and two loops drawing on one budget are caught before they start.
- Cleanup becomes provable: a count of zero replaces the phrase "cleaned up".
- Merges and deploys are reported against live state, not against a green label.
- Probing and quoting replace recalling and hedging, so answers stay grounded in current state.

## Procedure

### Launch and confirm

1. Start the job in the harness's background mode. Do not add shell `&`, `nohup`, or `disown`, because the parent shell can reap the child as soon as it releases its slot.

```bash
terminal(command="<command>", background=true, notify=true)
```

2. Record the returned session ID and PID, then confirm liveness in the same turn:

```bash
ps -p <pid> -o pid,etime,stat,command
```

3. If the harness cannot deliver a completion notice, say so. Poll the session ID with the harness's process-poll call, or wait, within the same turn. Never end a turn while expecting a ping that cannot arrive.
4. Before launching an engine or a paid loop on the same work, look for a live writer and join it instead of starting a twin. If the board does not return a worker PID, find it by task ID:

```bash
pgrep -fla "<progress-or-worktree-path>"
pgrep -P <wrapper-pid>
ps -axo pid,etime,stat,command | grep "<task-id>"
```

A wrapper that is alive with no child process is not an engine. Stop it and relaunch one writer.

### Status and completion

5. Before writing "still running", re-run the `ps` line for the same PID and quote its output. A status from the last turn is not evidence.
6. If the PID is gone and no result file exists, write: "Process `<pid>` died. No result landed." Do not soften it to "almost done" or "taking longer than expected."
7. For an engine that writes its output only at exit, judge progress by work product: commits, changed files, or the expected output path. Log size is not progress.
8. Before reporting completion, read the output file. Confirm that any wrapper utility you rely on exists first. `timeout` is not installed by default on macOS, so check with `command -v gtimeout` or drop the wrapper.
9. Confirm each artifact exists in the session that claims it, then compute its SHA-256 digest with the checksum tool your platform provides. On macOS that is `shasum -a 256`. Write a digest into any manifest only after the file is on disk:

```bash
ls -la <artifact-path>
shasum -a 256 <artifact-path>
```

10. For a deployed change, fetch the public address and quote the marker the user named. Check each stylesheet and script the page references too, because a 200 on the index page alone does not prove the page works:

```bash
curl -sI https://<domain>/<path>
curl -s https://<domain>/<path> | grep "<marker>"
```

### Merges, releases, and external state

11. Before reporting a PR as merged or a release as live, fetch its state in the same message:

```bash
gh pr view <number> --json state,mergedBy,mergeCommit,baseRefOid,headRefOid
```

12. Before a release marker, list the commits production will actually run. A release that names one PR often ships the whole branch tip:

```bash
git log --oneline <live-sha>..<release-tip> -- <app-paths>
```

13. Before a release script runs, fetch the live version identifier and compare it with the value recorded when the script was written. A mismatch means another release already landed. Re-plan before going further.

### Stop, kill, and reboot

14. To stop, enumerate every lane first: engine processes, runs started this session, and any worktrees they created:

```bash
pgrep -fla "<engine-pattern>"
git -C <worktree-path> status --short --untracked-files=all
```

15. Before killing a long-running session, confirm that no open card depends on it and that `git log origin/<branch>..HEAD` is empty. Back up uncommitted files to a dated directory first. Then remove only the named dirty paths. Never delete a whole worktree or touch a protected branch, and name the branch each worktree is on in the final report.
16. Send SIGTERM to each PID, confirm it is gone, and repeat the count until it is zero and stays zero across one retry:

```bash
kill -TERM <pid>
ps -p <pid> -o pid,etime,stat,command
```

Kill by PID, not by process group, when children share the parent's group, because a group signal also reaches the parent. Children can respawn while their parent runs, so stop the parent first when a spawn storm is involved.

17. Write a marker file in each affected workspace that names the lock scope and what was discarded, so a later turn reads "stopped" instead of relaunching.
18. Before a reboot, list each engine PID with its elapsed time and CPU. Wait for print-mode runs to exit on their own, because a reboot interrupts them rather than pausing them. After boot, check the main service PID and start time, the expected zero counts for headless browsers and tmux sessions, and the ports your services listen on. Fix anything red in the same turn.

### Live sessions, recovery, and reports

19. To learn a live tmux session's state, ask it directly. Send Enter as its own call, because a long paste can swallow the trailing Enter:

```bash
tmux send-keys -t <session> "<bounded status question>"
tmux send-keys -t <session> Enter
tmux capture-pane -p -t <session> -S -25
```

Wait 60 to 90 seconds before capturing. A session that never answers a bounded question is not working.

20. If you catch an unverified claim, say so in the next message, show the actual state, run the real job again with a fresh PID, and fix the rule that let the claim through.
21. Report each independent workstream as one labeled line with its evidence on the same line. Run `date` in the same turn before printing any timestamp:

```text
<WORKSTREAM_LABEL>: <status> - <pid, etime, stat, or artifact path>
```

Classify each blocker as MINE (you can clear it from disk or live state, so clear it this turn) or OPERATOR_ONLY (a credential, a personal login, or a vendor dashboard). Surface only the OPERATOR_ONLY ones, each with the one-step check that proves the state.

## Pitfalls

- **Never claim a process is running without a PID.** A running claim with no process identifier is fabrication, even when the job was probably started. The honest form is "I have not checked yet," followed by the check.
- **Never repeat a state claim from an earlier turn.** "Still running" in turn N is not evidence in turn N+1. Re-run the check and quote the output.
- **A dead PID is a failure, not a slow job.** Softening "died" into "almost done" hides a job that will never write its result. Say that it died and that no result landed.
- **Exit 0 proves only that the wrapper ended.** A loop that printed "command not found" can still exit 0 having done nothing. Read the output before reporting completion.
- **A session ID is not a live PID.** The launch call returns both, and either can die seconds later. Poll once after launch and again before each status update.
- **A live process is not necessarily making progress.** A process can burn CPU while doing no work, such as a session stuck at a login prompt. Check the last transcript entry or the output modification time before calling it productive. A process that sleeps with no children and no output after its last read is stalled on its provider: kill it, confirm it is gone, then retry once.
- **A process waiting on an OS permission dialog looks alive.** It shows a sleeping state with growing elapsed time. Name the dialog it is waiting on, and re-check after the operator responds.
- **A subagent's report is hearsay until you check its artifact.** A worker that says it wrote a file or opened a PR is self-reporting. Open the path or fetch the PR yourself, and do not report its verdict while the child is still running.
- **A worker that ends without its required artifact has failed.** A final turn with no verdict file means the review did not happen, even if the harness says completed. Require an early draft file so the artifact exists before the last turn.
- **A board status or heartbeat is not process liveness.** Board age and heartbeat times describe the board, not the worker. Use a process check for any process claim.
- **A "continue" order needs an action, not another identical status packet.** Inspecting state is discovery. The same turn must also repair, reroute, or name the exact external blocker.
- **An unreachable target is BLOCKED, not started.** When a host or path is out of reach, report BLOCKED with a reason per target, and never imply the work began there. Ping the host before concluding that a transport is missing.
- **A run ID belongs to the server that minted it.** A 404 from your host for a remote run proves nothing. Query the host that created the run.
- **A wrapper that waits on a child exits when the child exits.** Servers started inside it die with it. Start long-lived servers as their own background jobs, then fetch them.
- **Two writers on one checkout corrupt each other.** A second engine on the same worktree produces a twin diff. Check for live children first, and stop the duplicate.
- **Two loops against one budget double-charge.** A second paid run that writes the same progress file doubles the spend. Match the progress path, not a script name, before launching anything.
- **Fall back to another engine only as the work order allows, and name the switch.** A different engine started while the first is alive is a second writer. Mark the original task blocked, confirm its child PID is gone, then launch the allowed fallback.
- **Never widen an approval allowlist to clear a block.** A blocked command is a control working as designed. Report the exact command and get the operator's approval for that command.
- **Do not restart a service the operator has protected to load a patch.** A running process keeps its old code until its PID changes. Wait for the normal recycle and confirm the new start time.
- **A watchdog that errors silently is no watchdog.** A monitor whose last run raised an error sends no alert, so a real stall stays hidden. After each change, run it in the foreground and confirm exit 0 and the expected output.
- **A promise with no mechanism is not a plan.** "I'll watch for X" with no scheduled job, card, or verified PID does nothing, because the agent is not running between turns.
- **Do not end a message on an action that no tool call started.** "Kicking that off now" with no call in the same turn describes work that did not happen. Make the call first.
- **A status string is not activity.** A goal marked active with zero turns is a dangling intent, not a running loop. Count real turns or events before calling a job active.
- **A merge you did not perform is not your merge.** If another actor merged the PR, report the merge commit and the actor, and re-fetch the state in the same message.
- **A PR that exists is not a PR that can merge.** Require an open state, not a draft, an approving review decision, and a head commit that matches the latest instruction. Check state before spending review effort, because a merged PR cannot absorb a requested change.
- **A merged change is not live.** The deploy must read the branch that was merged, finish its build, and serve the new commit. Check all three before saying live.
- **A loopback address is not reachability.** A local address answers only on the machine that runs it. Verify from the device that needs the service.
- **No hash without a file.** A digest written into a manifest before the file lands is a receipt for nothing. Write null and a failure status, then fill in the hash after the file exists.
- **A count needs its predicate.** A headline "all pass" proves only what the script tested. Name the checks that ran next to the number.
- **Chase the write, not the report.** A send that the socket accepted does not prove the evidence landed. Check the file on disk, its modification time, and its final status token.
- **Parse verdicts from structured fields.** The last line of mixed tool output can look like a verdict when it is noise. Compare a declared status field to its exact value.

## Verification

Use this shape in a status message after a launch:

```text
Launched. session_id=<session-id>, pid=<pid>.
$ ps -p <pid> -o pid,etime,stat,command
  PID      ELAPSED    STAT  COMMAND
  <pid>    <elapsed>  S     <command-summary>
```

On completion, name the elapsed time, the exit status, and the artifact:

```text
<job-name>: finished. pid <pid> was alive <elapsed>, exit 0. Output <artifact-path> (<size>, sha256 <digest>).
```

A bare "All done." is not a verification.

Before any status claim, confirm the evidence in this turn:

- A process ID and a `ps` line for any running claim, or the words "died, no result landed" when the line is gone.
- The output file read, plus the artifact listing, for any completion claim.
- The live state fetched for any merge, deploy, or preview claim, with the public marker quoted.
- For any count, the number and the predicate it tested.
- After each stop, a count of zero that holds across one retry.
