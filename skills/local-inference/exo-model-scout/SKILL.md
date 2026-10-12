---
name: exo-model-scout
description: Use when picking MLX models for each memory tier of an EXO cluster. Covers discovery, size bands, same-band benchmarking, champion promotion, and report evidence rules.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [exo, mlx, model-scout, huggingface, benchmarking, automation]
    category: local-inference
related_skills: [exo-cluster, exo-uncensored-model-scout, mlx-inference]
---

# EXO Model Scout

## Overview
A model scout ranks MLX model candidates for each memory band of a cluster. It discovers candidates from the model hub, sorts them into bands by on-disk size, and benchmarks against the live model only when the cluster is actually serving one. Discovery and scoring still work when the cluster is down. Benchmarking does not. The report keeps three states apart: discovered, registered, and actually served.

## When to Use
- You need the best MLX model that fits a given memory budget on one or more Macs running EXO.
- You want a scheduled scan that reports a new candidate only when it beats the current champion by a set margin.
- The cluster changed size, and the current model no longer sits in the best band.

## Features
- Multi-strategy discovery: recently modified repositories, most downloaded repositories, and targeted searches for large model families, deduplicated into one list.
- Size classification from the hub's file-tree metadata into memory bands sized to your nodes.
- Keyword tagging of variants, so abliterated or uncensored builds are compared only within their band.
- Composite score: performance at 60 percent and a quality proxy at 40 percent, each benchmark run three times with the median kept.
- Promotion marker written only when a candidate beats the champion by the threshold.
- Report with the metric, the comparison set, the numbers, and the data source for every recommendation.

## Benefits
- Band-to-band comparison stops a small model from being scored against a large one.
- A scan still produces a useful discovery list when the cluster is offline, and the report says which steps were skipped.
- A champion change needs a measured margin, not an impression.
- Every number in the report can be traced to a run.

## Procedure
1. Define the memory bands from your hardware. Use the on-disk size of a model's weights, and set each band's ceiling from the combined memory of the nodes that will serve it, minus headroom. One five-band layout is: up to 35 GB, 35 to 100 GB, 100 to 140 GB on one 128 GB node, 140 to 260 GB on two nodes, and 260 to 320 GB on three nodes. Adjust the numbers to your cluster.
2. Discover candidates from three sources and deduplicate them:
   - the most recently modified repositories in the MLX community organization (about 50),
   - the most downloaded repositories (about 30),
   - targeted searches for large model families in each band.
   Expect 100 to 150 unique candidates.
3. Read each candidate's on-disk size from the hub's file-tree endpoint, not the sibling list. The sibling list reports zero for large files stored in LFS. Assign each candidate to a band.
4. Tag variants by name keywords (for example `abliterated`, `uncensored`, `unrestricted`). Compare tagged variants only against other models in the same band. Do not treat a tag as a quality claim.
5. Check the cluster API before benchmarking:
   ```zsh
   curl -s http://127.0.0.1:<api-port>/v1/models
   ```
   If it answers and lists a live model, read that model's band. If it does not answer, skip benchmarking and report discovery scores only.
6. Benchmark only models that have an instance running. For each one, run three trials and keep the median. Benchmark the recorded champion as the baseline, and the top same-band candidates against it.
7. Compute the composite score as 0.6 times the performance score plus 0.4 times the quality proxy. Keep the weights in one place in your script so the report can state them.
8. Promote a candidate only when it beats the champion by the threshold. For example, a threshold of 1.20 means a 20 percent margin. Write a promotion marker file when a promotion happens, and delete the marker after it is read so the same alert does not repeat.
9. Write the report and the leaderboard to the scout's own state directory. Keep the scan-state file for other workflows separate from the leaderboard.
10. Schedule a nightly discovery run. Run the full registration workflow on a separate, less frequent schedule (see the `exo-uncensored-model-scout` skill).

## Pitfalls
- **Benchmark the recorded champion, not the model named in the client config.** A config that names a model the cluster no longer runs makes every benchmark fail with 404 `No instance found`. Read the champion from the leaderboard instead, or skip the benchmark with a logged warning.
- **Registered is not the same as served.** The model list can include a model that chat completions cannot serve. Report it as registered, and do not present scores as benchmark results until a completion succeeds.
- **Recency sorting returns small models.** Recently uploaded repositories are often small quantizations, so a list sorted only by recency contains no large base models. Combine recency with popularity and targeted queries.
- **Discovery needs outbound access to the hub.** A scheduled run in a restricted network context can return zero models. Record that as a failed discovery step in the report, and fix the scheduled context's network allowance rather than working around it.
- **Verify the host before a scheduled run.** A scheduled job can run through a session attached to a different machine where the script and state directory do not exist. Check the hostname, the user, and the script path first.
- **Verify the script path.** Scheduled prompts can point at an old location. If the path is missing, switch to the profile path and record the change.
- **Build runtime paths from one home lookup.** Scheduled runs can resolve the home directory differently from an interactive shell. Use the same lookup everywhere.
- **An empty YAML file loads as `None`.** Check for `None` before calling `.get` on the result.
- **List every import in the environment's install list.** A script that imports a library the scheduled environment does not have fails on its first run. Install every import in that environment before the run.
- **A live process is not a bound port.** A service can show a running process while its API port is not yet bound. Check the port, not just the process.
- **Clear caches by name.** A recursive delete that starts at a parent directory can remove files that belong to the skill. Target each cache directory by its name and leave the parent directories alone.

## Verification
- The report lists every band with its candidate count, and each number names its source.
- A benchmark row exists only for a model that answered a completion request during this run.
- The promotion marker exists only when the threshold was met. No marker means no promotion.
- The runtime state directory is separate from the copy of the skill in the repository.

## Attribution
- MLX community models on Hugging Face.
- EXO distributed inference project by exo-explore.
