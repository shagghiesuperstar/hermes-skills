---
name: hindsight
description: Use when storing or retrieving long-term agent memories through the Hindsight memory system, diagnosing its daemon or retain failures, choosing its cloud or local mode, or running a bridge that reads Hindsight and mirrors facts to another store.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hindsight, memory, long-term, daemon, retain, recall]
    category: memory-knowledge
related_skills: [hermes-memory-providers, triple-threat-memory, graphiti-memory, hindsight-coding-agent-cloud-setup]
---

# Hindsight Long-Term Memory

## Overview
Hindsight stores durable agent memories as extracted facts in a bank, and it answers recall queries with consolidated text. It runs as cloud service or as a local daemon in one of two local modes. Its failures are mostly silent. A config file with the wrong name is ignored. A daemon that idle-stops closes its port. A write that is acknowledged can wait in a queue that never drains, because the extraction model behind it is stuck. This skill sets the order of checks for each of these, the rules for the extraction model, and the way to read a bank without duplicating or mistaking stale results for new ones.

## When to Use
- Choosing or changing the mode: cloud, local embedded, or local external.
- Storing or retrieving memories, or checking whether a write landed.
- A retain fails, hangs, or the daemon is down at the start of a session.
- Changing the model that does fact extraction, consolidation or reflection.
- Running a bridge that reads a bank and mirrors new facts to another store.

## Features
- Three modes with a rule for choosing among them.
- A configuration-resolution order, and the file-name trap that disables the provider silently.
- A daemon liveness check, a start procedure, and a warm-up signal to wait for.
- Role-specific model settings, with the base-URL bleed that the global setting causes.
- A retain and recall round trip that accounts for consolidated text.
- A triage ladder for a retain that hangs, with the queue counts that show the cause.

## Benefits
- A failed write is traced to its layer: config, daemon, network, model, or queue.
- A bridge run stays idempotent, and a frozen bank is recognized as the normal steady state.
- Stale results are not mistaken for new ones.

## Procedure
### 1. Choose the mode
| Mode | What it means | Choose it when |
|---|---|---|
| `cloud` | The hosted API, with an API key | The operator wants no local daemon |
| `local_embedded` | The provider starts its own daemon and database | No separate service exists, and the provider should own it |
| `local_external` | The provider connects to a daemon that is already running | A daemon already holds the data you need to keep |

Use `local_external` to keep an existing database. Use `local_embedded` only when no other daemon owns the same database. Two daemons on one database split the data.

Valid values are exactly `cloud`, `local_embedded` and `local_external`. An old alias that a plugin tolerates in one check should not appear in a configuration file.

### 2. Put the configuration in the right file
The file must be named `config.json`. The provider reads it in this order:
1. The profile's own folder, `<hermes-home>/hindsight/config.json`.
2. The shared legacy folder, `~/.hindsight/config.json`.
3. Environment variables. The default mode is `cloud`.

A file with any other name is read by nothing. The provider then falls back to the environment, finds no key, and its tools disappear from the agent's toolset with no other error. If the tools are missing, list the folder and check the file name first.

A shadow copy of the file can sit inside a profile's own home folder. If it disagrees with the real file, back it up, show the operator the diff, and delete it only on the operator's explicit go-ahead for that file.

Under `local_external`, the file names the running daemon's address:
```json
{
  "mode": "local_external",
  "api_url": "http://127.0.0.1:<port>",
  "bank_id": "<bank>",
  "recall_budget": "mid",
  "timeout": 120
}
```
Remove model fields (`llm_provider`, `llm_base_url`, `llm_model`) when the mode is not `local_embedded`. They are ignored in those modes and mislead the next reader.

Change the configuration through the setup wizard when the mode, the provider or the key changes. Hand-editing the mode and hoping the other fields follow leaves the file half-changed.

### 3. Check the daemon before any read or write
The daemon is often down at the start of a session, especially under `local_embedded`, which stops after an idle timeout. Probe first:
```bash
curl -sS --max-time 3 http://127.0.0.1:<port>/health
lsof -nP -iTCP:<port> -sTCP:LISTEN
```
- A healthy response reports `"status":"healthy"` and `"database":"connected"`.
- A connection refused means nothing is bound. Start the daemon.
- A `{"detail":"Not Found"}` response means some other process holds the port. Find that process with the listing command before you start a second daemon.

Start the daemon as a background process that the runtime tracks, not with a shell `&` inside a foreground call, because the shell can reap it when the call ends:
```bash
hindsight-api --host 127.0.0.1 --port <port>
```
Wait for the log line that reports schema migrations completed. That is the readiness signal, not the line that reports the application started. Budget a few seconds of warm-up after it. Until the worker pool reports idle slots, a recall can block. If a recall blocks for more than about 30 seconds, restart the daemon.

The daemon reads its own environment variables when it starts. It does not read the client's configuration file. Without its model variables, it falls back to a default model and endpoint, and every retain then fails with a connection error. Check the variables the running process was started with, and the connections that process holds, rather than the file on disk.

A leftover daemon, or one that failed to start, can hold the port. Stop the leftover processes, remove the stale lock file in the daemon's home folder, and start again. A process that is listed but holds no listening socket is a leftover. Find the owner of the listening socket instead.

Bind the daemon to loopback unless another machine needs it. If a peer must reach it, bind to one private network address, and restrict access with the host firewall. Do not expose it on all interfaces.

### 4. Set the extraction model by role
Hindsight uses a language model for three roles, and each role has its own provider, base URL, key and model variables:

| Role | Variables (prefix `HINDSIGHT_API_`) |
|---|---|
| Retain (fact extraction) | `RETAIN_LLM_PROVIDER`, `RETAIN_LLM_BASE_URL`, `RETAIN_LLM_API_KEY`, `RETAIN_LLM_MODEL` |
| Consolidation | `CONSOLIDATION_LLM_PROVIDER`, `CONSOLIDATION_LLM_BASE_URL`, `CONSOLIDATION_LLM_API_KEY`, `CONSOLIDATION_LLM_MODEL` |
| Reflect | `REFLECT_LLM_PROVIDER`, `REFLECT_LLM_BASE_URL`, `REFLECT_LLM_API_KEY`, `REFLECT_LLM_MODEL` |

Rules for these settings:
- Set each role's base URL explicitly. An unset role variable falls back to the global `HINDSIGHT_API_LLM_BASE_URL`, so an old global value leaks into every role. The result is slow calls to a stale endpoint, not an error.
- Set the base URL for every provider value, including `openrouter` and `openai`.
- Before you apply an environment list from a recipe, confirm each variable name against the installed package.
- A running daemon keeps the environment it booted with. Restart it after a change, then confirm each role's provider in the log.

Before switching a role to a new model, smoke-test it with a structured-output request, for example a prompt that asks for only a JSON object with one key. Then watch the first few retains in the daemon log for warnings about non-object JSON or empty message content. A single such warning means the model is unfit, so revert it. Waiting for the queue to fill and wedge is the slower way to learn the same thing.

Some models wrap JSON in markdown fences, or append a stray brace after it. The parser then retries. Small retry counts are tolerable. A rising retry rate means the model should change, or the response should be cleaned before parsing.

A small embedding model can index text but cannot extract facts. Retain then reports zero facts, and recall is empty, even though the write succeeded. Use an instruct model large enough for extraction in the retain role. A model that refuses structured output reports zero facts on every chunk. Confirm the extraction count in the daemon log. It must be greater than zero.

### 5. Prove a write with a round trip
A retain acknowledgement, such as "stored successfully", is a queue acknowledgement. The write is proven only when a recall returns it.

1. Retain a marker: a short, distinctive token in the content.
2. Recall with the same marker, and filter the results for it.
3. Report both status codes, and whether any 401 or 403 appeared, with its date.

The retain body is an object whose `items` array holds one or more entries. Each entry has `content`, and may have `context`, `tags`, `metadata` (string values only) and `document_id`. A body with `content` at the top level is rejected with a field-required error. The write endpoint is `POST /v1/default/banks/<bank>/memories`.

Recall returns consolidated text. The consolidation step rewrites an observation, so the marker can come back paraphrased, and a whole-string comparison fails on a healthy bank. Match the token anywhere in the returned results, and report the text you actually got.

A recall request ignores its `limit` in some builds, and can return dozens of results. Trim the results in code after parsing them.

A recall response carries an entity graph next to the memory results. Read the results array for memory content, and ignore the entity object when you enumerate.

### 6. Read a bank for a bridge or an audit
Use the REST routes under the bank path. Paths change between versions, so check the live API description before posting: `GET /openapi.json` lists the routes on the running server.
- Banks: list them under `/v1/default/banks`, and confirm the path in the live API description.
- Enumerate memories: `GET /v1/default/banks/<bank>/memories/list?limit=N&offset=N&sort=date&order=desc`
- Semantic sweep: `POST /v1/default/banks/<bank>/memories/recall` with `{"query": "...", "limit": N}`
- Bank statistics: `GET /v1/default/banks/<bank>/stats`
- Operations queue: `GET /v1/default/banks/<bank>/operations?limit=N`. Keep `limit` small, and use a modest page size.

The command-line client can default to a different port from the daemon. Export its URL variable before each use, and check the URL its help footer prints. Its positional arguments are the bank first, then the query.

Choose the sort field with care. The `mentioned_at` field changes every time a memory is recalled, so sorting by it lists the most recently touched memories, not the newest. For recency, sort by `date`, which holds the creation time. A recall ranks by similarity to the query, so a generic query keeps returning the same older cluster. Use the list route for enumeration and recall for coverage.

Recall often returns near-duplicate rows for one fact: a bare version, and one or more versions with a context suffix. Before you compare against another store, strip the suffix and keep the longest variant per fact. Otherwise each duplicate counts as a separate write.

A bridge run that reads a bank and writes to a second store should follow this order:
1. Confirm the daemon answers. If the configured address does not answer, probe the next address on a short list, and use the first that returns healthy. Do not trust a single address stored in a note.
2. Read the newest facts with the list route, sorted by `date`.
3. Check each fact against the second store's search before writing.
4. Filter out what should not be mirrored: counters and one-shot status values that carry no durable meaning, and any entry that holds a credential or personal identifier. Keep decisions, preferences, constraints, completed tasks and durable facts.
5. Write only the facts that are new, and report the counts: written to each store, and skipped.

A bank whose newest fact is weeks old, while the second store already holds everything from it, is frozen. A frozen bank with a high skip count is the correct steady state. Do not search for a fresher read path in that case.

### 7. Triage a retain that hangs
A recall can work while every retain hangs, because reads do not need the extraction model or the worker slots. Do not conclude that the daemon is healthy from a recall alone.

1. Count the operations by status. Pending and processing counts that do not change between runs mean stuck work.
2. Read the daemon's worker log for the pool statistics and any warnings about stuck stages. Slots that are all occupied, with a stage that has been running for minutes, point at the model.
3. Probe the extraction model directly with a small request, with a timeout. A healthy model answers in a second or two. A stream of empty chunks means the model is wedged.
4. Fix the model first, then restart the daemon. The consolidation recovery route retries failed operations but does not free slots held by stuck tasks. Pending operations are stored in the database and resume after a restart.
5. After the restart, watch the pending count drain, then repeat the round trip in step 5.

A retain that fails with a bare error after about two minutes can also be a payload-size limit in the tool that wraps the API, while the API itself is healthy. Test a short payload first. If a long payload fails and a short one succeeds, shorten the entry, split it into several retains that share a context key, or store the full text in a file and retain a pointer to it.

## Pitfalls
- **A file with the wrong name.** The provider reads only `config.json`. Any other name disables the tools with no error.
- **Idle-stopped daemons.** A closed port during idle is normal. Wake the daemon with a small request, then probe.
- **Two daemons on one database.** A second daemon starts on the same data and the two diverge. Use one owner, and point the provider at it.
- **Stale process environments.** A running daemon or gateway keeps the environment it booted with. Restart after changing it.
- **Global model settings leaking into roles.** An unset role base URL falls back to the global value, and calls go to an old endpoint, slowly.
- **Unverified environment recipes.** Look up every variable in the installed package before applying a list from a guide.
- **Trusting an acknowledgement.** A queued write is not a stored write. Recall the marker.
- **Whole-string checks on consolidated text.** Match the token, not the sentence.
- **Shared bank without attribution.** Writes to a shared bank carry no author unless the caller sets it. Several agents writing to one bank then cannot tell whose memories are whose, and they can start to treat another agent's preferences as their own. Attach an agent or profile tag at write time, from a stable per-agent identifier, and filter recall by that tag when an agent needs its own facts.
- **Hard-coded addresses in a bridge.** A single address can be dead on one run and alive on the next. Probe a short list.
- **Writing counters to a semantic store.** Counts and single status values make recall noisy. Filter them before mirroring.
- **Credentials in memory.** An entry that holds a credential or a personal identifier should stay in the store where it was written, and should not be copied to other stores.
- **Reading the environment for proof.** On macOS, another process's environment can be stripped when listed, and a loader can inject a value without exporting it. Prove the effective key with a live request.
- **A memory tool that is not the provider.** The built-in memory tool writes a local file. A write there proves nothing about the provider.
- **An unsupported provider value.** The daemon accepts only the provider names in its own list. Use `openai` for any OpenAI-compatible endpoint. Any other value stops the daemon at startup with an invalid-provider error.
- **Recall that finds nothing for a settled topic.** When recall returns nothing for something the operator treats as settled history, treat the recall as the suspect, not the operator's claim. Search the disk for the project name, and check the daemon log for the extraction count before answering that there is no record.
- **Cloud key precedence.** A key in the profile's configuration file takes precedence over the environment variable of the same name. A secret manager that loads one shared name at every start can overwrite a per-profile key, unless the profile lists that name as preserved. Give each host or profile its own key name, or list the name in the profile's preserve-existing secrets list.
- **Embedded database lifetime.** In embedded mode, the daemon manages its own database process. Stopping that process from outside the daemon is a data-affecting step, so confirm it with the operator first.
- **Containers.** Running the API in a container requires the model endpoint to resolve from inside the container. Use the host gateway alias, and pass each variable explicitly.

## Verification
- The retain response reports non-zero output tokens, and the daemon log shows one or more facts extracted from it.
- The mode is one of the three valid values, and the configuration file has the right name and sits in the profile's folder.
- The daemon answers the health probe on the port its configuration names, and `lsof` shows that same port bound by the expected process.
- Each extraction role reports its provider and base URL in the daemon log after a restart, and the structured-output smoke test passes.
- A marker retained in one call is recalled in the next, with the status codes recorded.
- A bridge run reports how many facts it wrote to each store and how many it skipped, and the skipped facts were confirmed present in the target store.

## Attribution
Hindsight is a memory system by Vectorize. Its API reference is at https://hindsight.vectorize.io/api-reference, and its API key documentation is at https://docs.hindsight.vectorize.io/api-keys/. The Python client is published as `hindsight-client`.
