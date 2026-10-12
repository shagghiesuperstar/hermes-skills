---
name: mlx-inference
description: Use when running or tuning local MLX inference servers on a Mac. Covers safe config edits, restarts, per-model settings, side-by-side variants, and single-GPU sharing.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [mlx, omlx, inference, model-tuning, apple-silicon, vision]
    category: local-inference
related_skills: [omlx-model-management, omlx-per-model-tuning, darkbloom-provider]
---

# MLX Inference Servers and Model Tuning

## Overview
MLX servers on Apple Silicon serve several models from one unified-memory pool through an OpenAI-compatible API. Their settings live in plain JSON files that the server reads once at startup, so the common failures are about configuration: an edit that never takes effect, a launch command that silently rewrites the file and drops other models' tuning, a new variant that overwrites a working one, or two servers fighting over one GPU. This skill covers how to change that configuration safely and how to verify what the server is actually applying.

## When to Use
- You are adding, removing, or tuning models on a local MLX server.
- A change to the settings file seems to have no effect.
- A model that worked before returns empty output, memory errors, or leaked reasoning text.
- You are choosing between a speculative-decoding server and a model manager with per-model settings.
- Two MLX-based services are installed on the same machine.

## Features
- Settings split into server-wide, per-model, and read-only statistics files.
- A copy-edit-review-apply workflow for any change to a live server's configuration.
- Restart and verification steps that confirm the server applies the new settings.
- A side-by-side pattern for trying a new model variant without risking the working one.
- Memory-guard tiers mapped to model size and workload.
- Guidance for vision models, thinking-capable models, and tool-calling clients.

## Benefits
- Per-model tuning survives later changes, because the server never rewrites the file from a launch command.
- Every change has a backup and a recorded review.
- A new variant can be rolled back by changing one name.
- Problems are traced to the file, the restart, or the GPU, instead of guessed.

## Procedure
### Choose the server
1. Use a speculative-decoding server when throughput on a single model matters most and the model supports multi-token prediction.
2. Use a model manager when you run several models with per-model settings, pinned helpers, and a separate vision profile.
3. Keep a separate environment for each server, so their Python packages do not conflict.

### Edit configuration safely
4. Find the configuration directory. Writing to a similar-looking directory has no effect. Confirm which directory the running server reads by checking its startup log.
5. Back up both the server settings file and the per-model file before any change:
   ```zsh
   cp <config-dir>/model_settings.json <config-dir>/model_settings.json.bak-$(date +%Y%m%d_%H%M%S)
   ```
6. Never start the server with explicit model arguments on a system that already has per-model settings. The server prunes its settings file to the models named on the command line and writes the trimmed file back, which deletes every other model's tuning. The only safe use of those arguments is a fresh install with an empty settings file.
7. Edit a copy, not the live file. Show the change to a person for review, and apply it to the live file only after approval:
   ```zsh
   cp <config-dir>/model_settings.json <config-dir>/model_settings_copy.json
   ```
8. Use the short model name as the key. Server APIs usually expose the short name, even when the model lives in a nested folder.

### Restart and verify
9. The server reads its settings once at startup. A change has no effect until you restart:
   ```zsh
   pkill -f "<server-process-pattern>"; sleep 2
   <server-start-command-without-model-arguments> &
   sleep 20
   curl -s http://127.0.0.1:<port>/v1/models
   ```
10. Confirm the server applies the settings, not just that it started. Models listed in the API response with a matching settings entry have their tuning applied. An entry with no matching model directory is ignored at startup, so compare the two lists.

### Set the memory guard
11. Pick a memory-guard tier from the workload. The aggressive tier rejects prompts early and suits a very large model on a single machine. The balanced tier is the default. The relaxed tier suits many small models loaded together. If small models get memory-guard errors, move one tier down or raise the guard's ceiling, then restart.

### Add a variant side by side
12. Link or copy the new variant into the model directory under a new, distinct name. Never overwrite an existing model's weights under the old name.
13. Duplicate the working model's settings block under the new name, and change only the variant-specific flags. Keep the working model as the default and pinned until the new one proves itself.
14. Add the new name to every client's model list that uses this endpoint.
15. Restart, confirm the name appears in the model list, and run a real completion against it. Roll back by switching the default back to the working model.

### Tune for thinking and tool calls
16. For a model whose chat template emits reasoning, turn off reasoning passthrough for tool-calling clients, and set the reasoning parser to the exact name the server documents. An unrecognized parser name can silently disable parsing and leave reasoning text in the content field.

### Share the GPU
17. Run one MLX inference process per machine when throughput matters. Two servers loading at once can starve each other or fail on memory. Stop the servers you do not need before starting another one.

## Pitfalls
- **Model arguments rewrite the settings file.** A launch command with explicit model flags on an existing system deletes the tuning of every model not named. Restore from a backup if it happens, then restart without those flags.
- **A settings edit without a restart does nothing.** The server keeps the old values in memory until it restarts. Test only after the restart.
- **Config entries without a matching directory are ignored.** A tidy-looking settings file can apply to fewer models than you think. Compare the server's model list with the settings file.
- **Do not hot-swap weights.** Replacing a model's files under the same name removes your rollback. Use a distinct name for every variant.
- **Reasoning text can leak into content.** Clients that expect a clean tool-call payload then receive garbled output or an end-of-sequence token. Fix it with the server's reasoning settings, not in the client.
- **Upgrades can regenerate the API key.** After an upgrade, an older key may return 401. Read the new key from the server's settings, update the clients, and keep key verification on, even for localhost.
- **Check the model directory after an upgrade or restart.** A restart can fall back to an empty default directory and discover zero models. Confirm the configured directories still point at your model storage.
- **Use the exact directory spelling the server is configured with.** A path that differs only in letter case can be treated as a different location on some volumes.
- **Keep three things separate in your notes.** Discovered, registered, and served are different states. A model can be registered and still fail its first completion.
- **Treat any third-party provider as the GPU's sole owner while it runs.** Its startup check can pick up unrelated cached models and report the wrong one, so pin the exact model it should serve.
- **Thermal tools change fan behavior.** Third-party fan-control tools and sustained high-performance profiles raise noise and wear. Use them only with the operator's agreement.

## Verification
- The settings file parses, the backup from before the change exists, and the change is present in the live file.
- After the restart, the model list contains the expected names, and each one has a settings entry that the server applied.
- A short completion against each changed model returns text, and a tool-call test returns clean structured output when the model is used for tools.
- Only one inference server is loaded on the GPU during a benchmark run.

## Attribution
- oMLX model server by jundot.
- MLX array framework by ml-explore.
