---
name: model-pipeline
description: Use when preparing a Hugging Face model for MLX. It is for MLX inference. Covers source verification, resumable download, shard repair, quantization choices, and benchmark gating.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [model-download, mlx-conversion, quantization, benchmarking, hf-cli, apple-silicon]
    category: local-inference
related_skills: [huggingface-download, mlx-inference, omlx-model-management]
---

# Model Pipeline: Verify, Download, Convert, Benchmark

## Overview
Turning a Hugging Face model into a local MLX artifact has more failure points than it looks. The wrong repository variant downloads cleanly, a partial download can exit with success, shard names can be rejected by the loader, and a converter may refuse to write into an existing folder or skip work silently. This skill sequences the steps and puts a check between each pair. Variants are judged only against a control that is not modified.

## When to Use
- Preparing a Hugging Face model as a local MLX or GGUF artifact for everyday inference.
- Producing 4-, 6-, and 8-bit variants of one source model and comparing them.
- Deciding whether a new variant is good enough to register with a local server.

This skill covers download, conversion, and benchmarking. Any step that changes model weights is outside its scope. If you perform one, record the method, re-test the model's behavior before and after, and label the output as modified. Never present a modified artifact as the unmodified baseline.

## Features
- Source verification that checks the exact repository, variant, and architecture before any download.
- A disk-space gate sized to the precision of the source.
- Resumable downloads with completion checks that do not trust the exit code.
- Shard-name repair for loaders that expect a different naming pattern.
- Conversion to several MLX quantization levels, with output-path rules.
- Benchmark gating against an unmodified control, reported as a decision packet.

## Benefits
- A wrong variant or truncated shard is caught before a long conversion starts.
- Each quantization level is measured against the same control on the same machine.
- Storage is reclaimed in a safe order, after every artifact has been verified.
- The decision packet makes the pass or fail call explicit and repeatable.

## Procedure
1. Verify the source. Confirm the exact repository id, the precision variant, and the model family and architecture. Common mistakes are a neighboring model version, a different precision, and a case-sensitive repository id:
   ```zsh
   hf info <repo-id>
   hf ls <repo-id>
   hf info <repo-id> | grep -i "model_type\|arch"
   ```
2. Gate on disk space. A bf16 model of about 30 billion parameters is roughly 60 to 70 GB, and quantized variants are typically a quarter to a half of that size. Check the destination volume first:
   ```zsh
   df -h <destination-volume>
   ```
3. Download with the current `hf` command. Re-running the same command resumes from the cache, because `--resume-download` is not supported:
   ```zsh
   hf download <repo-id> --local-dir <source-dir>
   hf download <repo-id> <filename> --local-dir <source-dir>
   ```
   Raising the worker count does not always raise throughput, so measure before you assume it helps.
4. Verify completion from the files, not the exit code. A download can exit non-zero even when every shard is present, and it can exit zero with a shard missing:
   ```zsh
   find <source-dir> -name "*.incomplete" | wc -l       # expect 0
   find <source-dir> -name "*.safetensors" | wc -l      # expect the shard count in the index
   du -sh <source-dir>
   ```
5. Repair shard names if the loader rejects them. Some downloaders write `model.safetensors-00001-of-0000N.safetensors`, while converters expect `model-00001-of-0000N.safetensors`. Rename the files and update the index file to match:
   ```zsh
   cd <source-dir>
   for f in model.safetensors-*.safetensors; do mv "$f" "${f/model.safetensors-/model-}"; done
   python3 - <<'EOF'
   import json, pathlib
   idx = pathlib.Path("model.safetensors.index.json")
   data = json.loads(idx.read_text())
   data["weight_map"] = {k: v.replace("model.safetensors-", "model-") for k, v in data["weight_map"].items()}
   idx.write_text(json.dumps(data, indent=2))
   EOF
   ```
6. Choose the quantization levels to produce, and convert each one into its own new folder. The converter needs its output path in `--mlx-path`, and it refuses to write into a folder that already exists:
   ```zsh
   mlx_lm.convert --hf-path <source-dir> --mlx-path <out-4bit> -q --q-group-size 64 --q-bits 4
   mlx_lm.convert --hf-path <source-dir> --mlx-path <out-6bit> -q --q-group-size 64 --q-bits 6
   mlx_lm.convert --hf-path <source-dir> --mlx-path <out-8bit>
   ```
   4-bit is the smallest and fastest, but it can lose the most quality. 8-bit is the closest to the source. 6-bit is often a balance point. A calibrated quantization, which records how strongly each weight's inputs activate on a representative text sample, spends more precision on the columns that matter. Its output is usually the same size as an uncalibrated quant of the same bit width, so use it when you have a suitable calibration corpus.
7. If a converter reports a data offset outside the file's range, the shard is likely corrupt. Delete that one shard and download it again, then convert again.
8. Keep the source until every conversion has finished and each artifact loads. Then, with the operator's approval, remove the large source folder:
   ```zsh
   rm -rf <source-dir>
   ```
9. Benchmark every variant against an unmodified control on the same machine, under the same settings. Record throughput in tokens per second, latency at the 50th and 95th percentiles, first-token latency, task accuracy on your own tasks, and tool-call stability. Write the control's numbers down with the hardware and software versions, so future runs compare like with like.
10. Write a decision packet for the operator: throughput against the control, task results, tool-call stability, a pass or fail recommendation, and the storage saved.
11. Register a passing variant with the local server. Add one entry per model under the server's provider block, with its base URL, its model key, and its context length. Keep API keys in the secret store, not in the config file.

## Pitfalls
- **Verify the exact variant before you download.** A cleanly downloaded wrong variant wastes hours of conversion.
- **Use `hf`, not `huggingface-cli`.** The older tool is deprecated.
- **Stale lock files block downloads.** If a download hangs with no running process, delete the stale lock files in the hub cache's lock folder. Never delete them while a download is still running.
- **Do not trust the exit code of a download.** Count the shards and check for `.incomplete` files.
- **A converter skips work silently when the target exists.** A run that failed after writing an index can leave a zero-byte file behind, and the next run then does nothing. Delete the partial output folder before retrying.
- **Check output sizes after each step.** A zero-byte file or an empty folder means the step failed, even if the command printed no error.
- **On APFS, deleting huge folders can be slow.** Use `find <dir> -type f -delete` in place. Moving files to a temporary folder frees no space when that folder is on the same volume as your data.
- **Poll background jobs instead of waiting on them.** A long wait on a background job can time out. Check progress with repeated short polls.
- **Do not modify the control.** Confirm its checksums or file dates before and after each benchmark run.
- **Delete the source last.** Removing it before every conversion has finished leaves you with nothing to reconvert from.
- **A model picker may reject a generic provider name.** Register the server under the exact provider slug the picker expects, and confirm with the server's model list.

## Verification
- Every expected shard is present, no `.incomplete` files remain, and the total size matches the source's expected size.
- Each converted artifact loads and answers a short prompt.
- The benchmark table lists the control and every variant, with the same settings and the hardware recorded.
- The decision packet states the pass or fail result and the storage saved, and the source folder is gone only after the last artifact loads.

## Attribution
- Hugging Face Hub, the source of the model repositories.
- MLX conversion and inference tools (`mlx-lm`) from the MLX project by ml-explore.
