---
name: execution-discipline
description: Use when an agent loops in analysis, narrates progress without acting, or must stop a running loop. Set read limits, pair every progress claim with a change, and halt processes so they stay halted.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [execution, loops, progress, blockers, halting, agent-behavior]
    category: agent-discipline
related_skills: [minimal-change-operator, agent-honesty, ask-before-assuming]
---

# Execution Discipline

## Overview
An agent that keeps reading, planning and narrating without changing anything burns time and context. The failure looks like diligence: each turn adds another "let me check", and no file changes. This skill sets three limits: a bound on evidence gathering, a rule that progress claims come with a real change, and a procedure for stopping loops and blocked work so they stay stopped.

## When to Use
- The agent is executing a task from a queue, a card or an assignment, rather than in a free-form conversation.
- Several pieces of evidence are in hand, and no decision has been made.
- The operator said to start, or to stop reading and do the work, and the agent is still reading.
- A response was cut off, and the agent is about to resume.
- The operator asked to halt a loop, a daemon, or a scheduled job.

## Features
- A read budget: decide after three sources, and never pass five without a decision or an action.
- A rule that a progress claim needs a state change in the same turn.
- Resumption rules for truncated responses, so the analysis is not repeated.
- A limit on credential searches, after which the task is blocked with a named cause.
- A halt procedure that removes the process from its supervisor, not just its process ID.

## Benefits
- Work moves from reading to changing within a few turns.
- A blocked task names its cause early, instead of searching until the budget runs out.
- A halted loop stays halted.

## Procedure
### 1. Bound the reading
Decide after the third piece of evidence. Never pass five sources without a decision or an action.

| Evidence gathered | Action |
|---|---|
| 0 to 1 reads | Keep gathering |
| 2 reads | Decide whether one more is needed |
| 3 or more reads | Act on what you have |

Find a file path with a search tool before reading it. If a read fails, search for the real location. Do not guess another path.

### 2. Pair every progress claim with a change
A sentence that says work has started, or is under way, needs a state change in the same turn: a file written, a patch applied, a process started, or a configuration changed. If the turn only read files, write "queued" instead of "started".

Check the end of each turn that reports progress. Did this turn change something? If not, make the change now or change the wording.

### 3. Resume from the last action, not from the analysis
After a truncated response, do not restart the analysis. Look at the last tool call:
- If it was a read, the next action is a write, or a read of a different resource.
- If it was a write, verify it.
- If the cut came partway through a tool call, retry that call.

Two consecutive turns with no tool call mean the loop has started. Stop narrating and act.

### 4. Act on a "do the work now" signal
When the operator says to stop reading and start, the next tool call must change state. Pick the most likely fix from what has been read, make it, verify it, and then move on. A wrong fix followed by a correction costs less than another round of reading. Block only on the conditions in step 6.

### 5. Limit credential searches
After two different search methods have failed to find a credential, stop searching. Report the task as blocked with a named cause, in the form `BLOCKED_ON <credential>: not in the environment, not in the secret store, no accessible source`. Do not try more search paths. A missing credential is a blocker, not a search problem.

### 6. Retry only the right failures
Retry once when:
- A tool call failed, with different parameters.
- A file was not found, and the alternate locations have not been checked.
- A network call timed out.

Never retry the same search method twice, and never repeat a turn that made zero tool calls.

Block, instead of retrying, when:
- Credentials are unavailable after two search methods.
- A required external system is down.
- A human decision is needed, such as a design or policy choice.
- The task specification cannot be resolved by reading more.

### 7. Halt a long-running loop
When the operator says to stop a process, a scheduled job or a loop:
1. Match jobs by their full name, not a truncated identifier.
2. Stop only the named jobs. Leave unrelated services running, including ones with similar names, unless the operator named them.
3. If a process manager can restart the process, remove it from the manager's list and disable its launch agent or service unit. Killing the process ID alone is not a halt, because the manager starts it again.
4. Confirm the process is gone, and that the manager does not respawn it.
5. Do not keep a loop alive to collect more samples unless the operator asked for them.

## Pitfalls
- **Narrating without changing.** A reply that says "starting now" after only reads is a false progress claim.
- **Re-analysis after truncation.** Resuming from the top repeats work and adds no new tool calls.
- **Credential search loops.** Trying method after method after the answer is "not available" wastes the budget.
- **Analysis paralysis.** Each turn asking "what else do I need to know" delays the first change. Decide at the third source.
- **Killing a supervised process by ID.** The supervisor restarts it, and the loop continues under a new ID.
- **Halting a job by a truncated name.** A prefix match can stop the wrong job or miss the right one.
- **Restarting a halted job because a status check looked stale.** A stale status is a reason to check again, not to restart.

## Verification
- Each progress claim in the reply has a state change from the same turn.
- A blocked task names its cause and lists the methods that were tried.
- A halted loop was verified gone, and its supervisor entry was removed or disabled.
- No job outside the operator's named set was stopped.
