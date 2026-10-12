---
name: opus-5-5-claude-code
description: Use when handing a long coding run, a design or copy task, or a pre-review pass to Claude Code or Claude apps running an Opus model. Covers the task brief, effort, stop rules, and checking results.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [claude-code, opus, prompting, effort, stop-rules, review]
    category: agent-orchestration
related_skills: [harness-task-prompting, claude-agent-teams-orchestration, claude-cli-model-switching, adversarial-review]
---

# Opus Models in Claude Code and Claude Apps

## Overview
The premium Opus lane is worth its cost for work where quality matters more than price: design, brand and landing-page copy, visual critique, long multi-step coding runs, and a review pass before a human reviews a change. Cheap, capable models handle bulk and mechanical work. This skill covers how to write the task so the run finishes, how to set effort, how to write stop rules so the run does not pause for no reason, and how to check the result before accepting it.

## When to Use
- Handing a long coding change through a large repository until its tests pass.
- Asking for design, copy, or creative work where the finished file is the deliverable.
- Running a review of a diff or pull request before a human reviews it.
- Checking a long plan, a deck, or a report for contradictions, or reading a chart, screenshot, or diagram.

Do not use the premium lane for bulk or mechanical work such as catalog rows, lookups, retries, or triage. Send that to the cheapest capable model.

## Features
- A one-message task template: the task, a checkable done state, and the one or two real stops.
- An effort rule: set effort with the effort setting, not with prompt words.
- A design brief pattern that lists the defaults to avoid, with the reference attached rather than retyped.
- A stop-rule starter for long runs that keeps the run going and names the stops that matter.
- A check-the-result routine that reads the blockers first and runs a block-only review pass.

## Benefits
- A run that has a finish line and named stops does not pause to ask whether to continue.
- Effort set at the setting, not in the prompt, avoids wasted reasoning text.
- A list of defaults to avoid pushes a design away from the generic look.
- Blockers and review findings are read before the rest of the output, so the operator sees the decisions first.
- Stopping at the right gates keeps destructive and external actions under human control.

## Procedure
1. Pick the lane. Use the premium Opus model for design, copy, creative work, long coding runs, and review. Use the cheapest capable model for everything else.
2. Set the effort with the effort setting. Default to `xhigh` for most work. Try `max` only as a deliberate comparison, and keep the results to compare.
3. Remove reasoning-instruction words from prompts and saved instructions, such as "think carefully," "think step by step," and "think hard." The model decides how much to think. For a short answer, say "Answer directly."
4. Write the whole task in one message, using this template:
   ```text
   <Task in one paragraph.>
   Done means: <checkable end state>.
   Stop and ask me only if: <the one or two real blockers>.
   Keep a checklist in a file. Tick each item when it is done, and add anything new you find.
   Mark anything you could not confirm, and say where you looked.
   End with three headings: Blocked on me, Changed, Found.
   ```
5. For design work, list the specific patterns to leave out. A bare request to avoid a "generic look" usually swaps one default for another. Attach the reference screenshot, chart, or design frame itself, and ask a specific question about it. Ask for the finished file, not an outline. Keep a running ban list for each brand, and paste it into every design request.
6. Write stop rules into the project's instruction file for long runs. A starter rule: keep going when a step does not need the person, put status notes in the same message as the next action, and stop only when the run cannot continue without the person or before anything destructive, such as deleting data, force-pushing, or changing anything outside the repository.
7. Keep permission prompts on for destructive commands, even when a keep-going rule is in place. Add project gates to the stop list: the agent never merges, and it stops before any change to money, publishing, DNS, email providers, or policy.
8. For an audit or migration across a large codebase, split the work: give each unit to its own subagent, check each subagent's evidence before accepting it, and finish with one table of unit, affected yes or no, and evidence. Keep the task list in a file, so progress survives context summarization.
9. Check the result. Read the "Blocked on me" section first. Then run a review pass with a narrow brief: list only problems that would block the merge, each with its file and line, why it is wrong, and how to show that it fails.
10. For research or long documents, require the run to mark anything it could not confirm, and to quote each contradiction it finds with its location.
11. If a run stops with a question such as "Want me to continue?", reply "continue." If that keeps happening, make the stop rule tighter.
12. When a run needs an agent team rather than subagents, start it in an interactive session. Print mode does not spawn teammates. Name each teammate and its model, and say "an agent team, not subagents."
13. After any model switch, confirm which model finished the work before accepting a design or creative result as the premium model's output.

## Pitfalls
- **Reasoning words in the prompt cost tokens and add no quality.** Set the effort instead, and remove "think hard" lines from saved instructions.
- **A run without a finish line never ends cleanly.** State the checkable end state in the first message.
- **Do not restart a long run to add a requirement.** Type the addition while the run works, because restarting wastes the work already done.
- **A stop rule that is too loose lets a destructive action through.** Keep destructive commands behind permission prompts.
- **Never automate the answers to permission prompts.** A cron or script that answers them removes the one check the prompt exists to provide.
- **When a usage limit blocks the run, report the limit and pause.** Do not switch to another account's login or copy a token into the environment to keep going. That is a cost guard being evaded.
- **Do not retry flagged content to get past a safety flag.** A flagged message moves to an older model, and the session continues there. Accept that, confirm which model finished the work, and reword the request only if the change is legitimate.
- **Do not ask for internal reasoning in the reply.** Ask for a short explanation of the choice instead.
- **Subagent reports are claims until checked.** Open the evidence the subagent names before accepting its result.
- **Fast mode costs more per token.** It suits back-and-forth work where the reply is read as it arrives, and it is a spend decision. Do not use it for unattended runs.
- **Long chats slow down.** Treat a finished answer as done in a chat where follow-ups matter, but not in a long analysis, where a later step can reveal an earlier mistake.

## Verification
- The task message has a done state, the real stops, and the three report headings.
- The effort is set at the setting, and the prompt holds no reasoning-instruction words.
- Design requests include the ban list, and the references are attached.
- The stop rules are in the instruction file, and destructive commands still prompt.
- The report's "Blocked on me" section was read first, and a block-only review pass was run before a human review.
- The model that finished the work is named in the report.

## Attribution
Adapted from "Getting the most out of Opus 5.5 in Claude and Claude Code," by Addy Osmani, claude.dev blog, September 2026: https://claude.dev/blog/getting-the-most-out-of-opus-5-5/
