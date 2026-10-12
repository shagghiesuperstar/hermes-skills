---
name: hermes-profiles
description: Use when creating a Hermes profile or copying its skills and MCP servers. Covers fresh creation, selective skill copies, per-profile wiring and kanban pins.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, profiles, skills, mcp, kanban, roster]
    category: hermes-operations
related_skills: [hermes-profile-config-yaml-debug]
---

# Hermes Profiles

## Overview
A profile is an isolated Hermes home with its own config, persona, memory, skills and MCP servers. Build each specialist
profile fresh, rather than cloning a busy one, because a clone brings along every skill and no allowlist exists to trim
it. Most profile problems come from assuming that something installed in one profile appears in another. Skills, MCP
servers, plugins and config do not propagate. This skill covers creating a profile, giving it an identity and a model,
copying only what it needs, and keeping the default profile safe while other sessions use it.

## When to Use
- You need a new worker or specialist profile for a kanban lane or a bot.
- A worker fails because a skill or MCP server it needs is missing from its profile.
- You are about to install a skill pack or a hub package and need to decide which profile receives it.
- A cron job or a model change in one profile appears to affect another profile.

## Features
- Fresh profile creation with a description that doubles as routing text for the kanban decomposer.
- Identity check that refuses a profile with only the stock persona.
- Skill diff between the default profile and a new profile, with a selective copy.
- Per-profile MCP and plugin wiring.
- Skill-pin check before a kanban card names a skill.

## Benefits
- Each worker carries only the skills it uses, so the index stays small.
- Workers do not get a gateway they do not need.
- A profile cannot route work to a model it has no key for, because the model is pinned in the same step as creation.
- A default profile that another session owns is left alone.

## Procedure
1. Create the profile fresh. Give the description as a capability statement, not as documentation text:
   ```bash
   hermes profile create <slug> --description "<capability the lane needs>"
   ```
   Use `--no-skills` when the profile should start with bundled skills only.

2. Avoid slugs that collide with system commands. A slug such as a short two-letter command name can create a profile
   but fail to create its alias. Prefer a longer slug, or invoke the profile with the profile flag.

3. Write the profile's identity. A profile whose persona file still holds the stock text has no identity yet. Write the
   persona before you assign any work to it.

4. Pin the model and provider in the same step as creation, so the profile never starts on an unset model:
   ```bash
   hermes -p <slug> config set model.provider <exact-provider-id>
   hermes -p <slug> config set model.default <exact-model-id>
   hermes -p <slug> config get model.default
   ```

5. Diff the skills against the default profile, then copy only the ones this profile needs:
   ```bash
   hermes skills list
   hermes -p <slug> skills list
   ```
   For each needed skill, copy its folder into the profile's skills folder with a Python copy that keeps the skill file
   and its support files. Do not copy a whole skill pack "to be safe". Every installed skill adds to the index, and
   every MCP tool is injected on every turn.

6. Install packages on the default profile, then copy the result. A skill or MCP install run inside a worker's own session
   writes to that worker's profile, not to the default profile. Install once from the default profile, and copy to the
   profiles that need it.

7. Wire MCP servers per profile. The MCP add command writes only the active profile:
   ```bash
   hermes -p <slug> mcp add <name> ...
   hermes -p <slug> mcp list
   ```
   Repeat the command for each worker that should see the tools. Enable a plugin per profile in the same way.

8. Before a kanban card names skills, check that each named skill exists on the assigned profile:
   ```bash
   hermes -p <assignee> skills list
   ```
   A missing name makes the worker fail at spawn. When a skill is absent from the lane, put the skill's instructions in
   the card body instead of pinning the name.

## Pitfalls
- **The default profile is the home directory itself**, not a folder under the profiles directory. A tool that expects a
  profile folder for the default profile fails. Treat the Hermes home as the default profile's root.
- **Workers do not run a gateway.** The kanban dispatcher runs inside the default gateway and starts a worker with a
  one-shot chat command for its profile. Do not start a gateway for a worker profile unless it is a messaging bot.
- **Do not mutate the default profile while another session owns it.** A running session may depend on its persona,
  platform toolsets and MCP servers. Do not restart the gateway, replace the persona file, or rewrite its MCP servers
  until the owner has agreed.
- **A model change in the desktop picker writes the global config.** It is not scoped to the chat. Read the file after a
  switch, and pin scheduled jobs to an explicit provider and model. A job with no pin can be skipped when the provider
  changes.
- **Use the profile flag or the config command for every change.** Hand edits to structured files break indentation
  without any error. Changes made through the CLI are scoped to the profile named.
- **Verify the board before a smoke test.** A board list command shows which board is current, and a card can land on
  a board you did not intend. Pass the board explicitly.
- **A scheduled job posting into a shared chat is not proof that it runs here.** Two machines that share a bot token and a
  chat can both post. Before you treat a job's output as yours, check that its job identifier appears in this machine's
  job list. If it does not, the job runs on another host, and the change belongs there.
- **Node names are not profile names.** Machine names on a private network and profile slugs on one machine are different
  things. Listing this machine's profiles does not inventory another machine. If a machine is not reachable on the
  network, its persona is out of reach, so do not compare it with a local profile that shares a nickname.
- **Auto-detecting installers can rewrite the global config.** Run third-party installers with their option that skips
  config changes, then wire Hermes yourself.
- **A community plugin that scans as dangerous stays blocked.** Forcing the install past that verdict is not a fix.
- **Workers on case-insensitive file systems can collide with bundled skills.** A local skill whose name differs only by
  letter case from a bundled one overwrites it on macOS. Copy the local skill under a separate folder name.

## Verification
- `hermes -p <slug> config get model.default` returns the pinned model, and the provider matches the registry.
- The profile's skill list contains every skill its cards name, and its MCP list shows only the servers it needs.
- A test card assigned to the profile starts, and the worker's first turn shows the intended model in the agent log.
- The default profile's persona file, platform toolsets and MCP list are unchanged after the work.
