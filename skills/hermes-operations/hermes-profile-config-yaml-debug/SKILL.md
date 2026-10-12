---
name: hermes-profile-config-yaml-debug
description: Use when a Hermes profile's config.yaml fails to parse, or a model change lands in the wrong profile. Covers scope checks, YAML repair, schema checks and restart verification.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, config, yaml, profiles, gateway, debugging]
    category: hermes-operations
related_skills: [config-verify-before-write, hermes-architecture-reference, hermes-gateway-ops]
---

# Diagnose a Broken Hermes Profile Config

## Overview
A profile's `config.yaml` can fail in two independent ways. The file can be malformed, so the gateway cannot parse it and
falls back to built-in defaults that ignore every override. Or the file can be valid but be the wrong file: the running
gateway reads one profile's config, while a command or an operator edits another. The two look alike from the chat side,
because the model appears not to change. This skill separates the two, repairs the file through the Hermes CLI where
possible, and proves the fix with a real turn.

## When to Use
- The gateway log reports that the profile config failed to load, or failed to parse, at a specific line.
- The gateway log reports that it is falling back to default config, so overrides are being ignored.
- A model change made through the CLI or the chat picker does not show up in the running gateway.
- A model label reports an unexpected provider, or the wrong model after a change.
- The gateway reports no messaging platforms enabled, although a token is set in the profile env file.

## Features
- Scope check that confirms which config file the running gateway actually reads.
- Syntax check and schema check, run as two separate gates.
- Repair order: CLI commands first, then a structured rewrite with a backup when the CLI cannot reorder a list.
- Restart procedure that verifies the new process through its lock file.
- End-to-end proof from a real turn in the agent log.

## Benefits
- A malformed file is found from its parse error, not from a series of unrelated symptoms.
- Edits land in the file the gateway reads.
- A restart is never used to test an unparseable config.

## Procedure
1. Confirm which config file the running gateway reads before you edit anything:
   ```bash
   hermes --profile <profile> config path
   pgrep -fl "hermes_cli.*gateway"
   lsof -p <gateway-pid> | grep -E "profiles/.*/(state\.db|gateway\.lock|logs)"
   cat ~/.hermes/profiles/<profile>/gateway.lock
   ```
   If the open files sit under the profile's folder, that profile is live. A command that runs without the profile flag
   reads the root config, regardless of which profile the gateway serves.

2. Back up the file before any change:
   ```bash
   TS=$(date +%Y%m%d_%H%M%S)
   cp ~/.hermes/profiles/<profile>/config.yaml ~/.hermes/profiles/<profile>/config.yaml.bak_$TS
   ```

3. Read the whole file. A short view can hide the fault. Look for:
   - top-level keys indented by two spaces, which makes the parser treat them as children of the previous key;
   - a block pasted at column zero with no parent key;
   - a commented documentation footer that was only partly commented out;
   - a key and its value written without a space after the colon, such as `key:value`.

4. Check syntax first. A parse failure stops everything, so fix it before anything else:
   ```bash
   python3 -c "import yaml; d=yaml.safe_load(open('<config-path>')); print('YAML OK; keys:', list(d)[:10])"
   ```

5. Check the schema and the version with the Hermes command. A valid file can still be missing required keys or be an
   older version:
   ```bash
   hermes --profile <profile> config check
   hermes --profile <profile> config migrate          # adds optional keys and bumps the version
   hermes --profile <profile> doctor
   ```

6. Make edits through the CLI when it can do the job:
   ```bash
   hermes --profile <profile> config get model.default
   hermes --profile <profile> config set model.default <exact-model-id>
   hermes --profile <profile> config set model.provider <exact-provider-id>
   ```
   `config set` keeps sibling keys. It cannot reorder a list. For a list that must be reordered, write the list
   through a structured YAML write (keeping key order), after the backup from step 2, then read the file back.

7. Restart through the supported command, then confirm the new process by its lock file, not by a name search:
   ```bash
   hermes gateway restart
   cat ~/.hermes/profiles/<profile>/gateway.lock
   ```
   Run the restart from an operator terminal when your agent session is hosted by the gateway. Restart only after the
   syntax check and the schema check both pass.

8. Prove the fix with a real turn. Send one message through the chat platform, then read the turn record:
   ```bash
   tail -30 ~/.hermes/profiles/<profile>/logs/agent.log
   grep "agent.conversation_loop" ~/.hermes/profiles/<profile>/logs/agent.log | tail -4
   ```
   The record names the model, the provider and the latency. Those values, not the command output, are the proof.

### Failure notes

### Wrong file in use
Commands that change a model write to whichever config the running gateway reads. If the gateway serves a different
profile than the one you edited, nothing changes. Check the open files and the lock file first, every time.

### Malformed YAML disables every override
A single syntax error can make the gateway ignore the whole file. Its log then says it is falling back to default config.
Auxiliary providers, the fallback chain, model settings, messaging, dispatch and routing are all ignored until the file
parses. Fix the parse error first, restart, and only then debug anything that depends on config.

### Sign of a missing space after a colon
`max_spawn_depth:2` is one token to the parser, not a key with a value. Hand-edits and some CLI values produce this.
Use the syntax check after every edit, and do not restart on a file that fails it.

### Case-sensitive model ids
`MiniMax-M3` and `minimax-m3` are different strings. Match the exact case that the provider registry lists. When you are
not sure, read the resolved default from the profile listing, not from memory.

### A removal can be a no-op
A remove command can report success while leaving the block in place, especially when the same name appears under two
sections of the config. After any removal, grep the config for the name, and check the credential or token folder for
leftover files. Remove leftovers by hand, with a backup, and read the file back.

### Startup lag that looks like a model problem
A delay of about twenty seconds on the first message often comes from a polling conflict, or from a retry backoff, not from
the model. Read the agent log for the conflict message before you change the model.

### Avoid sed for structured files
Sed can break indentation without any error. Use the CLI, or a structured write with a backup and a read-back.

## Pitfalls
- **Do not restart a gateway whose config fails to parse.** It boots on defaults and fails in ways that are harder to read
  than a refused start.
- **Do not trust a profile name to mean the right file.** The lock file and the open files are the ground truth.
- **Do not confuse a schema warning with a parse error.** The syntax check and the schema check are separate gates. Pass
  both.
- **Do not declare a change live from a file read or a CLI success line.** Only a real turn in the agent log proves it.
- **Do not bypass a refused write with another tool.** A refusal on a security-sensitive config file means the change needs
  the operator's terminal or an explicit approval. Report it and ask.
- **Do not change approval settings to make a command run unattended.** Approval prompts are a safety gate. Report what
  needs approval, and let the operator decide.
- **Pick the process with a lock-file check.** A name search can return a one-shot command that has already exited.

## Verification
- The syntax check prints the keys, and the schema check reports the current version with no missing keys.
- The open files of the running gateway sit under the profile folder you edited.
- The restart produces a new PID that matches the lock file.
- The agent log shows no parse or default-config warning after the restart.
- A real turn shows the intended model and provider, with a latency value.
