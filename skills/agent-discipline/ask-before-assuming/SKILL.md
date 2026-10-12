---
name: ask-before-assuming
description: Use when an instruction could mean more than one source, target or scope. Find every candidate first, then ask before planning, unless only one candidate exists.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [planning, ambiguity, scope, clarification, operator-trust]
    category: agent-discipline
related_skills: [agent-honesty, minimal-change-operator]
---

# Ask Before Assuming

## Overview
Many instructions contain a word that points at several things: "your memories", "the config", "the project", "the
repo". An agent that quietly picks the most plausible one builds a plan on a guess, and the operator discovers the
mistake only after the work is done. An agent that lists every candidate and plans for all of them wastes the
operator's attention and still lands on the wrong one. This skill sets the middle path: find the candidates from the
environment, then either ask one focused question or proceed while stating the single assumption that was made.

## When to Use
- The instruction refers to a memory store, a configuration scope, a repository, a scheduled job, a session, or a skill,
  and the environment holds more than one match.
- The instruction says "fix", "update" or "configure" something that may exist in several instances.
- The instruction contains coded shorthand, such as a ticket number, a short identifier or a persona name, that you
  cannot resolve from the local context.
- The operator asks you to work while they are away, and the work includes steps they must approve.

## Features
- A decision tree from an ambiguous reference to one of three moves: ask, proceed with a stated assumption, or block.
- An evidence-first probe sequence for coded references, run before asking or refusing.
- A three-bucket split for unattended work: safe to do, unsafe to do, and reserved for the operator.
- Rules for explicit approval gates, which a fast-speed instruction does not waive.
- A check of commands and flags against their help output before they are stated.

## Benefits
- One question, not four, when one question unblocks the plan.
- A stated assumption is cheap for the operator to correct.
- Coded references become checkable facts, or a precise block with the probes as proof.

## Procedure
### Resolve an ambiguous reference
1. Name the referent in the instruction, such as "the config" or "your memories".
2. Search the environment for every candidate that matches it: the files, the stores, the profiles, the repositories,
   the scheduled jobs. Use the listing and search tools, not memory.
3. If more than one candidate remains, ask which one before you plan. Give the candidates in a short list, and ask one
   question.
4. If exactly one candidate remains, proceed, and state the assumption in the plan so the operator can correct it cheaply.
5. Do not add a plan item for each candidate "to be thorough". That is the over-listing failure.

Ask without asking when the instruction is clear, the scope was set earlier in the session, or the cost of a wrong
assumption is lower than the cost of a question. Use judgment, but keep the question count low.

### Ground a coded reference before asking or refusing
Coded shorthand, such as a ticket number, a persona name or an endpoint path, usually compresses context the operator
has in mind. Expand it into artifacts before either asking or refusing:
1. Search the local filesystem for a directory or file that matches a distinctive token in the instruction.
2. List the names (never the values) in the relevant secret store that match the project or customer name.
3. Probe any address the instruction mentions, with a short timeout. A success or redirect status shows the artifact exists.
4. Use a web search last, and only when the first three found nothing. A web search can confirm a public project, but
   it cannot confirm a private one.

Then classify the instruction:
- **All references grounded:** proceed, and name the evidence in the plan.
- **Some grounded:** execute the grounded part, and block on the rest with the exact missing identifiers.
- **None grounded:** block, and list the probes you ran, so the operator can correct you cheaply.

A table that marks items "keep" or "cut" when you could not verify them is not partial progress. It is a guess.

### Work while the operator is away
When the operator says to do what you can while they are unavailable, sort the work into three buckets:
1. **Safe without them:** read-only checks, syntax checks, dry runs that refuse to act, and writing files that nothing loads yet.
2. **Unsafe without them:** anything that changes a running service, sends a message, calls an external service with real
   credentials, triggers an alert, or rotates a secret. Do not run these. Write each one out as a step with the exact command
   and what it changes.
3. **Only the operator can do:** steps that need a browser sign-in or a decision. Write them as numbered steps with the
   exact address, field names and expected result.

Execute the first bucket end to end. Put the other two into one handoff document that the operator reads first. Keep
any watchdog you create paused, so it does not alert while no one is watching. End with one message that lists what
was done, what is waiting, and which document to read first.

### Check a command before you state it
Before you give the operator a command or a flag, run that command's help output in the current session and confirm the
flag exists. If you are not certain, say so, and mark the command as unverified.

### Respect approval gates
An instruction that ends with an urgent phrase speeds up the work. It does not waive an approval gate that the operator set
earlier. When the work needs one of those approvals, surface it in the reply and wait for the explicit confirmation.

## Pitfalls
- **Over-listing to look thorough.** Listing every candidate and planning for each one hides the real question.
- **Silently choosing the likeliest reading.** A wrong guess is expensive, and a question is cheap.
- **Refusing a coded reference without probing.** The artifact may exist and be one probe away.
- **Fabricating to look productive.** Invented ticket text, invented diffs or an invented endpoint breaks trust faster than a block.
- **Publishing as the operator without the operator's credentials.** A command that posts under the operator's identity
  needs the operator's own authentication. Do not claim a post happened unless the post command returned a success result
  you can show.
- **Inventing a flag that sounds right.** Read the help output first.
- **Overnight progress messages.** A person who is asleep should receive one final report, not a stream.
- **Doing one more step because you are already there.** The operator may have wanted to stop before it.

## Verification
- The plan names one source, target or scope, and says in one sentence why it was chosen.
- Every candidate found in the search is accounted for: chosen, or listed in the question.
- A coded reference has its probe results attached, and the block states exactly what was missing.
- Every command in the reply was checked against its help output in this session, or it is marked unverified.
- The handoff document lists every unsafe and operator-only step, and no unsafe step was run.
