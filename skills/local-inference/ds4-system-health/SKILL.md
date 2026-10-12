---
name: ds4-system-health
description: Use when operating the DS4 inference server on macOS. It serves DeepSeek models. Covers launchd setup, health checks, safe restarts, model switches, and multi-Mac engine updates.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [ds4, deepseek, launchd, metal, apple-silicon, model-management]
    category: local-inference
related_skills: [ds4-local-coding-workbench, local-model-deployment, mlx-inference]
---

# DS4 Server Health and Operations

## Overview
DS4 is a narrow inference engine for DeepSeek V4 GGUF models on Apple Silicon. It serves an OpenAI-compatible API on one port and keeps its model and Metal shaders resident in unified memory. Under launchd it fails in ways a plain process does not: macOS privacy controls block reads from external volumes, a supervisor respawns the server after a kill, a stale lock file blocks the next start, and a second server competing for the port fails silently. This skill covers the health checks, the restart order that avoids those traps, the model-switch sequence, and an engine update across several Macs.

## When to Use
- The DS4 server is down, returns no models, or answers with the wrong model.
- You need to restart the server, switch GGUF variants, or rebuild the engine from source.
- A remote Mac running DS4 is unreachable or its agents report that the primary model failed.
- You are rolling a new engine build out to several machines.

## Features
- Health checks for the process, the listening port, the served model id, and upstream currency.
- A launchd configuration that loads the correct engine flags, the Metal shader environment, and the MTP draft model.
- A restart sequence that disables the supervisor first, clears the lock file, and waits for the model to load.
- A model-switch workflow covering symlink, cache clearing, and disk checks.
- A staged, verified cluster update across build and peer machines.
- A remote diagnosis checklist for hosts you reach over SSH.

## Benefits
- Restarts stop producing silent failures, such as a second server losing the port or a stale lock blocking the start.
- Model swaps avoid corrupted answers from a cache built for another variant.
- Cluster updates keep memory from spiking on several machines at once.
- Problems are diagnosed from measured process and port state, not from a remembered plist.

## Procedure
### Health checks
1. Confirm what is running, what owns the port, and what the server reports:
   ```zsh
   pgrep -af ds4-server
   lsof -i :<engine-port> -P -n | grep LISTEN
   curl -s http://127.0.0.1:<engine-port>/v1/models
   ```
   A port being open does not mean the model is loaded. Use the `/v1/models` response as the readiness test.
2. Check upstream currency from the engine source checkout:
   ```zsh
   cd <engine-src> && git fetch origin
   echo "behind: $(git rev-list HEAD..origin/main --count)"
   ls -la <engine-deploy-dir>/ds4-server
   ```
   A binary older than the latest commits you need means a rebuild.
3. Audit every launch agent that points at the engine before you load another one. Only one instance can own the port, and the others show a PID that is not serving:
   ```zsh
   ls ~/Library/LaunchAgents/*.plist | xargs grep -l ds4-server
   ps -o pid,args -p $(pgrep -f ds4-server | head -1)
   ```
   The arguments of the running process are the truth, not the plist on disk.

### Restart safely
4. For a planned restart, stop the supervisor before killing the server, because a keep-alive agent or a managing parent relaunches the process within about a second:
   ```zsh
   launchctl bootout gui/$(id -u)/<engine-label> 2>/dev/null || true
   ```
   If an agent gateway supervises the engine, switch that gateway to a fallback model first, or stop the gateway.
5. Kill the process and clear the lock file it leaves behind:
   ```zsh
   pkill -9 -f ds4-server; sleep 3
   rm -f /tmp/ds4.lock
   pgrep -af "ds4-server|launcher" || echo "clean"
   ```
6. Start the server with explicit flags and a working directory where its relative shader paths resolve:
   ```zsh
   cd <engine-deploy-dir>
   ./ds4-server -m <model-link>.gguf --ctx 131072 --host 127.0.0.1 --port <engine-port> \
     --kv-disk-dir <kv-cache-dir> --kv-disk-space-mb 51200 \
     --kv-cache-continued-interval-tokens 2048 --mtp <mtp-draft>.gguf
   ```
   Give the port explicitly. Without it the server can default to the same port as another local server.
7. Allow about 30 seconds for the model to load, then poll `/v1/models` until it answers:
   ```zsh
   for i in $(seq 1 20); do curl -sf http://127.0.0.1:<engine-port>/v1/models && break; sleep 3; done
   ```
8. Re-enable the supervisor only after the manual start works, or keep it disabled and run the server from a logged-in terminal or a background job.

### Launchd configuration
9. Keep the binary, the model file, and the Metal shader directory on the internal disk. Launchd-spawned processes cannot read from external or network volumes under macOS privacy rules, and the symptom is a process that hangs inside its first file open with no error output. The KV cache may stay on an external volume because it is memory-mapped.
10. Set every `DS4_METAL_*_SOURCE` variable the engine reads in the launch agent. Search the engine source for the pattern `DS4_METAL_.*_SOURCE` to list them. A missing variable fails at startup with `Metal source X not found`.
11. Do not put `--imatrix` on the command line. Calibration data is baked into the GGUF at conversion time. To use the calibrated variant, point `-m` at that file.

### Switch models
12. Follow this order. Skipping a step produces corrupted completions or a failed start:
    1. Stop the server.
    2. Download the new variant, and confirm the download has finished (no `.incomplete` files).
    3. Point the model symlink at the new file, and confirm with `readlink`.
    4. Delete the KV cache files. Cache entries from one calibration are incompatible with another.
    5. With the operator's approval, delete the old model. Do this only after the symlink is verified and after you check that no other tool still opens the file.
    6. Check free disk space.
    7. Start the server and run the readiness test.

### Update the engine across several machines
13. Run a pre-flight health check on every machine before touching it. Proceed only when free memory is comfortable, swap-out rate is low, and no stuck processes are present. Postpone a machine that is swapping heavily; restarting the engine there can push it into an out-of-memory crash.
14. Get explicit go-ahead from the operator, and move every agent that depends on the engine to a fallback model before the rollout.
15. Disable the supervisor and kill the server on each machine, then clear the lock file.
16. Build once on the build host from a reviewed tag or commit, and record the commit SHA. Then distribute the binaries and the Metal shader directory to the peers, and compare each peer's binary hash with the build host's `shasum -a 256` output:
    ```zsh
    cd <engine-src> && git fetch --tags && git checkout <reviewed-tag-or-sha> && git rev-parse HEAD && make clean && make -j4 && make ds4-agent
    scp <engine-src>/ds4-server <engine-src>/ds4-agent <peer>:<engine-deploy-dir>/
    rsync -av <engine-src>/metal/ <peer>:<engine-deploy-dir>/metal/
    ```
    Sync the shaders before the binary swap, because the engine reads them at runtime.
17. Confirm the model files exist before creating or changing any symlink. A link to a missing file starts a server that crashes at load.
18. Restart one machine at a time, about 30 seconds apart, and run the readiness test on each before starting the next.
19. Move the agents back to the engine, and confirm each machine answers on `/v1/models` with the expected id.

### Remote diagnosis
20. Ping the host first. If ping works but SSH times out, the host is alive and its SSH daemon is starved, so retrying SSH will not help. If ping fails, the host is offline or has panicked. Use an alternate access path only if you have one configured.
21. When SSH works, collect the running processes, launch agents, cron entries, and the port owner in one command, then fix the lock file and the agent in that order.

## Pitfalls
- **Stale lock file blocks every restart.** A killed server leaves its lock file behind, and the next start fails with `cannot open model` or exits silently. Remove the lock before each start.
- **Planned restarts need the supervisor stopped first.** A keep-alive agent or a supervising gateway relaunches the engine within a second, so stop it before killing the process.
- **Two plists for one binary.** Several agent files can load the engine with different flags. Only one wins the port, and the others look healthy in the launch list. Keep the single correct agent and unload or delete the rest.
- **Omitting the port flag causes a silent collision.** A missing `--port` makes the engine default to the port another local server uses, and one of them silently loses it.
- **Bind wide only on a private network.** Binding to all interfaces makes the engine reachable from the LAN and the private network. Use loopback unless another machine needs it, and never expose the port publicly.
- **Port open is not model ready.** Model loading takes a short period after start, about 30 seconds for a large model. Poll `/v1/models` until it answers.
- **Activity Monitor memory is misleading.** The launch-agent report can show a tiny resident size while the Metal mapping holds tens of gigabytes. Judge memory with `vm_stat` and `memory_pressure`.
- **Overcommitted memory kills the machine.** Several large model directories loaded at once can exceed physical memory, and the server then fails every request. Keep only the models you use loaded, and keep a healthy margin of free memory for the engine's working set.
- **A long-running worker can exhaust swap.** A sustained worker process on the same machine can drive swap to its limit and force a reboot. Check the top CPU consumers during health checks.
- **Stale binaries and backups are inert.** Files named with old suffixes are not running. Confirm that with `pgrep` before deleting them.
- **A phantom model returns empty answers.** If the configured model id does not match what the server lists in `/v1/models`, some servers return empty completions instead of an error. Compare the two before debugging anything else.
- **Context limits belong at the provider level.** If a client rejects a small context window, set the context length in the provider's config. Adding an unrelated minimum key does not help.
- **Thinking and token budgets.** Long reasoning output consumes the output budget before the answer. Set reasoning output to the minimum your client needs.
- **Hugging Face metadata is partial.** Per-file timestamps are often empty. Use the file-tree endpoint for sizes, and rely on the repository's card timestamp for recency.
- **Multi-token prediction is experimental.** The draft model is passed with `--mtp`, is not persisted across restarts, and is best suited to greedy decoding.
- **Strict shell flags hide errors in keep-alive scripts.** The script exits on the first failed command, the agent restarts it, and the loop repeats with no useful log. Test the script with `bash -x` to find the failing line.
- **Dashboards show dashes when the health endpoint is missing.** A telemetry dashboard that reads a health route shows empty metrics when the engine build does not expose it. Check the route before blaming the dashboard.

## Verification
- `/v1/models` on the engine's port returns the expected model id, and a short chat completion returns text.
- `pgrep -af ds4-server` shows exactly one process, and its arguments match the intended flags.
- `lsof` shows that one process owns the engine's port.
- `ls` shows the binary, the shader directory with 19 shader files, and a model symlink that resolves to a real file.
- After a switch or update, the KV cache directory holds no files from the previous variant.

## Attribution
- DS4 inference engine by antirez: https://github.com/antirez/ds4
