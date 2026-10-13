---
name: xai-grok-oauth
description: Use when Hermes must use xAI Grok by subscription login. It is used instead of an API key. Covers the browser login, model selection, fallback order and login troubleshooting.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [xai, grok, oauth, subscription, fallback, troubleshooting]
    category: hermes-operations
related_skills: [grok-multi-role-optimization-hermes, hermes-auth-debug, hermes-model-routing]
---

# xAI Grok Through a Subscription Login

## Overview
Hermes can use xAI Grok models through a browser-based OAuth login that uses an existing subscription, so no API key
is needed. Hermes refreshes the session in the background. The same login token is shared by the built-in xAI features,
such as speech output, image and video generation, and search over posts. This skill covers the first login, the
remote-session variant, choosing models, setting a fallback order, and the login problems that look like something else.

## When to Use
- You want Grok models in Hermes, and you have a subscription but no API key for xAI.
- A login has expired, was revoked, or fails with a state or timeout error.
- A Grok feature does not appear, or a model in the picker does not answer.
- You are setting Grok as the primary model or as a fallback in a profile.

## Features
- Browser login with the provider identifier and its aliases.
- Login over a remote session, using a local browser and a forwarded callback port.
- Login status check through the diagnostic command.
- Model selection through the model picker, with each model verified before use.
- Fallback order that lists the subscription model first, then a local or keyed tier.
- Troubleshooting for expired tokens, callback failures, and features that stay hidden.

## Benefits
- No API key has to be stored for this provider.
- Background refresh keeps the session alive without manual steps.
- A login problem is traced to its real cause, not to a security alarm.

## Procedure
1. Start the login. The operator approves access in the browser. The agent does not handle the approval page or the
   codes it shows:
   ```bash
   hermes model        # choose the xAI subscription entry, then approve in the browser
   ```
   The same login can be started with the auth command: `hermes auth add xai-oauth`. The provider identifier is
   `xai-oauth`, and the aliases `grok-oauth`, `x-ai-oauth` and `xai-grok-oauth` resolve to it.

2. For a remote session, forward the callback port from the local machine, and run the login on the remote host with the
   no-browser option. Open the printed URL in the local browser:
   ```bash
   ssh -N -L <callback-port>:127.0.0.1:<callback-port> <user>@<remote-host>
   hermes auth add xai-oauth --no-browser
   ```

3. Check the login state with the diagnostic command. Look for the xAI entry in the authentication section:
   ```bash
   hermes doctor
   ```

4. Pick a model with the picker, and verify it before you depend on it. A model in the list is not proof that the
   subscription includes it. Send one short request to the model through the Hermes route, and read the answer.

5. Set the fallback order. The subscription model fits as a first fallback because the token refreshes without an
   expiry notice. Put a local or keyed tier after it, and check the order:
   ```yaml
   fallback_providers:
   - provider: xai-oauth
     model: <grok-model-id>
   - provider: custom
     model: <local-model-id>
     base_url: http://127.0.0.1:<port>/v1
   ```
   ```bash
   hermes fallback list
   ```

6. Enable the built-in xAI features you need. Each one is a toolset that is off by default, and each reuses the login:
   ```bash
   hermes tools enable x_search
   ```

### Troubleshooting

### The token expired and the session stopped
Hermes refreshes the token before a session and again after an authorization error. If the refresh fails with an error
that says the grant is invalid, run the login again.

### The login timed out
The callback listener waits for a short window. Run the login again, and approve the access within that window.

### A "state mismatch" error on macOS
Upstream issue 27385 reports this error on macOS. Its cause is that the browser could not reach the local callback
listener, so no callback arrived and the wait timed out. Check whether something else holds the callback port, whether a
firewall blocks it, and whether the browser resolves the loopback address the same way the listener does. The no-browser
login with a manual paste of the returned link avoids the listener altogether. Check the stored login afterwards with `hermes auth list`. The xAI credential should appear after a successful login:
```bash
hermes auth list
```

### A feature such as search stays hidden
A feature is hidden when no xAI login is configured. Check the login state first, then enable the toolset.

### The login works but the API key is also set
When both a subscription login and an API key are configured, check which one the requests use before you rely on either. Send one short request through the Hermes route and read the answer.

## Pitfalls
- **An API key is not required for this provider.** The login covers the chat models and the built-in xAI features.
- **Built-in features are off by default.** Enable each toolset separately, even with a valid login.
- **Image-generation models answer a different endpoint.** Do not test them on the chat endpoint. They return a client error
  there, which looks like a broken model.
- **A suppressed provider keeps its stored login.** When another provider is the active one, Hermes does not route to
  the xAI login, but the stored login stays in place.
- **The model list can be ahead of the subscription.** Verify each model with one request before you report it working.
- **A stored last-error field can repeat an old error.** Judge the current run by its own output, not by that field.
- **Never print the stored token.** Check its presence and its modification time, not its value.

## Verification
- `hermes doctor` shows the xAI login as present and current.
- `hermes fallback list` shows the subscription model first, then the tier you chose.
- One short request to the chosen model returns an answer through Hermes.
- The enabled feature appears in the tool list, and its test request succeeds.

## Attribution
The loopback callback problem on macOS is tracked upstream at https://github.com/NousResearch/hermes-agent/issues/27385.
