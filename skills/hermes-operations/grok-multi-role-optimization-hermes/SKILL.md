---
name: grok-multi-role-optimization-hermes
description: Use when setting up Hermes with several xAI Grok roles over OAuth. Covers role-to-model mapping, delegation limits, memory settings and profiles.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [grok, xai-oauth, multi-role, delegation, orchestration, hermes]
    category: hermes-operations
related_skills: [xai-grok-oauth, hermes-role-orchestration]
---

# Multi-Role Grok Setup for Hermes Agent

## Overview
Hermes can run one xAI Grok model for planning, a second for coding and a third for infrastructure work, all through
xAI OAuth. The main gains come from routing each role to the model that fits it, bounding delegation so sub-agents do
not run away, and sending cheap side tasks to cheaper models. This skill gives the role split, the config keys to set,
and the prompting pattern for each role. Model IDs and context limits change, so check them before you apply anything.

## When to Use
- You want one orchestrator agent that delegates coding and infrastructure work to specialists.
- You are running Grok models through the xAI OAuth provider and want role-specific routing.
- Sub-agents are running long or costing more than expected, and you need delegation limits.
- You are splitting one Hermes install into profiles for separate roles.

## Features
- Role-to-model mapping for an orchestrator, a dev specialist and a DevOps manager.
- Delegation settings: which model sub-agents use, how many run at once, how deep they can nest, and how long each may run.
- Memory and compression settings, including a reasoning model for summaries.
- Auxiliary routing that sends vision, summarization and compression tasks to cheaper models.
- Profile split for role isolation, with one config, memory, skill set and gateway per role.

## Benefits
- Each role runs on the model it is best suited to, instead of one model doing everything.
- Delegation depth and concurrency are capped, so cost stays predictable.
- Prompt caching and cheap auxiliary models lower the cost of long sessions.
- Profiles keep one role's memory and skills out of another role's context.

## Procedure
1. Pick the model IDs and context limits from the provider's current model list, and record them in the table below.
   Model IDs change, so check them before each setup.

   | Role | Model | Provider | Use for |
   |---|---|---|---|
   | Orchestrator | `<orchestrator-model>` | `xai-oauth` | Planning, delegation, synthesis |
   | Dev specialist | `<dev-model>` | `xai-oauth` | Coding, debugging, refactoring, tests |
   | DevOps manager | `<devops-model>` | `xai-oauth` | Infrastructure, CI/CD, monitoring, security review |

2. Set the orchestrator as the default model and the dev specialist as the delegation model:
   ```bash
   hermes config set model.provider xai-oauth
   hermes config set model.default <orchestrator-model>
   hermes config set delegation.provider xai-oauth
   hermes config set delegation.model <dev-model>
   hermes config set delegation.max_concurrent_children 4
   ```

3. Set the memory and compression values. Use the reasoning model for compression, because it preserves meaning better
   than a fast model:
   ```bash
   hermes config set memory.compression_threshold 0.75
   hermes config set memory.compression_model <devops-model>
   ```
   Leave headroom below the context limit. Compress at about 75 percent of it.

4. Route side tasks to cheaper models. A summarization task does not need the orchestrator:
   ```yaml
   auxiliary:
     summarization:
       provider: xai-oauth
       model: <fast-model>
     compression:
       provider: xai-oauth
       model: <devops-model>
   ```

5. Turn on prompt caching and the reasoning-effort setting the provider documents for the model family. Confirm the key
   names against the configuration reference first, because a misspelled key is silently ignored.

6. Create one skill per role, each with its model and a short role brief. Make a folder with a `SKILL.md` for each role
   under that profile's skills folder, and list the skills with `hermes -p <role> skills list`.

7. For full isolation, create one profile per role and give each its own config, memory, skills and gateway:
   ```bash
   hermes profile create <role>
   hermes -p <role> config show
   ```

8. When delegating, state the role and the model in the call, and give the sub-agent a complete task. Do not rely on
   the sub-agent to infer the role from context:
   ```python
   delegate_task(
       task="<complete task with acceptance criteria>",
       role="dev_specialist",
       model="<dev-model>",
   )
   ```

9. Verify the result with `hermes config show`, then send one request to each role and confirm that the reply came
   from the expected model.

## Pitfalls
- **Check model IDs before you rely on them.** Model names and context limits change between releases. A wrong ID fails
  at request time, not at config time.
- **Unbounded delegation multiplies cost.** Cap concurrent children and spawn depth, and set a child timeout.
- **Do not give the orchestrator the coding job.** It is the most expensive role. Route code work to the dev specialist.
- **Use the reasoning model for compression, not the fast one.** The summary is the only record of what the session
  decided.
- **Role prompts are not personas.** A line that says "you are a senior engineer with 15 years of experience" adds
  nothing. Give concrete rules instead: plan before coding, review before reporting, and ask for a confidence level
  and alternatives on a plan.
- **Profiles do not share memory.** If two roles need the same fact, write it into both, or into the shared notes the
  roles read.
- **Verify key names.** A config key that does not exist is ignored without an error, so the setting looks applied
  when it is not.

## Verification
- `hermes config show` lists the orchestrator as the default, the dev specialist as the delegation model, and the
  delegation limits you set.
- A test delegation returns from the dev specialist model, not the orchestrator.
- The compression setting applies when a long session crosses the threshold. Check the logs for the model name used.
- Each profile lists only its own skills and memory.

## Attribution
Adapted from a public guide credited to Grok (xAI). The role
split, configuration keys, delegation limits and prompt guidance were restated here, and the persona lines were removed.
The steps have not been run against a live install, so check every key and model ID before use.
Model reference: https://docs.x.ai/developers/models/.
