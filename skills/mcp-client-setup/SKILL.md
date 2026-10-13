---
name: mcp-client-setup
description: Use when connecting an MCP server to a Hermes profile. The profile uses the server as a client. Covers pre-flight probes, the config block, the session boundary and smoke tests.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [mcp, hermes, config, client, setup, troubleshooting]
    category: integrations
related_skills: [mcp-server-authoring, tinyfish-cli]
---

# MCP Client Setup

## Overview
Connecting an external Model Context Protocol server to a Hermes profile is four steps: discover the server, authorize
the connection, verify the configuration, and start a new session so the tools load. The protocol is simple. The
difficulty is in the details: the add wizard prompts even for an open server, tools added in the current session do not
appear until a session boundary, the config key has an exact name, and tokens must not sit in the config file. This
skill covers those steps and the failures they cause. To build a server rather than connect to one, use the server
authoring skill instead.

## When to Use
- You want a profile to use an MCP server's tools.
- A server shows as disabled, or its tools never appear in a session.
- An OAuth-based server reports that it needs re-authentication.
- You are moving an MCP entry to another profile or another machine.

## Features
- Pre-flight probe of the health, the handshake and the tool list before any config change.
- Interactive add command, with the tool choices made by the operator.
- Config block shapes for an HTTP server and a command-launched server.
- Session-boundary rule, so the new tools are used in a session that starts after the change.
- Smoke test that calls one simple tool.
- Troubleshooting for disabled entries, host-header rejections, and silent launch failures.

## Benefits
- A server is proven reachable before the config changes.
- Tools are used only after the session that loads them starts.
- Tokens stay in the environment file, not in version-controlled config.
- Each failure is traced to one layer.

## Procedure
1. Probe the server before you add it. Check that it answers, that the protocol handshake works, and that the tool list
   returns:
   ```bash
   curl -sS -m 5 http://<host>:<port>/health
   curl -sS -m 5 -X POST http://<host>:<port>/mcp \
     -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"preflight","version":"0"}}}'
   ```
   A 401 or 403 means the server needs a credential. Gather it first. A 404 on the path may mean a different path, so try
   the other common path names before you call the address dead. A successful answer on a neighboring port is not proof:
   confirm the server name in the handshake answer.

2. Add the server with the add command, and answer the wizard yourself. The wizard asks whether the server needs
   authentication, then whether to enable all of its tools. Do not script the answers. Enable only the tools the task
   needs:
   ```bash
   hermes mcp add <name> --url http://<host>:<port>/mcp
   ```
   The success line reports how many tools were enabled. If that count differs from the tools you chose, re-run the add
   command and choose the tools explicitly.

   For a server that needs a credential, pass `--auth header` or `--auth oauth`, or choose the option in the wizard. Do not write a token
   into the config file.

3. Check the config block. The key is `mcp_servers`, in the plural, with snake case. Confirm it with the list command:
   ```bash
   hermes mcp list
   hermes -p <profile> config show | grep -B1 -A4 "mcp_servers:"
   ```
   An HTTP entry has a URL and an enabled flag. A command-launched entry has a command, an argument list, and an
   environment map. Environment values reference names in the profile's environment file, such as `${VAR}`.

4. Start a new session. Tools added or changed in a session do not appear in that session, because the set of tools is
   fixed at session start. Use the reset command in chat, restart the gateway from an operator shell, or relaunch the
   command-line client. Do not call a new tool in the same turn that changed the config.

5. Smoke-test one simple tool. Choose a tool that takes no arguments, or returns a fixed value. A successful result
   proves that the server is reachable from inside Hermes, the credential was passed, and the response parsed. If the tool
   is not found, the wizard enabled a different set than expected. List the entries and add again with explicit choices.

### Config Shapes
Command-launched server, with credentials in the environment file:
```yaml
mcp_servers:
  <name>:
    command: npx
    args:
      - '<package-name>'
    env:
      <API_TOKEN_NAME>: ${<API_TOKEN_NAME>}
```
- The command must be on the path, or be an absolute path.
- Credentials belong in the profile's environment file as placeholders. Hermes fills them in at startup.

Network server:
```yaml
mcp_servers:
  <name>:
    url: http://<host>:<port>/mcp
    enabled: true
```
Bind a network server to an address the clients can reach, and point clients at that address. Do not expose it on a wider
interface than its clients need.

### Troubleshooting

### The entry shows as disabled after an edit
1. Check the transport and the values in the list output against what you wrote.
2. For a command entry, run the same command by hand with the same environment values. If it fails, the server will not load.
3. For a network entry, probe the address. A timeout means the server is not listening there.
4. Read the gateway log for lines that mention the server.
5. Restart and wait a few seconds before you re-check. Discovery runs asynchronously.

### The network server rejects the request with a host error
The server accepts only the host names it was configured for. Point the client at the address the server expects, and
set the server's allowed hosts to include that name. Do not work around the host check by changing the request's host
header.

### A command entry starts and then fails silently
1. Run the command by hand with the environment variables the entry sets.
2. Install the missing package if the command reports one.
3. Check that each credential placeholder resolves to a real value in the environment file or the host environment.

### Tokens and secrets
Do not put a bearer token in the config file. Config files end up in version control, backups and error logs. Use the
environment file with restricted permissions, or the header option of the add wizard. Never print a token to confirm it is set.

### Re-authentication prompts for an OAuth server
An OAuth server can expire and show a re-authentication notice in a packaged desktop app. Check each enabled server with
the list and test commands, and check that the server's sidecar is running. For a browser login, the operator completes
the browser step. Do not start a browser login from a non-interactive session. After a successful login, restart the desktop
app fully, because a session reset alone does not clear its notice.

### Writing to the wrong profile
A bare add command writes to the active profile. Check the active profile before you add, and check the profile path in the
output.

## Pitfalls
- **Tools added in this turn do not work in this turn.** Tell the operator about the session boundary in the same reply that
  changes the config.
- **The config key is plural.** A block written under a singular or camel-case key is ignored without an error.
- **Probing a candidate URL is not the same as testing an entry.** The list and test commands only check configured entries.
- **Do not put a token in the config file.** Use the environment file or the header option.
- **A server that is up can still be disabled.** Check the enabled flag and the credential placeholders.

## Verification
- The probe returns the handshake answer and the tool list before the config changes.
- The list command shows the entry as enabled with the expected number of tools.
- A new session shows the new tools, and the smoke test returns a result.
- The config file contains no token value.
