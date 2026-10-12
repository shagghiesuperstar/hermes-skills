---
name: hermes-in-buzz
description: Use when connecting a Hermes gateway on one machine to a Buzz relay used from another machine. Covers the identity rules, admission checks, the outbound CLI, verification and media attachments.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, buzz, gateway, nostr, messaging, attachments, cross-platform]
    category: integrations
related_skills: [buzz-self-hosting, hermes-gateway-ops]
---

# Hermes in Buzz

## Overview
Buzz is a chat system built on a relay. A Hermes agent can run as a native gateway on one machine and answer in a Buzz
community that people use from another machine. Both sides connect independently to the same relay, so the client does
not need to reach the agent host, and the agent keeps running when the client is offline. Setting this up involves a
dedicated agent identity, a membership check on the relay, an external command-line client for outbound messages, and
verification that a real message goes both ways.

The current documentation for the Hermes Buzz integration and the Buzz release assets changes often. Read the current
pages before you start, and follow them where they differ from this skill.

## When to Use
- The Buzz client runs on one computer, and the Hermes agent should run continuously on another.
- An agent was created in Buzz, but the gateway stays silent.
- Errors show a missing command-line client, a relay membership requirement, zero channels, or mentions that are ignored.
- You are moving an existing native Buzz gateway to another operating system.

Do not use this native-gateway workflow when the operator wants the Buzz side to own the runtime. That is a different
topology, with its own owner-only rules.

## Features
- Architecture choice between a native gateway and a Buzz-owned runtime.
- Dedicated agent identity, with the secret entered locally and never in chat or on a command line.
- Relay admission check that compares the public identity and the channel list.
- Outbound command-line client, verified from its own help and output.
- Service setup by operating system, with approval before any install or persistence change.
- End-to-end test with one inbound and one outbound message.
- Attachment procedure for local media files.

## Benefits
- The agent has its own identity, so a leaked agent key does not expose the operator's key.
- Admission problems are found by layer, in a fixed order.
- A reply is counted as sent only when the relay confirms it.
- Attachments are posted through the native mechanism, not by pasting file paths.

## Procedure

### Hard security rules
1. Use a dedicated agent identity. Never reuse the operator's own key as the agent's key.
2. Never ask for a private key, a token or an owner key in chat, or through a question prompt.
3. Enter secrets locally with hidden input, never as a command-line argument, and never print or log them.
4. Store the agent key and its authorization data only in the active profile's secret environment file. Resolve the Hermes
   home for the active profile instead of assuming the default.
5. Set non-secret values with the Hermes configuration command, not by hand edit.
6. Start with access closed: no users allowed except an explicit owner list, and mentions required.
7. Ask for approval before installing a toolchain, downloading a client, or changing a service or persistence setting.
8. Keep any agent that runs terminal tools owner-only. A runtime that auto-answers permission prompts can run commands
   without a visible approval.

### Setup steps

1. Discover the host. Record the operating system, the processor type, the shell, the active Hermes home and profile, and
   which tools exist (the Hermes command, git, and the Buzz command). Check the Hermes status and the gateway status. Report
   only whether each Buzz setting is present, never its value.

2. Choose the architecture and record it:
   - **Native gateway (default):** full Hermes memory, skills, sessions and multiple messaging platforms in one gateway.
   - **Bridge runtime:** Buzz owns the transport and Hermes runs in a limited mode. Use it only when the operator asks for it.

   Collect only non-secret facts in chat: the relay address, the agent's display name, the owner's public key, the channels
   that should carry the agent, and whether other members may invoke it.

3. Create the agent identity. The operator creates the agent in the Buzz client, and copies its secret key once. The
   operator then enters that key on the Hermes host at a hidden prompt that does not echo the key, from a local terminal. Check that
   the stored key file has restricted permissions where the system supports that.

4. Install the outbound command-line client. Outbound messages need it even when inbound delivery works.
   - Query the current release listing for the Buzz client, and read the asset names, not just the release title.
   - Use a prebuilt asset only if it is a standalone command for the exact operating system and processor.
   - Verify the published digest when one exists, install to a user-writable path, mark it executable, and run its help.
   - Building from source needs approval first, because it installs toolchains.

5. Set the non-secret configuration with the configuration command, then read it back. Keep these values: the relay
   address, the owner list, mention-required, and the closed-access default.

6. Check admission in layers, in this order:
   - The public identity derived from the stored key matches the agent shown in the client.
   - The command-line client authenticates with the stored values, passed through its environment, not by sourcing a file
     in the shell.
   - Channel discovery returns the intended channels.

   A failure on authentication that names a membership requirement means the agent is not admitted to the relay. Ask the
   relay operator to add it. Do not regenerate keys to work around it.

7. Install the gateway as a service, using the operating system's service manager. Ask the operator before you install or
   change the service, and make sure the service's search path includes the command-line client's folder.

8. Verify end to end. The gateway log should show that the Buzz connection is up, that channels were discovered, and that
   the agent subscribed to each one. Then send one message in a channel with a mention, and confirm the agent answers. The
   answer counts as sent only when the outbound call returns a success result.

### Attachments
Use this when the operator asks to post a local media file into the current Buzz channel, and ordinary media delivery fails.
1. Confirm that the file exists and can be read. Use the media probe for video details when they matter.
2. Find the current channel identifier from the gateway log, from the operator's latest inbound message. Do not guess it.
3. Send the file with the native attachment option, and repeat the option to attach several files:
   ```bash
   buzz messages send --channel <channel-id> --content - --file <absolute-path>
   ```
4. Load the credentials through a dotenv parser into the subprocess environment, not by sourcing the file in the shell.
   Some values contain quotation marks that shell parsing breaks.
5. If the relay rejects an MP4, read the returned error. A file whose index block sits at the end needs a remux with the
   fast-start option. A file with metadata the relay forbids needs a re-encode that drops metadata, with the same
   video and audio settings the client itself uses. When neither suits, convert a short clip to an animated image.
6. Report success only when the outbound call returns a result with `accepted` set to true. Keep the returned event
   identifier as evidence.

## Pitfalls
- **A reply can end its turn without being sent.** On a headless agent, the final text is not posted automatically. The agent
  must send it, and must check the send result. A turn that finishes normally proves nothing about delivery.
- **The outbound client needs the same credentials as the gateway.** An environment that does not carry them makes every
  outbound call fail with an authentication error. Load them explicitly.
- **Do not scrape another process's environment for keys.** If the variables are missing in a shell, fix the service or
  the loader, and do not read keys out of a running process.
- **Long message bodies break quoting.** Write the body to a file in an allowed folder, and pass it on standard input.
- **Membership and channel membership are different.** Adding an agent to a channel does not admit it to the relay.
- **An ordinary media path may fall back to a generic video sender.** Use the native attachment option instead.
- **Keep converted files out of the original folder.** Write conversions to a temporary folder, and leave the original alone.
- **Converted animated images can be large.** Lower the frame rate, the width or the palette size before uploading.
- **Never print the agent key or any value from the environment file.**

## Verification
- The public identity matches the agent in the client.
- The command-line client lists the intended channels with the stored values.
- The gateway log shows the connection, the channel discovery and each subscription.
- One mention in a channel gets one answer, and the outbound call returned a success result with an event identifier.
- An attachment returns `accepted` set to true, and the attached file opens in the client.
