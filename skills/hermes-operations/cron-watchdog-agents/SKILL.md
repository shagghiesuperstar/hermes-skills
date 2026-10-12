---
name: cron-watchdog-agents
description: Use when authoring or debugging a cron job that runs CI, repo watches or other automation. Covers toolsets, silent failures, honest reporting and escalation.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [cron, automation, ci-cd, watchdog, monitoring, hermes]
    category: hermes-operations
related_skills: []
---

# Cron Watchdog Agents

## Overview
A cron job that drives an agent runs unattended, so its failures are quiet. The usual failure is not a crash. The job
runs, reports nothing useful, or reports "all clear" when no real check ran. This skill covers how to give a scheduled
agent the tools it needs, how to tell an environment gap from a code regression, how to keep reports comparable from
run to run, and when to escalate versus pause.

## When to Use
- You are creating a scheduled agent for CI lint or tests, a git repo watch, or a service health check.
- A scheduled report is empty, says "no useful content", or says "tools not found" on every run.
- A check reports green, but you suspect it did not actually run.
- A noisy alert has repeated for several runs and needs an owner, a fix, or a pause.

## Features
- Minimum-toolset table for common watchdog tasks, so the agent can run its commands.
- No-agent script mode for threshold checks: silent when healthy, one line when breached.
- A hard gate that rejects an all-clear when zero real checks ran.
- Failure triage: environment gap versus code regression, and blank output versus real failure.
- A fixed report shape and an escalation rule that keeps the channel useful.

## Benefits
- Silent failures become visible in the first run instead of after weeks of misleading green reports.
- Reports stay comparable from run to run, so a real change in state stands out.
- Environment gaps stop being mistaken for regressions, and regressions are not buried under environment noise.
- Operators get one clear message per problem instead of the same alert every cycle.

## Procedure
1. Declare every toolset the agent needs. Omitting one is the most common silent failure:
   ```python
   cronjob(
       action='create',
       name='CI Watchdog',
       prompt='Run lint and tests for the watched repos. Report PASS or FAIL per repo, with the first error lines.',
       schedule='0 * * * *',
       skills=['<skill-the-agent-must-load-first>'],
       enabled_toolsets=['terminal', 'file'],
       deliver='origin',
   )
   ```

   | Task | Required toolsets |
   |---|---|
   | Lint or test runs | `terminal`, `file` |
   | Git log or repo watch | `terminal`, `file` |
   | Web monitoring | `terminal`, `web` |
   | Browser automation | `browser`, `terminal` |

2. Preflight the environment on the machine that will run the job before scheduling it:
   ```bash
   git -C <repo> fetch --dry-run
   command -v ruff mypy pytest
   ls <repo> > /dev/null && echo accessible
   ```

3. Use a no-agent script for threshold checks such as disk, memory, service uptime or git drift. Make the script print
   nothing when healthy and one line when the threshold is crossed. An empty stdout means the scheduler sends no message:
   ```bash
   #!/bin/bash
   THRESHOLD=<limit>
   COUNT=$(<command-that-counts> 2>/dev/null || echo 0)
   if [ "$COUNT" -gt "$THRESHOLD" ]; then
     echo "Drift: ${COUNT} exceeds ${THRESHOLD}. Fix: <one-line repair>"
   fi
   ```
   Pass the script to the scheduler as a bare filename. The CLI resolves it inside the active profile's scripts
   directory, and absolute or `~` paths are rejected.

4. Run each tool by absolute path from inside the repo root:
   ```bash
   cd <repo> && <repo>/.venv/bin/ruff check . --quiet --exclude ".venv*"
   cd <repo> && <repo>/.venv/bin/python -m pytest --tb=short -q --no-header
   ```
   Exclude vendored environments from every lint count. Record the exact command in the report so the next run uses
   the same one.

5. Apply the hard gate before writing any all-clear. Count the checks whose status is `pass` or `fail`. If zero checks
   ran, the run is an infrastructure failure. Report it as one, and tag the owner. Never report it as green.

6. Triage every failure before you report it:
   - `ModuleNotFoundError` for a third-party package means an environment gap. Install the package into that repo's
     venv and re-run. Do not call it a regression.
   - `AssertionError`, `NameError`, `AttributeError`, or an `ImportError` from a relative import usually means a real
     regression. Report the file and line.
   - Blank test output is ambiguous. Check whether the repo has tests and whether its venv has pytest, then run the
     test collection step (`pytest --collect-only`) to get the real traceback before deciding.
   - Exit status 141 from a script that is silent on purpose is not automatically a broken script. Redirect its output to
     a file, then read the file.

7. Escalate by impact, not by how real the finding is:
   - Tag the owner only for a production blocker, a broken build in a deploy path, or an outage.
   - Put non-blocking findings in the table without a tag, even when they are real.
   - After three identical reports, send one message that asks "X is broken: fix or pause?" and stop repeating it.
   - If the owner has not acted in six hours, escalate to the orchestrator.

8. Write the report in one fixed shape every cycle: a one-sentence headline, one table with the same columns each run,
   and one to three next actions. Keep the counts you report comparable by using the same command and exclusions each
   time.

9. Control the job from the machine that owns it. `cron list` and `cron pause` only see jobs on the current machine.
   Pause or edit the existing job rather than removing and recreating it, because recreating resets run history.

## Pitfalls
- **Missing toolsets fail silently.** The agent runs, cannot execute commands, and writes an empty or generic report.
  Declare every toolset in the job definition.
- **Never call a vacuous pass green.** A runner can report an aggregate pass when every check was skipped, because its
  pass flag starts as true and only changes when a check runs. Count real runs before you trust the flag.
- **Do not suppress the alert when the toolchain is missing.** A silent run hides the outage. Send a short
  infrastructure alert every cycle until the toolchain is back.
- **Do not add a caveat after a green marker.** Downstream tools key off the marker, not the prose. A hedged all-clear is
  still an all-clear.
- **The hard gate starts the investigation.** When it fires, run the tools directly from their venv paths to get ground
  truth, then report both.
- **Do not `source` a venv between repos.** The activation persists across `cd`, and the next repo can silently run the
  wrong interpreter. Use absolute paths to the binaries.
- **Run tools from the repo root.** Run from anywhere else and the tools walk unrelated trees, such as mounted volumes or
  installed packages, and report errors that are not in the repo.
- **Count with venvs excluded.** Without the exclusion, lint counts include vendored site-packages and can swing by an
  order of magnitude between runs.
- **Do not pipe a silent script into `head`.** A reader that exits early causes SIGPIPE in the writer. Redirect to a
  file, then read it.
- **Question a sudden drop in lint counts.** A one-cycle drop with no commits usually comes from a cache or a config
  change. Re-run with a cleared cache before you report progress.
- **Do not retry a blocked command in a different shape to get past a tool's safety check.** Report the block, and use a
  supported path or ask the operator.
- **Check auth in both places.** A profile's auth file keeps credentials in a provider map and in a credential pool.
  Check both buckets. Treat an `active_provider` field there as metadata, not as the authority.
- **Do not treat a remembered fix as done.** Verify the live state before you say a previously reported issue is fixed.

## Verification
- Run the job once by hand with `cron run <job-id>` and read the output. It should show real check counts, not only a
  status word.
- Break one check on purpose in a scratch branch and confirm the alert fires. Then restore it.
- Confirm a healthy threshold script produces no output and no message.
- Confirm the report has the same columns and the same lint command as the previous cycle.
