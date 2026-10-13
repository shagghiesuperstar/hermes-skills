---
name: hermes-slack-direct-api
description: Use when an agent sends or reads Slack messages directly. The route is the Slack Web API. Covers token handling, mention IDs, thread replies and the limits of bot-to-bot wakeups.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [slack, web-api, bot-token, messaging, threads, automation]
    category: integrations
related_skills: [hermes-in-buzz, hermes-gateway-ops]
---

# Hermes Slack Direct API

## Overview
Sometimes a Hermes session needs to read or post in Slack outside the messaging gateway's own session. The gateway's
command-line helper for Slack may only print an app manifest and cannot send. In that case the Slack Web API is the
direct route. It takes a bot token, a method name and form fields. This skill covers how to hold the token, which calls
are needed, how to mention a bot or a person correctly, how to thread replies, and the limit that matters most: a
message posted by one bot does not reliably wake another bot.

## When to Use
- You need to post a message to a channel or a direct message, and the gateway's helper cannot send.
- You need to read a thread or the recent history of a channel from a script.
- You need to confirm the identity of the bot, a channel or a user before you address them.
- A request to another bot in a channel has gone quiet, and you need to decide what to do next.

Do not use this when the counterpart is already reachable through the gateway. Use the gateway's own session in that case.

## Features
- Token handling that keeps the value out of output and out of the conversation.
- The five Web API calls that cover identity, lookup, posting and reading.
- Mention rules: a mention is a user ID in angle brackets, never a display name.
- Thread rules: replies carry the parent message's timestamp.
- Bot-to-bot caveat, with a check for whether a wake actually happened.
- Read-only rule for pulls and polls.

## Benefits
- The token never appears in a log, a chat, or a shell history.
- A mention actually notifies the person or bot it names.
- Replies land in the right thread.
- A request that was not picked up is noticed, instead of waited on forever.

## Procedure
1. Load the token from the secret store into the environment of the process that makes the calls. Check only its presence
   and its length, never its value:
   ```bash
   test -n "$SLACK_BOT_TOKEN" && echo "present, length ${#SLACK_BOT_TOKEN}"
   ```

2. Confirm the identity before you address anyone. The identity call reports the bot's user ID and the workspace:
   ```python
   import json, os, urllib.parse, urllib.request

   def call(method, **fields):
       body = urllib.parse.urlencode(fields).encode()
       req = urllib.request.Request(
           f"https://slack.com/api/{method}", data=body, method="POST",
           headers={"Authorization": f"Bearer {os.environ['SLACK_BOT_TOKEN']}",
                    "Content-Type": "application/x-www-form-urlencoded"})
       with urllib.request.urlopen(req, timeout=15) as r:
           return json.loads(r.read())

   print(call("auth.test"))
   ```
   Check that the response is `ok` before you go on. Use the other calls the same way:
   - `conversations.info` with a channel ID, to confirm the channel;
   - `users.info` with a user ID, to confirm a person or a bot (its `is_bot` flag);
   - `conversations.members`, to confirm that a bot is in the channel before you mention it;
   - `conversations.history` and `conversations.replies`, to read recent messages and a thread;
   - `chat.postMessage` with `channel` and `text`, to post.

3. Mention by user ID. Write the mention as the user ID inside angle brackets, for example `<@U0EXAMPLE1>`. A plain display
   name in the text is only text, and the person or bot is not notified. Look up the user ID with `users.info` or the
   members list, and do not guess it.

4. Reply in a thread by passing the parent message's timestamp as the thread timestamp. A reply without it lands in the
   channel root.

5. Read before you write. Pull the thread or the recent history first, and answer what was actually asked. A summary of
   your own status posted into a thread that asked a question is not an answer.

6. Verify the post. Read the message back from the thread, or check the returned timestamp and channel. Do not treat a
   successful request as proof that a person saw it.

7. Respect rate limits. The read and write methods have per-minute limits. For a long pull, pause between calls, and
   read the limit headers when a call is refused.

### Bot-to-bot limits
- A message posted through the Web API by one bot does not reliably wake another bot's mention handler. Some bots only
  respond to a human's mention. Treat a bot's silence as a possible non-wake, not as a refusal.
- Do not wait in a loop for a reply that may never come. Set a short check, and if no reply arrives, hand the request to
  a person in a clear message, such as a ready-to-paste prompt, and move on.
- A read-only call works in every case. Only the wake (a posted mention) is limited.
- A channel can host several bots that each answer their own mentions. Address the one whose work it is.
- When two bots could both answer, a message that names only one of them belongs to that one. Do not answer it in
  another bot's name.
- For work between agents that do not need a person in the loop, a shared file folder with an acknowledgement file per
  request is more reliable than chat wakeups. The requester writes a request file. The worker writes an acknowledgement,
  then a result.

## Pitfalls
- **The gateway helper does not send messages.** Do not spend turns on guessed subcommands. Use the Web API.
- **A display name does not mention anyone.** Use the user ID inside angle brackets.
- **Posting from a session is not the same as posting as the person.** The bot's messages carry its own name, and people
  will read them as the bot, not as the operator.
- **Do not post during a read-only job.** A pull or poll must not call the posting method.
- **Do not paste lists of IDs into a channel.** Keep IDs in the working notes, not in the conversation.
- **Verify the workspace before any write.** The identity call names the workspace. A token for one workspace posts only there.
- **Never print the token, and never paste it into a message, a file or a ticket.**

## Verification
- The identity call returns `ok` with the expected bot name and workspace.
- A posted message appears in the thread, with the mention rendered as the person's or bot's name.
- A read of the thread returns the parent message and the replies in order.
- A request to another bot is either answered, or handed to a person with the prompt written out, with no open wait.
- The token length check shows the variable is set, and the value appears nowhere in the output.
