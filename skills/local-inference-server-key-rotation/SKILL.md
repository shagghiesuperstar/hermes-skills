---
name: local-inference-server-key-rotation
description: Use when a local inference server's key must be rotated. Rotation follows exposure or a maintenance schedule. Covers finding every consumer by hash, atomic updates, restarting only the server, and proving the new key works while the old one is rejected.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [secrets, key-rotation, local-inference, credentials, bitwarden, verification]
    category: security
related_skills: [local-model-deployment, chat-safe-secret-staging, bitwarden-secrets-manager-hermes]
---

# Local Inference Server Key Rotation

## Overview
A local model server (oMLX, DS4, vLLM, or similar) authenticates callers with one API key. That key is often copied into several places: the server's own settings, a secrets store, a profile's environment file, a launch agent, and a gateway's config. Rotating it means finding every copy, replacing all of them, restarting the server, and proving the change took effect. A missed copy makes the server fail intermittently, which is harder to diagnose than a clean failure. This skill keeps the key out of tool output the whole time and uses hashes, not values, to match copies and report results.

## When to Use
- A key was exposed in logs, command output, a chat message, or a repository's history.
- A server's credentials reach the end of a scheduled refresh period.
- The operator asks for a rotation as maintenance.

## Features
- A discovery pass that lists the server's process arguments, config files, and environment variables without printing their values.
- A consumer map where each copy is identified by an 8-character SHA-256 prefix (sha8).
- Backups of every file before it is edited.
- A probe that confirms the new key is accepted and the old key is rejected.
- A short rotation report that contains hashes and counts only.

## Benefits
- The key never appears in tool output, shell history, or a transcript.
- Every consumer is updated in one pass, so the server does not fail on a stale copy.
- The probe result, an HTTP status, is the proof of change, not a read of a config file.
- The report can be shared, because it holds no secret material.

## Procedure
### Critical rules
- Never print, echo, cat, or include any key value, old or new, in tool output or in a response.
- Handle keys only through shell variables, files with mode 600, pipes into the secrets CLI, and SHA-256 fingerprints.
- To confirm a copy, compare its sha8 with the expected sha8. Report only the sha8, never the value.
- Restart only the inference server. Never restart the agent gateway or daemon, because that disrupts every profile and active user.

### Step 1: Find the key source
Find where the server reads its key. Common places:
- **oMLX**: the settings file's auth field, or the `OMLX_API_KEY` or `OMLX_LOCAL_API_KEY` environment variable.
- **DS4**: an environment variable or a command-line argument. Check the config directory or the process arguments.
- **vLLM**: `VLLM_API_KEY` or `LLM_API_KEY`, or a startup flag.

Find the listening process and list its startup option names only. Option values can hold the key, so do not print them:
```zsh
lsof -iTCP:<port> -sTCP:LISTEN
ps -o command= -p <pid> | tr ' ' '\n' | grep -oE '^--?[A-Za-z_-]+'
```
Search the server's config directory for key fields, listing names and paths only:
```zsh
grep -rl "api_key\|API_KEY" <server-config-dir> --include="*.json" --include="*.conf"
```
Record the file path and the field or variable name for each source.

### Step 2: Identify every consumer
Find each copy of the current key by comparing sha8 values. Never compare full values in the output.

1. **Secrets store.** List the entries whose names suggest a key, then take the sha8 of each entry's value:
   ```zsh
   bws secret list | jq '.[] | select(.key | contains("API_KEY") or contains("LLM")) | {key: .key, id: .id}'
   bws secret get <id> | jq -r '.value' | shasum -a 256 | cut -c1-8
   ```
2. **Environment files.** Find the variable in each file, then take the sha8 of its value without printing it:
   ```zsh
   grep -rl "<KEY_VAR_NAME>" ~/<profile-dir> --include=".env"
   grep "<KEY_VAR_NAME>" <file> | cut -d'=' -f2- | tr -d '\n' | shasum -a 256 | cut -c1-8
   ```
3. **Config files.** Search for the field names, then take the sha8 of the value as above.
4. **Environment variables.** List the names that match, then take the sha8 of the current value:
   ```zsh
   env | grep -i "api_key\|llm" | cut -d'=' -f1
   printf '%s' "$VAR_NAME" | shasum -a 256 | cut -c1-8
   ```

List each consumer with its name, its file path or store identifier, and the sha8 of its current value. Keep the old key in a shell variable for the probe in Step 8, and record the old sha8 as `OLD_SHA8` for the report.

### Step 3: Generate the new key
Generate the key with a cryptographic source, and write it to a file that only you can read:
```zsh
NEW=$(openssl rand -hex 24)
KEYFILE=$(mktemp)
printf '%s' "$NEW" > "$KEYFILE"
chmod 600 "$KEYFILE"
printf '%s' "$NEW" | shasum -a 256 | cut -c1-8
```
A 24-byte value gives a 48-character hexadecimal key, which is a good default. Keep the key in a shell variable or in the mode-600 file. Do not echo it. The last line prints `NEW_SHA8`.

### Step 4: Back up every consumer before editing
Create a dated backup directory, and copy every file that will change into it:
```zsh
mkdir -p ~/.hermes/backups/key-rotation-$(date +%Y%m%d)
cp <server-settings-file> ~/.hermes/backups/key-rotation-$(date +%Y%m%d)/settings.json.bak
chmod 600 ~/.hermes/backups/key-rotation-$(date +%Y%m%d)/settings.json.bak
```
Repeat for each file. A backup that is not readable only by you should be fixed before you go on.

### Step 5: Update the secrets store
If a store entry holds the key, edit it by its identifier and pass the value from the file:
```zsh
NEW=$(cat "$KEYFILE")
bws secret edit <id> --value "$NEW"
bws secret get <id> | jq -r '.value' | shasum -a 256 | cut -c1-8   # expect NEW_SHA8
```
`bws secret edit --help` lists `--value <VALUE>` and no file or standard-input option. The value is therefore visible to other local users in the process list while the command runs. Tell the operator this exposure and get their approval before the write. If a later CLI version adds a file or standard-input option, use it instead.

If no store entry exists, create one with the key name and the project identifier. The create call takes the value as a positional argument, with the same process-list exposure as above:
```zsh
bws secret create "<KEY_NAME>" "$NEW" <project-id>
```

### Step 6: Update configuration files
Update each config file with a short script. The script reads the new key from the mode-600 file, sets only the one field, and writes the file back. Do not put the key on a command line, and do not use `sed` or `printf` pipes with the key value, because the key then appears in shell history.

For a Hermes profile's configuration, prefer a field that names an environment variable (a `key_env` style field) over a literal key. The literal key then lives only in the environment, not in the config file.

### Step 7: Restart the inference server
Restart the server with its own launch method, and wait a few seconds for it to come back:
- **oMLX**: its CLI restart command.
- **DS4**: restart it the way it was started, through launchd or systemd.
- **vLLM**: restart its launch agent with `launchctl kickstart -k gui/$(id -u)/<service-label>`, or restart its process manager job.

Confirm the server is answering again before you probe it.

### Step 8: Probe the new key and reject the old one
Both probes must pass. A new key that works does not prove the old key is gone, and an old key that is rejected does not prove the new key works.

Test the new key. Expect an HTTP 200, or 201 or 202 depending on the server:
```zsh
curl -s -m 20 -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:<port>/v1/chat/completions \
  -H "Authorization: Bearer $NEW" \
  -H 'Content-Type: application/json' \
  -d '{"model":"<model-name>","messages":[{"role":"user","content":"hi"}],"max_tokens":1}'
```

Test the old key, which is still in the shell variable from Step 2. Expect an HTTP 401, or 403 for a forbidden response:
```zsh
curl -s -m 20 -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:<port>/v1/chat/completions \
  -H "Authorization: Bearer $OLD" \
  -H 'Content-Type: application/json' \
  -d '{"model":"<model-name>","messages":[{"role":"user","content":"hi"}],"max_tokens":1}'
unset OLD
```

The HTTP codes are the proof. Read the server's config files only to explain a failure, not to confirm success.

### Step 9: Check the Hermes fallback
If the server is a fallback provider in a profile's configuration, list the fallbacks and confirm the server is still listed and reachable:
```zsh
hermes -p <profile> fallback list
```

### Step 10: Delete the temporary files
Overwrite and delete every temporary file that held a key:
```zsh
rm -P "$KEYFILE" 2>/dev/null
```
`rm -P` overwrites the file before it is removed on macOS. On Linux, use `shred -u` instead. Clear the shell's history for this session, or run the work in a session with history recording turned off. In bash, `set +o history` does that. `set +H` only disables history expansion and does not stop recording. Check the zsh equivalent in the zsh manual before you rely on it.

The backup copy made before the update also holds the old key. After the probes pass, overwrite and delete it with the same method, or tell the operator that it stays and why.

## Pitfalls
- **Comparing full values to check a match.** A value printed to compare it appears in output and logs. Compare sha8 values only.
- **Missing a consumer.** Search the process arguments, every config directory, the environment, and any launch agent definitions before you change anything. Search again after the change to catch stragglers.
- **Restarting the agent gateway instead of the inference server.** The gateway serves every profile. Restart only the inference server.
- **Testing a config file instead of the server.** Reading a file shows what was written, not what the server accepts. The probe result is the ground truth.
- **Testing only the new key.** Skipping the old-key rejection leaves it unknown whether the old key still works somewhere.
- **Leaving keys in shell history.** Use variables and pipes, clear the history afterwards, and do not paste keys into a chat.

## Verification
- The new key returns the success code, and the old key returns the rejection code.
- Every consumer found in Step 2 shows the new sha8, and a second search finds no copy of the old sha8.
- The store entry, if one exists, reads back with the new sha8.
- The rotation report lists the old sha8, the new sha8, the store entry name, the number of consumers updated, the restart method, and both probe codes. It contains no key values.
- Temporary key files are deleted.
