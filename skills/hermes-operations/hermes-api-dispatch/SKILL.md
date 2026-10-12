---
name: hermes-api-dispatch
description: Use when dispatching or steering an async agent run over the Hermes local API. Covers POST, polling, steering, stopping and wedge triage.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, api, dispatch, async-runs, orchestration, operations]
    category: hermes-operations
related_skills: [hermes-gateway-ops]
---

# Hermes API Run Dispatch

## Overview
The Hermes gateway exposes an OpenAI-compatible HTTP API on loopback. A script or another agent can start an agent run
asynchronously, poll it, steer it, or stop it. The contract is simple, but three things cause most failures: a run that
inherits the wrong model because a field was left empty, a steer sent to a run that already finished, and a status read
from the HTTP code instead of the run's `status` field. This skill covers the request contract, the run lifecycle, and
how to tell a live wedge from a harmless stale record.

## When to Use
- You need to start an agent run from a script, a cron job or another agent, and not wait for it to finish.
- A run is sitting in `waiting_for_approval`, or a poll and a control call disagree.
- You need to steer a running agent with a correction, or stop one that is going the wrong way.
- You are about to start a second writer on the same files, and need to check for sibling runs first.

## Features
- Liveness check and secret loading that keeps keys out of logs and process environments.
- `POST /v1/runs` dispatch with explicit model and provider, plus an optional idempotency key.
- Lifecycle control: poll a run, steer it while it is running, or stop it.
- Triage rules for wedges, stale session rows and cross-host run ids.
- A sibling-run check before dispatching writers.

## Benefits
- Runs land on the intended model every time.
- Duplicate dispatches are caught before two agents write the same file.
- Steering and stopping go to runs that will accept them, so the calls do not fail silently.
- Status is read from the right field, so a healthy record is not mistaken for a live process.

## Procedure
1. Confirm the listener before building a payload:
   ```bash
   curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:<port>/v1/models
   ```
   A 401 means the key is missing or wrong. It does not mean the server is down.

2. Load the key in a fresh child process, not in the shell. Use the Hermes secret loader from the agent's own virtual
   environment. Pass its arguments by keyword, because a positional home argument raises `TypeError`:
   ```python
   # run with <hermes-install>/venv/bin/python from a script file
   import os, sys
   sys.path.insert(0, "<hermes-install>")
   from <hermes-loader-module> import load_hermes_dotenv, hydrate_profile_secret_sources
   load_hermes_dotenv(hermes_home=<hermes-home>, load_external_secrets=True)
   hydrate_profile_secret_sources(<hermes-home>)
   key = os.environ.get("API_SERVER_KEY")
   assert key, "FATAL: API_SERVER_KEY not set after loading"
   ```
   Print presence and length only. Never print the key.

3. Dispatch with an explicit model and provider on every request:
   ```bash
   curl -sS -X POST http://127.0.0.1:<port>/v1/runs \
     -H "Authorization: Bearer $API_SERVER_KEY" \
     -H 'Content-Type: application/json' \
     -H 'Idempotency-Key: <one-key-per-logical-dispatch>' \
     -d '{"input":"<self-contained brief>","model":"<model-slug>","provider":"<provider>"}'
   ```
   A healthy dispatch returns HTTP 202 with a `run_id` and `status: started`. Keep the brief in a file and pass its
   contents, so multi-line text is not mangled by shell quoting.

4. Poll and control the run:
   - `GET /v1/runs/<run_id>` returns the run with its `status`. Statuses move through `queued`, `running`,
     `completed`, and `cancelled`.
   - `POST /v1/runs/<run_id>/steer` with `{"input": "..."}` sends a correction. It is accepted only while the status is
     `running`. Otherwise it returns 409 `run_not_accepting_steer`, and you should start a new run instead.
   - `POST /v1/runs/<run_id>/stop` returns 200 at once. The run then reads `cancelled`.

   Read the `status` field, not the HTTP code. A 200 on a cancelled run means the record exists, not that the agent is
   still working.

5. Check for sibling runs before dispatching any writer. Every message posted to the same session starts its own
   concurrent run. Find them in the agent log, group them by session, and keep one owner for each file:
   ```bash
   grep -Eo 'run_[0-9a-f]{32}' <hermes-home>/logs/agent.log | sort -u
   ```
   Fetch each run, group the results by `session_id`, stop the queued duplicates, and steer the rest.

6. Triage a run that looks stuck:
   - A run in `waiting_for_approval` is a real wedge. Deny that approval with
     `POST /v1/runs/<run_id>/approval` and `{"choice": "deny"}`. Do not approve configuration writes.
   - A session row with no end time whose run GET returns 404 is a stale record. The process forgot the run. Do not
     stop or close it as a fix.
   - A run id that returns 404 on this host may have been created on another host. Run records are per gateway.

7. Restart or stop the gateway only as a separate, operator-approved step through its service manager. An agent run
   should not restart the gateway that is hosting it. If a command is blocked by a safety check, report the block to
   the operator. Do not reword the command to get it past the check.

## Pitfalls
- **An empty model or provider field falls through to the config default.** That default can be the most expensive
  model. Pin both on every dispatch.
- **Do not use a real prompt to probe the API.** A POST with an empty body returns 400 `Missing 'input'` when the
  server is healthy. A 409 while a GET is in flight points to the deadlock class. Probe with the empty body, not a
  task.
- **There is no run listing endpoint.** `GET /v1/runs`, `POST /v1/runs/list` and `POST /v1/runs/search` return 405.
  Discover run ids from the session list or the agent log, then GET each one.
- **The 202 response is the run id.** Do not treat a chat session as the run id, and do not wait for completion in the
  dispatching turn.
- **A GET can return `provider: null` even when the POST pinned one.** Confirm the dispatch with the `model` field.
- **A new run can show a placeholder model for a moment.** Poll once or twice before deciding the wrong model was routed.
- **Never put a dispatch key or a provider key in a log, a report or a cron prompt.** Cron prompts can carry secrets.
- **Do not launch a working child with flags that disable its skills.** A child started that way parks instead of
  doing the work.
- **Check the live model list before pinning a slug.** Use the models endpoint and pin the name that was asked for.
  Do not substitute a near match.
- **Parallel workers collide on deterministic output paths.** On a stale-write block, read the file, check it against
  the brief, and report its path. Do not overwrite a peer's draft.
- **Steer text lands at the next tool boundary.** It does not rewrite output already in progress. Send corrections about
  scope, paths and locks, not partial edits.

## Verification
- The models endpoint returns 200 with the key, and the probe with an empty body returns 400 `Missing 'input'`.
- A dispatch returns 202 with a `run_id`, and a follow-up GET shows `status` of `running` or `queued`.
- A steer to a running run returns 200. A steer to a finished run returns 409 `run_not_accepting_steer`.
- After a stop, the GET shows `cancelled`.
- The sibling-run check lists one owner per file before any writer starts.
