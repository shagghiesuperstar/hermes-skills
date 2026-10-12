---
name: perplexity-holo-deep-research
description: Use when running deep-research turns in the Perplexity desktop app through a local vision-based desktop agent (HoloDesktop CLI) instead of the web.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [perplexity, deep-research, desktop-automation, holo, research]
    category: research-content
related_skills: [ai-search-question-bank, competitor-site-teardown, official-source-claim-factcheck]
---

# Perplexity Deep Research Through a Desktop Agent

## Overview
This skill drives the Perplexity desktop app with HoloDesktop CLI. That tool is a desktop agent: it reads the screen with a vision-language model, then clicks and types on it. The agent runs research turns a person would otherwise type, and reads each answer back in full. It is a slow and fragile lane. Use it when the research must run inside the desktop app, and use a web search or an API call when either will answer the question.

## When to Use
- The research has to run in the Perplexity desktop app, for example to use its deep research tab or its connectors.
- A person can leave the machine's screen alone for the length of the run.
- A local model can serve the vision model, so screen content stays on the machine.

Skip when a web search, an API or a browser-based run would answer the question, or when the screen is shared with other work.

## Features
- Prompt templates for a repository review, a product comparison and a follow-up turn.
- A mode check that confirms the app is in its search and research mode, not the agentic mode that costs more.
- A session tag on each thread, so the thread can be found later.
- Troubleshooting for permissions, the kill switch and runtime restarts.

## Benefits
- Research turns are repeatable from written prompts.
- The mode check stops an expensive agent mode from running by accident.
- Each answer is read back in full, so the operator sees the whole response, not a summary.

## Procedure

1. **Install and verify the tool.** Install with `npm install -g @hcompany/holo-desktop-cli@<pinned-version>`, or follow the vendor quickstart at https://hub.hcompany.ai/holo-desktop-cli/getting-started/quickstart. Activate the tool's Python environment in your shell. Run `holo doctor`. Keep exactly one activation line in your shell profile, because duplicates cause startup errors.

2. **Serve a vision model locally and point the agent at it.** Set the runtime's base URL and model name to a local OpenAI-compatible endpoint, for example `http://127.0.0.1:<port>/v1`. The model name must match the loaded model exactly, or the runtime fails with a configuration error. A cloud endpoint is slower, and it sends screen content off the machine, so use it only with the operator's approval.

3. **Grant macOS permissions once.** For the runtime app in the tool's runtime directory, grant Screen Recording (so the agent can see the screen), Accessibility (so it can click and type) and Input Monitoring (so the kill switch works). Check System Settings, Privacy and Security.

4. **Open the app yourself.** The agent is unreliable at launching apps through Spotlight. Open the app from a shell, wait a few seconds, and tell the agent the app is already open and frontmost.

5. **Confirm the mode before any research turn.** The app has a search or research mode and an agentic computer mode. The agentic mode costs more and uses a different model. Ask the agent to read the header and the sidebar, and to switch to search mode if the agentic icon is selected. Continue only after the expected header text is confirmed.

6. **Turn on deep research.** Deep research is a tab below the search box, not a toggle. Enable any connector you need from the icon row under the input.

7. **Tag and file the session.** Start each query with a unique tag you can search for later, such as `#RS-001`. If the app supports projects, pick the project by its full name, then confirm the choice by reading the header, because similar project names are easy to mis-click.

8. **Run one turn at a time.** Send one query, wait for the answer, then ask the agent to read the full response. Ask each further question as a follow-up in the same thread. A single turn takes one to three minutes, so set the terminal timeout to match.

9. **Keep the screen still.** The agent controls the visible desktop. Do not switch windows during a run. If a run hangs, press Escape twice to use the kill switch, then re-run the command.

10. **Record and check the answer.** Save the full answer text with its session tag and the date. Check every cited source before you rely on the answer, using `official-source-claim-factcheck` for claims about official sources.

### Prompt templates

Repository review:
```
Open the app in search mode, start a new thread, and enable deep research and the code-host connector.
Type: "Review the <owner>/<repo> repository. What are the ten most important commits in the last seven days? Explain why each matters and include the commit hashes."
Press Enter, wait for the answer, then read the full response.
```

Product comparison:
```
Open the app in search mode, start a new thread, and enable deep research.
Type: "Compare <product A> and <product B>. What are the key differences, pricing and recent developments?"
Press Enter, then read the full answer.
```

Follow-up turn:
```
In the current thread, type: "<follow-up question>". Press Enter. Read the new answer.
```

### Troubleshooting

| Problem | Fix |
|---|---|
| Configuration exception at startup | The model name in the environment must match the loaded model exactly |
| Screen not visible to the agent | Grant Screen Recording to the runtime app |
| Clicks do not register | Grant Accessibility to the runtime app |
| Run is stuck | Press Escape twice (kill switch), then re-run |
| App does not open | Open it yourself from a shell, then tell the agent it is open |
| Wrong project selected | Name the project explicitly and confirm it in the header |

## Pitfalls
- **The agent can click the wrong item in a long list.** Give a visual cue, such as "the project name near the top of the list", and confirm the result by reading the header.
- **A flag can select a config the runtime does not ship.** A fast-mode flag can point at a config the runtime does not ship. Use the default run command.
- **The runtime restarts itself after crashes.** Re-run the command. It starts again without manual steps.
- **Mode confusion costs money.** Confirm the mode before every research turn, not only the first one.
- **The agent controls the real desktop.** Use a session or machine that holds no sensitive windows for long runs.
- **Deep research is a tab, not a setting.** Click the tab; looking for a toggle will miss it.
- **Automated use of a consumer app may be restricted.** Check the service's terms for automated access before you run this lane.

## Verification
- `holo doctor` passes, and the local model endpoint lists the model you configured.
- A screenshot test describes the app's current screen correctly.
- The header confirms search mode before each research turn.
- One deep-research turn returns a complete answer, which you read back in full.

## Attribution

HoloDesktop CLI is a product of H Company. Setup and vendor documentation: https://hub.hcompany.ai/holo-desktop-cli/getting-started/quickstart.
