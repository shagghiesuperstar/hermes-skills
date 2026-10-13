---
name: huggingface-download
description: Use when fetching large model weights from Hugging Face. Covers token auth, resumable single-file downloads, per-file snapshots, and persistent background runs.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [huggingface, download, models, hf-token, gguf]
    category: local-inference
related_skills: [mlx-inference, model-pipeline, local-model-deployment]
---

# Hugging Face Model Downloads

## Overview
Model weights run from a few gigabytes to hundreds of gigabytes, and anonymous transfers are slow enough to take days. Authenticated transfers are far faster, resumable single-file downloads survive interruptions, and multi-file snapshots need more care than a single call. Most failed downloads come from the environment rather than the network: a token pasted into a shell command, a download process tied to a chat turn that ends, a script written to a temporary folder that disappears, or a `~` that resolves to a different home directory.

## When to Use
- Fetching a GGUF or MLX model repository, or one large weights file, from Hugging Face.
- A download is very slow, stalled at zero percent, or lost when the session ended.
- Setting up a machine that will pull models for local inference.

## Features
- Token-authenticated transfers, with the token read from a private environment file.
- Resumable single-file download with curl, writing to a `.part` file that is renamed only when complete.
- Python `hf_hub_download` for individual files and `snapshot_download` for whole repositories.
- Persistent background runs through a user launch agent or a scheduled one-shot job.
- Progress checks from disk usage on the destination folder.

## Benefits
- At about 300 KB/s, an 80 GB file takes several days. At 100 MB/s, the same file takes about 15 minutes.
- A `.part` file never looks like a finished model.
- Long downloads continue across chat-session boundaries and agent restarts.

## Procedure
1. Store the token in a private environment file that only your account can read, for example `<profile-dir>/.env`, as `HF_TOKEN=<token>`. Read it into a variable when a command needs it. Never paste it into a command line or print it into a log:
   ```zsh
   export HF_TOKEN="$(grep '^HF_TOKEN=' <env-file> | cut -d= -f2-)"
   ```
2. Check free space on the destination volume before starting:
   ```zsh
   df -h <destination-volume>
   ```
3. Download one large file with resume support. The `-C -` flag continues from the existing byte offset, and the rename happens only after curl exits successfully:
   ```zsh
   URL="https://huggingface.co/<org>/<repo>/resolve/main/<filename>"
   curl -# -L --fail -C - -H "Authorization: Bearer ${HF_TOKEN}" \
     -o "<dest>/<filename>.part" "$URL" \
     && mv "<dest>/<filename>.part" "<dest>/<filename>"
   ```
4. For multi-file repositories, write a small script in a persistent folder and run it from there, with absolute paths. Read the token from the environment, set the faster transfer variable, and call the hub library's single-file download once per file, passing the repository, the filename, the local directory, and the token as a parameter. Do not log in through the library, because that stores a credential in its cache. Download small files first, one at a time, so a failure is easy to locate and print the path after each file.
5. For multi-hour transfers, run the script as a persistent job, not as a process attached to a chat turn. A user launch agent works well. It needs `RunAtLoad` true and `KeepAlive` false, and it writes its output to a log:
   ```xml
   <key>ProgramArguments</key>
   <array>
     <string>/usr/bin/python3</string>
     <string><absolute-path-to-script>.py</string>
   </array>
   <key>RunAtLoad</key><true/>
   <key>KeepAlive</key><false/>
   <key>StandardOutPath</key><string><absolute-path-to-log></string>
   ```
   Load it with `launchctl load <plist-path>`. A scheduled one-shot job of the agent runtime is the other persistent option.
6. Monitor progress from disk usage and the log, not from the process list:
   ```zsh
   du -sh <dest>/<repo-folder>
   tail -n 5 <absolute-path-to-log>
   ```
7. For a remote machine, run the download on the host that has the disk. Verify where a file actually landed with `ssh <host> 'ls -l <path>'`, because an agent terminal can be attached to a different machine than the one you intended.

## Pitfalls
- **Never download without a token.** Anonymous transfers are rate-limited to a few hundred KB/s, which turns a large file into a multi-day job.
- **Do not run inline Python with `-c` over SSH.** Shell quoting mangles token values. Write a `.py` file, copy it to the host, and run it.
- **Set `HF_XET_HIGH_PERFORMANCE=1`** to use the faster transfer path.
- **Resume with `curl -C -`.** A broken transfer continues from its byte offset instead of starting over.
- **Snapshot calls with pattern filters can stall at zero percent** on large multi-file repositories. Download the files one at a time with `hf_hub_download` instead.
- **Keep scripts in a persistent folder.** Temporary folders can be cleared between sessions, and a script written on one machine is not present on another.
- **Use absolute paths in scripts.** In agent sandboxes, `~` can resolve to a different home directory than your shell uses.
- **A stalled progress indicator is a wedged transfer** when disk usage has not grown for several minutes, the process is still alive, and the hub still responds. Stop the client and resume the same file with the resumable method.
- **Use the current `hf` command.** The older `huggingface-cli` is deprecated.

## Verification
- The downloaded file size matches the size the hub reports for that file.
- No `.part` or `.incomplete` files remain in the destination folder.
- If the hub lists a SHA-256 for the file, `shasum -a 256 <file>` matches it.
- The model loads in its runtime, or its header is readable, before any other step depends on it.

## Attribution
- Hugging Face Hub, the source of the model repositories and the `huggingface_hub` Python library: https://huggingface.co
