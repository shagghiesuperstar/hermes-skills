---
name: say-do-verify
description: Use when telling the operator that something will happen, is done, is live, or was created. Run the check in the same turn, quote its output, and correct any earlier claim the check does not support.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [verification, promises, claims, status-reporting, live-checks, honesty]
    category: agent-discipline
related_skills: [agent-honesty, execution-discipline, source-grounded-investigation]
---

# Say, Do, Verify, Report With Proof

## Overview
The most damaging failure in an agent's status reports is a gap between the claimed state and the real state, with nothing that compares them. The agent reports memory, a card status, a worker's self-report or a list entry as fact. This skill closes the gap. Every promise is recorded with a check that probes the outcome. Every claim that something changed is backed by a tool result from the same turn. When a claim turns out to be false, the correction comes first.

## When to Use
- Before saying something will happen: "I'll merge it", "it will be live in about two hours", "the build is running".
- Before reporting status on a task, a deployment, a job or a site.
- When a notification or a scheduled message reports a completed step.
- Before naming an identifier, such as a card, ticket or build number.
- Before saying a deadline or an estimated time. Clock times need a real clock reading.

## Features
- A promise ledger: each promise has its outcome check, a time estimate, and the cards that carry it.
- A rule that a check must test the last clause of the promise, not an earlier step.
- Value assertions, not key-existence checks, for every probe of an API or a file.
- Same-turn proof for any sentence that says a one-shot action succeeded.
- A reprobe rule: a delivered promise that fails later is reopened at once.

## Benefits
- Status reports match live state, so the operator can act on them.
- Silent failures surface as alerts, not as surprises on a live page.
- Corrections are short, and they arrive before anything else in the reply.

## Procedure
### 1. Record a promise before stating it
When you tell the operator that something will happen, record a promise in the same turn. Write:
- The promise in plain words, as the operator heard it.
- The cards or jobs that carry it.
- A time estimate, from now, not from an earlier plan. Compute it with a real clock reading.
- A check: a runnable command that exits zero only when the outcome is real.

Run the check once immediately after recording it. It must fail on today's state. A check that already passes does not prove delivery. It shows the check is inverted or too weak.

### 2. Make the check probe the outcome
- Probe the live artifact, not the process that was supposed to make it. A card's status, a builder's report file and a branch's existence are not outcomes.
- Assert the value, not the presence of a key. A grep for a field name passes when the field holds an error message.
- Test every clause of the promise. If the promise names two outcomes, the check covers both, and prints a line for each with the measured value.
- Count the items the promise names, instead of grepping for a name that also appears in a legend or a definition.
- For a deployment, check that the deployed version contains the fix. Do not check that the version equals the fix commit, because a later commit would then fail the check forever.
- For a check that writes to production on every run, prove the route is live with a request the service must reject, and note in the promise that the full write was not exercised.

### 3. Make the check run
A check that cannot run is worse than no check, because it keeps reporting an error that looks like a failure of the work. Put multi-step checks in a script file. Test that the command runs and exits with a code the ledger can read. A check that returns "command not found" or exit 126 or 127 is a broken check, and it gets fixed before the promise is tracked.

### 4. Quote proof in the same turn
A sentence that says a discrete action succeeded needs the verifying output in the same turn. Examples: "the key works", "the secret is staged", "the build is deployed", "the PR is merged", "the workflow is written", "the page returns 200". If the verification is still running, write "unverified, checking now", and say so again on the next turn if it is still open.

Never write "I'll verify it next turn". The next turn may contradict the sentence, and the operator has already read it.

### 5. Use the words that match the evidence
- "Merged" means the pull request is merged. "Deployed" means the deployed version contains the merge. "Live" means the public page shows the expected content. Use each word only when its probe passed.
- "Sent" means the send output reports a count. A job that has started has sent nothing until its output says so. Report the stage instead, for example "pre-checks, 0 sent".
- "Running" needs a handle: a process ID, a run ID, or a log line from after the start time. A name in a status file is not a handle.
- "Created" and "dispatched" apply only to a card or job that a tool call created in this turn. Never use them for a card you have not created.

### 6. Verify identifiers before quoting them
Write an identifier in a report only when it came back from a tool call in this turn. An identifier from memory or an earlier notification is a guess. If you did not open an item, say "finished, reading it now", and do not summarize its result from a preview, because previews are cut off.

### 7. Run the check on every reply that reports status
Open a status reply with the ledger's current list. Give each item as verified, with its proof, or as not done, with the reason and the estimate. Counts such as "twenty merged" and "three running" are not status.

### 8. Correct a false claim first
When a later check shows an earlier claim was false, the next message opens with the correction, in plain words, before anything else. Reopen the promise in the ledger, cut a fix task if needed, and say which earlier sentence was wrong and what the real state is.

### 9. Reprobe delivered promises
A promise marked delivered is not final. When a probe shows a delivered promise failing, reopen it in the same turn, record the probe output, and tell the operator. Stale checks often fail for their own reasons: a renamed host, a moved path, a counter that changed. Fix the check when the check is wrong, and keep it when the work is wrong.

### 10. Deadlines are estimates of remaining work
- A new estimate is the remaining work from now, including review and deployment. Do not copy an earlier plan's time.
- Before stating a clock time, run the clock command, then state the time both as a clock time and as a duration from now.
- An estimate that crosses the night depends on the machine staying awake and powered. Check the power state first, and say so if the estimate depends on it.
- After a gap in the session, check the machine's sleep and wake log before blaming a worker for a stall.

## Pitfalls
- **A builder-done check.** A promise to deliver a reviewed change whose check only tests that the builder finished will report delivered before the review exists. The check must test the last word of the promise.
- **A deploy check that matches the wrong commit.** Equality fails on the next commit. Use a containment check.
- **Passing silently.** A check that prints nothing and exits zero can mark a promise delivered when nothing was measured. Make every check print what it measured.
- **Absence checks that match a longer name.** A substring check for a fixed name can also match a prefixed name. Anchor the match.
- **A report file as proof.** A file the builder wrote about its own work can be stale, or wrong. Check the review verdict and, for visual work, your own look at the output.
- **An activity word beside a promise.** Writing "the speed test is running" next to a promise id reads as a completed clause. Name the job, and state the promise's status separately.
- **A conditional that reads as a closure.** "Once it is live, that closes the promise" is a future claim. Say the promise stays open until the probe passes.
- **Repeated claims after a correction.** A corrected claim re-sent in a later message needs the correction again, or it reads as a new claim.

## Verification
- Every promise has a recorded check that failed before the work and passes after it, with each clause printed.
- Every sentence stating a completed action has a tool result from the same turn beside it.
- Every identifier in the reply came from a tool result in the same turn.
- Every time estimate is a clock reading plus a duration, and was computed in the same turn.
- Every false earlier claim was corrected at the top of the next reply.
