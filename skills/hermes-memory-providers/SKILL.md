---
name: hermes-memory-providers
description: Use when installing or debugging Hermes memory providers. They include Hindsight, Omega, Graphiti, or a bridge across them. Covers the setup wizard, key slots, per-profile isolation, retain and recall proof, and a triage ladder for failed writes.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, memory, hindsight, omega, graphiti, providers, triage]
    category: memory-knowledge
related_skills: [hindsight, triple-threat-memory, graphiti-memory, hermes-profiles]
---

# Hermes Memory Providers

## Overview
A Hermes profile can use one memory provider at a time, and several memory stores can run beside it. The usual failures are quiet. A plugin is installed into an environment that the running process never loaded. A key sits in a slot the provider never reads. A write is acknowledged and never stored. Each of these leaves a status check green while memory does not work. This skill sets the order of checks that finds the real state, the rules for keys and profiles, and a triage ladder for a failed write.

## When to Use
- Installing a memory provider, or switching one between cloud and local mode.
- A write or recall fails, or a tool reports the memory provider unavailable while the status command is green.
- Auditing key and configuration files across profiles for stale keys, wrong ports, or leftover settings.
- Setting up Graphiti's graph database, or Omega's local store, beside the provider.

## Features
- A routing table that says which store answers which kind of question.
- A setup path that uses the product's own wizard, with the constraints the wizard imposes.
- A key-slot model: which environment name each provider reads, and how to prove the effective key.
- A verification ladder that ends in a real retain and recall round trip.
- A six-step triage ladder for failed writes, ordered by how often each cause occurs.

## Benefits
- A green status line is never mistaken for working memory.
- Keys are compared by length and digest, so no secret is printed while the match is still proven.
- Each profile and each device is checked on its own.

## Procedure
### 1. Decide which store answers which question
| Question | Store |
|---|---|
| A durable fact or decision to keep | The main provider (retain); a bridge fans it out if one is installed |
| A fast "do we know X?" | The local store (Omega, when installed) |
| "Is X still true?" (time-sensitive facts) | The graph store (Graphiti, when installed) |
| One query across all stores, resolved for staleness | The bridge's recall tool, when one is installed |

Do not add a memory routing block to the identity file while a provider it names is missing.

### 2. Establish the identity of the machine and the profile
Before changing anything, record the host name, the active profile, and the memory mode each profile is set to. Treat a local daemon as owned by its machine and profile. Do not use another machine's daemon, bank or credentials as a shortcut unless the operator asks for cross-device work.

### 3. Run the product's setup wizard
Use the CLI rather than hand-writing the provider's configuration:
```zsh
hermes -p <profile> memory setup hindsight
```
The wizard's constraints matter:
- Cloud mode needs its API URL typed explicitly. Leaving the URL prompt blank keeps the previous URL, often a local one.
- A blank key prompt does not copy the process environment into the file. The wizard writes the key only when a value is typed.
- The wizard is a curses interface. Piped input is treated as a cancel, and the wizard writes nothing.
- Do not match the words "API key" to detect the key prompt. The mode screen contains the same words, and a secret typed there is shown in the clear. Wait for the prompt line itself.

If the agent runs the wizard itself, drive it over a real terminal session that it controls, and redact the log before saving it. If the operator runs it, give the operator the plain CLI command, and nothing else.

After the wizard, open a new session. A running process keeps the environment it started with.

### 4. Know the key slot the provider reads
A provider reads one environment name. A key stored under another name never reaches it, however correct the key is. Find that name from the provider's documentation or its installed plugin, and check the running process against it.

Three checks, in this order:
1. **File receipt.** Read the key from the profile's environment file in a script. Record its length and a SHA-256 digest truncated to 8 characters.
2. **Override scan.** Check whether an override name for the same profile or host is set in the environment, the secret manager, the configuration file, or a wrapper that starts the process. An empty override set means the file value is the one in use.
3. **Live round trip.** Send a request with the file key, and read the status code. A 200 on retain and recall proves that key works.

Process environment reads are not proof on macOS. The process list strips the environment of other processes, and a loader can inject a value without exporting it. An empty scan is a false negative. If a tool returns 401 while the file key returns 200, the tool path is resolving a different credential. Find which slot the running plugin reads, then fix that slot.

### 5. Verify in this order
1. `hermes memory status` shows the intended provider as available.
2. The profile's configuration shows the intended mode, endpoint and bank, with secrets not printed.
3. For a local daemon, its own status command reports it running under the expected profile.
4. The daemon's log shows the provider connected.
5. A retain of a harmless marker, then a recall of the same marker. A status check alone does not prove extraction or retrieval.

A retain acknowledgement such as "stored successfully" is a queue acknowledgement. Only a recall of the marker proves the write landed.

### 6. Prove a round trip without printing the key
Retain with the marker, then recall with the same marker:
- The retain request body is an object with an `items` array. Each item has `content`, and optionally `tags`, `metadata` and `document_id`. A body with `content` at the top level is rejected with a field-required error.
- Recall returns consolidated text, not the stored string. The consolidation step rewrites the observation, so a marker can come back paraphrased. Match on the marker token anywhere in the results, and do not compare whole strings.
- A broad recall can return many results. Filter the results for the marker.
- Report the status codes and the marker match. Date-stamp any 401 or 403 you cite, so an old failure is not reported as current.

Cloud endpoints for the Hindsight provider, as the vendor's API reference lists them, are `GET /v1/default/banks`, `POST /v1/default/banks/{bank_id}/memories` for retain, and `POST /v1/default/banks/{bank_id}/memories/recall` for recall. Check the live API description before posting, because paths have changed between versions.

### Triage a failed write
Work the ladder from the top. Stop at the first cause that the evidence supports.
1. **Read the error class.** Search the agent log for the failed retain, and note the exact error.
2. **A module-not-found error after an install.** The running process booted before the environment that holds the dependencies was selected. Restart that process. Do not copy packages into the old environment, and do not add a self-healing job that does it.
3. **A "plugin not installed" message.** The plugin was moved out of core, and its install was declined because the start was not interactive. Reinstall the plugin in an interactive terminal, for each profile that uses it.
4. **401 or an invalid-key message.** Run the key checks in step 4.
5. **A tool reports the provider's tools unavailable, while the status command is green.** The platform's toolset list omits the memory toolset. Enable the memory toolset for that platform with the CLI, then start a new session.
6. **Proof.** Retain a marker, read it back by its tag, and report the match.

A failed retain or recall is top priority. Find the cause in the vendor's current documentation, fix it there, and report it with evidence. Do not add a shim, a patch or a watchdog where the documentation names the fix.

### Profiles, devices and attribution
- Each profile needs its own provider plugin. A profile without the plugin silently falls back to built-in memory.
- The provider stamps the profile name on each write, but not the host. Set the retained tags to include the device and the profile in each profile's configuration.
- Worker profiles that should only use memory tools, and never write automatically, set automatic retain to off.
- Copy the profile's configuration, not the root one. A split between root and profile configuration is the most common cause of a profile that behaves differently from the others.

### Local providers and their stores
#### Omega
Omega is a local store built on a SQLite vector extension and an ONNX embedder. Storage needs no cloud key. Its source is at https://github.com/omega-memory/omega-memory. If the extension fails to load, a store and query round trip still works, but only as text match. Do not claim semantic search until a query returns a non-zero similarity with no degraded-search note.

#### Graphiti's graph database
Use a Neo4j server image for Graphiti, not a desktop application. The desktop application is a GUI, and it does not expose the server endpoints Graphiti needs. Run the community image `neo4j:5.26.0-community`, which is in the 5.26 line that Graphiti's driver supports, and publish its ports on the loopback address only (`-p 127.0.0.1:7474:7474 -p 127.0.0.1:7687:7687`). Set the authentication variable with a slash between the user name and the password (`neo4j/<password>`), and meet the server's complexity rules.

Point the client at `127.0.0.1`, not `localhost`. A name lookup can try the IPv6 loopback address first, and a port published only on IPv4 then fails.

If the graph server's HTTP port already answers, do not install another one. Diagnose the client before changing the model provider.

A graph probe that fails in about a millisecond is a connection refusal, not a model error. Start the database first, then look at the model settings.

### Keys, configuration and audits
- Enumerate the keys in a configuration file before reading any field. Entries in a job or configuration file often vary in shape, and a guessed field name produces false findings.
- Classify secret values with length, character class, prefix kind, and a digest of 8 characters for correlating which processes hold the same key. Never echo a character of the value, and never print a `repr` of it.
- Emit a value's length and digest with a script, not with a regular expression over grep output. A greedy pattern can mangle a healthy key, and a stray carriage return changes the length by one.
- Strip matching outer quotes from an environment value before using it in a header. Otherwise the header carries the quotes, and the server returns 401.
- Compare with the live secret manager's revision date, not an operator's memory of a key prefix. Remembered prefixes go stale.
- An LLM provider's extraction settings must agree across all of the provider's slots: retain, consolidate, reflect and default. A partial migration leaves one slot on the old provider. Keep a guard that checks the invariant and alerts on drift.
- Under cloud mode, local model fields in the configuration file are ignored at runtime. Remove them, so that a future reader is not misled.

## Pitfalls
- **Green status, failing writes.** The status command reads the provider's registration, not its last write. Always retain and recall.
- **Stale processes.** A process keeps the environment it booted with. After an install or an environment change, restart the process that needs it, and check which process that is first.
- **Environment files reach a process only at its start.** Editing the file does nothing to a running process. Restart the gateway with its CLI command when the environment has changed.
- **The memory tool is not the provider.** The built-in memory tool writes a local file, so a write that lands there proves nothing about the provider. Remove test markers from the local file afterwards.
- **Subprocesses start with a fresh environment.** A code-execution tool or a delegated worker does not inherit the key. Load the key inside the process that calls the API.
- **Piped setup.** A wizard that is fed input through a pipe cancels, and reports nothing.
- **Recall defaults.** A recall that filters to one memory type can return nothing while the facts are stored under another type. Include the types that durable facts use in the recall settings.
- **Health pollers on the wrong port.** A poller that checks a port the service no longer uses raises a false alarm. Check the port the service actually listens on.
- **Scheduled-job failures are not service failures.** A job can crash in its runner before it starts. Probe the service directly before you pause or blame it.
- **A stale process-info file.** After a reboot, a file that records a process ID can point at an unrelated process the OS reused. Clear the stale record, then restart the service.
- **Deleting a collection.** Deleting a whole bank or collection removes everything in it. Invalidate one memory by its ID, with a reason, instead.
- **Stale lock directories.** A lock left by a finished run can make every later tick skip. Confirm that no owning process is alive before removing the lock.
- **Local daemons that idle-stop.** A daemon can stop after an idle timeout, and a closed port during idle is normal. A probe should send a small request to wake it, then check the health endpoint.

## Verification
- The status command shows the intended provider as available, and a retain of a marker is recalled by its marker.
- Each profile in use has the plugin installed, its own configuration, and the correct retained tags.
- The key check shows the file key matches the digest of the value the running plugin resolves, and the round trip returns 200.
- No key value, token or full secret appears in the report, the log, or the transcript.
- Every slot of the LLM provider points at the same endpoint and model.

## Attribution
Hindsight is a memory system by Vectorize. Its API reference is at https://hindsight.vectorize.io/api-reference. Omega is a public project at https://github.com/omega-memory/omega-memory.
