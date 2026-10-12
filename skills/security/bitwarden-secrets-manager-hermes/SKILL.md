---
name: bitwarden-secrets-manager-hermes
description: Use when a Hermes host reads or writes Bitwarden secrets. It uses the Bitwarden Secrets Manager CLI for credentials. Covers machine accounts, scoped read grants, no-echo handling, upsert and verification, and disk-key consolidation.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [bitwarden, bws, secrets, machine-accounts, credentials, hermes-integration]
    category: security
related_skills: [hermes-scoped-secrets-wiring, chat-safe-secret-staging, secrets-migration-fleet-rollout]
---

# Bitwarden Secrets Manager for Hermes Hosts

## Overview
An agent host needs credentials, and the safest place for them is an organizational secrets store with scoped machine identities, not a plaintext file on each machine. The Secrets Manager is a different product from the personal password vault. It uses machine accounts with access tokens, and its CLI is built for automation. The discipline that matters most is handling values without ever printing them: compare by length and hash, write by identifier, and verify by re-reading. This skill covers the account and grant model, the read and write procedures, and how to consolidate keys that are scattered across disk.

## When to Use
- A profile or a remote agent needs a credential that should not live in a plaintext file.
- A credential must be added, updated, rotated, or granted to one more machine account.
- Keys for one provider are found in several profile files, and you need to know whether they match.

## Features
- A clear split between the organizational secrets manager and the personal vault, with the rule that automation uses the first.
- Machine accounts with one access token each, granted read access to specific secrets.
- Read paths that list names and compare values without printing them.
- A write procedure with a preflight, identifier-based edits, and hash-based verification.
- A consolidation gate that stops when two copies of a key disagree.

## Benefits
- Credentials stay out of transcripts, chat, and shared notes.
- A compromised host can be cut off by revoking its one machine account.
- A mismatched key is caught before any copy is deleted.
- Every write is checked by reading back what was stored.

## Procedure
### Accounts and grants
1. Use the organizational secrets manager's CLI for automation. The personal vault's CLI is for manual lookups and is not wired into agents.
2. Create one machine account per host or agent role, named after that role. Machine accounts are identities without a master password, so deleting a user does not delete their machine accounts.
3. Grant each machine account read access to the specific secrets it needs. Grants are made from the secret's own machine-account tab, with the narrowest permission the job needs.
4. Create an access token for the machine account and copy it at once. The token is shown only at creation, and a lost token must be replaced. Store it in a file readable only by your account, or in the profile's environment file. Never paste it into chat or notes.
5. Test the token with a read that returns a known project or secret list:
   ```zsh
   export BWS_ACCESS_TOKEN="$(cat <restricted-token-file>)"
   bws project list -o tsv
   ```
   An empty result from a valid token means the account has no grants yet, so check the grants before you blame the token.

### Read names and compare values
6. Before any write, confirm the CLI is connected to the expected organization by reading the organization name from the project listing.
7. Resolve a project's identifier from the project listing, and pass that identifier to secret commands. A profile name passed to a project flag fails with "profile does not exist", because the two flags are different things.
8. List names only when you audit. Filter the output so values never reach the terminal or the transcript:
   ```zsh
   bws secret list <project-id> | jq '[.[] | {key, id}]'
   ```
9. To compare a stored value with a source value, put both into shell variables and compare them. Print only the match result, and a length or hash if you need one:
   ```zsh
   BWS_VAL=$(bws secret get <secret-id> | jq -r '.value')
   [ "$BWS_VAL" = "$SRC_VAL" ] && echo "MATCH=yes" || echo "MATCH=no"
   ```

### Write with verification
10. Run a preflight. Confirm the key name and the project, and check the live state of the secret before you change it.
11. Read source values into variables. Never echo a variable that holds a secret. Run the sequence in one script with failure stopping the run, so a failed step cannot be followed by a mutation.
12. Edit an existing secret by its identifier, one field per call, and suppress the success output so the value is not echoed. `bws secret edit --help` lists `--value <VALUE>` and no file or standard-input option, so the value is visible in the process list while the command runs. Get the operator's approval for that exposure before the write:
    ```zsh
    bws secret edit <secret-id> --value "$SRC_VAL" -o none
    ```
13. Create a new secret with the key, the value, and the project identifier. For per-profile variants, name the key with the profile as a suffix, so each profile's copy is easy to find.
14. Verify by identifier. Re-read each secret, and compare its length and a truncated hash against the local copy. Report match or mismatch for each key, never the value.
15. Delete a malformed secret only after the replacement is verified and the operator approves that deletion.

### Consolidate keys from disk
16. Audit before any deletion. Find each literal copy of a key in the host-wide environment file, the profile environment files, and the configuration files. Skip copies that are placeholders that point at the store.
17. Compare every copy by length, a short prefix, and a truncated hash, never by the full value. Store the comparison in a table, one row per copy, with the location, the hash, and the result of a single harmless authentication request.
18. Decide with this gate:
    - Every disk copy matches the store's primary value: replace each copy with a placeholder that reads from the store. Then, after a backup and the operator's approval for each deletion, remove the plaintext copies.
    - A disk copy authenticates but does not match the primary: stop. It may belong to a different account. The operator decides whether to retire it, rotate it, or keep it.
    - A disk copy fails authentication and the primary works: the copy is stale. Remove it after a backup and the operator's approval.
    - Neither authenticates: stop, and ask the operator for a valid key.
19. A key on disk that matches no store entry usually means a profile was configured by hand. Do not delete it without the operator's confirmation, because the profile may depend on it.

### Rotate
20. Rotate by adding the new value to the store, verifying it with one request, switching each consumer, and only then revoking the old value. Revoke a machine account's token when a host is retired or compromised.

## Pitfalls
- **Printing a value by accident.** JSON output from the secret commands includes values. Filter it, or suppress it with the output flag.
- **Confusing the two CLIs.** The personal vault's commands do not work with the Secrets Manager, and the reverse is also true.
- **A token shown once.** A lost token cannot be recovered. Create a new one and revoke the old one.
- **Renaming a machine account does not rotate its token.** The old token keeps working under the new name, so rotate it explicitly.
- **An auth key is not an access token.** Device sign-up keys and machine account tokens are separate credentials.
- **A token in a file is not in the shell.** Export the token, or load it for each command, before running the CLI.
- **Deleting a key that matches nothing.** A key on disk that matches nothing in the store may be the only working copy for a profile.
- **Writing by name when an identifier exists.** Edit by identifier, so a name collision cannot change the wrong secret.

## Verification
- Each secret named in the task reads back with the expected length and hash, and the report shows match for each.
- No plaintext copy remains on disk after consolidation, except copies the operator kept on purpose.
- Each profile reads its credential through a placeholder that resolves from the store at run time.
- The machine account's grants list only the secrets its host needs.

## Attribution
- Bitwarden CLI: https://github.com/bitwarden/cli
