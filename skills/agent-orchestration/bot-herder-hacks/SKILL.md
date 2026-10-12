---
name: bot-herder-hacks
description: Use when creating, arming, tightening, or retiring a bot. Covers a multi-bot Hermes or Grok fleet. Sets outcome, instruction, and approval rules.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [bots, grok-bot, hermes-agent, agent-fleet, least-privilege]
    category: agent-orchestration
related_skills: [kanban-orchestration, kanban-card-lifecycle]
---

# Bot Herder: Arming and Retiring Hermes and Grok Bots

## Overview
A bot fleet fails in predictable ways. Bots with no defined outcome run on habit, bots share a login without anyone deciding to share it, and bots send things without an approval step. This skill sets the design rules for creating, arming, and retiring bots: one owned outcome per bot, three layers of instructions, quiet by default, draft before any send, and one explicit trust boundary per login. The method matters more than any single bot.

## When to Use
- Creating a bot, or changing what an existing bot owns.
- Designing a fleet with a front-door bot, named role bots, and scheduled routines.
- Installing a skill or integration on a bot that can send messages, spend money, or read accounts.
- Deciding whether a remote browser, a cookie sync, or outbound voice or email belongs in the fleet.
- Wiring a bridge between a local Hermes agent and a hosted Grok Bot.

Do not use this for product code (give that to a coding agent) or for routing board tasks (give that to the orchestrator).

## Features
- A keep, defer, or reject guide for candidate tools and integrations, with one reason for each.
- A three-layer instruction template: BASE rules every bot shares, ROLE for what the bot owns, and CURRENT FOCUS for the week.
- A creation procedure that starts from the weekly outcome a bot owns.
- Routine design with an explicit silence rule, so bots ping only on real hits.
- A counting test that retires bots which do not own an outcome.
- A bridge pattern for a local agent and a hosted bot that has no official API.

## Benefits
- Each bot has one job and a measurable outcome, so idle or duplicate bots show up.
- The shared BASE layer makes every bot ask before it spends money or sends anything external.
- Quiet routines cut notification noise and the attention cost of false alarms.
- Integrations that hold credentials are scoped to a dedicated profile, so one compromise does not expose the whole fleet.
- Bridges use a one-way trust rule, so a hosted bot cannot reach back into the local machine beyond the one path it needs.

## Procedure
1. Name the weekly outcome the bot owns. If you cannot name one, do not create the bot.
2. Write the instructions in three layers and paste them into the bot's instruction field:
   ```text
   BASE INSTRUCTIONS (every bot)
   - Ask before spending money, sending externally, or deleting files.
   - When a decision matters, check the current source. Do not answer from memory.
   - If blocked, say so in one line. Do not improvise a workaround.
   - Read the shared context folder before starting. Write a handoff note before passing work.
   - Draft first, then approve: email, direct messages, payments, public posts, production changes.

   ROLE
   - You are: <one sentence>
   - You own: <recurring jobs>
   - Evidence standard: <what proof>
   - You may / may not: <hard stops>

   CURRENT FOCUS
   - <this week>
   ```
3. Name the bot after one job and the one system it lives in. Do not give one bot several jobs across several systems.
4. For any non-trivial job, plan first and build second. A bot that changes code or data follows a written plan step by step.
5. Give each loop an owner, a worker, a verifier, and a stop rule, such as at most three rounds, or stop when the output fingerprint repeats.
6. Define silence for each routine: the trigger, the frequency, the output, what silence means (nothing to report), and when to page a human.
7. Harvest. When a bot's method works, extract it as a reusable skill and a registry entry. Do not spawn one-off bots.
8. After one week, run the counting test. Retire any bot whose outcome did not move.

### Shared trust boundary (hosted bot platforms)
- Treat all bots on one hosted computer as one trust boundary. They share files, browser sessions, and logins, so separate bots do not protect credentials.
- Scope access by which accounts are logged in, not by which chat window a bot uses. Start with read-only access to public data, and grant credentials later, one at a time.
- Do not sync a primary browser's cookie jar to any remote host. Use a dedicated, low-privilege browser profile, and threat-model the sync before you install it.
- Never point a bot at a personal machine with remote screen control or a personal browser. Use a separate machine or account.

### Bridge pattern (local agent to a hosted bot with no official API)
- Hosted bots often expose only an undocumented or community-built HTTP interface. Treat it as unstable, and verify each endpoint before a job depends on it. Before you build the bridge, read the hosted platform's terms of use and confirm that the interface is allowed for this purpose.
- Keep the interface on a private network only. Restrict it with network ACLs so the local machine can reach the bot host on that one port, and the reverse path is allowed only for the single reply route you need.
- Send long messages through a shared file and send only a short wake-up ping, because a request body can be dropped in transit.
- Keep the gateway token in a secret store, not in plaintext on the bot host. Assume the interface has no rate limiting.

### Keep, defer, or reject
- **Keep** a plan-first workflow for every non-trivial job.
- **Keep** one front-door bot that delegates to role bots.
- **Keep** draft-then-approve for sends, payments, and public posts.
- **Keep** a shared file folder as the memory bus, since bots do not share chat history.
- **Adopt later, with a task-level review,** a per-bot mailbox. Never share one personal mailbox across bots.
- **Defer** any tool that points a bot at a real personal computer until a security review is done.
- **Reject** outbound voice calls for non-urgent work, since people hang up.
- **Reject** letting an unsupervised bot clone itself or launch crews of bots. Errors compound across unsupervised copies.
- **Reject** public prompt rankings as a quality signal. A rank built on copy counts measures popularity. Read and test a prompt before you adopt it.
- **Reject** a second agent harness nested inside a bot as the default. It adds a layer you do not need.

## Pitfalls
- **A bot without an owned outcome is noise.** Retire it at the counting test rather than letting it run on habit.
- **Shared logins make the whole fleet one trust boundary.** Scope what a bot can reach by what is logged in.
- **Silence is a feature.** A routine that pings on every run trains people to ignore it. Ping only on real hits.
- **Draft-then-approve covers any action that leaves the machine.** Email, payments, public posts, and production writes need a human yes first.
- **Never auto-merge from a repository-triage bot.** Its output is a proposed change for review.
- **Shared personal mailboxes are off limits for bots.** Give each bot its own mailbox with its own approval gate.
- **Undocumented bot interfaces change without notice.** Re-probe the endpoints before a dependent job runs, and keep a fallback path.
- **Plaintext tokens and open ports are the usual way a bot host leaks.** Check the network ACL and the token location while arming the bot, not after an incident.

## Verification
- The roster lists each bot with its owned outcome and labels it as real (running) or experiment.
- Each real bot has BASE, ROLE, and CURRENT FOCUS layers in its instructions.
- Each non-trivial job has a plan file that exists before the build step ran.
- No bot can send money or an external message without an approval step. Check each bot's approval setting.
- The counting-test result for the week is written down, with any retired bots named.
- For a bridge, a connection from the bot host to the local machine on a port that is not allowed fails.

## Attribution
- Van Horn, "Every Grok Bot Hack I Know (Aug 2026)": the instruction layers, the silence rules, and the keep, defer, or reject guide.
- Av1dlive: the graph and loop engineering behind the loop and stop-rule guidance.
- Derek Colley: the Hermes and Grok Bot bridge pattern over a private network.
