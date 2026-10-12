---
name: free-sota-moa
description: Use when setting up a free-tier mixture-of-agents preset. Draws on free-tier model providers through a local OpenAI-compatible router. Covers install, live model discovery, and preset setup.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [mixture-of-agents, llm-routing, free-tier, router, model-discovery]
    category: agent-orchestration
related_skills: [hermes-role-orchestration, claude-cli-model-switching, harness-task-prompting]
---

# Free-Tier Mixture-of-Agents Preset

## Overview
A mixture-of-agents (MoA) preset sends one task to several reference models, which answer in an advisory role without tool access, and then to one aggregator model, which has the full tool set and writes the real response. Diversity of model family among the references drives most of the quality gain, not the raw number of references. This skill sets up such a preset on top of a local, self-hosted router that fans requests out to several free-tier providers. It discovers models from the router's live catalog instead of hard-coding names, and it stays within each provider's free-tier limits and terms of service.

## When to Use
- You want a MoA preset built from free-tier providers, behind a router on your own machine or private network.
- You need to refresh the preset after the router's model catalog changes.
- You are replicating the setup on another machine.

Do not use this for a routine single-model task, or where a paid, dedicated model is already available. The output quality is bounded by what the free tiers offer at the time.

## Features
- A local router that exposes one OpenAI-compatible endpoint over several provider keys.
- Live model discovery from the router's catalog, with a fallback when the catalog has no ranking metadata.
- Reference selection rules that pick from distinct provider families.
- A preset definition with separate reference and aggregator settings, registered as a provider in the agent platform.
- A request-log check that proves each MoA turn reached the router as one call per model.

## Benefits
- The preset tracks the current catalog, so a retired model does not stay in the configuration.
- Keys stay out of shell history, command output, and tracked files.
- A preset built from distinct families avoids the single-family failure mode.
- The router's request log confirms the fan-out, so a silent failure is visible.
- Free-tier limits are respected, so the setup does not depend on quotas being exceeded.

## Procedure
1. Check the prerequisites on the machine: a current LTS release of Node.js, Python 3.10 or later, and the agent platform.
   ```bash
   node --version
   npm --version
   python3 --version
   ```
2. Install the router from its public repository, and copy its example environment file. Generate its encryption key without printing it, and store that key in a secrets manager at once. A lost key makes the stored provider keys unreadable.
   ```bash
   git clone "<router-repo-url>" && cd "<router-dir>"
   cp .env.example .env
   npm install
   npm run dev
   ```
   Bind the router to the loopback address, or to a private network only. Never expose its port to the public internet. For a long-running host, use a process manager or a system service.
3. In the router's dashboard, add provider keys from at least three provider families. Family diversity matters more than the number of keys. Wait for the catalog to sync before you continue.
4. Copy the router's unified key into the agent's environment file without echoing it. The FreeLLMAPI router names this key `FREELLMAPI_UNIFIED_KEY`, and the commands below use that name. Restrict the file's permissions.
   ```bash
   umask 077
   printf 'Paste the unified key (input hidden): '
   read -rs KEY; echo
   printf '\nFREELLMAPI_UNIFIED_KEY=%s\n' "$KEY" >> "<agent-env-file>"
   chmod 600 "<agent-env-file>"
   unset KEY
   ```
5. Query the live catalog. Filter out non-chat models, such as embedding, speech, image, and moderation models. Sort by any ranking field the response provides. If the response has no ranking field, sort by identifier and rank by hand in the dashboard.
   ```bash
   set -a; . "<agent-env-file>"; set +a
   curl -s -H "Authorization: Bearer $FREELLMAPI_UNIFIED_KEY" "http://127.0.0.1:<port>/v1/models"
   ```
6. Choose the members of the preset from the list:
   - The aggregator is the highest-ranked chat model overall.
   - Each reference is the highest-ranked model from a provider family that no other member uses. Use three families where you can, and treat a list where every top model is from one family as a reason to override.
   Copy each identifier exactly.
7. Register the router as a custom provider in the agent platform, using its setup wizard, so the platform stores the key correctly. Check the connection with the platform's diagnostic command.
8. Define the preset. Give each reference model a moderate temperature, give the aggregator a lower one, and set a token ceiling. Use the platform's configuration command, or add the block to the configuration once. If the preset block already exists, merge into it.
   ```yaml
   moa:
     default_preset: "<preset-name>"
     presets:
       "<preset-name>":
         reference_models:
           - provider: custom
             model: "<reference-model-id-one>"
           - provider: custom
             model: "<reference-model-id-two>"
         aggregator:
           provider: custom
           model: "<aggregator-model-id>"
         reference_temperature: 0.7
         aggregator_temperature: 0.3
         max_tokens: 4096
         enabled: true
   ```
9. Verify the preset is listed, then run one short test call through it. Open the router's request log and confirm one entry per reference plus one for the aggregator, clustered by time.
10. Use the preset for the whole session, or for a single turn. Use a single fast model for latency-sensitive work.

### Refresh
Re-run the discovery step when the catalog changes, when a new provider is added, or once a month. If a reference fails repeatedly, check the request log and move that slot to the next model in the same family. If a provider's daily allowance runs out, remove its models from the references until it resets.

## Pitfalls
- **Keep the router off the public internet.** It holds upstream provider keys, so a reachable port exposes all of them. If the port is exposed, stop the router, bind it to loopback, and rotate every key it held.
- **Never write a key into a tracked file or into shell history.** Read keys with hidden input and write them straight to a restricted environment file.
- **A model identifier can be renamed without notice.** A missing identifier means the catalog changed. Re-run discovery and update the preset.
- **Reference failures are normal when a quota runs out.** The router reroutes, and the platform logs the failure. Treat a pattern of failures as a reason to rotate that slot, not as a bug in the preset.
- **A preset from one provider family gains little.** Three references from the same family agree with each other, so the diversity that drives the quality gain is lost.
- **A council adds latency.** References run before the aggregator, so use the aggregator model directly for latency-sensitive work.
- **Never set the aggregator to another preset.** Recursive presets are blocked by design.
- **Stay within each provider's free-tier limits and terms of service.** Do not create extra accounts or rotate keys to get around a quota. Rotating a model out of the references while its quota is spent is the correct response.
- **Do not describe the output as frontier-quality.** The output is the best of the free-tier pool available at that time, and it can change with the catalog.

## Verification
- The router answers `/v1/models` with the expected chat models, and the agent platform's diagnostic command reports the custom provider as healthy.
- The preset appears in the platform's preset list.
- One test call through the preset completes.
- The router's request log shows one entry per reference and one for the aggregator, and the aggregator entry matches the configured identifier.
- The router's port is bound to a loopback or private address, which a socket listing confirms.

## Attribution
- FreeLLMAPI, the self-hosted router: https://github.com/tashfeenahmed/freellmapi (by Tashfeen Ahmed and contributors)
- The mixture-of-agents method: Junlin Wang, Jue Wang, Ben Athiwaratkun, Ce Zhang, and James Zou, arXiv:2406.04692, https://arxiv.org/abs/2406.04692
