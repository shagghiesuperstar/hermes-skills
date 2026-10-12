---
name: exo-cluster
description: Use when building a distributed MLX inference cluster across two or more Apple Silicon Macs. Covers install, direct-link networking, storage, model placement, and recovery.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [exo, mlx, distributed-inference, apple-silicon, macos, cluster]
    category: local-inference
related_skills: [mlx-inference, omlx-model-management, multi-mac-fleet-ops]
---

# EXO Distributed Inference Cluster on macOS

## Overview
EXO shards one large model across several Apple Silicon Macs and serves it through an OpenAI-compatible API. Nodes discover each other over the local network, and a direct Thunderbolt link lets them talk fast. Most failures come from the surrounding system rather than from EXO itself: a direct link that loses its static address after a reboot, a model directory that is not mounted, two installs with different home folders, or a network daemon from the installer that rewrites the configuration every 30 minutes.

## When to Use
- You want one model too large for a single Mac to run across two or more Macs.
- Nodes show zero peers, or a model placement fails with a memory error even though the total memory looks sufficient.
- EXO fails to start after a macOS update, a reboot, or a reinstall.
- You need to choose between the packaged app and a source install, or to verify which copy of EXO is actually running.

## Features
- A repeatable install path that uses the packaged macOS app for current versions, with a source-install fallback for older ones.
- Static addressing for a direct link, configured so it survives reboots.
- Storage and port checks that stop silent fallbacks.
- Model download and registration through the cluster API, with partial-download tracking.
- Client configuration for any OpenAI-compatible tool.
- A recovery order for node restarts and a list of upstream issues to watch.

## Benefits
- Large models run across the combined memory of several machines instead of needing one expensive machine.
- Silent failures become visible checks: a missing model directory, a port collision, or a stale launch agent.
- Reboots no longer silently break a working cluster.
- Model downloads can be verified against expected sizes instead of trusted from estimates.

## Procedure
### Install on each node
1. Prefer the packaged macOS app from the official releases page. Copy it to `/Applications` and confirm the version from the bundle's `Info.plist`. The binary sits at `Contents/Resources/exo/exo` inside the bundle; use that path in launch agents.
2. For a source install, use Python 3.13 or later in a virtual environment, and build the dashboard first. Without the built dashboard, startup fails with `Unable to locate dashboard assets`:
   ```zsh
   cd <exo-src>/dashboard && npm install && npm run build
   <python3.13> -m venv <exo-venv>
   <exo-venv>/bin/python -m pip install -e <exo-src>
   ```
   Keep the clone in a persistent directory. Anything under `/tmp` is cleared on reboot.
3. Do not install the package named `exo` from the public package index. It is an unrelated tool. The EXO inference package is available only from the project's repository or its app release.
4. Verify the install on every node, and again after every operating-system update. Major macOS updates have removed a Python site-packages directory while leaving pip's metadata in place:
   ```zsh
   <python3.13> -c "import exo; print('ok')"
   ```

### Configure storage and ports
5. Set the models directory explicitly in the app preferences or the config file, and confirm the path exists on that node before you start. If a configured path is missing, EXO silently falls back to its default location and starts downloading there. This can silently start a duplicate download of tens of gigabytes.
6. Give every node its own API port and its own peer-to-peer port. Two nodes sharing a port enter a crash loop. Use free ports on loopback for the API.
7. Keep each node's EXO home directory in the user's space, not under a root-owned path. Migrate old root-owned data by copying the node identity and model cards. After the copy is verified and the operator approves, delete the old directory.

### Connect the nodes over a direct link
8. List the network services first. The service names differ by machine and by version, and a bridge service that exists on one Mac may not on another:
   ```zsh
   networksetup -listallnetworkservices
   ```
9. With the operator's approval, assign a static address on each node with `networksetup -setmanual`, using a /24 on a private range that is not your LAN. Verify each side with `ping`. Round trips on a Thunderbolt link should be sub-millisecond. Use `networksetup` rather than `ifconfig`, because `ifconfig` changes do not survive a reboot.
10. Make the address survive reboots. Macs can drop a manually disabled bridge or revert to DHCP after a boot. A small system launch daemon that reapplies the setting at boot is one option.
11. Check for installer-provided network daemons. One installer added a system daemon that destroyed the bridge and switched the network location every 30 minutes. Find these with `ls /Library/LaunchDaemons | grep -i <vendor>`, read the script each one runs. Show the operator each daemon and its script, and unload a daemon only after the operator approves it. Then configure the link by hand.
12. Expect the peer-to-peer link to need a restart of EXO on both nodes after any address change. Wait 60 seconds or more before judging discovery.

### Start the cluster
13. Start the secondary node first, then the primary. Each node needs the other node's peer identifier only if automatic discovery fails. Read the local identifier from the node's API:
    ```zsh
    curl -s http://127.0.0.1:<api-port>/node_id
    ```
14. Confirm the served model. List the models through the API:
    ```zsh
    curl -s http://127.0.0.1:<api-port>/v1/models
    ```
15. Expect node identifiers to change on restart in some versions. The cluster re-elects within about a minute. Do not patch around this; re-read the identifier after restarts.

### Download and place a model
16. Use EXO's own weight format. GGUF files are for other runtimes and waste bandwidth and disk for EXO, because the MLX backend cannot load them; for EXO, use the MLX-format weights.
17. Start downloads through the cluster API. A chat request for a model that is not downloaded returns "no instance found" and does not trigger a download. The download endpoint needs the target node identifier and the shard metadata. Read the schema from the API's `openapi.json`, and build the JSON body in a file rather than inline, because quotes in identifiers break shell escaping.
18. Authenticate large downloads with a Hugging Face token set in the EXO process environment. Anonymous transfers can be rate-limited to about 1 MB/s, while authenticated ones are typically much faster.
19. Track progress by file. Partial files show as `.partial`. Compare each file's byte count with the size the repository reports, rather than trusting an estimate. After a resume, check that the byte count grows; over some redirected CDN links a resume restarts from a few dozen bytes, so restart the file when the count does not grow.
20. Size the model against combined node memory minus OS headroom (for example, a ~120 GB 4-bit mixture-of-experts model across two 128 GB machines). If placement fails with a memory error, try a smaller quantization or a smaller model before changing the configuration.

### Point a client at the cluster
21. Set any OpenAI-compatible client to `base_url: http://127.0.0.1:<api-port>/v1` and use the model id from `/v1/models`. Use a placeholder key; the local API ignores it.

### Recover after a restart
22. Work in this order: confirm the node's network address, confirm the models directory exists, confirm the API port answers, confirm peers are visible, then restart. Time-box log reading once basic connectivity passes; a node restart is often faster.
23. Check which binary is actually running before changing anything:
    ```zsh
    ps aux | grep -i exo | grep -v grep
    ```
    Two installs with different home directories are common after a migration. The running process decides what is true.

## Pitfalls
- **Silent fallback to the default models directory.** A missing mount sends the download to the internal disk without an error. Check the path exists before every start.
- **Stale launch agents pass removed flags.** Current app versions removed a flag that older launch agents still pass, so the process exits at once. Remove the flag from the plist and reload.
- **Launch agents point at the wrong binary.** A plist that still runs an old module entry point fails. Point it at the binary the current install provides.
- **A bridge that reverts after reboot.** The static address and bridge state are not persistent by default. Re-apply them at boot.
- **Installer daemons rewrite network settings.** Unload them before manual configuration, or the cluster loses its link again within the hour.
- **A file-based key is unreadable before login.** On a disk-encrypted Mac, the SSH server may not read the user's key file until someone logs in at the console. Log in once or unlock the machine. Do not enable root login as a workaround.
- **Huge virtual memory is normal.** Model weights are memory-mapped and loaded lazily, so a process can report hundreds of gigabytes of virtual memory with a small resident size. Do not kill it for that alone.
- **Stale helper processes after remote sessions.** Long remote searches leave orphaned processes. Kill them after each remote session.
- **Deprecated download tools.** The command-line tool `huggingface-cli` no longer works; use `hf`. The environment variable `HF_HUB_ENABLE_HF_TRANSFER` is deprecated; use `HF_XET_HIGH_PERFORMANCE`.
- **Local snapshots fill the system disk.** Time Machine local snapshots can hold hundreds of gigabytes that the storage view does not show as used. List them with `tmutil listlocalsnapshots /`. Deleting them removes local recovery points, so confirm with the operator first.
- **RDMA needs matching systems.** Remote direct memory access needs identical operating-system builds on every node, a Thunderbolt 5 cable, supported hardware, and enabling from recovery mode on each machine. Without it, the cluster falls back to TCP over the same link with higher latency.
- **Kernel panics under distributed Metal load.** Some app versions triggered a Metal driver assertion (`completeMemory() prepare count underflow`) during distributed workloads. Check the linked upstream issues for the release that addresses it. A third-party wrapper that clears the Metal cache before each generation narrows the race but does not fix the driver; review its code before installing it.
- **Other model servers compete for the same memory.** Local servers on a cluster node share unified memory and the GPU. Stop or unload them while the cluster runs.

## Verification
- `curl http://127.0.0.1:<api-port>/v1/models` lists the expected model, and the node ID endpoint answers on every node.
- A short chat request through the cluster returns text from the placed model.
- `ping` between the nodes' static addresses succeeds, and the network service shows the static address after a reboot without manual steps.
- `ps` shows exactly one EXO process per node, and its path matches the install you intended.
- The model directory contains every expected shard at its expected size, with no `.partial` files.

## Attribution
- EXO distributed inference project by exo-explore: https://github.com/exo-explore/exo
- MLX array framework by ml-explore: https://github.com/ml-explore/mlx
- Upstream issues on the Metal driver panic: https://github.com/ml-explore/mlx/issues/3186 and https://github.com/exo-explore/exo/issues/1972
