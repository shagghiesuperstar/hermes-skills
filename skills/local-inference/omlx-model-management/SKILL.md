---
name: omlx-model-management
description: Use when adding, converting, or recovering oMLX models. Registration runs on an oMLX server. Covers download, conversion, admin-API registration, sleep and wake recovery, and cache placement.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [mlx, omlx, mlx-lm, quantization, apple-silicon, huggingface, model-install]
    category: local-inference
related_skills: [omlx-per-model-tuning, mlx-inference, huggingface-download]
---

# oMLX Model Management

## Overview
oMLX serves MLX-format model folders from one server. It does not convert weights itself, so a model reaches the server through a download, a conversion with the MLX tooling, a sanity generation, and a registration step. After that, recovery is the other half of the job: the GUI app does not always come back after sleep, a stale size estimate can refuse a model that would fit, and the SSD prefix cache needs a volume the app can write to. This skill covers the full path, one step at a time, with a check between each.

## When to Use
- Adding a new MLX model to an oMLX server, from a Hugging Face repository.
- Registering a model that already sits in the models folder but is not listed.
- The server refuses a model with a memory error, or stops answering after sleep or a reboot.
- The SSD prefix cache is slow or fails to write.

## Features
- Download of only the safetensors and configuration files a conversion needs.
- Conversion to MLX format with explicit quantization, plus a sanity generation before any settings change.
- Registration through the admin API, with a fallback to a backed-up settings-file edit when the server is down.
- Verification through the server's own model list and a real completion.
- Recovery steps for sleep and wake, port checks, and the app's auto-start setting.
- Cache placement rules for an external APFS volume and the permissions it needs.

## Benefits
- Each step has an explicit gate, so a broken conversion never reaches the settings file.
- Registration does not disturb other models' tuning.
- A memory refusal caused by stale file counts is diagnosed, not worked around by lowering the memory guard.
- Recovery after sleep is a checklist, not a search through logs.

## Procedure
1. Download the weights you need and exclude everything else. The download tool treats a second `--exclude` argument as a filename, so repeat the flag once per pattern, and confirm the output does not warn that it is ignoring an argument:
   ```zsh
   hf download <repo> --exclude "<pattern-a>/*" --exclude "<pattern-b>/*" --exclude "*.gguf" \
     --local-dir <staging-dir>/<model-name>
   ```
   Set the token in the session for authenticated transfers. Unauthenticated downloads are several times slower.
2. Convert into the models folder under the name the server will show. Quantize to 8 bits when memory allows. Use 4 bits as the fallback under memory pressure:
   ```zsh
   mlx_lm.convert --hf-path <staging-dir>/<model-name> -q --q-bits 8 --q-group-size 64 \
     --mlx-path <models-dir>/<model-folder-name>
   ```
   Check the conversion's final line for the bits-per-weight report. Confirm the output size is roughly the quantized fraction of the source.
3. Run a sanity generation before touching any settings. It is a hard gate. Reasoning-style preamble in raw output is expected, because the server strips it through the settings:
   ```zsh
   mlx_lm.generate --model <models-dir>/<model-folder-name> --prompt "test" --max-tokens 20
   ```
4. Add the model's settings entry, keyed by the exact folder name. Back up the settings file first, edit it with a structured JSON load and dump, and read back the new entry:
   ```zsh
   cp <config-dir>/model_settings.json <config-dir>/model_settings.json.bak-$(date +%Y%m%d_%H%M%S)
   ```
   Tune the entry with the procedure in the `omlx-per-model-tuning` skill. Do not change any other model's entry when you add one.
5. Register the change. Prefer the admin API while the server is running, because it applies and persists the change without a restart. Log in once with the server's API key to get a session cookie, then call the model-settings endpoint for the target model. Use the model's ID as the server lists it, which can differ from the folder path:
   ```zsh
   curl -s -c <cookie-jar> -X POST http://127.0.0.1:<port>/admin/api/login \
     -H "Content-Type: application/json" -d '{"api_key": "<api-key-from-settings>", "remember": false}'
   curl -s -X PUT "http://127.0.0.1:<port>/admin/api/models/<model-id>/settings" \
     -H "Content-Type: application/json" -b <cookie-jar> \
     -d '{"max_context_window": 131072}'
   ```
   Edit the settings file directly only when the server is down. Editing the file while the server runs can be overwritten by the server's next save.
6. After changing model folders on disk (moving, quarantining, or adding shards), ask the server to rescan: a reload request re-reads the settings, rediscovers models, recomputes size estimates, and reloads pinned models.
7. Verify through the server. Confirm the alias appears in the model list with the API key, then send one chat completion and check for a clean answer with no reasoning tags and no repetition loop.

### Recovery
### After sleep, wake, or reboot
8. Check the port and the process before assuming the server is fine:
   ```zsh
   lsof -i :<port> | grep LISTEN
   curl -s --max-time 3 http://127.0.0.1:<port>/v1/models
   ```
9. If the port is closed, start the app and wait about 15 seconds before retesting. The GUI app may not restart itself after sleep, even with auto-start set. Turn on the app's own auto-start setting so reboots are covered.
10. Do not add a background job that relaunches the app on a timer. A timer that reopens the app every few seconds fights the user's own shutdowns and hides real failures. If sleep recovery must be automatic, use the app's own auto-start option, and check the port after every wake as a manual step.
11. Confirm the client configuration still names the model the server lists. A renamed or removed model returns "not found" until the client's name is updated.

### Memory refusals that do not match real pressure
12. A refusal saying the model does not fit under the dynamic memory ceiling can come from a stale size estimate. The estimate counts every safetensors file in the folder, including shard files that an earlier version left behind and the current index no longer references. Check which shard set the index's weight map references:
    ```zsh
    python3 -c "import json,sys; m=json.load(open(sys.argv[1]))['weight_map']; print(sorted(set(m.values())))" <models-dir>/<model-folder-name>/model.safetensors.index.json
    ```
13. Move unreferenced shard files out of the model folder into a quarantine folder. Do not delete them until the model has run for a while. Then reload, and confirm the estimated size dropped to the real figure before retrying. The memory guard's suggested fixes are misleading in this case, so do not lower the guard to get past it.
14. Use the disk size of a model folder only as a rough guide. Folders often hold extra formats, such as a second quantized set or GGUF files that the server ignores, so the real memory footprint can be much smaller than the folder size.

### Unpin before unload
15. A pinned model is reloaded by the preload path as soon as it is unloaded. To unload it, first set its pin to false through the settings endpoint, then unload it. Re-pin only if the model is still the one clients depend on.

### Multi-token prediction heads
16. Multi-token prediction needs the head weights inside the model's safetensors index. Some conversions drop those tensors silently. Count the prediction keys in the index before you enable the feature. If they are missing, convert from the full-precision weights that contain them, or stitch the head from its extra shard file into a shard name the loader reads, then reload and check the load log for an active prediction line.
17. Leave the feature off for models whose weights do not contain the head, and for models whose architecture the server does not support for it.

### Cache Placement
18. Put the SSD prefix cache on a local APFS volume that the server process can write to. Set the cache directory and its size limit in the global settings file.
19. Give the server's Python interpreter the file-access permission its operating system requires for external volumes. A cache write failure with no other error is often a permissions prompt that was never answered.
20. Restart the server after changing global cache or memory settings. Those settings apply to every model on the server.

## Pitfalls
- **Never guess a setting key.** Keys change between releases. Check the installed version's settings module or the admin API.
- **Overwriting a working model removes your rollback.** Give every variant its own folder and name.
- **Download is not load.** Start a conversion or a load only after every shard is present and the index and configuration files exist.
- **Use one heavy model per memory budget.** Loading a second large model can evict the first, and a client that expects the first will stall.
- **Do not steal another client's pinned model.** Choose a new model name and leave existing pins alone unless the operator asks for a change.
- **Verify the model list after every change.** A model that loads from disk can still be absent from the list if its settings key does not match its folder name.
- **Keep a reasoning-capable model's thinking setting explicit.** Leave it on only when the client can use the reasoning output, and set a thinking budget so short probes do not use the whole output allowance.
- **Concurrency gains flatten.** Raise the concurrent request limit in steps and measure aggregate throughput before going higher. More concurrency also increases contention for tool calls.
- **Keep the server on loopback.** Bind it to `127.0.0.1` and do not expose it through a public tunnel. Keep API key verification on.
- **Strip credentials from notes.** Keep API keys and cookie files out of shared documentation and command history.

## Verification
- The model appears in the server's model list under its alias, and a completion returns clean text.
- The settings file contains the new entry, and no other model's entry changed (compare with the backup).
- After a restart or wake, the port answers and the model list is complete.
- After a memory refusal fix, the estimated size matches the referenced shards, and the model loads.
- The cache directory on the external volume receives writes without a permissions error.

## Attribution
- oMLX model server by jundot: https://github.com/jundot/omlx
- MLX conversion tools (`mlx_lm.convert`, `mlx_lm.generate`) from the MLX language-model project by ml-explore.
