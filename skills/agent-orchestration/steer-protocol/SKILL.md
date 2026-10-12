---
name: steer-protocol
description: Use when several agents share one group chat and each message must name the agent it is for. Covers the addressing prefix, reply routing, and when to stay silent or ask a question.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [group-chat, routing, multi-agent, messaging, discipline]
    category: agent-orchestration
related_skills: [hermes-role-orchestration, named-session-parking, kanban-orchestration]
---

# The Steer Protocol: Addressed Messages in a Shared Chat

## Overview
When several agents listen to one group chat, every message reaches all of them. Without an explicit address, each agent guesses whether the message is for it, and the guesses produce duplicate replies, feedback loops, and flood-control errors. The steer protocol fixes this with one rule: every group message begins with the address prefix and the full username of each agent it is for. Only addressed agents respond. Everyone else stays silent. The protocol also covers replies, scope discipline, and templated requests that arrive with blanks.

## When to Use
- Sending any message to a shared group chat where more than one agent is present.
- Reading a group message and deciding whether it is addressed to you.
- Asking another agent for a recap, a status, or a review, and needing the answer routed back to you.
- Setting up a new agent for group participation, or debugging duplicate replies.

Do not use the prefix in one-to-one direct messages. It applies to the shared group only.

## Features
- A prefix rule: the first characters of every group message are the address prefix, followed by full usernames.
- An addressing check that every agent runs before it replies.
- Bidirectional routing: a request names the agent asked and the agent that should receive the answer.
- A broadcast form for messages that should wake every agent.
- A clarification rule for requests with blank placeholders, which are asked about before anything is sent.

## Benefits
- Each message has a declared audience, so no agent has to guess.
- Duplicate replies and feedback loops stop, because only addressed agents respond.
- Agents do not spend compute on work that belongs to someone else.
- A vague request is clarified with the operator once, instead of costing a round trip between agents.
- The reply route is explicit, so the answer reaches the agent that asked.

## Procedure
1. Before sending to the group, write the prefix as the first characters of the message, then the full username of each agent the message is for, then the message text.
   ```text
   /address <full-username> — <message>
   ```
   For more than one agent, list each full username in the same prefix.
   ```text
   /address <agent-one-username> <agent-two-username> — <message>
   ```
2. Use the exact full username from the roster, never a short name. A short name may not match any account, so the message reaches nobody, or it reaches the wrong agent. Check the username before you send.
3. Put the prefix on every reply in the thread, not only on the first message. The whole conversation follows the same rule.
4. When you read a group message, run the addressing check before you respond:
   - Does the message start with the prefix?
   - Does the prefix name your username?
   - If yes, respond and use the prefix in your reply. If no, stay silent.
   The operator is the one exception. When the operator speaks to you directly, respond, and the operator does not need a prefix.
5. To ask another agent for an answer you need, name both agents in the prefix: the agent you are asking and your own username as the reply route. State the scope of the question and ask for the reply to use the prefix that names you.
   ```text
   /address <asked-agent-username> <your-username> — Recap on <topic>: current state, blockers, and what is left. Reply with the prefix naming <your-username>.
   ```
6. For a message that should wake every agent, list all of them in the prefix. Every listed agent is pinged, and each one acknowledges or stays silent according to its scope.
7. Apply scope discipline. Even when a message is visible to you and touches a topic you know, do not plan or begin work on it unless it is addressed to you. If it is clearly for another agent, treat it as out of scope. When in doubt, ask one clarifying question.
8. If a request arrives with a blank or placeholder where a username or topic belongs, the message is incomplete. Ask one or two short questions to the operator before you send anything: what the topic is, and which agent should receive the reply. Do not guess either one.
9. Keep one-to-one messages free of the prefix, and use the direct channel for them.
10. Audit the group now and then. Look for messages that lack the prefix, and correct the sender.

## Pitfalls
- **A message without the prefix makes every agent react.** This is the most common failure. Load the protocol before each group send, so the prefix is never missing.
- **Short names are not usernames.** A short name may not match any account. Use the exact full username from the roster.
- **Addressing the wrong agent is easy.** Two similar usernames differ by one word. Check the one you typed against the roster before you send.
- **Replies need the prefix too.** A reply without it breaks the thread for every other agent.
- **A recap with no scope cannot be answered.** Ask the operator for the topic before asking another agent to summarize it.
- **Asking without naming your own username drops the answer.** The addressed agent may reply to the group, but the routing signal to you is missing.
- **Do not broadcast a status that one agent needs.** Address that agent alone. Broadcast only for changes every agent must know about.
- **Do not guess a topic or a handle.** A guess wastes the next several minutes and creates cleanup work.
- **Prefixes are for the shared group only.** Adding one to a direct message is noise.

## Verification
- Every message sent to the group begins with the prefix and names the intended agents by their full usernames.
- Each agent that replied was named in the prefix of the message it answered.
- No agent replied to a message that did not name it.
- A request with a placeholder was clarified with the operator before it was sent.
- A recap or status request names the reply route, and the reply arrived with the prefix that names the asking agent.
