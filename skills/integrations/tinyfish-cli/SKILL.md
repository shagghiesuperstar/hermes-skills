---
name: tinyfish-cli
description: Use when connecting TinyFish search to coding agents. It applies to search and fetch. Covers key handling, unattended connection, the doctor check and a search-and-fetch proof.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [tinyfish, search, fetch, cli, coding-agents, mcp, api-key]
    category: integrations
related_skills: [mcp-client-setup, self-hosted-firecrawl]
---

# TinyFish CLI

## Overview
TinyFish provides search and page fetching as a command-line tool and as a remote MCP endpoint. The command-line tool can
connect the search and fetch capability to each coding agent installed on a machine, so those agents can use it. Setting
it up involves an API key that must never reach a transcript, a sign-in step that must not hang an unattended run, and a
check that reads the doctor report before anything is repaired. This skill covers that connection and a short proof that
search and fetch work. It does not cover general use of the service.

Read the vendor's current command reference before you run anything, because the options and the output shape change.

## When to Use
- You want installed coding agents on a machine to have web search and page fetching through TinyFish.
- A connection reports that an agent is connected, and you need to confirm it.
- A search or fetch returns an unexpected result, and you need to check that the service itself works.

Do not use this to start browser automation or agent runs. For connecting an arbitrary MCP server to a Hermes profile, use
the MCP client setup skill.

## Features
- Key handling that keeps the value out of output, and clears it when the run ends.
- Unattended connection that skips the browser sign-in step and reports which agents need it.
- Doctor check that lists repairs and runs only the ones that are safe to automate.
- Search and fetch proof that reads the structured output, not a title line.
- A report shape that separates connected, needs-browser and not-installed agents.

## Benefits
- The key does not leak through the command's own output.
- An unattended run never waits on a browser that no one is watching.
- Agents that are not installed are reported as skipped, not as failures.

## Procedure
1. Load the key into the environment of the shell that runs the command, from the secret store, by name. Print only that it
   was set and its length:
   ```bash
   test -n "$TINYFISH_API_KEY" && echo "set, length ${#TINYFISH_API_KEY}"
   ```
   Redact the key from anything the command prints. Unset the variable when the run ends.

2. Connect the detected agents without opening a browser:
   ```bash
   npx -y @tiny-fish/cli@<reviewed-version> connect --all --skip-launch --url "https://agent.tinyfish.ai/mcp"
   ```
   Pin `<reviewed-version>` to the version whose help output you read, in every command on this page. Before you run the connect command, check `connect --help`. If it lists an option that reads the key from the environment, or prompts for it, use that option and leave the key out of the command. If the only way to pass the key is `--api-key`, stop and ask the operator to run the connection interactively, because the key would appear in the process list while the command runs.

   The connection covers only the agents the command detects. An agent that is not installed is skipped, and the report
   lists it as not installed. A warning about the Node version is harmless if the connection step exits with zero and the
   doctor check later confirms authentication.

   The connection may write the key into the Hermes profile's environment file. That is expected. Do not print the file.

3. Run the doctor check and read its report. Parse the repair list first:
   ```bash
   npx -y @tiny-fish/cli@<reviewed-version> doctor --pretty
   npx -y @tiny-fish/cli@<reviewed-version> doctor
   ```
   Run a repair automatically only when the report marks it as safe to run unattended. A repair marked as not safe is a
   step for the operator, so list it and do not run it.

4. Prove search and fetch, using the lightest commands that answer the question:
   ```bash
   npx -y @tiny-fish/cli@<reviewed-version> search query "<query>" --pretty
   npx -y @tiny-fish/cli@<reviewed-version> fetch content get --format json "<url>"
   ```
   To return highlighted passages from a fetch, add `--highlights` to the fetch command.
   Read the page text from the structured output. The text is often a tree of nodes rather than a single string. A
   pretty-printed fetch can show only the title and the address, so an empty-looking body there does not mean the page is
   empty. Check the JSON output before you report that a page has no content.

5. Report with one fixed shape:
   - the host name;
   - the agents connected and verified;
   - the agents that need a browser sign-in;
   - the agents that are unfinished or not installed;
   - the doctor result, the repairs found, and the authentication mode;
   - the status, the proof commands used, and any blocker.

   Do not add other prose to the report.

## Pitfalls
- **The command can echo the key.** Redact it from output, and do not put it in arguments that a log will record.
- **Without the no-browser option, a connection can wait on a sign-in that no one will complete.** Always use the option
  for an unattended run.
- **The doctor command has no JSON flag.** Its plain form is already JSON, and the pretty form is for people.
- **An unsafe repair is a human step.** Do not run it from an agent.
- **A skipped agent is not a sign-in problem.** The agent is missing, so say so.
- **A fetch in pretty form can hide the body.** Read the structured form before you judge the content.
- **If `--highlights` returns a 403 error,** retry the same URL without it. The page can still be fetched.
- **Keep the proof light.** A search and a fetch are enough to show the connection works. Do not start heavier services
  to prove the same thing.

## Verification
- The key is set in the shell, and its value appears nowhere in the output.
- The connection step exits with zero, and the report lists each agent under the right heading.
- The doctor report shows authentication working, and no repair was run that is marked as not safe.
- A search returns results, and a fetch returns page text from the structured output.
- The key variable is unset at the end of the run.
