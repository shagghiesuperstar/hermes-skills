---
name: clude
description: Use when installing or fixing the Clude memory sidecar. It covers its MCP server and dream or reflection daemon, beside an existing memory system. Clude is additive and must not replace the memory systems already in place.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [memory, cognitive-memory, mcp, sidecar, dream-cycle, local-llm]
    category: memory-knowledge
related_skills: [hindsight, triple-threat-memory, hermes-memory-providers]
---

# Clude Cognitive Memory Sidecar

## Overview
Clude is a cognitive memory sidecar. It runs beside an agent's existing memory layers, stores typed memories through an MCP server, and runs periodic dream and reflection cycles from a separate daemon. It is additive only: it does not replace session context or an episodic memory store, and nothing in its setup should change how those systems read and write.

## When to Use
- Installing Clude alongside a memory system that already works.
- Connecting Clude's MCP tools to an agent client.
- Starting, checking or debugging the daemon that runs the dream and reflection cycles.
- Clude reports too few memories for reflection, or no embedding provider is available.

## Features
- A memory-role split that says which layer owns which memory types.
- A local stack: a Postgres-backed store started with the Supabase CLI, the clude-bot MCP server, and a runner for scheduled cycles.
- Configuration for a local OpenAI-compatible model endpoint, with the path-suffix rule that most often breaks it.
- Health probes for the MCP tools, each cycle, the daemon, and the store.
- A documented degrade path when embeddings cannot be installed.

## Benefits
- Existing memory layers keep their behavior, and Clude's failures stay contained.
- Each component is checked on its own, so a broken layer is named.
- Local models can serve the cycles without an external API key.

## Procedure
### 1. Map the memory roles
| Layer | Role | Access |
|---|---|---|
| Session context | Lossless within one session | Automatic |
| Episodic and entity memory | Cross-session recall | Automatic injection through hooks |
| Clude | Procedural, self-model, introspective and semantic memory | Explicit tool calls only |

Clude stores five memory types: `episodic`, `semantic`, `procedural`, `self_model` and `introspective`. Do not point the existing memory layers at Clude, and do not point Clude at their stores.

### 2. Check the ports before starting the store
The local store uses three ports by default: Postgres on 54322, the API on 54321 and the studio on 54323. The Postgres port must not collide with any Postgres already running, such as one on 5432.
```zsh
lsof -i :54322 || echo "port 54322 free"
```

### 3. Start the local store
```zsh
brew install supabase/tap/supabase
supabase start --workdir ~/.clude/supabase
```
Copy the API URL, the anon key and the service key from the start output. Keep them out of shell history and out of logs.

### 4. Install the MCP server package
Node 18 or newer is required.
```zsh
node --version
npm install -g clude-bot
npx clude-bot --version
```

### 5. Write the environment file
Create the environment file with owner-only permissions (mode 600), and use placeholders in any shared copy.
```env
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_ANON_KEY=<anon key from supabase start>
SUPABASE_SERVICE_KEY=<service key from supabase start>   # the variable is SERVICE_KEY, not SERVICE_ROLE_KEY

ANTHROPIC_BASE_URL=<local endpoint, without a /v1 suffix>
ANTHROPIC_API_KEY=<key the local endpoint expects, or a placeholder>
ANTHROPIC_MODEL=<model id the local endpoint serves>
```
- The SDK appends `/v1/messages` itself. A base URL that already ends in `/v1` produces a broken path.
- Some local servers do not check the key on localhost. Test the endpoint anyway, before relying on it:
```zsh
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"<model id>","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
```
The call must return a valid completion. An error page or an empty body means the endpoint is wrong, whatever the key.

Do not edit the installed package's files to make it work. The clude-bot package runs from environment variables alone, and updates do not need local patches.

### 6. Register the MCP server
```yaml
mcp_servers:
  clude-memory:
    command: npx
    args:
      - clude-bot
      - mcp-serve
      - --local
      - --port
      - "3456"
    env:
      DOTENV_PATH: <clude-home>/.env
```
Reload the MCP servers in the client (in Hermes, `/reload_mcp`). Then confirm the tools `store_memory`, `recall_memories`, `get_memory_stats` and `find_clinamen` are listed.

### 7. Run the cycles from a separate runner
The MCP server handles tool calls. Dream and reflection cycles need their own runner, because:
1. The cortex object must run its init call before any operation.
2. A signing key must be read from its file, because the SDK expects its content as a JSON string, not as a path in the environment.
3. Scheduled cycles need jitter, so several processes do not hit the local model at the same moment.

The runner should provide these subcommands:
- `daemon`: dream cycle every 6 hours, reflection cycle every 3 hours.
- `dream --once` and `reflect --once`: single manual runs.
- `test`: a smoke test of both cycles.

Log the daemon's process ID when it starts.

This skill does not cover the optional on-chain anchoring feature. It needs a funded signing key, and it is out of scope for an install guide.

## Pitfalls
- **Missing embedding model.** If the embedding model cannot be pulled, set `EMBEDDING_PROVIDER=none` in the environment file. Clude then scores by keyword and tag. Vector search is off, and every other feature still works.
- **Reflection skips.** The message "Too few memories for reflection — skipping" is a content gate, not a fault. Reflection needs about five episodic and procedural memories. Seeded self-model and procedural memories count, and semantic memories written by dream cycles do not.
- **Hanging one-shot runs.** A one-shot run can finish its work in about 30 seconds and then hang during cleanup until the tool times out. Daemon mode does not show this. Give one-shot runs a generous timeout, and check the output, not the exit.
- **Port conflicts.** Check the port before `supabase start`. If it is taken, stop the other process, or map the store to a different port.
- **Path suffix on the base URL.** A `/v1` suffix in `ANTHROPIC_BASE_URL` is the most common cause of a model call that fails with a path error.

## Verification
- MCP tools: `npx clude-bot recall --query "test" --types procedural` returns a result, not a connection error.
- Dream and reflection: each one-shot run finishes and prints its result or its skip reason.
- Daemon: `ps aux | grep <runner-name> | grep -v grep` shows one live process.
- Store: `curl -s -H "apikey: $SUPABASE_ANON_KEY" "http://127.0.0.1:54321/rest/v1/" | head -c 100` returns a response from the API.

## Attribution
Clude and its MCP package `clude-bot` are public projects. The project homepage is https://clude.io.
