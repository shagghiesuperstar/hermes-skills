---
name: multi-agent-telegram-loops
description: Use when agents in one Telegram group start a loop. It also applies to floods and repeated messages. Covers the causes, log checks, consolidated replies and fixes.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [telegram, gateway, multi-agent, loops, flood-control, group]
    category: integrations
related_skills: [hermes-gateway-ops, telegram-premium-hermes]
---

# Multi-Agent Telegram Loops

## Overview
When more than one agent is in the same Telegram group, a reply from one can become the input of another, which replies
again. The chain can repeat, multiply, or stall. The result is repeated short messages, flood-control errors, growing
queues, and a noisy channel that a person can no longer read. The agents are rarely the root cause. The usual causes are
missing routing between them, no rule that a bot ignores another bot's short status messages, and a restart that leaves
two copies of a session writing at once. This skill covers how to classify the loop, how to stop it without making it
worse, how to find its cause, and how to prevent it.

## When to Use
- The same short message repeats in a group, or two agents answer each other in turn.
- Flood-control errors appear, with retry waits that grow each time.
- A log shows recursion-depth or queue warnings, and messages pile up.
- A group stops receiving messages after its chat identifier changed.

## Features
- Classification into five loop types, each with its own check and fix.
- Log checks for recursion, flood control, polling and batching.
- A first-response rule that stops a relay echo without amplifying it.
- Operator-intent test that separates a real instruction from a relay repeat.
- Prevention rules for routing, mentions and session isolation.

## Benefits
- A loop is stopped with the smallest change, and the channel recovers without a restart storm.
- Each loop type is fixed at its cause, not by repeated resets.
- Operators see one clear status message, not a stream of repeats.

## Procedure
1. Measure before you act. Read the recent warnings and the group's recent messages, and count the repeats:
   ```bash
   grep -E "recursion depth|flood control|Flushing text batch" <hermes-home>/logs/errors.log <hermes-home>/logs/agent.log | tail -40
   ```
   Note the time of the first repeat and the sender of each repeated message.

2. Classify the loop:
   - **Relay echo.** A bot or relay repeats a short shape, such as a status line, a cursor, or a lone symbol. Agents that
     acknowledge it keep it alive.
   - **Agent-to-agent.** Agent A answers agent B's reply, and B answers A. The messages alternate between senders.
   - **Configuration mismatch.** A provider name fails to resolve, so each turn retries authentication and responds again.
   - **Flood cascade.** Too many sends in a short time. Telegram rejects them, and the retries add to the queue.
   - **Restart race.** A restart resumes an interrupted session while new messages are still being written to it. The
     message count rises by two each cycle.

3. Stop the amplification first. Do not add to the loop:
   - Send at most one consolidated status message, with the pending work listed briefly. Say that further repeats will be
     treated as noise.
   - Stop acknowledging repeats. Silence is a valid response to a relay echo.
   - Ask the operator to pause the agent that is repeating, if it can be paused from the operator's side.
   - Do not reset sessions or restart the gateway from inside the loop.

4. Find the cause. Check whether the repeats are forwarded or relayed, and whether a polling loop reconnects:
   ```bash
   grep -E "forward|via_bot|getUpdates" <hermes-home>/logs/gateway.log | tail -50
   ```
   A bot that polls many times a second with no new messages is a stuck relay. Check each bot's polling rate in the
   gateway logs.

5. Apply the fix for the class:
   - **Relay echo:** the cause is the relay or the peer that re-posts the shape. Stop that relay, or filter its messages
     out of the receiving agent's input.
   - **Agent-to-agent:** give each message one responder. Respond only when the message names the agent or replies to its
     own message, and ignore messages from other bots unless they are addressed to it.
   - **Configuration mismatch:** correct the provider name in the profile config, using the config command, and confirm it
     with the provider list.
   - **Flood cascade:** reduce the send rate, and clear the queue by waiting. Check for a second copy of the bot running.
   - **Restart race:** an operator stops the gateway from an operator shell, lets the interrupted session end, and starts
     the gateway again once the session is quiet.

6. Check for a chat migration. When a group becomes a supergroup, its identifier changes. Sends to the old identifier fail
   with a message that names the new identifier, and inbound messages stop arriving. Update any stored identifier in
   skills, memory and configuration, then send a test message.

7. If three fixes fail, stop changing settings. Write down the loop's timeline and the cause you found, and ask the
   operator to decide whether the group's design needs a change.

### Operator Intent
Treat a message as an instruction only when it comes from the operator's own account and asks for something, gives a
decision, or pastes material for reference. Treat as relay noise a message from another bot that is short, has no
request, or carries a forwarding or via-bot field. A repeat seen in the last few minutes is noise until the operator
writes something new.

### Prevention
- Give each agent a single job in the group, and route a request to one agent by name.
- Make each agent ignore its own bot identifier and the short status messages of other bots.
- Keep the session reset mode gentle, and do not combine per-user sessions in a group with an aggressive reset.
- Keep the provider names in config identical to the names the runtime registers.
- Keep the disk from filling up. A disk that fills stops session writes, and the backlog then sends in a burst when space returns.

### Disk-full bursts
A session write that fails with a disk-full error stalls the queue. When space returns, the queued handlers all fire at
once, and the burst exceeds the per-bot send limit even though each retry is correct. Check free space first, free it,
and expect the burst to pass. Deduplicate identical sends in a short window to limit the damage.

## Pitfalls
- **An ack to a relay echo is an amplifier.** Each acknowledgement is a new message for the relay to repeat.
- **Two agents with the same job answer the same message.** Give one of them the job, or route by name.
- **A reset is not a fix.** It clears one session and leaves the cause running.
- **A restart can revive the loop.** Stop the cause first, then restart.
- **Repeated identical messages in a group are a signal, not a status update.** Check the cause before you post.
- **Do not treat a silent group as a healthy group.** Check the send path after a migration or a restart.

## Verification
- The count of repeated messages in the group stops rising after the fix, and the flood warnings stop.
- Each agent answers only messages addressed to it, in a test with one message from the operator.
- The provider list shows each configured provider under the name the config uses.
- A send to the group's current identifier succeeds, and an inbound test message is received.
- Free disk space is above the level the logs show as the failure point.
