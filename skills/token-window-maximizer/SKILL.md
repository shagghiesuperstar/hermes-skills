---
name: token-window-maximizer
description: Use when choosing routes for expiring subscription quota. Covers evidence labels, per-window telemetry, Hermes-native routing and canary changes.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [llm, routing, quotas, subscriptions, telemetry, fallback]
    category: hermes-operations
related_skills: [hermes-model-routing, hermes-fallback-chain-deploy, hermes-auth-debug]
---

# Token Window Maximizer

## Overview
Some model subscriptions include a capacity allowance that resets on a window and does not carry over. Unused allowance
is lost when the window closes. This skill helps choose which included route should receive real queued work before
that allowance expires. It is a utilization method, not a cost minimizer, a benchmark, or a way to make work. Every
decision needs evidence for each quota window, and an unknown quota never drives an automatic change.

## When to Use
- Included or prepaid model capacity is about to expire, and real queued work is waiting.
- You need to choose which subscribed route should take the next piece of work.
- You need to inventory limits, remaining capacity, reset times, rate-limit headers or usage counters across routes.
- You are reviewing a router or a fallback order for how it spends a quota window.

Not for minimizing the price per token, picking the best model, getting around a provider's controls, or creating work
to spend quota. If there is no real work, the recommendation is no spend.

## Features
- Evidence labels for every material claim: verified, inferred, unknown.
- Classification of each named system before it goes into a route list.
- Separate tracking for throughput limits, subscription windows, spend caps, context limits and availability.
- Telemetry methods in order of trust, from live quota endpoints down to client-side estimates.
- A routing rule that prefers included capacity about to expire, and ranks only verified numbers.
- A minimal change procedure with a one-profile canary and a stated rollback.

## Benefits
- Included capacity is used for real work before it expires.
- Usage numbers are never presented as remaining allowance.
- Changes are small, reversible and proven on one profile before any wider rollout.
- Credentials stay inside the runtime that owns them.

## Procedure
1. Gather only the inputs that change the decision: the Hermes version, the profiles involved and their current provider,
   model, fallback and credential-pool settings, the kind of credential (API key, OAuth or pool, never the secret itself),
   the plan class, and the real work with its priority, deadline and tools. If an input would change spend, data exposure
   or availability and is missing, stop and ask one focused question.

2. Classify each system before listing it as a route:
   - inference provider: serves models and enforces a billing or capacity boundary;
   - aggregator or gateway: routes to upstream providers, and its own quota may differ;
   - agent product: consumes inference and may not expose the token window;
   - model creator: may not run the endpoint being used;
   - compute host: metered compute, not a shared token allowance unless proven;
   - local inference: owned hardware, with no expiring window unless an outside service imposes one.

3. Track each dimension separately: throughput (requests and tokens per minute, concurrency), subscription entitlement,
   spend or credit cap, context limit, and availability (rate-limit and server errors). Never combine them into one
   percentage. Name the binding dimension, which is the one most likely to block the next call.

4. Collect telemetry from the most trusted source that exists, and label the result:
   - Live quota endpoint for the exact account, project and model. Poll it conservatively.
   - The Hermes runtime for the exact profile and request.
   - Response headers, when the provider documents them. Re-check the header names before use, and do not assume that an
     OpenAI-compatible endpoint returns OpenAI headers.
   - A usage payload. It proves what one call used, not what remains.
   - An operator's dashboard reading, with its timestamp. It is true for that moment only.
   - Error responses only. They show throttling or exhaustion, but not the remaining total.

   Mark the result verified when it comes from one of the first three, inferred when it is reasoned from them, and unknown
   otherwise. Unknown capacity never wins an automatic routing decision.

5. Record each independently enforced entitlement as one state entry: the provider, the route, an opaque credential
   reference, the plan class, the quota dimension, the window kind, the limit, the remaining amount, the reset time in
   UTC, the observation time, the origin of the value, the confidence and the health. Keep the requests and tokens limits separate,
   and keep a short window and a weekly window separate. Never store a secret.

6. Filter routes before ranking them. Drop any route that lacks the capability, context length, tools, data-handling
   terms or deadline the work needs, that is below its reserve, or that is unhealthy.

7. Rank the remaining routes with the expiry arithmetic below. Only verified or operator-supplied numbers feed it:
   - remaining fraction = remaining / limit;
   - time fraction = seconds until reset / window length, capped at 1;
   - expiry pressure = 1 minus the time fraction;
   - stranding score = remaining fraction times expiry pressure.

   Prefer the route with the higher score among those that fit. Paygo, free, compute and local routes are outside this
   objective unless the operator includes them.

8. Track concurrent windows together. A route with an open short window and a nearly used weekly cap should not burn
   the short window in a way that empties the weekly cap. Show both windows in the recommendation.

9. Avoid thrashing. Keep the current route unless the score gap is material. Re-evaluate on new telemetry, at a task
   boundary, after a failure, or when the queue changes materially.

10. Use Hermes for routing. Confirm the commands and fields against the installed version's help and configuration
    schema before you write them. Use credential pools before custom key handling. Use the documented fallback order
    for cross-provider fallback. Fallback is failure-driven, so it is not a proactive scheduler.

11. Make any change by the minimal route:
    - list the exact files and the exact behavior change for each;
    - state why no simpler setting does the job;
    - give the verification command and the rollback path, which is the backup of the previous configuration;
    - apply it to one reversible profile first, and check the actual provider, model, usage and reset in the runtime;
    - roll back that profile on any mismatch, and expand one profile at a time after that.

### Hard rules
- **Legitimate work only.** Do not make dummy calls, inflate prompts, bust caches, or invent evaluations to spend quota.
- **Do not put an OAuth credential behind a proxy to spend it.** Hermes owns the lifecycle of its OAuth credentials, so
  route through Hermes. Do not build an outside router that spends an entitlement the provider does not document for it.
- **Do not copy example windows or sample headers into live state.** Use the live value, or record unknown.
- **Do not decrement a counter locally when the provider or Hermes can report it.** A local timer refill is not
  confirmation that a window reset.
- **Do not add a daemon, port or plugin before the native configuration has been tested.**
- **Do not deploy a shared file as a fleet router.** One file cannot prove the state of every profile.
- **Do not treat one 401 as a provider outage.** Check the credential, its refresh and its scope first.
- **No secrets in state, logs, diffs or chat.**

## Pitfalls
- **Invented quotas.** A window length or allowance without a source is deleted, not used.
- **Headers assigned to every endpoint.** Verify headers per endpoint.
- **One token factory assumed.** A creator, an agent product, an aggregator and a compute host each have their own
  entitlement owner. Classify them first.
- **Usage subtracted from an unverified allowance.** Record usage only.
- **Several windows reported as one percentage.** Split them and name the binding dimension.
- **A canary read as fleet completion.** One profile proves one profile.
- **Stale telemetry driving routing.** Refresh first.

## Verification
- The inventory classifies every route and names its credential kind without showing the credential.
- A header example computes a burn percentage only when the limit and the remaining amount share the same scope and window.
- A usage-only example reports usage and refuses to state a remaining amount.
- A route with an unknown capacity never wins an automatic decision.
- A compatible route with included capacity about to expire outranks paygo.
- No real work produces a recommendation of no spend.
- A canary shows the actual provider and model in the runtime, and a rollback restores the previous configuration.
- Nothing in the state, the logs or the recommendation contains a secret.

### Reference links
Re-verify each link before you rely on it.
- https://hermes-agent.nousresearch.com/docs/integrations/providers
- https://hermes-agent.nousresearch.com/docs/user-guide/features/fallback-providers
- https://hermes-agent.nousresearch.com/docs/user-guide/features/credential-pools/
- https://platform.openai.com/docs/guides/rate-limits/rate-limits-in-headers
- https://docs.anthropic.com/en/api/rate-limits
- https://console.groq.com/docs/rate-limits
