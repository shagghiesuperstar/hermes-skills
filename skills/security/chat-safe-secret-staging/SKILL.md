---
name: chat-safe-secret-staging
description: Use when a secret must reach an env file, not chat. Covers operator-entered staging, file permissions, gitignore-first, fingerprint-only verification, and clipboard hygiene.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [secrets, credentials, env-files, chat-safety, file-permissions, staging]
    category: security
related_skills: [bitwarden-secrets-manager-hermes, hermes-scoped-secrets-wiring, secrets-migration-fleet-rollout]
---

# Chat-Safe Secret Staging

## Overview
A secret that passes through a chat transcript is a secret that is stored, shared, and sometimes mangled. Chat platforms can mask secret-shaped text in one direction, so a pasted line can change silently in transit. A secret that is typed or pasted into a model's context can also be read back later. The safe pattern is to have the operator place the value in the destination file on their own machine, while the agent prepares the file, its permissions, its ignore rule, and the verification. The agent then proves the file is correct using only a prefix, a length, and a hash, never the value.

## When to Use
- An operator has a new key or token that must land in a local environment file for a service.
- A key was shown once by a provider and must be saved before the page closes.
- A service's configuration needs a credential that should not be committed to a repository.

## Features
- A staging sequence: prepare the file, ignore it in version control, let the operator write the value locally, then verify.
- Fingerprint-only verification: prefix, length, line count, permissions, and an ignore check.
- Clipboard hygiene: check the expected prefix, extract the token, and clear the buffer after a verified write.
- Guidance on display-safe output for any tool result that might contain a value.
- A store-of-record rule: the value lives in the organization's secrets manager, and the file is a copy.

## Benefits
- No secret value appears in chat, in a transcript, or in model context.
- A new file never exists in version control, and its permissions are restrictive from creation.
- A bad or truncated paste is caught by the length and shape checks before a service uses it.
- A reviewer can confirm the staging from the printed fingerprint alone.

## Procedure
1. Decide where the value lives. The organization's secrets manager is the store of record, and the local file is a copy the service reads. If the value is not yet in the store, say so, and add it there after staging.
2. Prepare the destination before the value arrives. Set a restrictive umask so the file is created with owner-only permissions, add the file name to the repository's ignore file, and prove the ignore rule applies:
   ```zsh
   umask 177
   grep -qx "<env-file-name>" .gitignore || echo "<env-file-name>" >> .gitignore
   git check-ignore -v "<env-file-name>"
   ```
3. Have the operator write the value into the file. The operator uses a local editor, or a terminal command they run themselves. Give them the exact file path and the exact key name, and ask them to save and say "done". Do not ask them to paste the value into chat, and do not show them a command whose text includes the value.
4. Do not route around an access rule. If a rule stops the agent from writing or reading a credentials file, stop and tell the operator. Ask them to write the file or to change the rule. Do not rename the file, move it to a different folder, or hide its name in a variable to get past the rule.
5. Verify without printing the value. Confirm the permissions, the line count, the key names, and a short prefix of each value:
   ```zsh
   ls -l "<env-file-name>"
   grep -c '^[A-Z_]*=' "<env-file-name>"
   cut -d= -f1 "<env-file-name>"
   cut -c1-30 "<env-file-name>" | sed 's/=\(....\).*/=\1.../'
   ```
   Expect owner-only permissions, the expected number of lines, the expected key names, and recognizable prefixes. The printed output contains no secret material.
6. Check the length of each value against the provider's documented length, when the provider documents one. A length mismatch usually means a truncated or padded paste, and the operator should write the value again.
7. Clear the clipboard after a verified write, so the value does not stay in the buffer:
   ```zsh
   pbcopy < /dev/null
   ```
8. Report the staging result as prefix, length, permissions, and the ignore rule. Never report the value.

### Clipboard Hygiene
- Check the expected prefix before a write. Extract the token with a pattern, not by printing the whole buffer, because rich-text copies add formatting that corrupts a plain match.
- Validate the extracted value with a case statement and stop on a mismatch.
- Write the value in the same command sequence as the check. The buffer changes whenever the operator copies anything else.
- Some one-time-shown keys cannot be recovered after the page closes. If the clipboard misses, create a new key in the provider's interface and stage that one.

### Display-Safe Output
- Never print a value, a full configuration file, or a raw JSON response that includes a value field.
- Filter tool output to the fields you need, such as the identifier and the key name, before it reaches your context.
- Redact subprocess output before you show it. Replace any copy of the value, and any hash or prefix longer than the fingerprint, before it is printed.
- A display mask in the interface is not a mask in the model's context. Assume anything the agent read can be repeated, and keep the value out of the agent's reads.
- Do not paste secret-shaped lines into a chat code block. Some platforms rewrite them, and a snippet that was rewritten can fail silently.

## Pitfalls
- **Asking for the value in chat.** Ask the operator to write it locally instead.
- **Writing the file before the ignore rule exists.** Add the rule first, and prove it with the ignore check.
- **Creating the file with default permissions.** Set the umask before the write.
- **Trusting a shortened paste.** Check the length and the prefix before a service uses the value.
- **Routing around an access rule.** If a rule blocks the write, the rule is the control. Ask the operator.
- **Declaring a leak without checking the surface.** Decide whether the value was actually visible to a person or stored in a shared artifact before rotating. Rotate when it was, and say why.
- **Setting a cloud variable from a pasted value in chat.** Stage the value on disk, read it from there, and report only the prefix and length of what was set.
- **A daemon that reads an old environment.** Restart the service after writing the file. An edit reaches only new processes.

## Verification
- The file has owner-only permissions, is listed by the ignore check, and contains the expected key names.
- Each value's prefix and length match the expected pattern, and the printed output contains no secret material.
- The service reads the new value after a restart, confirmed by a request that uses the credential and returns a success status.
- The clipboard is clear after the write.

