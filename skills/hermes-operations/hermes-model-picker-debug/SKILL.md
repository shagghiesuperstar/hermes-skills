---
name: hermes-model-picker-debug
description: Use when the Hermes model picker shows zero, duplicate or stale models. Covers config-versus-session truth, picker data formats, cache refresh and picker implementation bugs.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, model-picker, providers, models, cache, debugging]
    category: hermes-operations
related_skills: [hermes-model-routing, hermes-auth-debug, hermes-fallback-chain-deploy]
---

# Hermes Model Picker Debugging

## Overview
The model picker lists providers and their models from three sources: the config file, the live session, and each
provider's model list. Most picker problems come from a mismatch between them. A picker can show zero models because a
provider's list is cached empty, duplicate rows because one provider has two slugs, or a stale model because a session
override was saved while the config said otherwise. This skill gives the order in which to check these sources, the
formats the picker accepts, and the implementation bugs to rule out when the code itself is at fault.

## When to Use
- The picker shows a provider with zero models, or shows the same provider twice.
- A model you configured does not appear, or a removed model still appears.
- The picker says one model is active, but the requests are served by another.
- A picker button fails to render, or the picker takes many seconds to open.
- A scheduled job needs the picker's cache refreshed and the refresh refuses to run without a terminal.

## Features
- Ordered check of live session state, config file and provider endpoint.
- Read-only inventory script that prints what the picker would show.
- Accepted `models:` formats, and what each field means.
- Auto-discovery of local endpoint models, with a rule for context-length values.
- Cache refresh from an interactive terminal, and a report of the fallback chain from any shell.
- Checklist of picker implementation bugs and their fixes.
- Cost check that compares the model the picker shows with the model that served recent calls.

## Benefits
- Config and session disagreements are found in one pass, without guessing.
- Picker bugs are separated from endpoint problems.
- Cost leaks from a stale override or a silent fallback are found from logs, not from the picker's label.

## Procedure
1. Check live session state first. The picker and the session override reflect what the operator chose, which can
   differ from the file:
   ```bash
   hermes model        # interactive; shows the active provider and model
   hermes config show
   ```
   If the two disagree, the session state is the choice in effect. Write it back to config with the model command when
   the operator confirms:
   ```bash
   hermes model --provider <provider> --model <model>
   ```

2. Print what the picker would list, read-only. Use the Hermes Python environment and the same listing function the
   picker uses, with the config's custom providers passed in:
   ```bash
   cd <hermes-clone> && source venv/bin/activate
   python -c "
   import yaml
   from hermes_cli.model_switch import list_authenticated_providers
   cfg = yaml.safe_load(open('<hermes-home>/profiles/<profile>/config.yaml'))
   for p in list_authenticated_providers(current_provider='<current>', custom_providers=cfg.get('custom_providers')):
       print(p['slug'], p['total_models'], 'current' if p['is_current'] else '')
   "
   ```
   Check only the provider names and counts. The credential pool holds tokens, so never print its contents.

3. Confirm each custom provider's endpoint lists the models you expect. The picker can show only what the config lists,
   and a local server may list models that are loaded but not healthy:
   ```bash
   curl -s http://<endpoint>/v1/models
   ```
   Take the `id` field of each entry in `data`, and compare it with the config's `models:` keys.

4. Refresh the picker's model cache. The cache is per profile, and a fresh cache is written only when the live fetch
   runs. Run `hermes model --refresh` from an interactive terminal. Headless jobs cannot pass the terminal check, so
   do not work around that check. Report the refresh as needed from the operator's terminal, and continue with the
   checks that do not need a terminal.

5. Report the fallback chain from any shell. It has no terminal requirement:
   ```bash
   hermes fallback list
   ```

6. For a model that is listed but fails, probe one real completion against the exact endpoint, key and model name. A
   listing alone does not prove inference works.

### Accepted `models:` Formats
The `models:` field takes either a flat list of names or a mapping of names to per-model settings.

Flat list, for models with no settings:
```yaml
- name: <provider-name>
  base_url: <endpoint-base-url>
  api_key: ''
  api_mode: chat_completions
  models:
  - <model-a>
  - <model-b>
```

Mapping, when a model needs a context-length value. An empty mapping means "use the server default":
```yaml
- name: <local-provider>
  base_url: http://127.0.0.1:<port>/v1
  model: <default-model>
  models:
    <default-model>:
      context_length: <tokens>
    <other-model>: {}
```

Rules that matter:
- `context_length` is the client's knowledge of a model, and a limit on how much context it sends. It is not the
  server's setting. If the client's value is higher than the server's, the server truncates silently.
- An empty mapping means the server default. Use it for a model that has not been tuned.
- Drop placeholder values that are clearly not real. A very small context length on a model that was never tuned is a
  placeholder.
- The singular `model:` field is the default. The mapping is the list the picker shows.
- If the mapping lists fewer models than the endpoint serves, the picker shows only the listed ones.

### Auto-Discovery for Local Providers
Prefer the endpoint's own list to a hand-written one. Probe the endpoint, parse the ids, and write the config once. The
config is static, so no watcher or scheduled job is needed. Local servers list only the models they have loaded, so the
list is more reliable than scanning model files on disk, which may include models the server cannot run.

When adding models to an existing provider:
1. Probe the endpoint and compare its ids with the existing keys.
2. Add each missing model with an empty mapping.
3. Keep every context-length value the operator has tuned.
4. Write the file and read it back.

### Picker Implementation Bugs
If the config and the endpoint are right and the picker still misbehaves, check these in the picker's listing code:

- **Telegram callback data has a short size limit.** A long provider slug can push the callback past that limit. The
  whole keyboard then fails to send, with no error in the logs. Send a short index instead of the slug, and look the
  slug up in the handler. Check every callback with a length assertion:
  ```python
  for i, p in enumerate(providers):
      cb = f"mp:{i}"
      assert len(cb.encode()) <= <callback-byte-limit>, f"{cb} too long"
  ```
- **A saved-provider section can read only the singular field.** If it ignores the list field, the picker shows zero
  models for a provider whose config is correct. Read both fields, the way the endpoint-defined section does.
- **Duplicate rows come from prefix mismatches.** A built-in provider and a custom entry with the same name carry
  slugs that differ only by a custom prefix, and an exact-match merge never joins them. Strip the prefix from both sides
  before comparing, and merge models into the existing row.
- **A hard skip must mark the slug as seen.** A bare `continue` in one loop leaves the slug unmarked, and a later loop
  adds the provider back. Mark the slug in the skip branch, or add the same skip to every later loop.

### Session Overrides and Real Cost
The picker's label shows the configured intent or the session override. It does not show the model that served the last
call. When a provider's credits run out or its endpoint fails, the fallback chain serves the turn, and the label does
not change.

Check the serving model from logs and from the session record:
```bash
grep -aE "Fallback activated|API call #|API call failed" <hermes-home>/profiles/<profile>/logs/agent.log | tail -20
sqlite3 <hermes-home>/profiles/<profile>/state.db "SELECT id, model, billing_provider FROM sessions ORDER BY started_at DESC LIMIT 3"
```
If repeated fallback lines appear, treat it as a cost leak. A session override that names a model with the wrong
provider can route every turn to a costly backstop. Fix it by choosing the correct provider and model in the picker,
which writes through the gateway. Editing the session store directly is an operator task. The gateway holds session
routing in memory and writes it back on shutdown, so stop the gateway first, edit, back up first, and start it again.
Do not edit the store while the gateway runs.

Check each fallback entry with one real request, and order the chain so a fast-failing provider cannot send every turn
to the most expensive tier. Prune entries whose provider is not configured.

### Local Server Returns 500 on Inference
A local server can list a model as loaded while every completion for it returns HTTP 500. The picker sees the model as
available because the listing does not test inference. Send one short completion with a small token limit to the exact
model name. If it fails, read the server's own log for the error. Corrupted weights, a quantization mismatch, and a
crashed generation core each show a different message. Switch the primary to a model that completes, and restart the
server from its own app, not from the gateway.

### Slow `/model` Opening
If the picker takes many seconds to open, the picker is probably doing live inventory calls on open. Each provider's
catalog, pricing and model endpoint is called before any button is drawn. Render the picker at once from the cache, and
refresh the live data in the background. Keep the blocking, live scan for an explicit refresh command, and bound each
probe with a timeout, running them in parallel.

### Policy Hiding a Provider
When a profile must not show a provider that Hermes supports, remove every reference first: the credential entries, the
config entries, the custom providers and the fallbacks. If a built-in row still appears, the fix is a code change to the
listing function. Ask for approval before making that change. After any change, restart the gateway, request a fresh
picker, and check that only the intended providers remain. A cached keyboard from before the restart can show old rows.

## Pitfalls
- **Check session state before you trust config.** A picker selection can change the session without touching the file.
- **A picker count of zero is often a cache, not a missing provider.** Refresh the cache from a terminal, then check again.
- **Do not print the credential pool.** It holds tokens. Print provider names and counts.
- **A listing is not an inference test.** Always finish with one real request.
- **The `local` provider can show zero models and still be fine.** Some local inference exposes no list endpoint.
- **Do not work around the terminal check on the refresh command.** Use the terminal, or report the refresh as pending.
- **Profile-scoped paths differ from the root path.** Look in the profile's folder for the cache and the session store.

## Verification
- The listing function shows each intended provider once, with a model count above zero for every reachable provider.
- Each custom provider's endpoint list matches the `models:` keys in its config.
- A test completion on each listed model returns a real answer.
- `hermes fallback list` shows the intended chain with no retired entries.
- The most recent agent-log turns name the model and provider you expect, with no fallback line after them.
