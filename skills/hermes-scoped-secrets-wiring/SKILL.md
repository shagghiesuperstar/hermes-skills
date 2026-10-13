---
name: hermes-scoped-secrets-wiring
description: Use when a key must reach only some Hermes profiles. It must reach them through the secrets command helper, not bulk Bitwarden injection. Covers the helper script, per-profile config, override safety, and fingerprint checks against the store.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, secrets, bitwarden, command-helper, profiles, credentials, scoped-access]
    category: security
related_skills: [bitwarden-secrets-manager-hermes, chat-safe-secret-staging, secrets-migration-fleet-rollout]
---

# Hermes Scoped Secrets Wiring

## Overview
A Hermes profile can load secrets in two ways. Bulk Bitwarden loading reads every secret in a project into the profile, so a profile that needs one provider key also receives unrelated tokens, such as chat or messaging credentials. The command helper runs a small script that prints one `KEY=value` line, so a profile receives only the key its helper returns. This skill sets up that helper, applies it to each target profile with safe defaults, and checks that the profile resolves the same value as the store, without printing the value.

## When to Use
- A profile needs exactly one API key, and other profiles must not receive it.
- Turning on the full Bitwarden loader for a profile would inject credentials the profile does not use.
- The key is stable and lives in a Bitwarden Secrets Manager project that the host can read.
- You need proof that the key a profile resolves is the one in the store.

## Features
- A short helper script that resolves a single key from the store.
- Per-profile command-helper settings, with an override guard that keeps keys set by other loaders.
- A check that the bulk loader is off and that no unrelated keys are resolved.
- A forced-fallback run that shows the target key reached the fallback provider.
- A fingerprint comparison between the store value and the helper's output.

## Benefits
- A profile receives only the credentials it uses.
- A key that another loader already set in a profile is left in place.
- A wrong project, a wrong key name, or a stale copy fails a check instead of passing silently.
- Verification reports match or mismatch, never the value.

## Procedure
### Choose command helper or bulk loading

| Scenario | Use | Reason |
|----------|-----|--------|
| One profile, one key | Command helper | Scoped, no side effects |
| Several profiles, same key | Command helper on each profile | One script, per-profile config |
| All profiles, all keys | Bulk Bitwarden loading | Simpler, and no script is needed |
| Some profiles, some keys | Command helper | Other profiles do not receive unrelated keys |
| Key rotated often | Command helper | Each profile can be tested on its own |
| Key kept outside Bitwarden | Command helper | Point the script at the other source |

### Step 1: Write the helper script
Place the script at `~/.hermes/scripts/<key>-only.sh` and make it executable with `chmod 700`. The script does these things, in this order:
1. Read `BWS_ACCESS_TOKEN` from the environment. If it is not set, read its line from `~/.hermes/.env` with `cut -d'=' -f2-`, and stop if the result is empty.
2. Export the token explicitly with `export BWS_ACCESS_TOKEN="$token"`.
3. Find the `bws` binary with `which bws`, and fall back to the known install path if that fails.
4. List the project's secrets as JSON with `bws secret list <project-id> -o json`.
5. Select the one key with `jq` and a `select(.key=="<KEY_NAME>")` filter.
6. Print exactly one line, `<KEY_NAME>=<value>`. Send every error message to stderr, so stdout carries only the line.
7. Exit zero only when the key was found. Exit non-zero when the key is missing or when `jq` fails.

### Step 2: Back up and configure each target profile
Back up the profile's configuration before any change, then set the four helper keys with the Hermes CLI:

```zsh
profile="<profile-name>"
profile_config="<path-to-the-profile-config.yaml>"

cp "$profile_config" ~/.hermes/backups/<date>/$profile-config.yaml

hermes -p $profile config set secrets.command.enabled true
hermes -p $profile config set secrets.command.command "$HOME/.hermes/scripts/<key>-only.sh"
hermes -p $profile config set secrets.command.helper_timeout_seconds 20
hermes -p $profile config set secrets.command.override_existing false
```

- `secrets.command.enabled`: `true` turns the helper on.
- `secrets.command.command`: the absolute path to the helper script.
- `secrets.command.helper_timeout_seconds`: `20` leaves room for a `bws` call on a local network.
- `secrets.command.override_existing`: `false` keeps keys the profile already has. The helper fills only the keys that are missing.

### Step 3: Confirm the bulk loader is off and the helper is active
```zsh
hermes -p <profile> config get secrets
```
Expect `bitwarden.enabled: false` (or the key absent), `command.enabled: true`, the absolute script path under `command.command`, and no "missing secrets.command.command" error. A successful load reports that the command helper applied one secret. Read the output for setting names and status only, and do not paste it into chat.

### Step 4: Confirm unrelated keys are absent
```zsh
hermes -p <profile> config get secrets | grep -E "SLACK_BOT_TOKEN|TELEGRAM"
```
Expect no output. If any line carries a value, filter the output to names before it reaches your context.

### Step 5: Run a forced-fallback test
Set the primary provider's key to a deliberately invalid value for one run, and send a request that the primary cannot answer. The fallback chain must then answer. A reply from the fallback provider proves two things: the chain was tried, and the target key was resolved and passed to the fallback. If the key had not been resolved, the fallback would also fail for lack of valid auth.

The example below uses a MiniMax primary. Substitute the profile's own primary provider and model.

```zsh
mkdir -p ~/.hermes/tmp

MINIMAX_API_KEY="forced-invalid-test" hermes -p <profile> -z 'Reply PONG' \
  --provider minimax --model MiniMax-M3 \
  --usage-file ~/.hermes/tmp/<profile>-usage.json 2>&1 | tail -3

jq '.provider, .model' ~/.hermes/tmp/<profile>-usage.json
```

Expect the usage file to name the fallback provider and model, for example `anthropic` and a Haiku model.

### Step 6: Compare fingerprints with the store
Compare a truncated SHA-256 of the store value with a truncated SHA-256 of the helper's value. Print only the match result:

```zsh
bws_fp=$(bws secret list <project-id> -o json \
  | jq -r '.[] | select(.key=="ANTHROPIC_API_KEY") | .value' \
  | shasum -a 256 | cut -c1-8)

helper_fp=$($HOME/.hermes/scripts/<key>-only.sh \
  | cut -d'=' -f2- | shasum -a 256 | cut -c1-8)

[ "$bws_fp" = "$helper_fp" ] && echo "MATCH=yes" || echo "MATCH=no"
```

Expect `MATCH=yes`. On `MATCH=no`, the helper is reading a different project or account, or the key was rotated after the profile was set up. Correct the project or the key name before you change anything else.

## Pitfalls
- **Bulk loading when only one key is needed.** A profile with the full loader enabled receives every secret in the project. Keep the loader off and use the helper.
- **Loading the token with `export $(grep ...)`.** In some shell contexts the variable does not reach the `bws` subprocess. Use the explicit read, non-empty check, and export from Step 1.
- **Setting `override_existing: true`.** A key already set by another loader would be replaced without warning. Keep `false`, so the helper fills only missing keys.
- **Parsing secret JSON with grep and sed.** Escaped characters break regex parsing, and the output format can change. Use `jq` with `select()`.
- **Helper prints nothing.** The usual cause is a `select()` that matches no key. Key names are case-sensitive. List the names in the project with `bws secret list <project-id> -o json | jq '.[].key'`, which prints names, not values.
- **Timeout on first use.** `bws` can take a while on its first call, while it sets itself up. Use 20 seconds or more for the first run, and lower the setting later if it stays fast.
- **Exit code zero with no secret applied.** The script printed nothing, or an empty line. Confirm the script is executable with `chmod 700`, and confirm the `jq` filter matches the key name.

## Verification
- The configuration shows the bulk loader off, the helper on, and the absolute script path, with no errors.
- No unrelated key names appear in the resolved secrets for the profile.
- The forced-fallback run is answered by the fallback provider, and the usage file names it.
- The fingerprint check prints `MATCH=yes` for each profile that uses the helper.
- A backup of each profile's configuration exists before the change.
