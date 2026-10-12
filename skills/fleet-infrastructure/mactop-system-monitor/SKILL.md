---
name: mactop-system-monitor
description: Use when reading live Apple Silicon metrics. Covers CPU, GPU, memory and thermal data, the interactive view, one-shot JSON for telemetry, and export.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [macos, apple-silicon, system-monitor, cpu, gpu, memory, telemetry]
    category: fleet-infrastructure
related_skills: [multi-mac-fleet-ops, disk-cleanup]
---

# mactop: Apple Silicon System Monitor

## Overview
mactop is a terminal monitor for Apple Silicon Macs. It shows CPU, GPU, unified memory, network, disk, battery, temperatures, and fan speed in one live view, and it can emit a single JSON sample for scripts and telemetry. Use the interactive view when a person is at the machine. Use one-shot JSON when an agent or a scheduler needs a reading, because each run is a fresh process with clean memory.

## When to Use
- You need to see what is loading a Mac right now: CPU cores, GPU, unified memory pressure, or heat.
- A model server or build feels slow, and you want the memory and thermal picture before you change anything.
- A scheduled telemetry job needs one structured reading per run.
- You need a short metrics file for a time window, for example to attach to a report.

## Features
- Interactive full-screen view with a configurable refresh interval.
- Single-sample JSON output that exits after one reading, with no sudo needed in headless mode on recent macOS versions.
- Prometheus-format export for a local scraper.
- Menu bar and overlay modes for a quick glance while working.
- Fields for chip and core counts, thermal state, core temperatures, and GPU utilization in the JSON output.

## Benefits
- One tool covers the metrics that matter for local inference: unified memory, GPU use, and thermal state.
- A telemetry job gets a clean, parseable reading each time.
- Long-running monitor processes do not accumulate memory, because each run starts fresh.
- Readings can be attached to a report with a timestamp, so later comparisons are fair.

## Procedure
1. Install from the official project, either from its source repository or with the package manager. Build from source needs a recent Go toolchain. After installing, confirm the version and the flags:
   ```zsh
   mactop --version
   mactop --help
   ```
   Source is at https://github.com/metaspartan/mactop. Check the version before relying on the headless JSON fields, because older releases lack some of them.
2. For a person at the machine, open the interactive view and set the refresh interval in milliseconds:
   ```zsh
   mactop -i 2000
   ```
   Press `q` to quit. The interactive view needs a real terminal, so it cannot run through a remote agent session.
3. For a script or telemetry, take one sample and exit:
   ```zsh
   mactop --headless --format json --count 1
   ```
   Read fields such as the CPU and GPU utilization, the memory used and total, the thermal state, and the chip summary. Run it fresh each time, instead of leaving one process running.
4. For a short time series, take a fixed number of samples into a file:
   ```zsh
   mactop --headless --format json --count 60 > <output-dir>/metrics.json
   ```
5. For a scraper that already runs on the machine, expose the Prometheus endpoint on a loopback port:
   ```zsh
   mactop -p <metrics-port>
   curl -s http://127.0.0.1:<metrics-port>/metrics | head
   ```
6. For a quick glance while working, use the menu bar or overlay modes. They need macOS permissions for the terminal app, and the overlay needs Screen Recording permission to show frame rate. Start them from a terminal you keep open, not from a shell command that backgrounds itself.
7. Record each reading with a timestamp and the machine's name, so later readings are comparable.

### Reading the Numbers
- **Unified memory:** the figure that matters for local models. Check it against the memory the models need before loading another large model, and watch the pressure figure rather than the used figure alone.
- **Thermal state:** a sustained elevated state means throttling is likely. Compare sustained readings, not one spike.
- **GPU utilization:** low GPU use with high memory use usually means a model is loaded but idle.
- **CPU per core type:** efficiency and performance cores show different load, so read them separately.

## Pitfalls
- **A long-running monitor process can grow in memory.** In headless streaming mode the process can reach a gigabyte or more over hours. Use `--count 1` in a loop, or a fresh invocation per reading.
- **Two installs can disagree.** A package-manager build and a source build can differ in version and fields. Check `mactop --version` on the machine where the script runs.
- **Thermal readings may need elevated access.** The interactive view can ask for elevated access for some thermal readings. The headless mode is designed to run without it on recent macOS versions. Do not add elevated access to a script just to read one field; check whether the field appears first.
- **Interactive mode needs a terminal.** Running it from an agent session that has no terminal fails or hangs. Use the headless JSON mode there.
- **Menu bar and overlay need OS permissions.** A missing permission looks like a blank window, not an error. Grant the permission to the terminal app, then restart the mode.
- **Do not treat one sample as a trend.** A single reading can catch a short spike. Take several samples over a window before drawing a conclusion.

## Verification
- `mactop --version` prints the expected release, and `mactop --headless --format json --count 1` prints one JSON object and exits.
- The JSON object includes the memory and thermal fields the script reads.
- A monitor process started for a session exits when the session ends, and the memory use stays flat across repeated one-shot readings.

## Attribution
- mactop by metaspartan: https://github.com/metaspartan/mactop
