---
name: darkbloom-provider
description: Use when onboarding a Mac as a Darkbloom provider node. Covers install, device link, MDM, model pinning, daemon start, and the done gate.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [darkbloom, provider-node, apple-silicon, mdm, launchd]
    category: local-inference
related_skills: [darkbloom-fleet-ops, mlx-inference, omlx-model-management]
---

# Darkbloom Provider Node

## Overview
Darkbloom pays Macs that serve catalog models to a coordinator-routed inference network. A provider runs an in-process MLX daemon as a launchd agent, so it competes for the same Apple Silicon GPU as any other local model server. The console account is shared across machines, but each Mac needs its own device-code login, its own MDM enrollment, and its own model download. Earnings also require hardware trust, which only MDM enrollment provides.

## When to Use
- Adding a Mac to a Darkbloom account, or rebuilding a provider after a reinstall.
- The daemon runs but earnings stay at zero. The cause is usually the model pin or the MDM step.
- Freeing unified memory from other local model servers so a catalog model can load.
- Setting up a node that also serves your own agent's traffic.

## Features
- A hardware gate that reads real RAM and OS version before any install.
- Ordered per-node setup: install, device login, MDM enrollment, model pin, background download, daemon start.
- A done gate covering daemon state, hardware trust, warm model, served-request count, and doctor checks.
- Competing-runtime cleanup, plus guidance for keeping the node awake and logged in while it serves.
- An optional local OpenAI-compatible endpoint that shares the same loaded model.
- A rollback path and a secret-free inventory line for the fleet record.

## Benefits
- Earnings start on the first working pass instead of after a silent misconfiguration.
- Human-only steps (device link, MDM password) are isolated, so an automated run does not stall on them.
- Reboots and app relaunches no longer quietly reclaim the GPU.
- Each node's identity stays on that machine.

## Procedure
1. Gate the hardware. Confirm Apple Silicon, macOS 14 or later, and the RAM figure from the kernel, not from a marketing label:
   ```zsh
   sysctl -n machdep.cpu.brand_string
   sysctl -n hw.memsize | awk '{printf "RAM_GB=%.0f\n", $1/1024/1024/1024}'
   sw_vers -productVersion
   ```
   Check each model's minimum RAM in the live catalog (`darkbloom models catalog`). A Mac below a model's floor can act as a controller but cannot serve that model. A provider needs at least 8 GB just to start.
2. Free the GPU from competing runtimes for this session. In-process MLX fights other servers for the same memory. Ask the operator to name each runtime to stop, such as oMLX, DS4, or Ollama. Stop only the runtimes they name, with a graceful stop first:
   ```zsh
   launchctl bootout gui/$(id -u)/<competitor-label> 2>/dev/null || true
   pkill -f '<competitor-process-pattern>' 2>/dev/null || true
   pgrep -lf '<competitor-process-pattern>' || echo 'competitors gone'
   ```
   Do not touch a runtime another job has pinned for its own work. Stop and ask instead. Use a forced kill only if a process still runs after its graceful stop, and only with the operator's approval.
3. Install the CLI from the official script. Use 0.8.10 or later (the tested version), and confirm it. Download the script and read it before you run it. Compare its checksum with a published one when the publisher gives one. Do not pipe the script into a shell:
   ```zsh
   curl -fsSLo <install-script> https://api.darkbloom.dev/install.sh
   less <install-script>
   shasum -a 256 <install-script>
   bash <install-script>
   export PATH="$HOME/.darkbloom/bin:$PATH"
   darkbloom --version
   ```
4. Pin the model before you download anything. Put `enabled_models` under the `[backend]` table in `~/.config/darkbloom/provider.toml`:
   ```toml
   config_version = 2

   [backend]
   enabled_models = [
     "<catalog-model-id>",
   ]
   ```
5. Link the device (human step). Run `darkbloom login` in a real terminal, open the link page in the browser where the console account is signed in, enter the code, and wait for `Account linked successfully!`. Start one login at a time, because a second login mints a new code and orphans the first. Codes expire in about 15 minutes.
6. Enroll MDM (human step). Run `darkbloom enroll`, open the generated profile, then approve it in System Settings under Device Management. Verify:
   ```zsh
   profiles status -type enrollment
   darkbloom doctor | grep -i mdm
   ```
7. Download the pinned model in the background, and watch disk growth rather than console output:
   ```zsh
   darkbloom models download <catalog-model-id>
   du -sh ~/.cache/huggingface/hub/models--<model-dir-name>
   find ~/.cache/huggingface/hub/models--<model-dir-name> -name '*.part' | wc -l   # expect 0
   ```
8. Start the daemon and wait before judging it:
   ```zsh
   darkbloom start --model <catalog-model-id>
   sleep 60
   darkbloom status
   darkbloom doctor
   ```
9. Optional unified mode. To serve the coordinator and a local OpenAI-compatible endpoint from one daemon, use the local-endpoint option that `darkbloom --help` lists, bind it to loopback on a free port, then read the base URL and key:
   ```zsh
   darkbloom --help
   darkbloom local
   ```
10. Confirm the done gate in the Done Gate section below before you call the node finished.

### Fleet rollout
- Finish one node end to end, then repeat per node. Each one gets its own login, its own MDM profile, and its own start.
- To skip a long download, copy a complete model cache from another of your own machines over the LAN. Still run login, enroll, and start locally.
- Never copy another node's `~/.darkbloom` directory, auth token, or MDM profile. Keys are bound to the machine's hardware, so copies do not work, and the token leaks an account credential.
- Keep one primary earning model per large Mac. A second, cheaper model shares the single GPU slot and splits the KV cache, so it can earn less than the primary alone. Add a second model only after the ledger shows it earns and the Mac holds both.

### Hardening against reboots and relaunches
A `bootout` only stops the current session.
- **Competing runtimes start again at the next login.** Stop them for this session. Decide with the operator whether they should stay off at login, and change that only in each app's own settings.
- **Keep the node awake while it serves.** Serving stops when the Mac sleeps or reboots. With the operator's approval, set power management with `sudo pmset -a` for `standby`, `autopoweroff`, `proximitywake`, `womp`, and `networkoversleep`, all set to 0, and verify with `pmset -g`.
- **Auto-login does not work on a FileVault Mac.** FileVault requires a human password at the pre-boot screen. Do not automate unlock or weaken FileVault. Accept one human login per reboot, and add a heartbeat check from another machine that alerts when the status goes stale.

### Node routine (controller pattern)
- Route your own agent's inference to owned nodes with the provider's prefer header, and keep a paid fallback for hard turns. If the console shows fleet-served billing for your traffic, no owned node served that model at that time. Fix supply on the node, not the client.
- Maintenance every six hours: run doctor, restart the daemon only if it is down, confirm your agent config still carries the prefer header, and record the result in a status file. If an update is available, report it and wait for the operator's go-ahead before the CLI update runs.
- Hourly report: have the node print one JSON status object (host, chip, RAM, provider version, trust, connected, loaded models, thermal state, uptime, doctor result), and send that real output, not a summary from memory.
- Wrap every CLI call in a timeout. A doctor call killed by its timeout exits 137, which means it timed out, not that it failed.
- Stop a provider only on an explicit order. A stopped node earns nothing.
- Never enable private-only mode, which removes you from the paid network, and never edit the auth token file.

### Ground truth: commands and names that do not exist
- There is no Homebrew formula. Install with the official script and update with `darkbloom update`.
- There is no `darkbloom serve`, no `provider sync`, and no earnings command. Earnings are read in the web console.
- Model ids are catalog ids from `darkbloom models catalog` or the `/v1/models` listing, never the upstream Hugging Face repository id.
- `/tmp` is cleared on reboot. Keep scripts in a persistent directory.
- The extra-headers setting belongs under a named custom provider, not on the model block.

## Pitfalls
- **Pin under `[backend]`.** Place `enabled_models` under the `[backend]` table, the placement the tested version reads. A key outside that table is not applied, the doctor then picks the largest local weight, and earnings are zero. Check the pin with `darkbloom doctor` before you rely on it.
- **The doctor scans the whole Hugging Face cache.** Without a pin it may report a model you never serve as the one that fits. Pin the catalog id, and do not delete weights that other tools share.
- **Device link and MDM are human steps.** An agent's terminal wait times out before the browser link completes, and the code dies with it. Run these in a real terminal.
- **Earnings need hardware trust.** Without MDM enrollment (proofs `mdm,mda`) the daemon runs, but traffic never arrives.
- **Start reports false negatives for about a minute.** It prints "started" and then "not running" while the weight hasher runs. Re-poll after 45 to 60 seconds.
- **Port 8000 is the default for common local servers.** Choose a free port for the local endpoint.
- **Never use `--no-auth`.** Keep the local endpoint on `127.0.0.1` with its key enabled.
- **Foreground long jobs get cut off.** Use the agent runtime's background-job mode with a completion notice. Shell-level wrappers such as `nohup` or `disown` may be rejected, and a re-run starts a duplicate download or daemon.
- **Stopping a wedged daemon can disable auto-start.** After a stop on a stale service, re-enable auto-start before leaving, or the daemon will not return after a reboot.
- **Activation is per machine.** Secure Enclave keys and serial binding mean a copied profile or config is useless on another Mac.
- **Sleep blocks serving.** Serving needs a logged-in GUI session for attestation. Keep the node logged in, on power, with display-only sleep.

## Verification
- The done gate above passes on the node itself, not on a remembered state. Re-run `darkbloom status` before reporting.
- After a reboot, the daemon is running after the one human login, with no other manual step.
- The inventory line is generated from live values, not typed from memory.

### Done gate
All of these must hold before the node counts as earning:
- `darkbloom status` shows the daemon running, trust at hardware level and online, an enabled-model filter equal to the pin, the pinned model warm, and a requests-served count that increases.
- `darkbloom doctor` passes account link, MDM enrollment, coordinator trust, and model fit for the pinned model.
- `darkbloom doctor | grep -i competing` passes after cleanup.
- The provider console lists this Mac online under the shared account.

Inventory line for the fleet record (no secrets, no profile bytes):
```text
host=<local-hostname> serial=<serial> account=linked model=<catalog-model-id> mdm=PASS daemon=running console=yes
```

### Rollback
Run the rollback only on the operator's go. It uninstalls the CLI and unenrolls this machine.
```zsh
export PATH="$HOME/.darkbloom/bin:$PATH"
darkbloom stop --uninstall
darkbloom unenroll
```
Then remove the Darkbloom profile in System Settings. Delete the CLI config and model cache only after you confirm no other tool uses them. If you disabled a competing app's launch agent, restore its saved plist and bootstrap it from a GUI session.

## Attribution
- Darkbloom official provider setup: https://console.darkbloom.dev/providers/setup
