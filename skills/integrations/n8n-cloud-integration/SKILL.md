---
name: n8n-cloud-integration
description: Use when connecting an agent to an n8n Cloud instance through its instance-level MCP server. Covers OAuth, tool whitelists, the fixture-proof gate and human approval for publishing or executing.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [n8n, mcp, workflows, oauth, automation, integrations]
    category: integrations
related_skills: [mcp-client-setup, chat-safe-secret-staging]
---

# n8n Cloud Integration

## Overview
n8n Cloud can expose its workflows to an agent through an instance-level MCP server. The agent can search, build, edit,
test and run workflows, while n8n keeps the scheduling, data transforms, retries and routing. The division of labor
matters. The agent handles judgment, state and exceptions. Deterministic steps stay in the workflows. This skill covers
the prerequisites, the hard rules, the wiring, a fixture-based proof that the connection works, and the approval boundary
for changes that reach production.

The vendor's current documentation for instance-level MCP is the authority on tool names, version gates and OAuth details.
Check it before you wire anything.

## When to Use
- The operator has an n8n Cloud instance and wants an agent to inspect, build or run workflows.
- A workflow needs deterministic retries, schedules or transforms that should not depend on a model.
- You are checking whether an n8n connection that someone reported as "connected" really works.

Do not use this for a self-hosted n8n instance, which needs its own setup. Do not use it when a single tool call or a
single webhook is enough.

## Features
- Prerequisites with the version gates the instance needs for each capability.
- OAuth wiring, with the token kept out of the configuration file and out of chat.
- Tool whitelist that exposes read and build tools first, and holds publish and execute tools back.
- Fixture-proof gate: create, test, diff and retire a harmless workflow to prove the wiring.
- Approval boundary for publishing, executing and archiving production workflows.
- Pitfall list with the failure signatures that look like success.

## Benefits
- The connection is proven with a fixture before anyone relies on it.
- Production workflows run only after a person approves them.
- Credentials never appear in the configuration file or in logs.
- A claim that a connection works is checked against a real result.

## Procedure
### Prerequisites
1. Confirm the instance URL and that the plan includes instance-level MCP access. Enable it in the instance settings, and
   choose OAuth as the sign-in method.
2. Check the instance version against the capability you need. Creating and editing workflows through MCP, per-client
   connection setup, and automatic exposure of new workflows each have a minimum version. Pin to the current stable release
   when unsure.
3. Make each workflow available to MCP on purpose. A search result that lists a workflow is not access to read, change or
   run it.

### Rules before wiring
- **Access is per workflow.** Full read, modify and execute access requires that each workflow is marked as available to MCP.
- **Use OAuth.** Do not place an API key in the configuration. Use the sign-in flow, which stores its token in a
  profile-protected file.
- **The agent is an MCP client.** An MCP server trigger node inside a workflow is a different feature, and it does not
  replace instance-level MCP.
- **Treat every MCP-exposed workflow as a security boundary.** A workflow that handles personal data or secrets should be
  hardened before it is exposed, and its results can be read through MCP.
- **Do not trust a tool's read-only hint.** A server can label a tool read-only without it being so. Keep the approval
  step on for any tool that changes state.
- **Leave the vendor's agent skill pack unedited.** Install per-server additions in the agent's own skill folder instead.

### Wiring
Add the server to the profile's MCP configuration, through the configuration command, with the instance's MCP address and
OAuth. Do not add a token or header with a secret value:
```yaml
mcp_servers:
  <server-name>:
    url: "https://<instance-domain>/mcp-server/http"
    auth: oauth
    timeout: 120
    connect_timeout: 60
```
Then run the sign-in command for the server, complete the browser step yourself, and never paste the resulting token into chat.

Whitelist the tools for production. Start with search, validation and reading tools, and leave publish and execute tools out:
```yaml
    tools:
      include:
        - search_workflows
        - get_workflow_details
        - validate_workflow
        - create_workflow_from_code
        - update_workflow
        - test_workflow
```
Add a publish or execute tool to the whitelist only for a specific reviewed change, and remove it afterwards.

### Fixture-proof gate
Declare the connection working only after this sequence passes:
1. **Reachability, with no credentials.** Send a plain request to the MCP address and read the status:
   - 401 with an authentication hint means the server is live and needs sign-in.
   - 405 on a plain GET with a successful initialize that asks for authentication means it is live and needs sign-in.
   - A successful initialize with no credentials means the server may be misconfigured or open. Do not trust it.
   - A timeout or a certificate error means a network problem. Stop there.
2. **Sign-in.** Complete the sign-in flow, and confirm the token is stored in the protected token file.
3. **Read-only search.** Search for a name that no workflow has. Expect a successful response and an empty list.
4. **Fixture.** Create one workflow named with a unique marker, containing only a manual trigger with no effects. Expect a
   success result with its identifier.
5. **Isolated test.** Test the fixture with pinned input, and read back its execution. Expect success.
6. **Diff against itself.** Compare the fixture's version with itself. Expect no added or changed nodes. Any change means
   the test changed state, so stop.
7. **Retire.** Archive the fixture, or delete it if archiving is not available. Search again and confirm it is gone.
8. **Approval check.** If the workflows you plan to change are outside the approved scope, stop and ask the operator for a
   decision before any publish or execute step.

Record the workflow identifier, the execution identifier, the token's age, and the tool list you whitelisted.

### Approval boundary
Publishing, executing against a non-fixture workflow, and archiving a production workflow need explicit approval from the
operator for that workflow and that change. A general instruction to "build the integration" does not cover them. Record
the approval in the task that asks for the change.

### Verification recipe
1. The configuration command or the list command shows the server as enabled, with a recent successful probe.
2. A search with an empty query returns only the workflows the operator wants the agent to see.
3. The fixture gate passes end to end, and the fixture no longer appears in the search.
4. A test run of an approved workflow shows its execution, and the execution's own data confirms the expected effect.

## Pitfalls
- **A listed workflow is not an accessible workflow.** Read and run access depend on the per-workflow setting.
- **An execution search that comes back empty can mean the workflow is not available to MCP,** not that it is dead.
- **A fixture that reports success is only proof if its output is checked.** Read back the effect the fixture was built to produce.
- **A code step that returns a write decision does not prove that a write happened.** Confirm the write in the target system.
- **A status-only execution read hides the data.** Ask for the run data when you need the outputs.
- **Authentication failures can look like missing workflows.** A header-based call that is missing its credential can return
  a 403 with no execution record. Check the credential before you read the workflow as missing.
- **Third-party HTTP nodes need their own rate limits.** A freshly saved workflow starts with an empty cache, so its first
  run can hit a provider's limit at once. Set the limit inside the node configuration.
- **An alert node that fails on any skipped step makes every run look red.** Alert on transitions between states instead.
- **The OAuth callback for n8n Cloud is the vendor's shared callback address.** Use the address the vendor's current
  documentation names for the instance, not a guess built from the instance's own address.
- **Built-in credentials can have a narrower scope than the service needs.** A vendor credential template may not carry
  the mail scope you need. Check the scopes before you rely on the credential.
- **Verify deletion and archiving by searching afterwards.** A success message from an agent is a claim, not a fact.
- **Do not let OAuth fall back to an API key silently.** Check which provider the status page reports after sign-in.
- **Do not paste a token into chat or into a file.** Use the sign-in flow, and keep the token file's permissions tight.
- **Do not answer how a workflow works from memory.** Read its current definition.
- **Do not ask the operator to paste a credential that is already stored where the agent can reach it.** Look for it first, verify it, and ask only when no stored value exists.
- **A "connected" status from a delegated worker is a claim.** Re-run the fixture gate after any configuration change.
- **Some clients cannot whitelist tools.** For those, restrict the blast radius with the per-workflow setting, start with a
  canary workflow, and keep state-changing tools behind approval.

## Verification
- The server is listed as enabled, and the token file exists with restricted permissions.
- The fixture gate passed each step, and the fixture is gone afterwards.
- The configuration has no secret value in it.
- Each publish or execute action has a recorded approval for that workflow.
