---
name: petdex
description: Use when a Hermes user wants an animated mascot. It can run in the terminal or on the desktop. Covers browsing, installing, selecting, sizing and diagnosing pets.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [petdex, mascot, display, cli, tui, desktop]
    category: hermes-operations
related_skills: [hermes-profiles, hermes-gateway-ops]
---

# Petdex Mascots

## Overview
A petdex is an animated mascot that reacts to agent activity, such as idle, running a tool, reviewing, error and done. It
appears in the terminal interface and in the desktop app. Pets come from a public gallery. Hermes installs them into the
active profile's own folder, and it stores the selection in the display settings. This skill covers finding a pet,
installing and selecting it, sizing it, and diagnosing why one does not show. It does not generate sprite art.

## When to Use
- A user asks for a mascot, or for "pets" in the terminal or the desktop app.
- A user wants to change, preview or turn off the active pet.
- A pet is installed but does not show, or renders as plain text.

## Features
- Gallery search with a substring filter.
- Install with an option that makes the pet active at once.
- Preview with a state cycle, so every animation can be seen.
- Size control that applies to every display surface.
- A diagnostic command that reports the resolved pet, the render mode and the effective mode.

## Benefits
- A pet is installed into the active profile, so other profiles are not changed.
- Size and enabled state are set through commands, and the settings are stored in the profile's config.
- A pet that does not show can be diagnosed from one report.

## Procedure
1. Find a pet by name, or list the gallery:
   ```bash
   hermes pets list <query>
   ```
   Note the slug of the pet you want.

2. Install it and make it active in one step:
   ```bash
   hermes pets install <slug> --select
   ```

3. Preview it. Press Ctrl+C to stop:
   ```bash
   hermes pets show
   hermes pets show <slug> --cycle
   ```

4. Confirm the setup:
   ```bash
   hermes pets doctor
   ```
   The report names the resolved pet, the configured render mode, the detected graphics protocol and the effective mode.

5. Adjust the size if needed. One factor applies to every surface, and the value is clamped between 0.1 and 3.0:
   ```bash
   hermes pets scale <factor>
   ```

6. To turn the pet off, or to remove it:
   ```bash
   hermes pets off
   hermes pets remove <slug>
   ```

Pets install into the active profile's folder. Selecting a pet writes the pet's slug and the enabled flag to the profile's
config, under the display settings.

## Pitfalls
- **A pet shows only when it is installed, selected and enabled.** Check all three with the diagnostic command.
- **Terminal rendering is off when there is no terminal.** Output that is piped or redirected has no screen to draw on.
- **Full-fidelity rendering needs a terminal with graphics support.** Other terminals fall back to a text-block rendering,
  which is selected automatically.
- **Use the profile's own install command.** A pet installed with another tool's installer lives in a different folder,
  and Hermes does not read it.

## Verification
- `hermes pets doctor` reports the pet as ready.
- `hermes pets show` animates the pet in the terminal.
- After a change of size, the pet's size matches the value that was set.

## Attribution
The pet gallery is the public petdex project, at https://github.com/crafter-station/petdex, with the gallery site at
https://petdex.dev.
