---
name: incident-forensics
description: Use when a process restarted, quit, or died on its own and the cause must be found from evidence. Covers timelines, ranked elimination, probe hygiene, and an honest report.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [forensics, root-cause, macos, launchd, logs, restart, incident]
    category: fleet-infrastructure
related_skills: [infrastructure-guardian-agent, macos-remote-access, mactop-system-monitor]
---

# Incident Forensics

## Overview
An incident that already happened has no repro loop, so the only tools are the records it left behind: logs, crash reports, process history, shell history, launch-service state, and file modification times. The discipline is strict. State only what the records show, never guess the cause, and say "unknown" when the records cannot identify it. Work through candidate causes one at a time, and eliminate each one with a named artifact before moving on.

## When to Use
- A service or app restarted, quit, or disappeared, and nobody knows why.
- Several restarts were reported as one event, and they need to be separated.
- A process keeps coming back after it was stopped, and the cause is unclear.
- A report must say what was ruled out, with the evidence for each item.

## Features
- A timeline builder that normalizes timezones before correlation.
- A ranked list of likely causes for a self-restart, with an elimination step for each.
- Probe hygiene rules that stop a missing tool from looking like a clean result.
- Guidance for tracing which file or process is actually in effect.
- Guidance for zombie processes, abandoned sessions, and detached helpers.
- A fixed report shape that separates events, eliminations, unknowns, and live state.

## Benefits
- A conclusion is drawn only after every candidate has been checked against an artifact.
- Unknowns are named, not filled with a plausible story.
- A kill or cleanup does not destroy work that exists only in a session.
- A retraction is checked with the same rigor as the original finding.

## Procedure
1. Build the timeline first. Pull exact event timestamps from the most authoritative lifecycle record: the service's own log, the application's main log, the system log for the process, and the launch service's state. Check each log's timezone, convert everything to one zone, and then correlate.
2. Rank candidate causes. For a self-restart, the usual order is: a crash or unhandled error; memory pressure that makes the system kill the process; a termination signal sent by the process itself or by another process; an operator action visible in shell history or the reboot record; an update or installer that relaunches the service; a scheduled job; and a configuration change followed by a restart.
3. Eliminate each candidate with a fresh read and name the artifact that supports the elimination. Examples: a crash-report directory listing, a memory-pressure query, a shell-history file's modification time used as a record of activity, an installer log, the scheduled-job list, or a configuration file's modification time. Never write "ruled out" without the artifact.
4. Correlate every event in the report. One complaint can contain several separate restarts. Put them on the same timeline before naming any cause.
5. Say "unknown" when the record does not identify the sender. If a shutdown record shows that the parent of the signal is not recorded, state that the sender cannot be identified, then list what was ruled out. Do not invent a culprit.
6. Confirm the live state at the end with a fresh query in the same report: the process list, the port owner, or the service state.

### Probe Hygiene
- **A missing tool is not a clean result.** A search tool that is absent exits with an error, and a pipeline that swallows the error still reports "no matches." Read the exit code. Exit 0 means matches were found, exit 1 means none were found, and anything else means the probe did not run. Only exit 1 supports an "absent" claim.
- **Prove a negative with a positive control.** Before you claim a string is absent, show that the same search finds a string you know is there.
- **Re-run each load-bearing negative bare, and record its exit code** in the transcript.
- **Scope broad searches.** A recursive search across a large home directory can time out and return partial results that look complete. Search the live configuration and the active profile first, then widen.
- **Trace the active file to its owner.** For a file a service reads, find the process serving the port, read its full command line, and identify the file it selects. Then confirm the loader's rule in the code. A documentation page alone is not proof.
- **Source code and logs do not prove execution.** A command string inside a script is not evidence that it ran in the incident window. An error log that quotes a command shows the command failed, not that it succeeded. Check the file's time against the window, the session records for an actual invocation, and the output lines around the entry.

### Zombie and Repeating Processes
- **Kill the top-level process, not a helper.** Browser-style apps run renderer and utility helpers under one main process. Killing a helper makes the parent start it again. Find the process whose parent is the launch service or whose parent is alive, and stop that one. Verify with a fresh process count in the same report.
- **Process liveness is not work liveness.** An agent session can stay alive for days while its login has expired. Read the session's transcript to see whether it is doing any work. A transcript whose last line reports an expired login, and whose modification time is days old, is an idle session.
- **Check before killing a long-lived session.** Confirm that no tracked task references it, that it has no unpushed commits (compare the local branch with its remote), and that any uncommitted files are backed up first into a dated folder. If all checks pass, the session's work is in version control and on the board, and stopping the session loses nothing.
- **Detached helpers need a deliberate cleanup.** Headless browsers and other children can detach and never be cleaned up. Use a scheduled janitor that targets only the helper type you own, skips anything with a live parent, applies an age limit, and logs each kill. Do not rely on each session to clean up after itself.

### Retractions and Verification
- **Reproduce the other method before disputing a finding.** Re-running your own weaker probe with more confidence is not a disproof. Check the artifact's hash to rule out a different file, and if the hash matches but the results differ, compare the methods step by step.
- **Scan structured data recursively.** A check that looks only at top-level keys can certify a file that contains sensitive values nested deeper. Walk the whole structure.
- **Refresh the verdict after tests.** Tests can rewrite the artifact you are judging. Capture the verdict before the tests, run them, then base the final disposition on a fresh verdict.
- **Verify append-only records by their top-level field.** After a write, parse the file and confirm the new top-level timestamp appears exactly once. A raw text search can count nested copies of the same value.

### Report Shape
1. What happened, with the exact time of each event on one line each.
2. What was ruled out, with the artifact that supports each elimination.
3. What remains unknown, stated plainly.
4. The current live state from a fresh query made in this report.
5. Whether user data survived. A detached session is not a deleted session, and child processes that were not killed keep running.

## Pitfalls
- **Guessing the cause to close the story.** An unidentified sender stays unidentified.
- **Trusting one log.** Correlate at least two independent records before naming a cause.
- **Mixing timezones.** A UTC log and a local-time log can place events hours apart.
- **Killing helpers instead of the parent.** The parent restarts them, and the symptom appears unchanged.
- **Killing a session with unsaved work.** Check version control and the board first.
- **Writing an absence claim from an empty result.** Check the exit code and run a positive control.
- **Treating a quoted command in an error as a successful run.** Read the lines around the entry.

## Verification
- Every elimination in the report names its artifact.
- The timeline uses one timezone and lists every distinct event.
- The live-state query was run in the same report and its output is quoted.
- Any kill has a fresh process count showing the result.
- Any retraction was checked with the other party's method.
