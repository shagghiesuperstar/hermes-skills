---
name: openwarp-deployment
description: Use when installing and auditing an open-source terminal fork (OpenWarp) that connects to a local model server on a Mac. Covers identifying the right binary in the bundle, configuring a local provider, auditing outbound connections, building from a pinned commit, and MCP configuration.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [openwarp, terminal, macos, byop, local-models, network-audit, mcp]
    category: devops
related_skills: [local-model-deployment, mlx-inference, omlx-model-management]
---

# OpenWarp Deployment on macOS

## Overview
OpenWarp is an open-source fork of a terminal application that can use a model provider of the operator's choice, including a local model server. A fork ships in two forms: a prebuilt application bundle and a source build. The bundle can include a command-line agent that makes network calls on first launch. This skill covers how to tell the binaries apart, how to point the terminal at a local model server, how to audit the network before the operator trusts the install, and how to build from a pinned commit when the prebuilt bundle fails the audit.

## When to Use
- The operator wants a terminal app that uses a local model server instead of a cloud provider.
- An install of this fork must be checked against a local-only requirement.
- A custom MCP server list must be added to the app.

## Features
- A binary check that names which executable is the terminal and which one is a command-line agent.
- A local-provider setup that points the app at an OpenAI-compatible local endpoint.
- A network audit of the running process, with the expected result stated in advance.
- A source build pinned to an audited commit, with a check for telemetry settings.
- MCP configuration rules for the accepted JSON shapes.

## Benefits
- The operator knows which binary makes network calls before any run.
- A failed audit leads to a clear decision for the operator, not a silent workaround.
- A source build from a pinned commit can be reviewed.
- MCP servers are configured in the app's own settings, which avoids a stale or mistaken repository file.

## Procedure
### Identify the binaries
A bundle can hold more than one executable. The file named for the command-line agent is not the terminal app. Check the version of the executable you plan to run:
```zsh
"/Applications/OpenWarp.app/Contents/MacOS/<agent-binary>" --version
```
The agent's subcommands (for example, login, model listing, or cloud commands) can require a network account. Commands that need an account can time out on a local-only machine. A version check runs without the network, so use it to confirm the binary.

### Obtain the prebuilt bundle
Check the latest release tag first, then download the macOS disk image from the project's release page. Mount the image, copy the application into the Applications folder, and detach the image:
```zsh
curl -s "https://api.github.com/repos/zerx-lab/warp/releases/latest" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['tag_name'])"
hdiutil attach <downloaded-image>.dmg
cp -R "<mounted-volume>/OpenWarp.app" /Applications/
hdiutil detach "<mounted-volume>"
```
If macOS blocks the application because it is not signed, do not remove the quarantine attribute from the agent's session. Stop there. The operator decides whether to approve the app in the system's privacy settings, after the audit below.

### Configure a local provider
Open the application's settings, then the AI provider section, and add a provider with these values:
- Name: a label of your choice, such as `local-omlx`.
- Base URL: the local server's OpenAI-compatible endpoint, such as `http://localhost:<port>/v1`.
- API key: the placeholder that the local server accepts, if it requires one.

Fetch the model list. If the list stays empty, enter the model identifier by hand, using the identifier the server returns from its models endpoint. Set that model as the active model.

### Audit outbound connections
Run the audit after the application has launched and has been used for a few minutes:
```zsh
lsof -i -n -P | grep -i "<agent-binary>" | grep -v "127.0.0.1\|::1"
```
The expected result for a local-only setup is no connection to a host outside the local machine. A connection that remains after a full launch is a finding. Record the destination, and do not treat the audit as passed.

### Decide what to do with a failed audit
A prebuilt bundle can connect to cloud infrastructure on first launch. When the audit shows that, the operator chooses one of these paths:
1. Build from source, from a pinned commit, if the operator accepts the build time and the toolchain.
2. Accept the connections with written approval from the operator.
3. Use a different tool.

Do not continue to use the prebuilt bundle on a machine with a local-only requirement until the operator has chosen one of these.

### Build from a pinned source commit
Use this path only when the operator has chosen it. Install the Rust toolchain through the package manager, not through a script piped from the network:
```zsh
brew install rust rustup
export PATH="$(brew --prefix rustup)/bin:$PATH"
rustup toolchain link system "$(brew --prefix rust)"
rustup target add aarch64-apple-darwin
```
Clone the repository, check out the commit that was audited, and build the agent binary:
```zsh
git clone https://github.com/zerx-lab/warp.git <work-dir>/openwarp
cd <work-dir>/openwarp
git checkout <audited-commit>
cargo build --release --bin warp-oss
```
The build can take tens of minutes, and it needs the platform's graphics SDK, which comes with Xcode. Run the build in a background process, and check its output when it finishes.

Check that the telemetry settings in the binary's entry source are empty:
```zsh
grep -n "telemetry_config\|crash_reporting_config" app/src/bin/oss.rs
```
The entry source should set both to none. Then search the application source for the telemetry client names, and confirm that the hits are only in tests or comments.

### Configure MCP servers
The application does not read a repository's MCP file. Add MCP servers in the application's agent settings, by pasting the JSON there, or through the application's own API. A server entry must have exactly one of these:
- A `command` string, with an optional `args` array of strings, for a local stdio server.
- A `url` string, for an HTTP or event-stream server.
- A `warp_id` UUID, for a server registered in the cloud service.

Optional fields are `env` (string values only) and `headers` (for URL servers). The parser accepts the server map at the top level, or under a `mcpServers`, `servers`, or `mcp.servers` key. Use the top-level map, because it has the fewest parts to get wrong.

## Pitfalls
- **Running the agent's account commands on a local-only machine.** They contact the network and time out. Use the version check to confirm the binary.
- **Trusting a clean launch.** The audit is the test. Run it after the application has been used.
- **Removing the quarantine attribute to get past the system's prompt.** Stop and ask the operator. The approval is theirs to give.
- **Piping an install script from the network into a shell.** Install the toolchain through the package manager.
- **Building an unpinned branch.** Check out the audited commit.
- **Expecting a repository MCP file to load.** Add servers in the application's settings.
- **Sending a non-string value in an MCP environment map or in the arguments array.** The parser rejects it.
- **Two MCP entries with the same name.** The parser rejects duplicates.

## Verification
- The version check of the agent binary runs without a network account.
- The provider is set, and a request through the application returns a reply from the local server.
- The outbound-connection audit shows no destination outside the local machine, or the operator's written decision covers each destination it shows.
- A source build, if used, is from the audited commit and has the telemetry settings empty.
- Each MCP entry parses, and each name is unique.

## Attribution
- OpenWarp is an open-source fork of the zerx-lab project, published at https://github.com/zerx-lab/warp. The product site is https://openwarp.zerx.dev/.
