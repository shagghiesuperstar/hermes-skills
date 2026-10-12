---
name: hermes-slash-command-coaching
description: Use when a Hermes user needs the right slash command for a running task. Covers the decision rule for steer, queue, background and interrupt, plus goal, loop and plan.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, slash-commands, steer, queue, goals, operator, guidance]
    category: hermes-operations
related_skills: [hermes-api-dispatch, hermes-gateway-ops]
---

# Hermes Slash Command Coaching

## Overview
A Hermes session can take a new message while a turn is still running, and the right response depends on two questions:
is the message about the running task or a different one, and does it need to act now or after the turn. The slash
commands answer those questions. Choosing the wrong one restarts a turn that did not need to restart, or queues a
correction that should have landed at once. This skill is the decision rule, the trigger signals in a message, the
format for a one-line tip, and the anti-patterns to avoid.

Command names and defaults change between releases. Before you rely on one, check the installed version's help output
for that command.

## When to Use
- A user asks how to steer, queue or background a running task.
- A user's message fits a slash command better than a plain reply, and a one-line tip would help.
- A user asks how to run a long objective, a timed check, a plan, or a context compression.

## Features
- Decision table for a message sent during a running turn: background, steer, queue, interrupt, or side question.
- Decision table for the shape of the work: goal, loop, plan, compress and undo.
- Trigger-phrase table that maps a message to a command.
- A strict one-line tip format, given only after the work is done.
- Anti-patterns that cause wrong advice.

## Benefits
- A correction lands without restarting the turn.
- A new subject runs in its own session, and the current chat stays free.
- Long objectives run to a judged finish instead of stopping after one turn.
- Tips stay short, so they help without interrupting the work.

## Procedure
1. Decide with two questions about the message:
   - Is it about the task that is running now, or a different task?
   - Does it need to happen now, or after the current turn?

   | Situation | Command | What it does |
   |---|---|---|
   | Different task, do not wait | `/bg <prompt>` | Runs in a separate session; the current chat stays free |
   | Same task, correction, now | `/steer <note>` | Lands after the next tool call, with no restart |
   | Same task, follow-up, later | `/queue <prompt>` | Waits until the current turn finishes |
   | Same task, wrong direction | Plain message (interrupt) | Stops the turn; the agent restarts on the new input |
   | Side question, no action | `/btw <question>` | Answers about the conversation without changing the task |

2. Pick a command for the shape of the work, when interruption is not the issue:

   | Situation | Command |
   |---|---|
   | Multi-hour objective with a finish a judge can check | `/goal <objective>`; draft the contract first, add deterministic checks, or park on a process |
   | Same check on a timer, stopping on evidence | `/loop <interval> <prompt> [--times N] [--until <condition>]` |
   | Think before touching anything | `/plan <task>`; writes a plan file and runs nothing |
   | Context is long and drifting | `/compress <focus>` |
   | Rerun with different framing | `/undo`, then retype the message |

3. Set the default busy behavior if the user wants a different one. Check the current default in the config, then set
   it through the config command. A message can override it for one turn with the busy-mode command.

4. Match the user's message to a trigger, and only nudge when the signal is clear. If two triggers fit, use the higher row
   of the trigger table:

   | Signal in the message | Command |
   |---|---|
   | "also", "one more thing", during a run, same task | `/steer` |
   | "after that", "when you're done", "next", during a run | `/queue` |
   | A new subject during a run | `/bg` |
   | "stop", "wait", "wrong", "undo that" | Interrupt; no tip needed |
   | "what does X mean", no action wanted | `/btw` |
   | "keep going until", "end to end", "overnight" | `/goal` |
   | "every N minutes", "poll", "until it is green" | `/loop`, or a scheduled job if it must outlive the session |
   | "how would you", "don't do it yet" | `/plan` |
   | The context has been compacted more than once, or the user re-explains a lost detail | `/compress <topic>`, or a fresh session with a title |
   | The same objective is restated in plain chat a third time | `/goal` |

5. Give the tip only after the work is done. Use one italic line at the end of the reply, with the command, a reason of
   six words or fewer, and what would have changed. Give at most one tip per message, and do not repeat a tip the user
   already uses.

### Tip format
> *Operator tip: `/steer` fits this, because it is a same-task correction. Plain input restarts the turn; `/steer <note>` lands it without a restart.*

Rules for the tip:
- The requested action comes first. The tip never replaces the work.
- One tip per message, and no paragraphs.
- If the user asks to stop tips, stop them for the rest of the session.

## Pitfalls
- **Coaching from a summary of a command is not enough.** Check the installed version's help for the exact subcommands and
  the exact timing. For example, a steer lands after the next tool call, not at an arbitrary point.
- **A "also" that concerns a different topic is a background task, not a steer.** Match the topic first.
- **Nudging on an ambiguous signal wastes the user's attention.** When the signal is unclear, say nothing.
- **A long objective started in plain chat has no finish condition.** Give it a goal with a judge, and a task record on the
  team's board in the same turn if the team uses one.
- **Do not turn a tip into a lecture.** Six words of reason, one line.

## Verification
- The chosen command appears in the installed version's help output.
- A correction sent with the steer command lands in the running turn without a restart.
- A tip, when given, is one italic line placed after the completed work.
- The user's busy-mode default is the one stated in the config after any change.
