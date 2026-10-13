---
name: openrouter-mcp
description: Use when you need live model benchmarks or pricing. The data also covers provider latency and credit balance, from the OpenRouter MCP server. Covers tools, billing, routing suffixes, tokens and a REST fallback.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [openrouter, models, benchmarks, pricing, mcp, routing, research]
    category: integrations
related_skills: [mcp-client-setup, hermes-model-routing]
---

# OpenRouter MCP

## Overview
OpenRouter is a router that offers many model providers behind one API. It also publishes live data about its models:
benchmark scores, prices, provider latency, rankings and credit balance. Its MCP server exposes that data as tools, so an
agent can answer a question about current models from the live source instead of from memory. One tool, the chat call,
sends a real request and is billed. Everything else is a lookup. This skill covers which tool answers which question, how
to authenticate and keep the token working, the routing suffixes that change which provider serves a request, and a REST
fallback for when the MCP tools are not available in the session.

## When to Use
- The operator asks which model scores highest on a benchmark, or how two models compare on price or latency.
- The operator asks for the current credit balance before a batch of test requests.
- A request needs a model's live provider list, or its price on each provider.
- The MCP tools are missing, and you need the same data over the REST interface.

## Features
- Tool table that separates free lookups from the one billed chat tool.
- Benchmark filters for source, task type, arena and category.
- Routing suffixes that choose a provider by speed, price, or web grounding.
- Token and spend-cap rules, with the re-authentication command.
- REST fallback with the same benchmark filters.

## Benefits
- Answers cite a live result, with the model, the benchmark provider, the score, the provider and the cost.
- The billed tool is used only when a test request is actually needed.
- A stale token is found from the tool list, not from a silent failure.

## Procedure
1. Use the lookup tools first, and call the chat tool only for a test request:

   | Tool | Use | Billed |
   |---|---|---|
   | benchmarks | scores by source, task type, arena or category | no |
   | models-list | models filtered by use case, sort, price or context length | no |
   | model-get | one model's details, by its author and slug | no |
   | model-endpoints | the providers serving one model, with their latency and price | no |
   | providers-list | the list of providers | no |
   | rankings-daily | today's model usage ranking | no |
   | credits-get | the current credit balance | no |
   | generation-get | the cost and provider of one past request, by its identifier | no |
   | chat-send | one test request to a model | yes |

2. For a model comparison, follow this order: benchmarks for the task type, then models-list to narrow the candidates,
   then model-endpoints for each candidate's providers. Report the benchmark provider, the score, the provider chosen and the price.

3. For a test request, check the balance first. Then send one short request with the model slug, and read back the
   generation's cost and provider:
   ```
   chat-send(model="<author>/<slug>:nitro", message="<short test prompt>")
   generation-get("<generation-identifier>")
   ```
   If the balance is below the amount you plan to spend, tell the operator before sending.

4. Use the benchmark filters. Each source has its own names:
   - source: the benchmark provider's name, or all sources when omitted;
   - task type: coding, intelligence, agentic or arena;
   - arena: models, builders or agents, for the design arena source only;
   - category: a design or media category, for the design arena source only;
   - maximum results: a whole number, or all results when omitted.

   Treat a benchmark score as one input. It is not a guarantee of how a model behaves on your task.

5. If the MCP tools are not available in the session, call the REST interface with the same filters, and read the key
   from the environment variable:
   ```bash
   curl -s "https://openrouter.ai/api/v1/benchmarks?source=artificial-analysis&task_type=agentic&max_results=10" \
     -H "Authorization: Bearer $OPENROUTER_API_KEY"
   ```

### Routing Suffixes
A suffix on the model slug changes which provider serves the request:
- `:nitro` picks the fastest available provider.
- `:floor` picks the cheapest provider.
- `:online` adds web search grounding.
- `:free` uses a free endpoint where one exists.

Provider ordering in the request body only sets a preference among providers. It does not turn on fastest-provider routing.
To get fastest-provider routing, use the suffix, or the sort setting in the routing preferences.

### Setup
Add the server to the profile's MCP configuration through the configuration command, then authenticate:
```yaml
mcp_servers:
  openrouter:
    url: https://mcp.openrouter.ai/mcp
    auth: oauth
    timeout: 60
    connect_timeout: 30
```
```bash
hermes mcp add openrouter --url https://mcp.openrouter.ai/mcp --auth oauth
hermes mcp test openrouter
hermes mcp list
```
The operator completes the browser step, and sets the spend cap for the key at the provider's settings page. Use a
separate key for this server, so it can be revoked on its own.

The OAuth token expires after a set period. When the tools stop answering, re-authenticate:
```bash
hermes mcp auth openrouter
```
The tools appear in a session only after authentication, and a session that started before it keeps its old tool list.
Start a new session, or restart the gateway from an operator shell.

### Setting the Model
Set the default model with the configuration command, then read the value back:
```bash
hermes config set model.default <author>/<slug>:nitro
hermes config show
```
Edit the configuration file that matches the profile in use. A default-profile file and a profile file are separate.

## Pitfalls
- **Only the chat tool is billed.** Lookups are free, so do not send test requests to answer a lookup question.
- **A silent authentication failure looks like a missing tool.** Run the test command to tell the two apart.
- **MCP tools live in the main conversation.** A sub-session, a script, or a terminal session may not receive them, even when
  the server is listed as enabled. Use the REST interface in those contexts.
- **A key that returns an authentication error may be marked exhausted in the credential pool.** The agent then falls back to
  another provider without saying so. Check the served provider on the generation record.
- **A test request through a sibling model can fail in ways that look like a review result.** Check the failure before you
  report the review.
- **Do not present model knowledge from memory as current.** Cite the live lookup, with its time.
- **Do not paste the key into chat or into a file.** Keep it in the environment file or the token file.
- **Benchmark indexes are not behavior guarantees.** Test the model on your own task before you commit to it.

## Verification
- The test command reports the server as connected, with the expected tools listed.
- A lookup answer names the benchmark provider, the score, the model slug and the time of the lookup.
- A test request shows its cost and its provider on the generation record.
- The balance is recorded before and after a batch of test requests.
