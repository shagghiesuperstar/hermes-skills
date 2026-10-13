---
name: telegram-premium-hermes
description: Use when a Hermes Telegram bot needs large-file handling. It covers reactions and the optional local Bot API, including troubleshooting. Covers the limits, the config keys and the agent behavior rules.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [telegram, bot-api, gateway, media, reactions, configuration]
    category: integrations
related_skills: [hermes-gateway-ops, multi-agent-telegram-loops]
---

# Telegram Premium and Large Files for Hermes

## Overview
A Telegram user can hold a Premium subscription, and a Hermes Telegram bot is a separate thing with its own limits. The
subscription raises what the person can send and store. It does not raise what a bot can download through the public Bot
API, which tops out at 20 MB. A self-hosted Bot API server can raise that ceiling, at the cost of running another service.
This skill covers the difference, the configuration that matters without any extra service, the optional local server,
and how an agent should answer when a file is too large.

Check the current Hermes documentation for the Telegram messaging platform before you change its keys, because the keys
and their defaults change between releases.

## When to Use
- A user sends a file, a voice note or a video to the bot, and the bot cannot download it.
- You want reactions and streamed status on in the Telegram integration.
- An operator asks whether Premium lets the bot handle larger files.
- You are considering a local Bot API server, and need the trade-offs first.

## Features
- A table that separates the person's subscription from the bot's limits.
- A map of what a local Bot API server unlocks, and what it does not.
- Always-on configuration that needs no extra service.
- Optional local-server configuration, with the loopback binding rule.
- Agent behavior rules for oversized files.

## Benefits
- Operators are not told that a subscription fixed a bot limit.
- Large files get a path that works, without an unneeded server.
- A local server is installed only when someone has decided it is worth the cost.

## Procedure
### 1. Separate the three things
| Thing | What it is | What it is not |
|---|---|---|
| The person's Premium subscription | A paid user subscription | Not a bot upgrade. Does not raise the public Bot API download limit |
| The Hermes Telegram bot | A bot token, talking to the Bot API, feeding the gateway | Not a user account. Cannot read channels it is not in |
| A local Bot API server | The same Bot API software, run on a machine you control | Not a scraper, and not a user session. Bot rules still apply |

### 2. Apply the always-on settings, through the configuration command
These need no extra service:
```bash
hermes config set telegram.reactions true
hermes config set gateway.max_inbound_media_bytes 2147483648
hermes config set display.platforms.telegram.streaming true
```
Keep rich drafts off unless the operator has approved them, because they change how the desktop client shows drafts.
After any change, restart the gateway from an operator shell and read the values back.

### 3. Decide about a local Bot API server
Run one only when a specific case needs more than 20 MB through the bot, and the operator has approved it. Do not install
a container runtime or a Bot API server on a whim. When it is approved:
- run the server bound to the loopback address only, and never expose its port to the internet, because a bot token in a
  request path gives full control of the bot;
- point the Telegram platform's extra settings at the local address, under the platform's own extra section. A top-level
  copy of the same keys may be ignored;
- move the bot from the public API to the local server with the server's log-out call, once, after the operator approves it;
- check the local server with its identity call, and check the gateway log for the custom base address.

### 4. Answer an oversized file correctly
When a user sends a file over 20 MB and the download fails:
1. Say that the public Bot API limit is 20 MB, and that the person's subscription does not change it.
2. Offer the paths that already work: a shared drive or repository link under the limit, or an attachment through the
   other channel the team uses.
3. Offer the local server as an option, with its cost, and wait for a decision. Do not install it, and do not claim the
   subscription fixed the limit.

### 5. Verify
```bash
hermes config get telegram.reactions
hermes config get gateway.max_inbound_media_bytes
```
Send a short voice note and check that it is transcribed. Check that a reaction appears in place of a progress message.
A file over 20 MB is tested only after a local server is approved and running.

### Other rules
- **Do not scrape other channels with a bot.** A bot sees only the chats it has joined, and the updates Telegram sends it.
  Reading channels a bot has not joined needs a separate user-session tool, with its own risks and its own approval. Do not
  build one without written scope from the operator.
- **Bot membership gives the bot the chat.** For a channel you control, add the bot as a member with the rights it needs.
- **Authorization does not change.** The allowed-user list and the owner rules apply to large files too.
- **Prefer reactions and short status to progress messages in a shared group.** Long progress messages add to a loop in
  a multi-agent group.

## Pitfalls
- **The subscription does not raise the bot's download limit.** Explaining otherwise sends the user to the wrong fix.
- **A top-level extra key can be silently dropped.** Set the local server's address under the platform's extra section.
- **Never expose the local server's port publicly.** The token is part of the request path.
- **Do not change the default model or the fallback chain as part of a Telegram change.** Those are separate decisions.
- **Do not paste the bot token or the API hash into chat or a log.** Use the secret store.

## Verification
- The configuration reads back the values set in step 2.
- A short voice note is transcribed, and a reaction appears.
- If a local server is in use, its identity call answers on the loopback address, and the gateway log names the custom address.
- A file over the limit gets the explanation and the working alternatives, not a claim that the limit was lifted.
