---
name: graphiti-memory
description: Use when diagnosing or fixing Graphiti MCP timeouts, CancelledError hangs, Neo4j connection-pool pressure, MCP keepalive drops, or a Graphiti write that fails with missing credentials. Covers the tuning ladder and the event-loop and embedder traps.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [graphiti, neo4j, mcp, memory, timeouts, connection-pool]
    category: memory-knowledge
related_skills: [triple-threat-memory, memory-stack-snapshot, hindsight]
---

# Graphiti Memory: Diagnosis and Tuning

## Overview
Graphiti is a temporal knowledge-graph memory that stores its data in Neo4j and is often reached through an MCP server. Its common failures look alike from the agent's side: a call hangs past a minute, a task is cancelled at a fixed timeout, or a write is silently skipped. The causes differ, and each has a different fix. This skill sets the order for diagnosing them, the tuning ladder from the lowest-risk change upward, and the traps that the upstream documentation does not warn about.

## When to Use
- The Graphiti MCP tool returns a cancellation error or hangs for more than about 60 seconds.
- The Neo4j log shows bolt connector or pool errors.
- A scheduled memory-bridge job retries without reporting why.
- An operator asks to raise a timeout, a pool size or a job's cadence.
- A Graphiti write fails with a message about missing credentials, while the rest of the system works.

## Features
- A health check of the Neo4j listeners and the HTTP query endpoint, before any tuning.
- A check of the server's live configuration, so no key name is guessed.
- A four-step fix ladder ordered by blast radius.
- An explicit embedder argument for Graphiti when the default embedder needs a provider key you do not use.
- A driver-result access note for ad-hoc queries.

## Benefits
- Tuning starts from the live configuration, not from a remembered key name.
- Low-risk fixes come first, so restarts and code changes are a last resort.
- Silent skips show up in logs, instead of looking like success.

## Procedure
### 1. Record the failure
Write down the timestamp, the exact error text (cancellation, bolt error, or authentication), and what triggered the call: a scheduled job, a new session, or an agent request.

### 2. Check Neo4j health
Check both listeners, then run a trivial query over the HTTP query endpoint:
```bash
nc -z 127.0.0.1 7687 && echo "bolt UP" || echo "bolt DOWN"
nc -z 127.0.0.1 7474 && echo "http UP" || echo "http DOWN"
curl -s --netrc-file <netrc-file> \
  -X POST http://127.0.0.1:7474/db/neo4j/query/v2 \
  -H "Content-Type: application/json" \
  -d '{"statement": "RETURN 1 AS n"}'
```
Read the password from the secret store that holds it, and write it into the netrc file, which must be readable only by you. The netrc file has a `machine 127.0.0.1` entry with the login and the password. Do not put the password in a script, on a command line, or in a shared note.

### 3. Read the live pool and timeout settings
Query the server's configuration, and only then pick a setting name:
```bash
curl -s --netrc-file <netrc-file> \
  -X POST http://127.0.0.1:7474/db/neo4j/query/v2 \
  -H "Content-Type: application/json" \
  -d '{"statement": "CALL dbms.listConfig() YIELD name, value WHERE name CONTAINS \"pool\" RETURN name, value"}'
```
Use a name exactly as the server returns it. On Neo4j 2026.05.0, the server-side bolt connection-pool setting does not exist. Older guides still list it, and setting it makes the server refuse to start. Revert any configuration file you changed, from its backup.

Read the MCP client's timeout settings from the profile's configuration file, with a parser rather than a text search.

### 4. Find other writers on the same schedule
List the scheduled jobs whose names mention memory, Graphiti or the other memory layers. Several jobs that run every few minutes on the same quarter-hour all open pool connections at once.

### 5. Apply the fix ladder, lowest blast radius first
1. **Stagger the schedules.** Move competing jobs to different minutes in the scheduler's file. Back up the file first, and change only the schedule expression. The scheduler picks up the change on its next tick, so no restart is needed.
2. **Raise the MCP connect timeout.** Increase the client-side connect timeout in the profile's MCP entry. The MCP server reads it when the gateway spawns it, so the gateway must respawn the server. Restart the gateway through its own service manager, not by killing a process ID in a shell.
3. **Lower in-process concurrency.** Reduce the Graphiti semaphore limit, which sets how many tasks in one process compete for pool connections. A high limit against a rate-limited model provider also causes 429 errors, so lower it there too.
4. **Raise the client-side driver pool.** The starving pool is the client driver's, not the server's. The Neo4j Python driver defaults to a pool of 100 connections and a 60-second acquisition timeout. Raise them where the driver is constructed, for example with `max_connection_pool_size` and `connection_acquisition_timeout`. If the Graphiti library's factory builds the driver, patch that factory, because no configuration file exposes the value.
5. **Change the server's asyncio timeout in code.** This is the highest blast radius. Edit only after the steps above, with a backup and a test run, because the timeout is not exposed in any configuration file.

### 6. Check the event loop before blaming the pool
Graphiti's async driver binds its sockets to the event loop that created them. Two patterns fail in different callers:
- Calling `asyncio.run()` for each call fails on the second call with an "attached to a different loop" error.
- Running a persistent loop with `run_until_complete` on the caller's thread works from a plain script, but fails inside a server whose tools run on a loop-owning thread, with "cannot run the event loop while another loop is running".

A pattern that works from every caller: one persistent loop on a dedicated daemon thread, with each coroutine submitted by `asyncio.run_coroutine_threadsafe(coro, loop).result(timeout)`.

### 7. Pass the embedder explicitly
The Graphiti constructor falls back to a default embedder when the embedder argument is empty. That fallback needs an OpenAI key in the environment, and it fails with "Missing credentials" when the system uses a different model provider. Check each of these:
- Pass `llm_client`, `embedder` and `cross_encoder` explicitly. When the LLM provider is routed through an OpenAI-compatible endpoint, the default embedder cannot use that provider's credentials.
- Use a local embedder class that implements the same embed call, when no embedding endpoint is available from the provider.
- Check that the environment file does not set the key to an empty string. An empty value counts as set, so the fallback runs.
- If the environment is loaded in a parent shell and used in a child process, the variables may not reach the child. Load them in the process that builds the client.

### 8. Log silent skips at warning level
Code that skips Graphiti after an error must log that skip at warning level, not debug level. A skip logged at debug level hides the fact that a memory server is running without its graph store. Log the skip at warning level, so that the per-source result list shows the gap.

### Fix reference
| Symptom | Likely cause | Action |
|---|---|---|
| Cancellation at exactly the connect timeout | Pool starved, or timeout too short | Steps 5.1 to 5.4 |
| Server refuses to start after a configuration edit | Setting name not valid on this server version | Revert the file, then use names from step 3 only |
| Bolt port not listening | Still booting (allow 30 to 90 seconds), or a configuration error | Read the server log |
| Service fails to start with an I/O error from the service manager | A bootstrap race from an earlier failed start | Stop the service, wait a few seconds, start it again |
| MCP process not running | Normal: the gateway starts it on first use | Call the tool again |
| Authentication failure on bolt | Wrong password | Read the password from the secret store |
| 429 from the model provider | Concurrency above the provider's tier | Lower the semaphore limit |

### Neo4j driver result access
Driver records may not support key access on every version. A numeric index always works, and converting the record to a plain dictionary first is the safest form:
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "<password>"))
with driver.session() as s:
    result = s.run("MATCH (e:Episodic) RETURN e.group_id AS gid, count(*) AS c")
    for record in result:
        r = dict(record)
        print(r["gid"], r["c"])
```

## Pitfalls
- **Guessed configuration names.** A name taken from an old guide can be removed in a new server version. Read the names from the live server.
- **Pool fixes that do not reach the process.** A pool setting in the server's file does nothing for a starved client pool.
- **Restarts by process ID.** The supervisor starts the process again, so a kill is not a restart.
- **Staggering without measuring.** Schedules that overlap at the same quarter-hour are the cheapest thing to fix, so fix them first, then measure.

## Verification
- Both Neo4j listeners answer, and the query endpoint returns the trivial result.
- The live pool and timeout settings were read from the server, and each changed setting is listed with its old and new value.
- A test call through the MCP tool completes inside the new timeout.
- The scheduled jobs no longer share a minute.

## Attribution
Graphiti is an open-source project by Zep. Its MCP server documentation is at https://github.com/getzep/graphiti/blob/main/mcp_server/README.md, and its example configuration is at https://github.com/getzep/graphiti/blob/main/mcp_server/config/config.yaml. The Neo4j connector settings reference is at https://neo4j.com/docs/operations-manual/current/configuration/connectors/. Treat the upstream examples as a starting point, and check each setting name against the live server.
