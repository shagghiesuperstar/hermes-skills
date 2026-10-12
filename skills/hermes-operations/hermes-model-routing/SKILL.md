---
name: hermes-model-routing
description: Use when wiring a model provider or fallback chain. It also applies to auxiliary lanes and to sweeping a retired model from every route. Covers slugs, lanes, pools and quota signals.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, model-routing, providers, fallback, credentials, auxiliary, subscriptions]
    category: hermes-operations
related_skills: [hermes-model-picker-debug, hermes-fallback-chain-deploy, hermes-auth-debug, config-verify-before-write]
---

# Hermes Model Routing

## Overview
Hermes routes each kind of work through a model layer made of providers, credential pools, auxiliary lanes, a fallback
chain and a picker. A route is only as good as its weakest surface: a model can be retired in the main config yet still
named in a preset, a cron prompt or a profile's standing instructions. This skill covers how to choose a lane for a
model, how to add one safely, how to sweep a retired model from every surface, and how to tell a real quota limit from
a transient or mis-set one. Examples use placeholder names, so substitute your own providers and slugs.

## When to Use
- You are adding a model to an advisor, judge, review, planning or other auxiliary lane.
- You are arming or reordering a fallback chain.
- A model is retired, banned, or its credit is nearly gone, and every route to it must change.
- A provider returns a rate-limit or quota error and you must decide whether to retry, fall back or re-login.
- An operator asks why a model changed, or why a provider appears more than once.

## Features
- Docs-first procedure: read the current official page before any local note.
- Lane-selection rules that keep the implementer model apart from advisor and review lanes.
- Canonical slug resolution by probing the provider, not by trusting an alias.
- A three-tier smoke test: upstream, Hermes resolver, and a real turn.
- Pool-strategy rule based on whether credential rows share a reset window.
- Quota-signal triage that separates a window limit from a model throttle and a stale credential.

## Benefits
- The implementer model is never changed by an advisor-lane wire.
- A retired model is removed from every surface, not just from the main config.
- Fallback slots are armed only after a live probe, so a dead slot does not fail silently.
- Quota problems are fixed at the right layer, without rotating keys that are not the cause.

## Procedure
1. Read the current official docs before anything else. Start from the docs index, open the page for the task, and run only the command that page names. If a local note disagrees with the page, the page wins, and you update the note in the same turn.

2. Classify the wire before you write anything. Pick one of three cases:
   - **Built-in provider.** The provider is already registered. The wire is an API key in the profile's env file under the documented name, plus an optional entry in a preset. Do not create a custom entry for a built-in provider, because that splits credentials and confuses the picker.
   - **Custom OpenAI-compatible endpoint.** Register it under the custom providers section with its base URL, its key reference, and the model names it serves.
   - **Existing provider, new model.** Resolve the canonical slug, then append it to the right preset or lane. Nothing else changes.

3. Pick the lane. Keep these apart:
   - the **implementer** model, which does the coding and sets `model.default` and `model.provider`;
   - **advisor, judge, review and planning** lanes, which feed the implementer and are usually more expensive;
   - **auxiliary** tasks such as vision, compression, titles and task decomposition;
   - the **fallback chain**, whose first slot is effectively the primary for cost purposes.

   A new advisor-only model goes into a preset or an auxiliary lane. It never goes into `model.default`, `model.provider`,
   or the first slot of the fallback chain. Verify after the write that the implementer keys are unchanged.

4. Resolve the canonical slug by probing, not by trusting a name. Catalogs publish preview aliases that return a
   "not found" message naming the canonical id. Send one short completion with a small token limit:
   ```bash
   probe=$(mktemp)
   curl -s -o "$probe" -w "HTTP=%{http_code}\n" --max-time 30 \
     -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
     -d '{"model":"<alias-or-slug>","messages":[{"role":"user","content":"hi"}],"max_tokens":20}' \
     https://<provider-base>/v1/chat/completions
   rm -f "$probe"
   ```
   - 200 with non-empty content: the slug is canonical.
   - 404 that names a successor: use the successor, and do not retarget silently.
   - 401 or 403: the key is wrong or does not cover this model. Stop and ask.
   Read the key from the secret store into a variable, and never print it.

5. Apply the change with the verification ladder from `config-verify-before-write`. Add a scope check so only the
   intended section changes:
   ```python
   drift = [k for k in parsed if k != "<target-section>" and parsed[k] != parsed_post.get(k)]
   assert not drift, f"FATAL: unexpected change in {drift}"
   assert parsed_post["model"]["default"] == parsed["model"]["default"]
   ```

6. Smoke test in three tiers:
   - **Upstream:** the probe from step 4, repeated on the canonical slug, asserting HTTP 200 and expected content.
   - **Hermes resolver:** `hermes chat --provider <provider> --model <slug> -Q -q "say ok in one word"`. A slug the picker does not recognize falls back silently here, so check the reply and the log.
   - **Real turn:** the first live turn that uses the lane, then the logs for that turn. A 200 reply does not prove the intended route served it.

   For long prompts, write the prompt to a file and use the query-file option. Passing a large prompt as an argument fails on the operating system's argument-size limit.

7. Sweep a retired model with a fixed order:
   1. Survey every surface: the main config's model, fallback and auxiliary keys, every preset's aggregator and reference
      lists, every profile's own config, each profile's standing-instruction and memory files, cron job prompt text,
      harness settings keys, skill files and engine scripts. Grep the whole tree for the id, not just the model sections.
   2. Back up every file you will touch into one dated folder, and verify the folder exists before the first edit.
   3. Classify each hit as **active** (a future run could execute or advertise it) or **citation** (a dated record of
      why it died). Rewrite active hits to a named successor. Leave citations verbatim.
   4. Point every live route at its successor. Never leave a gap.
   5. Verify with a case-insensitive grep over the same list, print the count per file, and report how many citations
      remain.
   6. Write a summary table of file, old value and new value, and the end-state chain per profile.

### Fallback Chains
- Failover is on error. Hermes walks the chain only when the primary fails. It does not drain a cheap tier first. To
  use a free or cheap tier first, make that tier the primary, or route that work to it explicitly.
- A reset-aware chain stays on a fallback until the primary's reset time passes, when the primary reports one. This is
  why a weekly window can keep a fallback in use for days.
- Chains are per profile. A change to the default profile does not reach other profiles. Loop over the default profile
  and every profile directory, and verify each with `hermes -p <profile> fallback list`.
- Arm the chain with the official command, and read the written file back:
  ```bash
  hermes -p <profile> config set fallback_providers '[{"provider":"<p1>","model":"<m1>"},{"provider":"<p2>","model":"<m2>"}]'
  hermes -p <profile> fallback list
  ```
  The interactive add command cannot run from a script. Parse-validate every edited config file before you close the
  change, because a config error does not show up until the next restart.
- Probe each fallback slot with a real completion before you arm it. A slot with a dead model name fails silently until
  it is needed. A local slot whose server is down adds its full timeout to every cascade, so do not arm an unchecked
  local slot.
- Do not change the chain or the model while a production session is live. A mid-turn change resets the prompt cache.

### Credential Pools and Quota
- A pool row is a credential slot, not a subscription. One login can appear as several rows, and two subscriptions can
  show four or more rows. Map rows to identities with the provider's identity endpoint or a token fingerprint before
  you report counts.
- Choose the pool strategy by reset cycle, not by parallelism:
  - **Fill-first** when the rows share the same weekly window and reset day. Round-robin would drain both at once.
  - **Round-robin** when the rows reset on different cycles, for example a weekly window alongside a monthly one.
- Access tokens expire silently and refresh in the background. Ask whether a row is still being served, not whether its
  token is valid.
- A provider can throttle one model while the account is healthy. Check three things in order: the usage endpoint, a
  small request to a model the account is known to serve, and the request to the throttled model. If the first two
  pass and only the third fails, back off and retry, or pin a different model. Do not re-login or rotate keys.
- Some providers gate models by client version string. Probe with the current client version, or a supported model
  looks unsupported.
- Some providers have two independent limits, a short rolling window and a weekly balance. Clear both before you say
  the provider is available. Name the limit that is hit and its reset time.
- A rate-limit response that carries a plan or quota code is a terminal signal for that pool on the first attempt. Mark
  the pool exhausted, fall back immediately, and let a later run retry. Retrying the same exhausted pool multiplies
  load on one bucket.
- A row can stay out of service while it looks healthy. Check its per-model cooldowns, and check for an environment
  variable that shadows the pool. Clear the shadow and reset the cooldown. Changing priorities does not fix either.
- Switching the model for a live session does not switch the credential. Probe the target row directly with the target
  model before the live switch. If the probe fails, do not switch.
- A secrets manager can re-inject an old token into every new process. Delete the stale item, then start a new
  process. A running session keeps the old environment.
- Never run a keychain command from a chat tool. It can open a login prompt the operator reads as suspicious.

### Quota Signals
- Read the signal before you act. A window limit (short reset) is different from a weekly limit (long reset), and both
  differ from a throttle on one model. Each has a different fix.
- A "usage limit reached" row with a short reset means wait for the window. Fall back for that window.
- A model-level throttle on a healthy account means back off, or pin another model on the same account.
- A stale credential usually shows as a repeated unauthorized or forbidden response on a single row. Re-login through
  the operator's terminal, then probe again.
- Some 403 responses come from the provider's account layer and clear after a fresh login. Re-login first, and do not
  change the config to dodge the error.

### Free and Keyless Tiers
- A free or keyless tier can list models that the provider no longer serves. A catalog listing is not proof of service.
  Probe an anonymous completion before you arm it.
- A tier whose terms allow the provider to train on prompts may need an explicit consent flag before unattended use.
  Set the flag through the config command, read it back, and keep such tiers to low-stakes work.

## Pitfalls
- **Never change the implementer model as a side effect of an advisor wire.** Verify the implementer keys after the write.
- **A listing is not an inference test.** Finish every wire with one real completion.
- **An alias can resolve in the picker and fail in a one-shot command.** Check which lane served a session in the
  session record, not in the reply text.
- **Prompt text is a routing surface.** A model id written into a cron prompt, a task file or a skill step routes
  work even when no model field names it.
- **Standing instructions are a routing surface.** A profile's instruction file can pin a model that the config does
  not mention.
- **Silent failover can look like a picker change.** Before you explain a switch, check the turn record, the fallback
  lines and the gateway log. If none of them show a failover, the display or the stored override drifted, and that is a
  different fault.
- **A session override can name a model with the wrong provider.** Every turn then routes to the wrong place. Check the
  session record and fix it through the picker.
- **Do not claim failover that the logs do not show.** Mark any unproven mechanism as partial.
- **Pin the check to the provider's own page.** Community caches and metadata files can lag retired ids and mislabel
  free tiers.
- **Do not assume a healthy account means a healthy row.** Check the row that will serve the request.

## Verification
- `hermes -p <profile> fallback list` shows the intended chain for every profile in scope.
- Each lane's model answers a real completion, and the turn record names the model and provider you expect.
- The implementer's `model.default` and `model.provider` are unchanged after any lane change.
- A sweep leaves no active references to the retired id. Citations remain, and the count is reported.
- The config parses after every edit.
