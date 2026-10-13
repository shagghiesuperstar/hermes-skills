---
name: aperture
description: Use when attaching an agent to Tailscale Aperture. Aperture is a gateway. Covers MCP connector setup, least-privilege grants, and tailnet-only inference routing.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [aperture, tailscale, mcp, tailnet, inference]
    category: fleet-infrastructure
related_skills: [macos-remote-access, tailscale-fleet-macos, darkbloom-provider]
---

# Tailscale Aperture Gateway

## Overview
Aperture is Tailscale's AI gateway. It runs on the tailnet, exposes an MCP endpoint that agents can attach to, and can route model traffic between tailnet nodes using Tailscale identity instead of API keys. Its built-in connectors are enabled on the gateway itself, not installed from an agent's catalog, so the agent sees them only after they are enabled, granted, and re-discovered. Keep the gateway tailnet-only and grant each connector narrowly.

## When to Use
- You want an agent to use Aperture's MCP endpoint, including the Tailnet and TailnetSSH connectors.
- You are serving local models to other tailnet nodes through a gateway.
- You are setting default tool permissions or provisioning nodes through Aperture.

Do not use it for ordinary SSH from a person (use `tailscale ssh` directly), and do not treat the gateway as the live model router until you have confirmed it routes your traffic.

## Features
- MCP attachment that checks the gateway, lists tools, and confirms the expected connector tools appear.
- Connector setup for node provisioning and SSH-enabled machine listing, with the admin steps kept separate from the agent steps.
- Least-privilege grants by connector ID rather than broad labels.
- A future-state pattern for sharing one node's local model with other tailnet nodes.
- Verification by listing models, listing tools, and running a single test completion.

## Benefits
- Agents reach tailnet machines through one audited gateway instead of per-machine credentials.
- Identity comes from the tailnet, so clients need no API keys for the gateway.
- Scoped grants keep a compromised agent from reaching every connector.
- Each step has a clear pass condition, so a half-finished setup is easy to spot.

## Procedure
1. Confirm the gateway answers and the agent can see it. The MCP test must report connected and list at least one tool:
   ```zsh
   hermes mcp test aperture
   ```
2. If the server is not configured yet, add it. Use the gateway's MCP URL, and answer the authentication prompt honestly. Choose no authentication only when the gateway is tailnet-only and the MCP endpoint is documented as such. Review the tool list before enabling any tool:
   ```zsh
   hermes mcp add aperture --url "http://<gateway-host>/v1/mcp" --connect-timeout 25
   hermes mcp list
   ```
3. Start a new agent session after changing MCP servers. Tools discovered in an existing session may not appear.
4. Enable connectors in the gateway's admin interface, which is an operator task. Two connectors exist:
   - **Tailnet** provisions a node with a single-use auth key approved in a browser. It needs an OAuth application with the auth-key creation scope, and the approval step needs a human.
   - **TailnetSSH** lists SSH-enabled machines and runs one command per call as the gateway's node. It needs no extra credential.
5. Grant access by connector ID rather than by the system label. The system label covers only the built-in web connector:
   ```json
   { "connectors": ["Tailnet/**", "TailnetSSH/**"] }
   ```
6. Re-run the MCP test after the grants. Expected additional tools include the Tailnet provisioning tool and the TailnetSSH list and run tools. Call the machine-list tool once and confirm it returns a table or an explicit empty state.
7. (Future state, only with the operator's approval) Share a local model with other tailnet nodes. Serve the model on a loopback or tailnet-only endpoint, add it to the gateway as an OpenAI-compatible provider with its base URL and model list, and point other clients at the gateway. Clients authenticate by tailnet identity. Verify with a one-token completion from a second node and confirm the request shows up in the gateway's usage view.

## Pitfalls
- **Use the documented gateway address.** Use the address in the official Tailscale Aperture documentation, not a guessed hostname.
- **Connector tools are not catalog entries.** They live on the gateway. Do not install an unrelated community MCP server as a substitute for a vendor connector without reviewing its code and permissions first.
- **Answer the MCP add prompts yourself.** Scripting the answers to an interactive prompt skips the review step. Run the command interactively and read each prompt.
- **A bare curl to the MCP endpoint hangs.** The endpoint streams over server-sent events, so a curl without a timeout waits forever. Use the MCP test command, or a curl with `--max-time`.
- **Each `run_command` call is a fresh SSH session.** No working directory or environment carries over between calls. Grant the command tool narrowly.
- **Node provisioning needs a human at the approval link.** The agent can collect the key only after the operator approves it, and the approval has a short expiry.
- **Keep the gateway off public exposure.** Do not enable public funnels for the gateway. It is designed for tailnet use.

## Verification
- `hermes mcp list` shows the gateway enabled.
- `hermes mcp test aperture` connects and lists tools, including the connector tools after the grants.
- `GET <gateway-host>/v1/models` returns a JSON list. An empty list means the gateway is up with no models configured.
- A single machine-list call through the MCP endpoint returns the SSH-enabled machines, or an explicit empty state.

## Attribution
- Tailscale Aperture documentation: https://tailscale.com/docs/aperture/
- Tailscale Aperture general availability announcement: https://tailscale.com/blog/aperture-ga
