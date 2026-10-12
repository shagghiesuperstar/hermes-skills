---
name: external-coding-agent-orchestration
description: Use when delegating repository changes to a headless coding agent CLI while the orchestrator keeps scope, safety, review, and verification.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [coding-agents, orchestration, delegation, verification, headless-cli]
    category: agent-orchestration
related_skills: [harness-task-prompting, adversarial-review, cursor-agent-cli, codex-cli-integration]
---

# External Coding Agent Orchestration

## Overview
An orchestrator can hand implementation work to a headless coding-agent CLI such as Grok Build, Claude Code, Codex, or OpenCode, and keep control of the scope, the safety rules, the review, and the verification. The delegated agent's final message is a claim, not proof. The orchestrator verifies the diff, re-runs every gate itself, and sends findings back to the same agent session. When the agent is sandboxed and cannot reach the network or a git remote, a separate driver with that access finishes the job.

## When to Use
- The user needs a named external model or CLI to do repository work, and the current agent must orchestrate rather than author the change.
- A long, multi-file change needs an implementation pass plus an independent review.
- An external lane needs to drive a service through an MCP server rather than a repository. The same dispatch rules apply, with the upstream artifact verified on the live instance instead of a diff.

Do not use this skill to install or log into a CLI. Use the setup skill for that.

## Features
- A workflow that establishes repository doctrine and a clean baseline before any delegation.
- A delegation prompt template that states the exact path, the reading list, numbered invariants, prohibited actions, required commands, and a report schema.
- A sandboxed-agent driver pattern: the agent produces local work, and a driver with network access verifies and ships it.
- Headless dispatch rules: confirm each launch with a process identifier, smoke-test each engine first, pin the model identifier, and set effort as a flag.
- Judge, long-session, and remote-SSH dispatch patterns for common delegation shapes.
- Review heuristics for policy that must hold end to end, for whole-collection writes, and for reports that mix intent with outcome.

## Benefits
- Scope and safety rules are fixed before the agent starts, so they are not renegotiated mid-run.
- A launch is confirmed with evidence, so a dispatch that never started is not reported as running.
- The driver pattern keeps unverified citations and placeholder rows out of a shipped change.
- Independent review finds policy gaps that a passing test suite does not show.
- Each finding goes back to the same session, so the agent keeps its context and the fix is checked again.

## Procedure
1. Establish doctrine before delegating.
   - Read the repository's agent instructions, architecture notes, and any contracts the task depends on.
   - Confirm the absolute repository path and the branch.
   - Check the working tree. If the task requires a clean start, stop on any unexpected change.
   ```bash
   git -C "<repo>" status --short --branch
   ```
   - Run any baseline check the task requires before the first edit.
2. Discover the CLI's real headless interface. Check the installed version and the help text, and do not guess flags.
   ```bash
   command -v "<cli>" && "<cli>" --version && "<cli>" --help
   ```
   Select the required model explicitly. For a long prompt, write it to a file outside the repository. The file is an auditable record of the delegation.
3. Smoke-test each engine with one trivial prompt before you read any context, such as "Reply with exactly: <SMOKE_OK>." This shows that authentication, dispatch, and output parsing work. A cached model list does not prove the engine will serve a request. If the required model fails the smoke test, stop. Do not switch to another model or engine without the operator's approval. If one engine of a requested pair is blocked, continue with the working one and report the error.
4. Write the delegation prompt. Include:
   - the exact absolute repository path;
   - the documents to read first;
   - the implementation contract as numbered invariants;
   - the prohibited actions and protected paths;
   - the exact commands to run and the evidence to return;
   - an instruction to keep fixing failures until the gates pass;
   - a no-commit rule when the task requires one;
   - a report schema: changed files, commands and results, status, and blockers.
   End the prompt with a completion line the orchestrator can grep, such as `<PHASE>_DONE key1=<n> key2=<n>`. Name any required output as a file that must exist on disk when the run ends.
5. Run the agent headlessly with the explicit model. Give it enough turns for implementation, tests, and repair. Keep the permission settings the operator has already approved for this profile. Ask the agent to run in the foreground and not to start background forks, because a background fork can be cut off when the run ends. For a bounded long run, start a tracked background process and poll it. Do not start an untracked daemon.
6. Confirm the launch with a process identifier. Quote the identifier in the same message in which you report the dispatch. Poll that identifier until it exits. Judge liveness by file modification times and sizes, and by the process's CPU use, not by whether output has appeared recently.
7. Inspect the result independently.
   ```bash
   git -C "<repo>" diff --stat
   git -C "<repo>" diff --name-only
   git -C "<repo>" diff --check
   git -C "<repo>" status --short --branch
   ```
   Read the new and high-risk files directly. Trace each invariant through every boundary it crosses, from configuration to record to plan to executor to report, rather than checking only the most visible script. Search specifically for bypasses of policy, destructive writes, and defaults that are documented but not enforced.
8. If the review finds a gap, send the finding back to the same agent session. Give the exact code path, the missing regression test, and the full gate again. Do not fix the delegated implementation yourself when the task required the external agent to do the work. Require a fix with a test, and then review again.
9. Re-run every required gate yourself, using the exact commands. For a negative rule such as "no forbidden path," scan the produced artifacts programmatically and fail on any violating value. Check the latest artifact by its timestamp and path, not a stale report.
10. Report verified state: the absolute paths of changed files, the commands with their results, the generated artifacts, and the final Git status. Separate tracked source changes from generated outputs. State whether any live write, commit, or protected-path access happened. List blockers and residual risks separately.

### Sandboxed agent and driver pattern
Some agents run in a sandbox that blocks `git push`, pull request creation, and outbound HTTP. Such an agent can still read the repository, write files, run local scripts, and commit locally.

The default failure is an agent that exits with status 0, leaves a local commit, and reports success. That commit often has citations it never fetched, placeholder rows, or a push that was rejected without anyone noticing. Treat the exit status as a claim.

The fix is a driver: a separate context that has network access and git remotes.
1. Design the work so the agent can finish something useful offline. Give it a local build and a deterministic verifier that re-runs the gate from a list of inputs. The verifier should expose every URL or value it expects the driver to check.
2. Run the agent headlessly. Capture the exit code and the agent's handoff, and treat the handoff as a checklist of unverified inputs. A verifier that ran with zero fetches is a failed gate, even when it reports a pass.
3. The driver re-runs every gate that touches the outside world. It fetches each cited URL and confirms the supporting text is on the page. It runs each banned-term check against the actual files, using the repository's own list. It checks the remote ref and the pull request state directly, and never takes "pushed" on the agent's word.
4. The driver fixes the stubs on the same branch and adds a follow-up commit. The first commit shows what the sandboxed agent produced, and the follow-up shows what the driver changed. Use a commit message that names the engine and what the driver corrected.
5. The driver pushes, opens the pull request, and reports the live state. The agent's handoff goes into the report as its own section, so the reviewer can see both halves.

This pattern fixes a gap in network access. It does not catch an agent that invents facts or misreports its own actions. Apply the separate anti-fabrication checks for that.

### Judge dispatch (headless, single-shot)
Run an independent judge over a frozen artifact, such as a diff, a plan, or a checkout state. The judge never edits anything.
1. Pick a judge from a different vendor than the builder, and make sure it is billable right now. A model listed in a cache does not prove it can serve requests. If the judge reports a hard credit or billing block at start, do not retry it. Switch to the fallback judge and log the substitution, keeping the same verdict shape.
2. Write the judge prompt to a file. It must say the judge is advisory only, with no file edits and no builds. It must ask for a verdict, cited evidence (a path and line, or a quoted snippet), and the minimal fix path, and it must cap the answer's length. Carry the repository context inline: the symptom, the prior root-cause notes, and the current checkout state. The judge sees only its own working directory.
3. Verify that the judge read the code. A verdict that cites concrete files and values is usable. Generic advice with no citations earns a retry with a tighter scope.
4. Strip banners, transport errors, and hook output from the judge's output before you read the verdict. An error line is not a verdict.

### Long autonomous sessions
Use an autonomous coding harness for work that will outlast one orchestrator turn: multi-file, pipeline, or integration work, or anything expected to take an hour or more. Use a direct worker for a single-file edit or an emergency hotfix.
1. Build the task brief from the objective, the spec, the branch name, the acceptance criteria, and the rule that the tests pass and a pull request opens against the main branch.
2. Launch the session as a tracked background process. Log the start time and record the process identifier.
3. Poll the process every few minutes. Do not read a quiet period as a stall, because some harnesses keep working through a context compaction. Judge liveness by fresh artifacts and process activity.
4. When the pull request appears or the process stops, report either the pull request link or, if there is none, the last known output as a blocker.
5. If the session stops early with no pull request, the model probably dropped a tool call, so restart with a stronger model. If it runs for hours with no pull request, send a steering correction instead of killing it.
The orchestrator steers, reviews, and merges. It does not write the code during the session.

### Remote headless dispatch over SSH
- Run the remote command non-interactively with an explicit key file, and do not forward the agent socket. Verify the remote host key instead of turning host-key checking off.
- Measure the target's context window in headless mode. If the orchestrator's instructions exceed it, use a smaller model, a narrower working directory, or trimmed instructions.
- Check the target's memory headroom before you load a model. A model that does not fit is refused or evicts pinned models. Restart the local model service to free slots, and confirm its health endpoint before you dispatch.
- Put flags in the order the CLI expects. A global flag placed after the subcommand is rejected.
- Keep the provider configuration file on the remote host, outside any repository, and keep its keys local.

### Review heuristics

#### Policy must hold end to end
A default in a configuration file and a command-line flag are not enough. Confirm the rule at config loading and precedence, at record construction, in the pure planning function, at the executor's inputs and side effects, in the timestamped report, in the summary report, and in the tests.

#### A whole-collection write needs an atomicity check
When a backend replaces a collection or a metadata field in one request, a later corrective merge does not undo an earlier destructive write. Before you implement a repair for a large collection:
1. Check the installed dependency for an incremental create, attach, or detach route. Do not infer that a route is missing from one rejected request shape.
2. If only full replacement exists, send one minimal, complete payload, and report its serialized size.
3. Treat a deterministic payload-size rejection as non-retryable. If the complete payload is refused, preserve the old collection and report a blocker. Do not try growing prefixes, because the final request still replaces the whole collection.
4. Test with a fake that refuses an oversized combined payload and accepts the exact minimal one, and assert that the final collection matches exactly.

#### A dry run must not change state
A dry run may write a plan file with a timestamp. It must not advance counts, recovery phases, or the last-run record. A dry run that promises an exact comparison needs an authoritative read from the live system. If a read fails, fail that item's plan. Do not present stale state as current. Only a verified live run may advance state.

#### An allowlist must match exactly
For an allowlist, test the exact set of accepted values, not only the absence of a forbidden token. A check that rejects only names containing one forbidden word will accept many names it should reject.

#### Agent output is not verification
Rerun the tests and read the artifacts after the agent exits. A green summary can hide a stale report, an incomplete scan, or a gap that no test covers. A structured field such as a pull request URL, a file count, or a build status is also a claim. Check it with the host's own tools, for example by listing open pull requests and reading the branch's diff stat, and quote those results.

#### Reports must separate intent from outcome
Count results from recorded outcomes: success, skipped, verification failure, and operational error. Fill in real identifiers only from a successful response or a read-back. Keep planned identifiers in their own field. A dry run leaves the result fields empty. Test each path with a fake client: full success, a repeated run, a skip, a verification failure, and a transport error.

#### Scope cleanup by ownership
When a pipeline removes resources from a shared parent, check both ownership and eligibility. A filter that removes everything that looks forbidden can delete a sibling's resources. Match on an explicit owner key, and test owned, sibling, and operator-managed entries together.

#### Scan artifacts by their fields
Do not treat a prose note as a file path because it mentions a file extension. Check the enumerated fields that hold paths. If a recursive scan is unavoidable, extract the path tokens first, validate those, and print how many were inspected and which values violated the rule.

## Pitfalls
- **Do not treat a delegated agent's success report as the ship signal.** An independent review can find a destructive intermediate write or an ungated branch that the tests never reached.
- **Do not edit the product repository from the orchestrator when the operator required an external agent to do the work.** Write specs and tasks instead, and send small visual fixes to a lightweight task.
- **Do not wait for a background run that has already finished its work.** An optional preview step that is still running is not a reason to hold the commit.
- **A launch that was announced but never started is a silent failure.** Confirm each process with its identifier before you report it. Report anything you cannot confirm as unverified, and check it on the next turn.
- **Do not claim a result from memory.** A status from an earlier turn is not evidence. Only a fresh process check or a fresh file read counts.
- **A required model that fails its smoke test is a stop, not a substitution.** Upgrading the tool, or swapping to a default model, changes what was reviewed.
- **Keep the cost cap as a hard limit.** A budget cap on a headless run is a guard, and hitting it is a failure to handle, not a target to aim for. Preserve the partial result before you stop the run or relaunch it.
- **Do not ask a headless run for token counts or cost in its report,** and do not copy usage fields into a status message. Parse only the result field.
- **Treat a clean exit as unverified until the repository says otherwise.** Always capture the final Git status and the diff checks.
- **Serialize writers.** Only one agent, or the orchestrator, may edit a given plan or state file at a time. Running a second writer against the same checkout produces a mix of both sets of edits.
- **Judge a second reviewer only after the first writer has exited,** or give it a frozen copy of the material.
- **A wrong premise needs a restart, not a correction.** When new information shows the brief targets the wrong repository or domain, stop the run, correct the prompt file with the change marked clearly, and relaunch.
- **Route flags are guide rails, not walls.** A model-facing permission flag can change meaning between CLI versions. If you need a guarantee, enforce it in a wrapper that checks each call before it runs.
- **Deduplicate runs by item and commit, not by time.** Record each reviewed commit after its result is posted. A repeated trigger for the same commit should do nothing.
- **Fix an upstream flaw upstream when you can.** A local workaround for a bug in a shared project helps only this machine. Reproduce the bug on a separate clone, find an analogous fix the project already accepted, and send a minimal change upstream. Record the change's link in the local workaround, and mark the workaround as temporary.
- **Do not test an upstream change on the live installation.** Use a separate clone. Otherwise the next update silently removes the local patch, and the test results do not match a clean build.
- **Do not auto-create a missing engine configuration to pass a health check.** A missing configuration is a setup failure to report, not something to paper over.
- **A judge's ready verdict is not a pause.** If the standing goal is still open, queue the next allowed task instead of waiting for the operator to ask.
- **Run unattended wrappers from a scheduled job that is silent on success and loud on failure.** Write an alert file and exit nonzero on failure, and verify the job's fields rather than its creation status.
- **Restart a service from a separate shell.** A process cannot restart itself through its own service manager.
- **Short-lived provider tokens expire mid-run.** A 401 from a provider usually means the token expired. Refresh it with the platform's login command, then retry.
- **A custom provider needs an explicit model map.** Without one, model resolution fails.

## Verification
- [ ] Required repository documents read
- [ ] Initial Git state captured
- [ ] Requested model explicitly selected and smoke-tested
- [ ] Safety constraints stated in the delegation prompt
- [ ] Each launch confirmed with a process identifier
- [ ] External agent edited the files and ran the tests
- [ ] Independent diff and code review performed
- [ ] Findings sent back to the same agent session
- [ ] Every required gate re-run independently
- [ ] Generated artifacts scanned programmatically
- [ ] Final absolute paths and Git status reported
