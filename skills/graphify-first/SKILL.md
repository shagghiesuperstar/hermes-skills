---
name: graphify-first
description: Use when starting any coding or repository task. Query the code-graph server for the touched area before reading repository files, check freshness, and if the graph is unreachable or stale, say so and continue.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [code-graph, mcp, repository, discovery, blast-radius, freshness]
    category: agent-discipline
related_skills: [mcp-stdio-health-probe, minimal-change-operator, source-grounded-investigation]
---

# Graphify First

## Overview
Before reading repository files for a coding task, query a code-graph server for the area you will touch. One graph lookup returns the relevant symbols, their source paths and their callers, which replaces many search and read round trips. A graph is a snapshot, so each use checks freshness. If the server is unreachable or stale, the work continues with normal reading, and the handoff says so. The graph never blocks the work.

## When to Use
- Starting a coding task or a repository change, when the code area is not already known.
- Before changing a shared helper, component or module, to see what depends on it.
- When asked how two parts of a codebase connect.
- When a code-graph server appears in the tool list, for example an MCP server that exposes query tools.

Skip the graph for a task that only probes a deployed site and reads no repository code.

## Features
- A four-call sequence: find the area, get node details, check the blast radius, and trace a path.
- A freshness check that compares the file's last change with the index time.
- Explicit handling of stale and unreachable graphs, with wording for the handoff.
- A project-path rule for graphs that hold several repositories, so results stay within one repository.
- A reminder that the graph points to files, and the files still need reading and testing.

## Benefits
- Fewer blind searches, and fewer files opened.
- The blast radius of a shared change is checked before the change.
- A stale or unreachable graph is reported, not trusted silently.

## Procedure
### 1. Confirm the server is up
Call the graph-statistics tool first. It is the cheapest reachability and sanity check. If the graph tools are not in the tool list, load them through the tool-search mechanism your client provides, then call them. Do not guess argument names: read the tool's schema first.

### 2. Find the area
Run the query tool with a plain question in the vocabulary of the code. Start with a broad breadth-first search, then narrow it. Set a token budget. If the output reports truncation, raise the budget or narrow the filter. Do not paste the whole result into the context.

### 3. Get details for each candidate
Use the node-details tool for a symbol or file from step 2. Read its source path, line and module. The same label can exist in two apps or packages, so read the source path before editing anything.

### 4. Check the blast radius
Before changing a symbol, use the neighbors tool. It lists callers, callees and imports. Read each caller the change could break.

### 5. Trace a path when needed
Use the shortest-path tool to explain how two symbols connect, for example why a UI change reaches a backend service.

### 6. Pass the project path on every call
In a graph that holds several repositories, pass the path of the repository the task touches. Without it, results mix repositories, and a query can return symbols from another project with no warning. A "file not found" error on the path argument means the path is wrong. It does not mean the repository is unindexed.

### 7. Check freshness once per task
The graph is a snapshot. For the file you will edit:
1. Read the file's last change time from version control.
2. Compare it with the index time for that repository, if the server reports one.
3. If the file changed after the index, or an expected symbol is missing, the graph is stale for that area. Use it only as a pointer, read the file itself, and write `graphify: stale (indexed <date>, file changed <date>)` in the handoff.

If the server does not report an index time, write that freshness could not be checked.

### 8. Handle outages without stalling
Symptoms include a tool-call timeout, a refused connection, a missing tool, or a server that gave up after repeated reconnect attempts.
- Retry once.
- If it still fails, continue with normal repository reading.
- Write `graphify: unreachable (<error>, <time>)` in the handoff.
- Do not repair the server from inside the task. Reporting the outage is the alert.

### 9. Report what the graph contributed
Quote the three to five relevant nodes, with their labels and source paths. Do not paste the full dump.

### Serve and verify a graph endpoint
When the task is to start or check a graph server, rather than use one:
- Probe the endpoint with an initialize request. A valid server-info result shows the server is serving. A TCP connect does not.
- Send the initialized notification with the session header from the initialize response, then request the tool list and count the tools. The count is the acceptance check.
- Confirm the bind address with a listening-socket listing on the server. Bind to a private network interface, not to all interfaces.
- A request by host name can fail with an invalid-host error. Send the matching host header, or use the address the server binds to.
- A 4xx status on the endpoint shows the port is live. It is not a health check. Confirm with the handshake.
- Compare the endpoint URL in every client profile that uses the server. A stale URL in one profile breaks only that profile.
- Back up the client configuration before editing it. Read the file back after each edit, because a tool can report success without writing.

### Build or rebuild a graph
1. Orient from disk. Read the corpus root, the repository list and the newest build log before answering a status question.
2. Keep provider keys in the operating system keychain or a secret manager. Verify a key exists with a metadata lookup on its service name. Never print the value, and never write it to a log or into a remote URL.
3. A password read can fail in a headless session even when the key is valid. Check the item's metadata first. A successful build that used the key is evidence the key works.
4. Non-interactive HTTPS pulls fail without a credential helper. Set one up before a scheduled build. A failed pull can leave a repository with no graph for that run, so check the log for pull failures before diagnosing extraction.
5. Semantic extraction is billed per file and is partial by design. Rerun to retry files that produced no nodes. Use a partial-overwrite override only on purpose.
6. Report each build step as done, blocked or not started, with the artifact that proves it: a file and time, a log line, or a node count.

## Pitfalls
- **Same label, two apps.** A label such as a component name can exist in more than one package. Read the source path before editing.
- **Stub nodes.** External-library stubs have no source path. Ignore them.
- **A pointer, not a proof.** The graph shows where to look. It does not replace reading the file before an edit, or running the tests.
- **Keyword search, not meaning search.** Many graph queries match words in the code. Phrase questions with the names that appear in the source.
- **Parameter names differ.** One server may take a question argument, another a query argument. Read the schema.
- **Compliance by token ping.** A single trivial call at the end does not count. Make one real query on the touched area before editing.

## Verification
- Graph statistics or a handshake was observed before the first query, or the outage was written in the handoff.
- Each graph-derived claim is backed by a node's label and source path, and the file was read before editing.
- The freshness result is in the handoff: fresh, stale with dates, or not checkable.
- Every blast-radius check lists the callers that were read.
