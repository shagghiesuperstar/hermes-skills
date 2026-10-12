---
name: mcp-server-authoring
description: Use when building a small Python MCP server from a spec. Its tools are wired to a fetch or scrape function. Covers the runtime, library version traps, FastMCP wiring and config.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [mcp, fastmcp, python, server, scraping, authoring]
    category: integrations
related_skills: [mcp-client-setup, openrouter-mcp]
---

# MCP Server Authoring

## Overview
An MCP server exposes functions as tools that an agent can call. A small Python server usually has four parts: a runtime
with the right Python version, a function that fetches or computes the data, a server that exposes that function as a
tool, and a config entry in the agent's profile. Most of the time goes to three traps: an old Python on the machine, a
library whose API changed between versions, and a config file that must be edited through the command. This skill covers
the build order and those traps. To connect an existing server to a profile, use the MCP client setup skill.

## When to Use
- You need a small MCP server that wraps a function, such as a web fetch, a calculation or a CLI.
- You have a spec that names a library version, and the code you wrote fails on it.
- A server starts but its tools do not appear in the agent.

## Features
- Project layout for a single server with its scraper, requirements and environment example.
- Runtime check that the virtual environment really uses a current Python.
- Tool registration with the framework's decorator, and a health check.
- Notes on library API changes that break older examples.
- Config registration through the command, followed by a session restart.

## Benefits
- The environment is proven before any code runs.
- Library changes that break older examples are caught early.
- Tools are registered once, with descriptions the agent can use.

## Procedure
1. Lay out the project:
   ```
   project/
     server.py          # tools and the HTTP app
     scraper.py         # fetch or compute functions
     requirements.txt
     .env.example       # names only, never real values
     README.md
   ```

2. Build the runtime on Python 3.10 or newer. A system Python that is older than that cannot install a current
   framework. Create the virtual environment with the newer interpreter, and check the environment's own interpreter:
   ```bash
   /path/to/python3.x -m venv .venv
   .venv/bin/pip install -r requirements.txt
   .venv/bin/python --version
   ```
   The version printed must be 3.10 or newer. A virtual environment can have links that point back to an older
   interpreter, so check the version through the environment's interpreter, not the system's.

3. Write the fetch or compute function. For a browser-based scraper, this skill's examples target crawl4ai, a public Python
   crawler. Check the installed version's API first. Newer versions renamed options and return a result container, not a
   single object. Iterate the container and take the first result:
   ```python
   async def fetch(url: str, wait_selector: str | None = None) -> str:
       # Stub: the builder writes the run config for the installed crawl4ai version, runs it on the URL,
       # then iterates the result container and returns the page markdown from the first result.
       raise NotImplementedError
   ```
   Respect the target site's terms and its robots instructions. Cache results, so repeated tool calls do not repeat requests.

4. Wire the server. Expose each function with a decorator that gives the agent a one-line description. Read the host and
   port from the environment, with a default:
   ```python
   from fastmcp import FastMCP

   mcp = FastMCP(name="<server-name>", instructions="<what the server does and when to use each tool>")

   @mcp.tool(description="<one-line description for the agent>")
   async def <tool_name>(<arg>: str) -> dict:
       return await <scraper_function>(<arg>)
   ```
   Start the server with the transport the framework version supports. Check the framework's documentation for the
   current transport names.

5. Check the server answers. Use the health endpoint that the transport exposes. For a server-sent-events transport, the
   first event names the message path for the session.

6. Register the server in the profile. Use the config command, not a direct edit of the config file. The `-p` flag selects the profile, as in `hermes -p <profile> <command>` from the top-level help:
   ```bash
   hermes -p <profile> config set mcp_servers.<name>.transport <transport>
   hermes -p <profile> config set mcp_servers.<name>.url "http://127.0.0.1:<port>/<path>"
   hermes -p <profile> config show
   ```
   Restart from an operator shell, then start a new session. The new tools do not appear in a session that started before.

7. Install browser binaries only if the scraper needs them. A browser download can take several minutes on the first run.

### Library traps
- **Pydantic settings moved.** In recent Pydantic releases, the settings base class lives in a separate package. Install that
  package, and import the class from it. The old import raises an import error that names the new package.
- **Result containers.** A scraper library may return a container that has no useful attributes until you iterate it.
  Iterate it and read the fields from the item.
- **Old option names.** An option that a library version removed fails with a type error. Read the installed version's
  options, not an older example.
- **Client-rendered pages.** Some pages fill in prices or changing values with scripts. A plain fetch returns empty fields
  for those. This is a limit of the fetch method, not a bug in the server. Say so in the README, and do not hide it.
- **Pages behind a login.** A fetch cannot read content that needs a login. Document the limit, and do not try to get
  past the login.

## Pitfalls
- **Using the system Python.** It is usually too old for a current framework, and the install fails with no matching version.
- **A venv with links to the wrong interpreter.** Check its version every time you create it.
- **Writing the config file by hand.** The profile's config is changed through the command. The command also checks the values.
- **Expecting new tools in an old session.** Start a new session after a config change.
- **Committing a real token in the example environment file.** The example file lists names only.
- **Exposing the server on every interface by default.** Bind to the address the clients need, and no wider.
- **Port conflicts.** Check whether the port is free before you start, and change it in the environment file if not.

## Verification
- The environment's interpreter reports 3.10 or newer.
- The server's health endpoint answers, and its tool list includes each function.
- One tool call returns the expected result for a known input.
- The profile's config shows the server entry, and a new session lists its tools.
- The README states the fetch limits, such as client-rendered fields and login walls.
