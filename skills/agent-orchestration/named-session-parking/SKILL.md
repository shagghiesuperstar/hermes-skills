---
name: named-session-parking
description: Use when you need to create or reuse a titled agent session as a parked slot for later resume. Starts the slot without doing any work.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [sessions, parking, resume, session-management, agent-cli]
    category: agent-orchestration
related_skills: [steer-protocol, kanban-orchestration, harness-task-prompting]
---

# Named Session Parking

## Overview
A parked session is a titled agent session created or reused so that a later turn can resume it, with no investigation or work done when it is created. The two failure modes are a duplicate session that splits the history, and a new session that starts working on whatever standing instructions it inherits. This skill covers the reuse-first lookup, a one-shot spawn that exits after a single acknowledgement, and the checks that prove the slot is parked and not running.

## When to Use
- The operator asks for a named session to be parked on a particular model, for later resume.
- A title must be reserved for a session that will be resumed in a later turn.
- A parked session must acknowledge only, with no tools called and no work started.

Do not use this for finding, renaming, or archiving existing sessions after the fact. Do not rename the current conversation into the parked title. The parked slot is always a separate session identifier.

## Features
- A reuse-first lookup that finds an existing session with the exact title before creating one.
- A single create-or-reuse command with a fixed acknowledgement prompt and no tool use.
- A model choice that is checked against the provider's current model list before it is used.
- A confirmation step that compares the title, identifier, and last-active time in the session list.
- A fixed one-line reply shape that the orchestrator can parse.

## Benefits
- Operators keep one session per title, so the history is not split across duplicates.
- A parked slot cannot start work it was not asked to do, so it does not spend budget.
- Model names are checked against the live list, so a parked slot never silently runs on the wrong model.
- The one-line reply makes the parked state easy to confirm in a log or a message.

## Procedure
1. Reuse first. List the sessions and look for an exact title match. If a titled session already exists, resume that identifier. Do not spawn a duplicate, and do not retitle the current chat to reuse the slot.
   ```bash
   hermes sessions list
   ```
2. If no usable match exists, create the slot or reuse an empty one in one command. Use a one-shot run with a fixed acknowledgement prompt, and tell the slot to call no tools.
   ```bash
   hermes -p "<profile>" chat -Q --oneshot --create-if-missing -c "<TITLE>" -t '' -q "PARKED. Reply with exactly PARKED. Do no investigation and call no tools." -m "<model-slug>" --provider "<provider>"
   ```
   The empty toolset flag applies only to this no-work park, so the slot cannot pick up a standing mission. The one-shot flag makes the process exit after the acknowledgement, so no interactive child keeps running. The create-if-missing flag reuses a session with the same title, including an empty one.
3. Pin the model, and check it first. List the provider's current models and use a slug from that list, or the model the operator named if it is listed. If the operator names a version that is not listed, park on the nearest listed slug and say so.
4. Confirm the slot. Run the session list again and check that the title, identifier, and last-active time match what you expect. Then reply with the one-line status.
   ```text
   SESSION_ID=<id> MODEL=<slug> STATUS=parked
   ```
5. Do not narrate, paste transcripts, or start the parked work in the same turn.

## Pitfalls
- **A slot that inherits standing instructions starts working.** The park is safe only because of the empty toolset and the one-shot acknowledgement, and the check is that the reply is exactly PARKED with no tool calls. Never reuse the park command for a session that is meant to act.
- **Use one-shot mode so the spawn exits.** A left-running interactive child keeps consuming resources and can answer messages the operator did not intend for it.
- **Never store a parked slot as a tool-only session.** A session hidden from the default list will look missing to the operator.
- **Verify with the session list, not by opening the state database.** The list is the supported view, and reading the database directly can show partial writes.
- **Titles are the resume identity.** Keep the operator's title exactly, including case and spacing, or a later resume will not find the session.
- **Check the provider's model list before you name a version.** A requested version that is not advertised is not served, and the slot would park on a different model than the one named.
- **The chat flag takes the query option, not a message option.** Use the flag the help text lists, or the command fails with an unrecognized-argument error.
- **Never convert the current conversation into the parked session.** Spawn or reuse a separate identifier, so the current conversation keeps its own history.

## Verification
- `hermes sessions list` shows exactly one session with the title, and its identifier matches the reply.
- The reply is the single line in the fixed shape, with the model slug that was actually invoked.
- The parked session has no tool calls and no output beyond the acknowledgement.
- Later, resuming the identifier returns the parked acknowledgement, and no work has been added to it.
