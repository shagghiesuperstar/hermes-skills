---
name: claude-code-local-stack
description: Use when routing Claude Code to local models on a Mac. Covers a stripping proxy, three-tier model routing, per-model server settings, and preflight checks.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [claude-code, local-llm, omlx, apple-silicon, proxy]
    category: local-inference
related_skills: [omlx-model-management, omlx-per-model-tuning, local-model-deployment]
---

# Claude Code on a Local Model Stack

## Overview
Claude Code can run fully offline against models served on the same Mac, but a plain local model server rejects the requests it sends. Claude Code adds Anthropic-specific beta headers, a `system` role message, and a `?beta=true` query parameter. A small stripping proxy sits between Claude Code and the model server to remove those, and three model tiers (frontier, middle, fast) map onto Claude Code's opus, sonnet, and haiku slots. Every component binds to loopback only.

## When to Use
- You want Claude Code to run without cloud calls on Apple Silicon with enough unified memory for at least one large model.
- Claude Code fails with HTTP 422 `messages[N].role` or 401 errors when pointed at a local server.
- A Hermes agent must launch Claude Code as a subprocess against local models.
- Claude Code's opus, sonnet, and haiku slots should resolve to different local models.

## Features
- A stdlib-only proxy that drops `system` messages, strips the `?beta=true` parameter, and forwards only an allowlist of headers plus its own bearer token.
- Server-sent-event pass-through, so streamed tokens reach Claude Code as they are generated.
- Three-tier routing through `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, and `ANTHROPIC_DEFAULT_HAIKU_MODEL`.
- Per-model server settings: context window, sampling, idle TTL, pinning, KV-cache quantization, and reasoning output off.
- A memory budget and cache sizing rule tied to unified memory.
- A preflight checklist and an end-to-end Claude Code test.

## Benefits
- Coding sessions work with no data leaving the machine and no per-token cloud cost.
- The three-tier split keeps the large model for planning and sends routine calls to a fast model.
- Known failure modes (422 role errors, 401 key errors, silent tool-loop stalls) each map to one setting.
- The whole stack is reproducible from one settings file and one proxy script.

## Procedure
1. Check versions. Tested with oMLX 0.3.12 and Claude Code 2.1.156; confirm your versions:
   ```zsh
   omlx --version
   claude --version
   python3 --version   # 3.11 or later
   ```
2. Configure the model server in `~/.omlx/settings.json`. Bind to loopback, enable the memory guard, and set the cache limits:
   ```json
   {
     "server": {"host": "127.0.0.1", "port": 8000},
     "memory": {"memory_guard_tier": "aggressive", "soft_threshold": 0.87, "hard_threshold": 0.96},
     "scheduler": {"max_concurrent_requests": 4, "chunked_prefill": true},
     "cache": {"enabled": true, "ssd_cache_max_size": "<size>", "hot_cache_max_size": "<size>"},
     "auth": {"api_key": "<local-api-key>", "skip_api_key_verification": false},
     "claude_code": {"mode": "local", "context_scaling_enabled": true, "target_context_size": 131072,
                     "opus_model": "<frontier-model>", "sonnet_model": "<middle-model>", "haiku_model": "<fast-model>"}
   }
   ```
3. Set per-model rules in `~/.omlx/model_settings.json`. Each key must equal the model's folder name under the model directory:
   ```json
   {
     "version": 1,
     "models": {
       "<middle-model>": {"max_context_window": 131072, "temperature": 0.6, "top_p": 0.95,
                          "enable_thinking": false, "ttl_seconds": -1, "is_pinned": true,
                          "forced_ct_kwargs": ["enable_thinking"]},
       "<fast-model>": {"max_context_window": 65536, "enable_thinking": false, "ttl_seconds": 120},
       "<frontier-model>": {"max_context_window": 131072, "temperature": 1.0, "enable_thinking": false,
                            "turboquant_kv_enabled": true, "turboquant_kv_bits": 4.0,
                            "ttl_seconds": 60, "is_pinned": false}
     }
   }
   ```
   Use the sampling values from each model's card. Only the middle tier is pinned.
4. Start the proxy from the script in the Proxy Script section below. Export the local key from your secret store, run the script in its own terminal (or under launchd, step 7), and confirm it with a probe. The proxy has no GET route, so use a POST:
   ```zsh
   export LOCAL_LLM_API_KEY=<key-from-your-secret-store>
   UPSTREAM_PORT=<server-port> LISTEN_PORT=<proxy-port> python3 -u <proxy-dir>/proxy.py
   curl -s -X POST http://127.0.0.1:<proxy-port>/v1/messages -H 'Content-Type: application/json' \
     -d '{"model":"<fast-model>","max_tokens":16,"messages":[{"role":"user","content":"Say ok."}]}'
   ```
5. Point Claude Code at the proxy. Write this to `$HOME/.claude/settings.json`, merging into any existing `env` block:
   ```json
   {
     "env": {
       "ANTHROPIC_BASE_URL": "http://127.0.0.1:8002",
       "ANTHROPIC_AUTH_TOKEN": "<local-api-key>",
       "ANTHROPIC_DEFAULT_OPUS_MODEL": "<frontier-model>",
       "ANTHROPIC_DEFAULT_SONNET_MODEL": "<middle-model>",
       "ANTHROPIC_DEFAULT_HAIKU_MODEL": "<fast-model>",
       "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": "1",
       "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
       "DISABLE_TELEMETRY": "1"
     }
   }
   ```
6. Set the GPU wired-memory limit below total RAM, so macOS keeps headroom for itself and its other processes:
   ```zsh
   sudo sysctl iogpu.wired_limit_mb=<MB>
   ```
7. (Optional) Run the proxy under launchd so it survives reboots. Create a LaunchAgent plist with `RunAtLoad` and `KeepAlive` set to true, `ProgramArguments` of `/usr/bin/python3 -u <proxy-dir>/proxy.py`, and log paths for stdout and stderr. Load it with `launchctl load <plist-path>`.
8. Start Claude Code from an agent with an explicit child environment. Copy the parent environment, remove `ANTHROPIC_API_KEY`, add the proxy variables and the key from the secret store, and launch the CLI with a timeout. Do not pass the key through a shell string.

### Proxy Script
Save this as `<proxy-dir>/proxy.py`. It drops `system` messages, removes the `beta=true` query parameter, forwards only a short allowlist of headers, and adds its own bearer token. It handles non-streaming responses; check streamed responses before relying on them.

```python
#!/usr/bin/env python3
"""Claude Code to local model server shim. Stdlib only; loopback only."""
import http.server, json, os, re
from http.client import HTTPConnection

UP, LISTEN = int(os.environ.get("UPSTREAM_PORT", "8000")), int(os.environ.get("LISTEN_PORT", "8002"))
KEY, KEEP = os.environ["LOCAL_LLM_API_KEY"], {"accept", "content-type", "user-agent", "anthropic-version"}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        body["messages"] = [m for m in body.get("messages", []) if m.get("role") != "system"]
        data = json.dumps(body).encode()
        headers = {k: v for k, v in self.headers.items() if k.lower() in KEEP}
        headers.update({"Authorization": f"Bearer {KEY}", "Content-Length": str(len(data))})
        conn = HTTPConnection("127.0.0.1", UP, timeout=300)
        conn.request("POST", re.sub(r"[?&]beta=true", "", self.path), body=data, headers=headers)
        resp = conn.getresponse()
        self.send_response(resp.status)
        self.send_header("Content-Type", resp.getheader("Content-Type", "application/json"))
        self.end_headers()
        while chunk := resp.read(64):
            self.wfile.write(chunk)
        conn.close()

http.server.ThreadingHTTPServer(("127.0.0.1", LISTEN), Handler).serve_forever()
```

## Pitfalls
- **Never export `ANTHROPIC_API_KEY` to Claude Code.** It is sent as an `x-api-key` header, which the local server ignores, so every request fails with 401. Use `ANTHROPIC_AUTH_TOKEN`, which becomes a bearer token.
- **Point `ANTHROPIC_BASE_URL` at the proxy, not the model server.** Going straight to the model server returns 422 on every request because of the system-role message and beta headers.
- **Confirm `$HOME` before writing settings.** Claude Code reads `$HOME/.claude/settings.json`. Isolated agent profiles often set a different `HOME`, so the file lands where Claude Code never looks.
- **Keep thinking output off for tool-calling models.** Reasoning tokens consume the budget before any visible output, so tool calls look hung. Set `enable_thinking` to false everywhere and force it with the forced-kwargs list where supported.
- **Never set `ttl_seconds` to 0.** The model unloads after every request, adding a 1-2 second load to each tool call. Use `-1` for the always-hot model and a finite TTL for large or rarely used ones.
- **Pin only the model that must stay loaded.** Loading all three tiers at once can exceed unified memory. Add up the resident sizes before you load a second large model. Pinning the frontier model prevents the other tiers from loading.
- **Quantize the KV cache for very large models.** A 128K-token KV cache for a large model can need about 126 GB unquantized but about 24 GB at 4-bit, which is the difference between fitting and an out-of-memory crash.
- **Respect the model card's sampling values.** Some frontier models require temperature 1.0; their model cards warn that temperature 0 causes endless thinking loops.
- **Keep the version field an integer.** `"version": "1"` as a string silently disables every per-model setting. Model keys are case-sensitive and must match the folder name.
- **Keep every listener on loopback.** Bind both the model server and the proxy to `127.0.0.1`, never `0.0.0.0`, and do not expose either port through a tunnel. Keep `skip_api_key_verification` false and keep the key out of shell history, logs, and commits.

## Verification
- Model server answers with auth: `curl -s http://127.0.0.1:8000/v1/models -H "Authorization: Bearer <local-api-key>"` lists each tier's model id.
- The probe request in step 4 returns a `message` object, not an error.
- Proxy inference works: POST a one-message request with `max_tokens` 16 to `/v1/messages` through the proxy and get a `message` object back.
- Claude Code works end to end: `claude --print "say hi"` returns text, and `claude --print "what model are you running right now?"` names the routed tier.
- Log check: the proxy log shows a 200 from the model server for each request, with no `system` role left in the messages.

## Attribution
- oMLX by jundot, the local model server this stack is built on: https://github.com/jundot/omlx
- Claude Code gateway and authentication docs: https://docs.anthropic.com/en/docs/claude-code/llm-gateway and https://docs.anthropic.com/en/docs/claude-code/authentication
