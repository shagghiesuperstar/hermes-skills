---
name: hermes-auth-debug
description: Use when a Hermes provider login or key fails. The login or key may look expired. Covers the runtime credential check, credential pool cleanup and env-versus-pool confusion.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, auth, credentials, oauth, api-keys, debugging]
    category: hermes-operations
related_skills: [hermes-model-picker-debug]
---

# Hermes Auth and Credential Debugging

## Overview
Hermes keeps provider credentials in a credential pool, and some keys also appear in environment variables. These are
two separate systems. An OAuth provider such as Nous Portal has a short-lived access token and a longer-lived inference
key. The status command reports the access token, which can look expired while inference still works. The reliable
health check is the runtime credential resolver, which tries to mint or refresh a key. This skill shows how to check
each layer without printing any secret.

## When to Use
- A provider reports "not logged in", "unauthorized", or a 401 or 403 on a request that used to work.
- A status command shows an expired date, but you are not sure whether inference is actually broken.
- A key is set in the environment but the agent does not use it.
- The credential list has grown with old, inert entries after several re-logins.
- A model is "not found" and you need to rule out the credential path before changing the model ID.

## Features
- Status check for an OAuth provider, with the fields that matter and the ones that can be stale.
- Runtime resolution check, which is the ground-truth test for whether inference works.
- Credential pool listing that shows ids, labels and error state, but never token values.
- Cleanup of stale credential entries by index.
- Checks for the same model reached through two providers with different credential paths.

## Benefits
- You stop re-logging in when the runtime check already shows inference is healthy.
- Secrets stay out of terminal output, chat and logs.
- Stale entries are removed in a deliberate step instead of piling up.
- A "not found" error is traced to the right layer: model ID, credential, or base URL.

## Procedure
1. Open the Hermes install's virtual environment so the Hermes modules import. Run the checks from that environment:
   ```bash
   cd <hermes-install>
   source venv/bin/activate
   ```

2. Read the OAuth provider's status, printing only the fields you need:
   ```python
   from hermes_cli.auth import get_nous_auth_status
   import json

   status = get_nous_auth_status()
   keys = ("logged_in", "expires_at", "agent_key_expires_at", "has_refresh_token")
   print(json.dumps({k: status.get(k) for k in keys}, indent=2, default=str))
   ```
   `expires_at` is the short-lived access token. `agent_key_expires_at` is the inference key. Do not act on a past
   `expires_at` alone. Check `has_refresh_token` first.

3. Run the runtime check. This is the health check that counts. It attempts to mint or refresh an agent key, so it
   answers whether inference will work:
   ```python
   from hermes_cli.auth import resolve_nous_runtime_credentials
   import json

   creds = resolve_nous_runtime_credentials(min_key_ttl_seconds=300)
   safe = {k: v for k, v in creds.items() if k not in ("access_token", "refresh_token", "agent_key")}
   print(json.dumps(safe, indent=2, default=str))
   ```
   If this succeeds, inference works, whatever the status command says. Look at `source`: `cache` means a stored
   key was reused, and `fresh` means one was just minted.

4. List the credential pool with secrets removed. Never print the raw pool, because it holds tokens:
   ```python
   from hermes_cli.auth import read_credential_pool

   pool = read_credential_pool()
   for provider, entries in pool.items():
       if not isinstance(entries, list):
           continue
       for e in entries:
           print(provider, e.get("id"), e.get("label"), e.get("last_status"), e.get("last_error_code"))
   ```

5. Re-authenticate through the CLI, not by editing files. The login command has been replaced:
   ```bash
   hermes auth list
   hermes model        # starts the provider's auth flow when it is not logged in
   ```

6. Remove stale entries by index after you confirm the newest one works. Re-logging in adds a new entry and leaves the
   old one in place:
   ```bash
   hermes auth list
   hermes auth remove <provider> <index>
   ```

7. For a provider key that lives in an environment variable, confirm it reaches the pool. An environment variable is
   not the same as a pool entry. Add the key through the CLI's auth commands. Do not write key values into a file or a
   script by hand.

8. If a model is "not found" or fails, check the three things that differ between paths: the model ID format for that
   provider, which credential is used (environment variable, OAuth, or manual), and the base URL.

9. Check the rotation strategy for a provider with several keys, and confirm it in the config:
   ```bash
   hermes config set credential_pool_strategies.<provider> least_used
   hermes -p <profile> config get credential_pool_strategies.<provider>
   ```

## Pitfalls
- **Never print the raw credential pool or the resolver output without filtering.** Both contain tokens. Print ids,
  labels, dates and error codes only.
- **An expired access token does not mean broken inference.** Run the runtime check before you re-login.
- **Re-login adds an entry. It does not replace one.** Old entries become inert but stay in the list. Clean them up
  after you verify the new one.
- **An environment variable does not put a key in the pool.** Check the pool, not the environment, when a provider
  ignores a key you set.
- **The same model can exist under two providers with different credentials and base URLs.** Check which provider path
  the request actually took before you change the model name.
- **The login command was removed in later releases.** Use the auth commands or the model command.
- **An OAuth access token is not an API key.** Stored in an API-key variable, it is rejected as an invalid key. Let the
  runtime read the provider's own OAuth store, and verify routing with one live request.
- **Do not paste a key into chat, a skill, a prompt or a commit.** If a key is exposed, rotate it at the provider.
- **Do not edit config or credential files by hand to fix auth.** Use the CLI, then read the result back.

## Verification
- The status command shows `logged_in` as true, and the runtime check returns a credential without an error.
- A test request to the provider succeeds and reports the expected model.
- `hermes auth list` shows one current entry per provider, with the old ones removed.
- The strategy grep prints the strategy you set.
