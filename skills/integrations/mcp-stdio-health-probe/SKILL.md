---
name: mcp-stdio-health-probe
description: Use when probing a stdio MCP server that has no client set up. Covers the handshake, the tool list, evidence records and the silent-server case.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [mcp, stdio, json-rpc, probe, health-check, verification]
    category: integrations
related_skills: [mcp-client-setup, mcp-server-authoring]
---

# Probe a stdio MCP Server

## Overview
A stdio MCP server talks JSON-RPC over its standard input and output, not over a network port. To find out whether such a
server is up and what it exposes, you can spawn it as a child process, send the handshake messages, and read the replies.
This is a one-off check for verification or an audit record. It does not register the server with a profile. For
long-running use, register the server through the MCP client setup instead.

## When to Use
- You want to confirm that a binary's stdio MCP mode works before you configure it.
- You need the current tool list as evidence, for an audit or a regression report.
- A server is reported as broken, and you need to know whether its handshake still answers.

Do not use this for an HTTP or server-sent-events server, which needs its own request framing. Do not use it for a
server that a profile already runs; read its entry with the list command instead.

## Features
- Process-level probe that spawns the server with pipes on both sides.
- Three-message handshake: initialize, the initialized notification, and the tool list.
- Bounded waits, so a silent server ends the probe instead of hanging it.
- Evidence record with the time zone, host, binary path, protocol version, server name, tool count and verdict.
- Clear verdicts: pass, fail, or inconclusive when the server stays silent.

## Benefits
- A server's handshake is proven without touching the profile's config or restarting anything.
- A silent server is recorded as inconclusive, not guessed at.
- The record can be checked later against the same fields.

## Procedure
1. Read the server's help before you start it. Look for a flag that describes a stdio or JSON-RPC mode. A port option that
   belongs to a different service does not mean the server listens on that port. Expect no network listener from a
   stdio server, so an empty port check proves nothing.

2. Run the probe. Save this helper as a file, and call `probe` with the command as a list of arguments:
   ```python
   import json, select, subprocess, time

   def send(proc, msg):
       proc.stdin.write(json.dumps(msg) + "\n")
       proc.stdin.flush()

   def read_frame(proc, timeout=10.0):
       deadline = time.time() + timeout
       while time.time() < deadline:
           if select.select([proc.stdout], [], [], 0.5)[0]:
               line = proc.stdout.readline().strip()
               if line.startswith("{"):
                   return json.loads(line)
       return None

   def probe(argv):
       proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
       try:
           send(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
               "protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "probe", "version": "0"}}})
           init = read_frame(proc)
           send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
           send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
           return init, read_frame(proc)
       finally:
           proc.kill()
           proc.wait()
   ```
   Run it with `probe(["<server-binary>", "<mode-flag>"])`. The first result is the initialize reply, and the second is the
   tool list. Either can be `None`, which means the server did not answer within the wait.

3. Read the results. The initialize reply must carry a protocol version and server information. The tool list must carry a
   non-empty list of tools, each with a name and an input schema. Take the names from that list. Do not write a tool list
   from the documentation.

4. Optionally call one read-only tool, such as a listing or a status tool that takes no arguments. Send a `tools/call`
   request with the tool name and its arguments, and read one reply. Use a longer wait for a tool that does real work.

5. Write the evidence record. Append one block to an evidence file at an absolute path. Include:
   - the time with its time zone, and the host name;
   - the binary's absolute path and its version;
   - the protocol version and the server name from the initialize reply;
   - the tool count and the tool names;
   - the result of the optional call;
   - the verdict.

6. Give the verdict. Pass means the handshake and the tool list both answered. Fail means an error reply or a wrong
   reply. Inconclusive means the server stayed silent after the handshake, so the record should say that and nothing else.

### Silent servers
Some servers accept the connection and then send nothing back, with no error and no output. When that happens:
- Record the symptoms: the exit state, the byte counts on both output streams, and the time waited.
- Mark the probe inconclusive.
- Stop. Do not try a series of different messages to guess the expected format. Report the case, and let the operator decide
  whether to change the server's setup.

Some servers also need a one-time permission on the host before they answer. Ask the operator to approve and perform any
such step. Do not change a system's automation or permission settings yourself.

## Pitfalls
- **A stdio server opens no network port.** An empty port check is normal, so it does not mean the server failed.
- **A notification has no ID and gets no reply.** Send the initialized notification and move on at once. Waiting for a reply hangs the probe.
- **Send the initialized notification before the tool list.** A strict server rejects other requests until it has seen it.
- **Read frames by line.** The protocol is one JSON object per line. A single read can return several lines.
- **Read from the server's output, write to its input.** Reversed pipes make the server see end-of-file and exit at once.
- **A ready message in the logs is not a reply.** Wait for a JSON frame on the output stream.
- **Stop the child process.** A probe that leaves the server running can hold a session open and break the next start.
- **Do not paraphrase the tool list.** If the server did not answer, the list is unknown, and the record says so.
- **Use absolute paths in the evidence file.** A relative path resolves to whatever folder the caller happens to be in.
- **Check for an earlier record before you append.** A repeated run should not write the same time stamp twice.

## Verification
- The initialize reply carries the protocol version and the server name.
- The tool list is non-empty, and every name in the record appears in the reply.
- The evidence file has one new block with the time zone, the path and the verdict.
- No server process from the probe remains after the run.
