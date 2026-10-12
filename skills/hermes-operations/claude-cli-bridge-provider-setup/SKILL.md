---
name: claude-cli-bridge-provider-setup
description: Use when wiring a local Claude CLI bridge into Hermes as a provider. Covers bridge install, custom provider registration, launchd keepalive, and OAuth re-login.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [claude, cli-bridge, hermes, provider, launchd, oauth]
    category: hermes-operations
related_skills: [claude-cli-model-switching, hermes-model-routing]
---

# Claude CLI Bridge Provider Setup

## Overview
Hermes can use a Claude subscription without storing an Anthropic API key by routing requests through a local
OpenAI-compatible shim. The shim listens on loopback and runs `claude --print` as a subprocess, so inference uses the
CLI's own keychain login. This skill covers building the shim, registering it as a Hermes custom provider so its models
appear in the model picker, keeping it alive under launchd, and re-authenticating when the OAuth session expires.

## When to Use
- A host needs Claude subscription models through the local Claude CLI and must not hold an API key in Hermes.
- The bridge provider is missing from the model picker, or its model list is empty.
- The bridge process is down, or chat fails while the health check still passes.
- Inference returns an OAuth "session expired" error.

Not for ordinary interactive Claude Code sessions, or for the model slug tables (see `claude-cli-model-switching`).

## Features
- OpenAI-compatible `/v1/models` and `/v1/chat/completions` shim bound to `127.0.0.1` only.
- A Hermes `custom_providers` entry with a pinned model map that drives the picker.
- Two LaunchAgents: a KeepAlive bridge and a watchdog that heals health and flags auth failures.
- A PTY-driven re-login procedure for an expired OAuth session.
- A truth probe that tests real inference instead of login status text.

## Benefits
- Claude models work from Hermes with no API key stored in Hermes config.
- The bridge survives crashes and reboots without a manual restart.
- Auth failures surface in one probe and in the watchdog flag, not in a failed user session.
- Loopback binding keeps the shim off the network.

## Procedure
1. Resolve the Claude binary and confirm the CLI login with a real inference call:
   ```bash
   CLAUDE_BIN="$(command -v claude || true)"
   [[ -x "$HOME/.hermes/node/bin/claude" ]] && CLAUDE_BIN="$HOME/.hermes/node/bin/claude"
   [[ -x "$HOME/.local/bin/claude" && -z "$CLAUDE_BIN" ]] && CLAUDE_BIN="$HOME/.local/bin/claude"
   "$CLAUDE_BIN" --version
   "$CLAUDE_BIN" auth status --text
   "$CLAUDE_BIN" --print --model haiku 'reply with exactly: ok'
   ```
   Done when the last command prints `ok` and exits 0. If it fails, stop and run the re-login procedure below.

2. Build the bridge tree at `~/tools/cli-bridge/` unless `bridge.py` already exists. The shim, `bridge.py`, comes from the
   upstream Daimon-Law/cli-bridge project: take its script from that project, then write the configuration below. If another
   host has a known-good tree, copy it instead of fetching the shim again:
   ```text
   ~/tools/cli-bridge/
     bridge.py
     bridge.conf        # KEY=VALUE; loaded without overriding existing environment
     requirements.txt   # aiohttp>=3.9
     run.sh
     .venv/
     logs/
   ```
   Write `bridge.conf` with the loopback host, a free loopback port (shown here as `<port>`) and the absolute Claude path:
   ```bash
   CLI_BRIDGE_HOST=127.0.0.1
   CLI_BRIDGE_PORT=<port>
   CLI_BRIDGE_BIN=<absolute-path-to-claude>
   CLI_BRIDGE_DEFAULT_MODEL=<default-slug>
   CLI_BRIDGE_TIMEOUT=600
   CLI_BRIDGE_MODELS=<comma-separated-slugs>   # e.g. the opus, sonnet and haiku slugs your account can run
   ```
   `run.sh` should `cd` to its own directory and `exec .venv/bin/python bridge.py`.

   The shim must:
   - answer `GET /health` with an ok body;
   - list `CLI_BRIDGE_MODELS` at `GET /v1/models` and `GET /models`;
   - handle `POST /v1/chat/completions` by running `claude --print --output-format text --model <id> <prompt>` and
     returning an OpenAI-shaped `choices[0].message` object;
   - strip a trailing `-max` from the model id and pass `--effort max` (Opus models only);
   - refuse bind hosts `0.0.0.0` and `*`, forcing `127.0.0.1`;
   - load the config file without overriding variables already set in the environment.

   Then create the venv and install dependencies:
   ```bash
   cd ~/tools/cli-bridge && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
   chmod +x run.sh bridge.py && mkdir -p logs
   ```

3. Start the bridge. For debugging, run it in the foreground with `./run.sh`. For persistence on macOS, run it as a
   LaunchAgent in the user's GUI session (`gui/$UID`), never a LaunchDaemon: the Claude login lives in the user's login
   keychain and a root daemon cannot read it. Write the plists with `plistlib`, then reload with bootout and bootstrap:
   ```bash
   launchctl bootout gui/$(id -u)/ai.custom.cli-bridge 2>/dev/null
   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.custom.cli-bridge.plist
   ```
   Give the bridge `KeepAlive` and `RunAtLoad` with `CLI_BRIDGE_HOST=127.0.0.1` in its environment. Give the watchdog
   a `StartInterval` of 120 seconds. Confirm:
   ```bash
   curl -sS --fail --max-time 5 http://127.0.0.1:<port>/health
   lsof -nP -iTCP:<port> -sTCP:LISTEN     # must show 127.0.0.1, never *:<port>
   curl -sS http://127.0.0.1:<port>/v1/models
   ```

4. Register the Hermes custom provider. Back up the config first:
   ```bash
   TS=$(date +%Y%m%d-%H%M%S)
   cp -a "$(hermes config path)" "$(hermes config path).bak_cli_bridge_${TS}"
   ```
   Append under `custom_providers:`. Do not touch `model.default` or `fallback_providers`:
   ```yaml
   custom_providers:
     - name: claude-cli-bridge-test
       base_url: http://127.0.0.1:<port>/v1
       api_key: cli-bridge-local
       api_mode: chat_completions
       model: <opus-slug>
       models:
         <opus-slug>:
           context_length: 200000
         "opus[1m]":
           context_length: 1000000
         haiku:
           context_length: 200000
   ```
   Add one `models:` key for every `CLI_BRIDGE_MODELS` entry. Edit with PyYAML or the `hermes config` helpers, not
   hand-run `sed`. Then run:
   ```bash
   hermes config check
   hermes model --refresh
   ```

5. Run the end-to-end smoke test through the bridge and through Hermes:
   ```bash
   curl -sS -m 120 http://127.0.0.1:<port>/v1/chat/completions \
     -H 'Content-Type: application/json' \
     -d '{"model":"haiku","messages":[{"role":"user","content":"reply with exactly: ok"}]}'
   hermes chat -q 'reply with exactly: ok' --provider claude-cli-bridge-test --model haiku
   ```
   If `hermes chat` is blocked in your agent shell, report the block and ask the operator to run that command from a
   terminal. Done when both paths return `ok`.

6. Expand the model list when a new slug is needed:
   1. Verify the slug: `"$CLAUDE_BIN" --print --model <slug> 'reply with exactly: ok'`.
   2. Add it to `CLI_BRIDGE_MODELS` in the config, and to the plist environment if launchd runs the bridge.
   3. Add the same key under `claude-cli-bridge-test` → `models:` with a `context_length`.
   4. Reload with bootout and bootstrap, then `curl -s http://127.0.0.1:<port>/v1/models` and `hermes model --refresh`.
   5. Run one chat smoke on the new slug.

### Keepalive and watchdog
The watchdog runs every 120 seconds and does four things:
1. Probes `GET /health`. On a miss it runs `kickstart -k`, then bootout and bootstrap. If the port is still held, it stops
   only a process whose command line is this bridge's own command. It logs that process's PID and command first, and it
   leaves any other process on the port alone and reports it.
2. Runs the auth truth probe. On failure it writes `state/auth_flag.json` with `need_reauth: true`.
3. Schedules the next truth probe at a randomized 20 to 28 hours. Give each host a different first-check time so a
   fleet does not probe at the same moment.
4. Starts at most one re-login attempt, guarded by a lock file that expires after 30 minutes, so repeated ticks do not
   launch parallel logins.

Launchd environment rules:

| Change | Correct action |
|---|---|
| Models or env under launchd | Edit the plist (or the config, then re-run the installer), then bootout and bootstrap |
| Models or env, foreground only | Edit the config and restart `./run.sh` |
| Any plist change | Never rely on `kickstart -k` alone for environment changes |

### Re-login after OAuth expiry
Symptoms: `/health` is ok but chat returns `process exited rc=1`, or the CLI reports that the OAuth session expired and
could not be refreshed. `auth status` can still show a logged-in account.

1. Run the truth probe. If it prints `ok`, clear the flags in step 5 and stop.
2. Start `claude auth login` under a pseudo-terminal driver, run with a Python environment that has the driver
   library installed. The driver reads the authorize URL the login process prints and gives it to the operator.
   Send the returned code to the driver's input once it is available. Do not start the login as a background
   job with its input closed.
3. Open the authorize URL that this login process printed. Follow the consent pages in order (authorize, sign in, choose
   the account, authorize again) until a page shows the authentication code. Passwords, two-factor codes, passkeys and
   billing are entered by a human, never by the agent.
4. Save the returned `code#state` string to the code file. Do not print it, paste it into chat, or send it to a
   notification channel.
5. Verify and clear the flags:
   ```bash
   "$CLAUDE_BIN" --print --model haiku 'reply with exactly: ok'
   curl -sS -m 120 http://127.0.0.1:<port>/v1/chat/completions -H 'Content-Type: application/json' \
     -d '{"model":"haiku","messages":[{"role":"user","content":"reply with exactly: ok"}]}'
   rm -f ~/tools/cli-bridge/state/oauth_code.txt
   ```
   Set `need_reauth` to `false` in `state/auth_flag.json`, remove the lock file, and if health is ok but chat still
   fails, run `launchctl kickstart -k gui/$(id -u)/ai.custom.cli-bridge`.

## Pitfalls
- **Health is not auth.** `/health` can return ok while every chat fails with an expired OAuth session. Always run the
  haiku probe through the bridge.
- **An empty picker has three causes.** Check the `models:` map, whether the bridge is running, and whether
  `hermes model --refresh` ran. Check all three before editing anything else.
- **Editing only the config under launchd leaves a stale environment.** Plist `EnvironmentVariables` win over the
  config loader, so re-run the installer and reload with bootout and bootstrap.
- **Never bind `0.0.0.0`.** Any other interface exposes your Claude subscription to the network.
- **Keep the bridge out of the default and fallback chains unless the operator approves it.** It is a picker-only
  provider by default.
- **Quote bracketed model names in YAML.** An unquoted `opus[1m]` is parsed as a flow sequence and breaks the config.
- **Do not run `bridge.py` forever in a foreground terminal.** Use launchd or another process manager so it survives
  restarts.
- **Do not restart the Hermes gateway to fix the bridge.** It is outside this job and it ends other sessions.
- **Use a Python environment that has the driver library.** Agent shells often run a Python that lacks it.
- **Never reuse an OAuth code after its login process has exited.** The CLI rejects it with "Invalid state parameter".
- **Never pipe into the login process with a named pipe or a background job with stdin on `/dev/null`.** The code
  cannot reach the process; use a pseudo-terminal driver.
- **A human completes the OAuth browser steps.** The agent does not click through the consent pages or enter any
  credential.

## Verification
Report the verbatim output of each command:
```bash
"$CLAUDE_BIN" --version
"$CLAUDE_BIN" --print --model haiku 'reply with exactly: ok'
curl -sS http://127.0.0.1:<port>/health
lsof -nP -iTCP:<port> -sTCP:LISTEN
curl -sS http://127.0.0.1:<port>/v1/models
grep -A40 'claude-cli-bridge-test' "$(hermes config path)" | head -50
```
PASS when all of these hold:
- health is ok;
- the listener is on `127.0.0.1` only;
- the models list is non-empty;
- haiku returns `ok` both directly and through the bridge;
- the provider is present in config;
- default and fallback providers are unchanged.

## Attribution
The bridge shim is the upstream Daimon-Law/cli-bridge project's script. This skill covers its configuration, its launchd setup and the keepalive procedure.
