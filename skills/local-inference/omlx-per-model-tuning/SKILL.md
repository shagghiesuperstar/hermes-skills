---
name: omlx-per-model-tuning
description: Use when tuning, validating, promoting, or rolling back one model's settings in an oMLX server. Covers schema-first edits, read-back checks, promotion gates, and benchmarking.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [omlx, mlx, model-tuning, benchmarking, promotion, rollback]
    category: local-inference
related_skills: [omlx-model-management, mlx-inference, claude-code-local-stack]
---

# oMLX Per-Model Tuning and Lifecycle

## Overview
Per-model work on an oMLX server means changing one model's settings, proving the change took effect, and deciding whether the model is good enough to become a default or a routed model. The schema is the authority, not a guess: setting keys change between releases, an unknown key is silently ignored, and the server's model list is the only reliable name for a model. Every change follows the same cycle: back up, edit one thing, read back, restart only if required, run a real completion, benchmark against a baseline, then keep or revert.

## When to Use
- You are inventorying or tuning a specific model's context window, sampling, cache, or thinking settings.
- A model should become the default, a pinned helper, or a routed model for an agent.
- A setting change seems to have no effect, or a model disappeared from the list after a change.
- A model must be rolled back to an earlier configuration.

## Features
- Schema-first editing: confirm each key against the installed version's schema before writing it.
- Identity resolution that maps the runtime model ID to the key the settings file uses.
- Apply-semantics table showing which changes apply live and which need a reload or restart.
- A promotion gate covering cold and warm loads, memory headroom, tool calls, and the operating context window.
- A benchmark harness for OpenAI-compatible local servers, with the endpoint and tokenizer quirks spelled out.
- A failure-signature table that maps symptoms to a safe first response.

## Benefits
- Settings changes are verified after they are written, not assumed from the file's contents.
- A model is promoted only after it has passed the tests its intended job needs.
- Rollback restores an exact backup and then re-verifies real inference.
- Benchmark numbers are comparable because prompt length, output cap, and concurrency are fixed.

## Procedure
1. Record the baseline without changing anything:
   - the installed server version and its live model list,
   - the parsed per-model settings for the target model,
   - the global settings that the model inherits from,
   - the model's on-disk size, quantization, and available unified memory,
   - the startup log lines for discovery, cache restore, and load failures,
   - every client and scheduled job that routes to this model.
   Report a setting as persistent only after it survives the relevant restart or reload.
2. Resolve identity. Take the runtime ID from the live model list. Find the key the settings file uses for that model, which is the directory or canonical ID, not an alias. If the two differ, write the mapping down. Do not assume an alias resolves in the settings file.
3. Check the schema for the installed version before writing any key. Keys come from the server's own settings module or its admin API. An unknown key is ignored on load, so an ignored key looks like a successful edit.
4. Change one class of setting at a time, through the server's admin API when one exists, or through a structured edit of the settings file followed by a reload:
   ```zsh
   curl -s -X PUT "http://127.0.0.1:<port>/api/models/<runtime-model-id>/settings" \
     -H "Content-Type: application/json" \
     -d '{"max_context_window": 131072, "is_pinned": true}'
   ```
   Use a structured parser (for example a Python `json` edit) for file changes. Do not use `sed` or `awk` on JSON or plist files.
5. Back up before each write, read back the whole modified record, and confirm the target key exists exactly once.
6. Apply the change the way the schema requires:
   - Sampling, alias, thinking, pin, and default changes normally apply live through the admin API.
   - Engine-construction fields, such as the model type override, can unload and reload the model.
   - A raw edit to the per-model file needs a reload request or a process restart.
   - Global cache, memory, and scheduler settings need a full server restart, and they affect every model.
7. Confirm the startup or runtime log recognized the setting, then run one cold completion and one warm completion with the exact runtime ID.
8. Benchmark at a fixed prompt length, output cap, concurrency, and temperature. Compare with the baseline, then keep the change or revert it.
9. Promote only after every gate passes (see Promotion Gate).

### Promotion gate
A model can become pinned, default, or routed only after all of these pass:
- The runtime ID survives a restart and matches its settings record.
- One cold completion and one warm completion succeed.
- Memory headroom is measured at the intended context and concurrency.
- Tool calls return the expected structure, if the model's job includes tools.
- Long-context behavior is tested at the proposed operating window. The model card's maximum context is not evidence that the window works on your hardware.
- Any routing changes in clients are read back separately.

### Rollback
Restore the exact backup, reload or restart as the schema requires, and re-run a real completion. If a promoted default disappears from discovery, choose an explicit known-good default. Do not leave whichever model happens to be listed first as the default.

### Routing clients (after the server is healthy)
1. Register the exact served model ID in the client's model map.
2. Set the client's context length to the tested operating window, not the architecture maximum.
3. Add the model to a primary or fallback route only after an end-to-end request succeeds without fallback.
4. Verify the live session state separately from the static config, because a picker can show a stale selection.
5. Record the provider, model ID, endpoint, and rollback target in your change record. Keep credentials and host-specific addresses out of shared notes.

### Benchmarking an OpenAI-compatible local server
Use an evaluation harness that can target a local endpoint. Two endpoint styles matter:
- **Completion-style tasks** that score answer choices need the server to return token log-probabilities. Check that the server does. If it does not, do not fabricate log-probability values. Scores from fabricated values are meaningless. Use a generation-based task or a server that supports log-probabilities.
- **Chat-style tasks** need the endpoint that applies the chat template, and the base URL must end at that endpoint. A wrong suffix returns a validation error that names the missing field.

Other practical points:
- Pass the model name the harness needs for tokenizer mapping, if the harness requires one, and send string prompts when the server expects strings.
- The server's maximum prompt length can be lower than the window you configured. When a prompt is truncated on the left, confirm the configured window in the settings file before you trust the score.
- Before a benchmark, send one short completion. A model can be listed and still fail, and a crash during a long run wastes the run. Check the server's logs for parameter mismatches and crash reports.
- Prioritize instruction-following and code tasks for agents that run unattended. A knowledge score far below the reference for the same model family is a reason to re-check the quantization.
- Keep credentials in an environment variable, not in the command or the script.

## Pitfalls
- **Never invent a settings key.** A key from another server, a model card, or an old machine may not exist in this version. An ignored key looks like a working edit.
- **A file edit is not an applied setting.** Read the parsed record back, then reload or restart as the schema requires, then check the log.
- **Settings are keyed by the directory ID, not the alias.** A key that matches only the alias is ignored.
- **Mutually exclusive acceleration features do not combine.** Some pairs of speculative or cache features conflict. Enable one at a time and benchmark each.
- **Profiles cannot hold lifecycle state.** Pin, default, visibility, and alias belong to the model record, not to a reusable profile.
- **Version-gated workarounds are temporary.** A type override that one release needs can be unnecessary in the next. Verify the installed build and remove the override after a clean reload succeeds.
- **Do not promote on a card's claims.** Quality and speed claims from a converter or community card are experiments until your own benchmark confirms them.
- **Do not tune global memory or cache settings for one model** without checking the effect on every other model on the server.
- **A pin can cause boot pressure.** If a pinned model leaves too little headroom, the server evicts other models or fails to start. Unpin, measure, then retry.
- **Intake claims are pending until verified.** Size, speed, and quality figures from a publisher or the operator are inputs to validation, not results.

### Failure Signatures
| Symptom | Likely class | Safe first response |
|---|---|---|
| Model not found although files exist | ID or path mismatch | Trust the live model list; check startup log and the key mapping |
| Chosen default ignored | Default no longer discoverable | Set an explicit known-good default |
| Edit saved, behavior unchanged | Wrong settings surface, cached state, or unsupported key | Find the real persistence owner; read back; restart and check the log |
| Pin causes eviction or boot failure | Memory budget exceeds headroom | Unpin, measure cold and warm peaks, retry with less |
| Long context stalls or crashes | Architecture maximum exceeds local capacity | Reduce the tested operating window and re-test |
| Client falls back to another model | Routing map diverged from the runtime ID | Validate direct inference first, then the client's exact provider and model call |

## Verification
- The live model list contains the exact runtime ID, and the settings record for it has the intended values after a read-back.
- A cold completion and a warm completion both succeed with that ID.
- The benchmark table compares the candidate with the recorded baseline under identical settings.
- The rollback path is documented and was tested on a copy before the change went live.

## Attribution
- oMLX model server by jundot, including its per-model settings schema: https://github.com/jundot/omlx
