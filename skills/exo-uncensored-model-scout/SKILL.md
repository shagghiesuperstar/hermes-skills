---
name: exo-uncensored-model-scout
description: Use when registering uncensored MLX models on EXO. It applies to an EXO cluster. Covers curated discovery, RAM-budget scoring, API registration, download, verification, and state tracking.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [exo, mlx, uncensored, abliterated, local-llm, model-management]
    category: local-inference
related_skills: [exo-cluster, exo-model-scout, mlx-inference]
---

# EXO Uncensored Model Scout

## Overview
This workflow finds uncensored or abliterated MLX models in curated Hugging Face collections, scores them against a RAM budget, registers the best one with an EXO cluster, downloads it, and verifies it with a test completion. It runs on a schedule and records each model in a state file so it is not processed twice. Each stage reports its own result. A model that is registered is not yet served, and a model that loads locally is not yet served by the cluster. The report keeps those states separate.

## When to Use
- You want to add an uncensored or abliterated MLX model to a running EXO cluster.
- A scheduled scan should check the monitored collections for new releases that fit the budget.
- A model was downloaded or registered, and you need to know whether the cluster actually serves it.

## Features
- Curated discovery from the configured collections, filtered to MLX text-generation models.
- A hard RAM-budget gate, then a composite ranking.
- Model-card generation through the cluster's registration endpoint, with a manual card as the fallback.
- Download through the cluster's download script with a long timeout and progress polling.
- Two-part verification: registration appears in the model list, and a short test completion returns text.
- A state file that skips models already handled.

## Benefits
- The RAM budget is enforced before any download starts, so an oversized model never reaches the cluster.
- Scheduled scans add new candidates without repeating old work.
- Failures are reported at the stage where they happened, not as a generic error.
- The workflow works on another cluster after its configuration values change.

## Procedure
1. Confirm the cluster API answers before anything else. Stop and report if it does not:
   ```zsh
   curl -sf "<exo-api>/state/topology"
   ```
2. Discover candidates. For each configured collection, query the hub for MLX models with the text-generation pipeline tag. Remove any model already listed in the state file.
3. Score the candidates in two stages:
   - **Hard gate:** exclude any model whose total weight size exceeds the RAM budget in bytes. Total size counts, not active parameters: a mixture-of-experts model with a small active set still loads all of its weights.
   - **Ranking:** combine log-scaled download and like counts with log-scaled size and parameter terms. Prefer 8-bit over 6-bit over 4-bit at the same parameter count. Prefer architectures the cluster has confirmed working. Keep the weights in the scoring script so the report can cite them.
4. For the top candidate, report it to the operator and wait for their go-ahead. Do not run steps 4 to 9 in a scheduled run without it. After the go-ahead, fetch the model's configuration file from the hub, then register it:
   ```zsh
   curl -sf -X POST "<exo-api>/models/add" \
     -H "Content-Type: application/json" \
     -d "{\"model_id\": \"<org>/<model>\"}"
   ```
   Registration fetches metadata and creates the card. It does not download weights. If it fails, write the card by hand from the documented schema. Name the card file by replacing each `/` in the model id with `--`, for example `<org>--<model>.toml`.
5. After the go-ahead, download the weights with the cluster's download script, using a long timeout. Poll the download-state endpoint for progress. Trust the script's exit code over its log.
6. Verify registration. The model must appear in the model list with its custom flag and a populated context length.
7. Verify serving. Send one short completion request with `max_tokens` set to 32 and streaming off. Expect coherent text:
   ```zsh
   curl -sf -X POST "<exo-api>/v1/chat/completions" \
     -H "Content-Type: application/json" \
     -d "{\"model\": \"<org>/<model>\", \"messages\": [{\"role\": \"user\", \"content\": \"Reply with one short sentence.\"}], \"max_tokens\": 32, \"stream\": false}"
   ```
8. Append the model id to the state file so later scans skip it.
9. After the go-ahead, commit the new card and the state file only if they sit inside a git repository. Check with `git rev-parse --show-toplevel` first. If there is no repository, report the commit as skipped.

### Configuration
Set these values through the agent's configuration tool, not by editing scripts:
- `exo_scout.ram_budget_gb`: total cluster RAM ceiling in GB.
- `exo_scout.exo_api`: the cluster API base URL.
- `exo_scout.hf_collections`: comma-separated collection slugs to monitor.
- `exo_scout.custom_cards_dir`: where cards are written.
- `exo_scout.state_file`: the JSON file that tracks processed models.

## Pitfalls
- **Registration is not serving.** A registered model can appear in the list and still fail chat completions with a 404 error. Report it as registered. If the cluster still cannot serve it, load the downloaded directory locally with the MLX language tools and report it as locally verified, not as served by the cluster.
- **Multi-device clusters need tensor support.** The card must set tensor support to true for tensor-parallel operation across nodes.
- **Offline mode blocks metadata fetches.** Registration fetches the model's configuration from the hub. If the environment sets an offline flag, run registration from a session that can reach the hub, and leave the offline setting in place elsewhere.
- **The card directory must exist before the cluster starts.** If it is missing, the startup scan skips custom cards without an error.
- **Gated models need a token in the process environment.** Without one, downloads fail with 401 or 403. Set the token in the environment of the process that runs the scan, not in the shell history.
- **Check the endpoint's method.** A POST to an endpoint that accepts only GET returns 405. Read the method from the API schema before scripting it.
- **Partial downloads hide as `.incomplete` files.** A stalled client leaves them behind. Kill the client and retry the file.
- **Shard sizes do not sum from the first file.** A single safetensors file can be much smaller than the full model because quantized shards are separate. Compare totals from the index file, not one shard.
- **Use the current hub CLI.** The older `huggingface-cli` tool is deprecated; use `hf`.
- **Uncensored is not a safety rating.** Removing refusal behavior is a property to test for your own use case, not something this scan evaluates. Run your own checks before any user-facing use.

## Verification
- The model appears in the cluster's model list with its custom flag and a context length.
- The test completion returns text, and the reply is stored in the run log.
- The state file contains the model id, and the next scan skips it.
- The card file exists in the custom cards directory.
- If the completion fails with 404 after registration, the report states "registered, local verification only" and not "served".

## Attribution
- Josiefied abliterated MLX models in the mlx-community collection: https://huggingface.co/mlx-community/josiefied-and-abliterated-models
- MLX community models on Hugging Face: https://huggingface.co/mlx-community
- EXO distributed inference project by exo-explore.
