---
name: secrets-migration-fleet-rollout
description: Use when auditing plaintext secrets on a host and migrating them to a shared Bitwarden Secrets Manager project. Covers inventory without reading values, cross-referencing the store, updating consumers, read-only surface checks, and shredding only after operator approval.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [secrets, migration, bitwarden, fleet, inventory, plaintext-removal, operator-approval]
    category: security
related_skills: [bitwarden-secrets-manager-hermes, hermes-scoped-secrets-wiring, chat-safe-secret-staging]
---

# Secrets Migration, Fleet Rollout

## Overview
Several hosts running the same agent stack often hold plaintext copies of API keys and admin tokens. Those values should live only in the organization's secrets store. This skill audits one host from end to end, moves each plaintext value into the store, switches every consumer to read from the store at run time, checks the result, and removes the plaintext files only after an operator approves. Each host is audited on its own, because each one has its own scripts, schedules, and launch agents. The shared list of known secret names is the only thing that is the same across hosts.

## When to Use
- A host is joining a fleet that uses a shared secrets store, and its plaintext copies must move there.
- An audit finds plaintext keys in workspace folders, environment files, or scripts.
- A migration must be rerun on a host where some values already moved. The procedure is safe to rerun.

## Features
- A file inventory that finds secret-shaped files and enumerates environment-file key names without reading their values.
- A cross-reference of the store, so each plaintext value is matched to an existing entry or a new one.
- Three consumer classes: scripts that read plaintext, scripts that write it, and scheduled jobs or launch agents.
- A verification pass that checks the static search, a live call with a store-fed value, and that the scheduler still runs.
- A read-only expanded inventory of SSH keys, git credentials, keychain presence for each expected service, and application settings.
- A shred step that needs an explicit operator approval for each host.

## Benefits
- Plaintext values are removed only after the store copy has been checked.
- No secret value appears in tool output, in a chat, or in a report.
- Every file touched has a backup, so each change can be undone.
- Scheduled jobs and launch agents are reported to the operator instead of rewritten without review.

## Procedure
### Prerequisites
Confirm each item on the target host before any change:
1. The store's command-line tool is installed and reports version 2 or later.
2. A store access token is configured. Check that its line exists without reading the value, for example with `grep -c '^BWS_ACCESS_TOKEN=' <env-file>`.
3. The token authenticates, by listing the projects it can read.
4. A dated backup directory exists or can be created.
5. The external services the migration calls can be reached. Use each service's own verification endpoint.

If a prerequisite fails, stop and tell the operator. Do not work around it.

### Step 1: Inventory plaintext on disk
Find secret-shaped files, and skip backups, cache folders, and version-control worktrees:
```zsh
find ~ -maxdepth 5 -type f \( \
  -name "*_secret_key" -o -name "*_jwt" -o -name "*_pubkey" \
  -o -name "*_pat" -o -name "*.token" -o -name "*.key" \
  -o -name "credentials*" -o -name "service-account*.json" \
  -o -name "*.pem" \) \
  2>/dev/null | grep -v "__pycache__\|\.bak\|/repos/"
```

Find live scripts that read those paths, skipping prose files:
```zsh
grep -rln -E "_secret_key\b|_jwt\b|_pubkey\b|<other-known-path-pattern>" \
  ~/<workspace-dir> ~/src 2>/dev/null \
  | grep -v "\.md\|\.bak\|__pycache__\|/repos/"
```

For environment files in repositories you trust, list the key names only. Do not print values:
```zsh
find ~/src -name ".env*" -not -name "*.bak*" -exec sh -c \
  'echo "=== $1 ==="; grep -oE "^[A-Z][A-Z0-9_]+=" "$1" | sort -u' _ {} \;
```

Save the inventory to a file in the backup directory. Do not print it in full into the chat.

### Step 2: Cross-reference the store
List the secrets in each project the host reads, showing names and short identifiers only:
```zsh
bws secret list <project-id> -o json \
  | jq -r '.[] | "  \(.key)  id=\(.id[0:8])…  created=\(.creationDate[:10])"'
```

For each plaintext file from Step 1:
- If a store secret already holds the same value for the same purpose, reuse its identifier in the consumer update (Step 4).
- If no store secret exists, create one (Step 3).

If a plaintext value does not clearly belong to any project, stop and ask the operator which project it belongs in. Do not guess.

### Step 3: Move plaintext into the store
For each plaintext value with no store counterpart, create the secret from the value file, and suppress the value in the output. `bws secret create --help` lists `<KEY> <VALUE> <PROJECT_ID>` as positional arguments and no file or standard-input option, so the value is visible in the process list while the command runs. Get the operator's approval for that exposure before you run this loop:
```zsh
bws secret create <KEY> "$(cat <VALUE_FILE>)" <PROJECT_ID> --note "<context>" -o json \
  | jq -c 'del(.value)'
```
Record the new secret's identifier, in its short form, in the inventory file. A small helper can wrap this command: it reads the value from the file, creates the secret, and prints only the identifier, the key name, and the creation date. Keep the helper under about 25 lines, and test it on sample data before using it on a host.

### Step 4: Update the consumers
There are three classes. Handle each one separately.

#### 4a. Scripts that read plaintext
For each script that opens a plaintext file or runs `cat` on one:
1. Back up the script into the dated backup directory, with a timestamp in its name.
2. Replace the plaintext read with a fetch of the store secret by its identifier. Use the identifier, not the key name, because the get command takes an identifier. A short fetch function that runs at start-up is enough.
3. Run a static check. The search for the old path should return nothing for that file.
4. If the script makes a real call to a service, run it once and expect a success status.

Where a script has a default path constant, change the default to empty and fetch the value from the store at run time.

#### 4b. Scripts that write plaintext
Some scripts mint or refresh a value and write it back, such as a token refresher. Update these so they write to the store with an edit by identifier, and pass a note that says what changed:
```zsh
bws secret edit <secret-id> --value "$NEW_VALUE" -o json | jq -c 'del(.value)'
```
`bws secret edit --help` lists `--value <VALUE>` and no file or standard-input option, so the value is visible in the process list while the command runs. Get the operator's approval for that exposure first.

#### 4c. Scheduled jobs and launch agents
Flag these. Do not rewrite them automatically.

List the scheduled jobs and check whether each job's prompt or wrapper reads a plaintext file. For each one that does, follow the pattern in 4a, then confirm the next run uses the store. Use the scheduler's own list command, for example `hermes cron list`.

List the launch agents and find any that hard-code a secret in their environment variables or program arguments. This check is read-only:
```zsh
launchctl list | grep -iE "secret|key|token|api"
ls ~/Library/LaunchAgents/*.plist | xargs -I{} grep -l "EnvironmentVariables\|secret\|key\|token" {}
```

For any launch agent that hard-codes a secret, report the file path, the key name, and the recommended start-up injection pattern to the operator. Do not rewrite the agent. A launch agent restart can affect services that users rely on. When the operator approves, load the value at start-up from the store, and never inline it in the agent.

### Step 5: Verify
After all migrations, run these checks and save the results to the backup directory:
1. **Repeat the search from Step 1.** Only prose files, backup files, cache folders, and worktree entries should remain.
2. **Run a live call with a store-fed value.** Read the value into a shell variable, and use it in one request to the service's verification endpoint. Expect a success status:
   ```zsh
   umask 077
   printf 'user = "%s:"\n' "$(bws secret get <secret-id> -o json | jq -r '.value')" > <restricted-curl-config>
   curl -sS -K <restricted-curl-config> "<service-verification-url>"
   rm -P <restricted-curl-config>
   ```
3. **Check that the scheduler still runs.** Check the modification time of its heartbeat file. It should be recent.
4. **Check the launch agents.** Each expected service should be listed and running.

### Step 5.5: Expanded inventory (read-only report)
Plaintext can also sit outside the workspace. Inventory these areas, and report the findings to the operator. Do not shred or migrate anything in this step.

```zsh
ls -la ~/.ssh/ 2>/dev/null
ssh-add -l 2>/dev/null
git config --global --list 2>/dev/null | grep -E "credential|helper"
security list-keychains 2>/dev/null
security find-generic-password -s "<expected-service-name>" >/dev/null 2>&1 && echo "present" || echo "absent"
find ~/Library/Application\ Support/ -maxdepth 4 -type f \
  \( -name "*.json" -o -name "*.toml" -o -name "*.yaml" -o -name "credentials*" -o -name ".env*" \) \
  2>/dev/null | head -30
grep -rln -E "cat +~?/?[A-Za-z_/-]*_(secret_key|jwt|pubkey|token|key)" ~/.hermes/ 2>/dev/null | head
```

Save the findings to the backup directory. For keychain items, confirm only that the one expected item exists for its service. Do not list the other accounts on the machine. Keychain items are not moved automatically, and any move is the operator's decision.

### Step 6: Shred the plaintext
Shredding is a separate approval. Verification alone is not permission to shred.

1. Stop after Step 5 and Step 5.5. Write the draft report (Step 7) and send it to the operator.
2. Wait for an explicit approval for this host. Record it in the report.
3. Shred only the plaintext files that were migrated and verified:
   ```zsh
   rm -P <plaintext-file>
   ls <plaintext-file>   # should report that the file does not exist
   ```
   `rm -P` overwrites the file on macOS. On Linux, use `shred -u`.

Never shred these:
- Code files, even if they still refer to the removed paths.
- Documentation that mentions the removed paths. It is a historical record.
- Backup files.
- Anything in a cache folder or a version-control worktree.
- Environment files, or any backup of them.
- SSH keys, keychain items, or application-settings files. These need a separate operator decision.

If you are unsure whether a file is secret material, stop and ask.

### Step 7: Write the migration report
Save the report to the backup directory. Include:
- The inventory result from Step 1.
- The cross-reference result, with each store secret that was reused or created.
- Each script migrated, with its backup path, its identifier, and its smoke-test result.
- Each scheduled job or launch agent, and what was changed or flagged.
- Each file shredded, with its original path, backup path, and shred time, and the operator's approval.
- Anything left on disk, and why.
- The verification results: status codes, heartbeat age, and launch agent state.

The report must not contain any secret value.

## Pitfalls
- **Running the migration on a host the operator has not approved.** Each host gets its own inventory, verification, and approval.
- **Shredding right after verification.** Verification is not approval.
- **Printing a value to check it.** Enumerate key names from environment files, and filter store output with `jq` to drop the value field.
- **Passing a value as a command argument.** Other local users can see arguments in the process list while the command runs. Check the CLI's help for a file or standard-input option.
- **Migrating code or files inside repositories.** Surface those to the operator. Do not edit them in this procedure.
- **Rewriting a launch agent to fix a hard-coded secret.** Report it and let the operator decide.
- **A login session that expires.** A platform CLI login may need an interactive sign-in. Tell the operator instead of trying to automate it.
- **A value that stays in model context.** Chat surfaces may mask some secret-shaped text, but the value can still be read later. Rotate any value that stayed in context beyond a single turn.

## Verification
- The inventory, the cross-reference, and the verification results are saved, and none contains a secret value.
- Each migrated value reads back from the store with the expected length and a matching truncated hash.
- The live call with the store-fed value returns a success status.
- The scheduler's heartbeat is recent, and each expected launch agent is running.
- Plaintext files are shredded only after the operator's recorded approval for that host.
