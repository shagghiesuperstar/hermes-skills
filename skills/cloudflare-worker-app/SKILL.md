---
name: cloudflare-worker-app
description: Use when building a Cloudflare Worker with KV storage. It has a cron snapshot and sits behind Cloudflare Access for public-internet users. Covers server-side secrets, disabling preview hosts, JWT verification, free-plan limits, fail-visible data, and verification.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [cloudflare, workers, kv, cron, access, zero-trust, mfa, serverless]
    category: devops
related_skills: [cloudflare-pages-site-ship, chat-safe-secret-staging, secrets-migration-fleet-rollout]
---

# Cloudflare Worker App (Workers, KV, and Access)

## Overview
A dynamic app on Cloudflare can run as a Worker that reads a third-party API on a schedule, stores the result in KV, and serves it to a browser behind a login. The third-party credentials stay on the server. The browser reads only the Worker's own snapshot. Access handles the login in front of the Worker, and the Worker checks the Access token itself, so a misconfigured policy does not expose the data. This skill covers the design, the setup, the limits that break polling apps on the free plan, and the checks that prove the app is live and honest about its data.

## When to Use
- A read-mostly app must sit behind a login on the public internet, and it needs data from a third-party API on a schedule.
- A dashboard or status page must poll an API within a daily call budget.
- A Worker app must be deployed, gated by Access, and verified from outside the private network.

Use a static Pages site instead when there is no server logic. Use a database-backed service when the app needs writes, real-time updates, or per-user state.

## Features
- A snapshot loop: a cron trigger fetches each source, wraps each result with its status and time, and writes one KV key.
- Access gating with a single allow-list policy, and session and MFA settings.
- Verification of the Access token inside the Worker, against the team's certificates and the application's audience tag.
- A plan check and a free-plan design option, with the limits listed.
- A seeding step that copies an existing copy's state into KV before the first cron run.

## Benefits
- Third-party credentials never reach the browser or the repository.
- Each data source shows its own status and fetch time, so an old value is never shown as current.
- Failures stay visible, and a single failing source does not hide the others.
- The app is checked from outside the private network, not only from its own deploy log.

## Procedure
### Always-on rules
- Keep credentials on the server. A third-party key never goes into static assets, a configuration file, a browser-readable KV value, or HTML.
- Use secrets, not plain variables, for any value that must stay out of the repository. A secret is set with `wrangler secret put <NAME>`, and the Worker reads it from its environment like any variable. A plain variable in the configuration file is public to anyone who can read the repository.
- Disable the `workers.dev` address and the preview addresses for production. Both can reach the Worker without going through Access. Bind a custom hostname, and reject any request whose Host header is not that hostname.
- Check the Access token inside the Worker on every request. Access alone is not enough. Reject any request without a valid token with a 401, and serve no dynamic content.
- Do not store personal data in KV. KV values can be read by anyone who has the namespace identifier and a token. Access gates requests to the Worker, not KV reads. Store references, not names, addresses, or phone numbers.
- Do not report an app as live from the deploy output. Live means the custom hostname resolves, Access login works from outside the private network, and the data is current.

### Step 1: Decide whether KV is enough
Use this stack when the app is read-mostly, public, behind one login, and the third-party API can be polled on a schedule of 15 minutes or longer. If the app needs writes, real-time updates, or per-user state, use a different storage design.

### Step 2: Check the plan before designing the loop
The default plan for a new account can be Free, and its limits break most polling apps. Check the plan through the account settings endpoint, which reports the usage model. A "bundled" value means a paid plan. A "standard" value does not confirm the plan. If the plan matters and the API cannot confirm it, ask the operator to read the dashboard. Do not infer the plan from a $0 usage charge, because a free account with no overage also shows $0.

Verify the current limits in Cloudflare's Workers documentation before you rely on them. The main limits at the time of writing are:

| Limit | Free | Paid |
|---|---|---|
| Subrequests per invocation | 50 | 10,000 |
| CPU time per cron run | 10 ms | 30 s for cron intervals under one hour |
| Wall time per cron run | 15 min | 15 min |
| KV reads per day | 100,000 | 10,000,000 |
| KV writes per day | 1,000 | 10,000,000 |

On the free plan, a loop that calls about ten endpoints per run fails on every run that exceeds 50 subrequests. The failure looks like a network error from the third party. Wrap each third-party call so that it keeps the original message and the HTTP status. A catch that reduces the reason to "Error" hides the real cause.

If the operator will not approve a paid plan, design for the free plan from the start:
- Use one composite endpoint per third party where the API offers one, instead of many small calls.
- Cache the third party's access token in KV, so a token refresh does not count as a separate call each run.
- Split the snapshot into one KV key per source, so a run re-reads only what changed.

### Step 3: Seed KV from an existing copy
If the Worker replaces an older copy that already has data, do not let the Worker start from an empty namespace. The first cron run would spend the third party's daily budget re-reading everything, and the tiles would stay empty.
1. Stop the older copy before the Worker's first cron run, so only one process calls the third party.
2. Copy the older copy's state into the Worker's KV under the same key names, with `wrangler kv key put` or `wrangler kv bulk put`.
3. Read a key back from a fresh session to confirm it, before you report the app as live.

Write a small script that reads the older state file and prints one `wrangler kv key put` command for each key. The script prints the key names and sizes only, never the values.

### Step 4: Set up the project
- One Worker, with a configuration file that sets the name, the entry file, and the cron trigger.
- One KV namespace, bound to a name such as `SNAPSHOT`.
- One cron trigger for the snapshot, such as every five minutes. Cron times run in UTC unless the dashboard shows another zone.
- A custom hostname bound through the configuration or the dashboard.
- Static assets next to the Worker source. Workers Static Assets serves a directory at the root path, not under its own name.

### Step 5: Run the snapshot loop
1. The cron trigger fires, and the Worker calls each required endpoint with its secret-bound credentials.
2. Wrap each result as `{status: "ok" | "error", fetchedAt, data, error}`. On an error, keep `data` empty. Never invent data.
3. Write the merged snapshot to one KV key, with an expiration of 30 minutes or less as a safety net.
4. The browser requests the snapshot from the Worker. The Worker reads KV and returns the JSON. The browser never calls the third party.

Show `fetchedAt` and the source status in the interface. Treat a snapshot older than 15 minutes as stale, and show a banner. Give each block its own status, and never collapse a failure into one global "OK".

### Step 6: Gate the app with Access
- Use the account's default identity provider, which is email and password, or add a one-time PIN provider that sends a code to the user's email.
- Turn on multi-factor authentication at the organization level. Check the current plan terms before you rely on the free tier's user cap, because that cap has changed over time.
- Create one Access application for the custom hostname.
- Add one policy that allows the listed email addresses only.
- Set the session length to suit the use. A week is long enough for a display that stays logged in.

### Step 7: Verify the Access token in the Worker
Each request that reaches the Worker carries the Access assertion header. The Worker must check it:
- The signature, against the team's public keys from Access's certificate endpoint. The Access documentation gives the path.
- The audience tag, which matches the application's audience value in its Access settings.

Use a maintained JWT library, or Cloudflare's own examples. On failure, return 401.

For local development, run `wrangler dev`. If the token check blocks local requests, use a development-only Access application for a development hostname. Do not add a code switch that skips the check, because such a switch can reach a deployed Worker.

### Step 8: Deploy and verify
1. After the operator gives the go-ahead, deploy from a clean, pushed tree with a pinned version: `npx wrangler@<pinned-version> deploy`. Do not add `--yes`. Do not test the deployment's own address, because it can bypass Access.
2. Confirm that the custom hostname resolves and that its TLS certificate is valid.
3. From a browser outside the private network, log in, complete the MFA prompt, and check that the app renders.
4. Trigger a cron run from the dashboard, and check that the snapshot time advances.
5. With the operator's go-ahead, break one source on purpose. Point a test binding at a deliberately invalid value, never at a live key. Check that the affected block shows "no data" with the reason, and that the other blocks keep working.

## Pitfalls
- **Testing the wrong address.** The Workers subdomain and the preview addresses bypass Access unless they are bound. Test the custom hostname only.
- **Promising passwordless login.** The default identity provider uses a password. Passwordless login needs a one-time PIN provider or a paid identity provider.
- **Hiding the last good data after a quota pause.** When the third party's budget runs out, keep the last good data on screen, with a stale badge that shows the last read time. Show "no data" only when there was never any data. Hiding good data is the same defect as collapsing failures into "OK". The freshness indicator must use the stored fetch time, not the current time.
- **Silent cron failures on the free plan.** A green deploy does not prove the cron runs. Check the plan, then check the logs after the second and third run.
- **Secrets in the browser.** Filtering a key out in the Worker does not make it safe. Keep the key as a secret, and never store it in KV.
- **Missing an email code.** A one-time PIN that never arrives is often blocked by the recipient's spam filter, not by Cloudflare. Test with a second mailbox, and do not resend in a loop, because that triggers the rate limiter.
- **MFA setup that fails silently.** A per-app MFA prompt needs the Access App Launcher turned on at the organization level, with one allow policy attached. Without it, the user sees a message to contact the administrator.
- **Treating an encrypted-at-rest claim as access control.** KV encryption does not stop a reader who holds a namespace token. Design the data as readable by that reader.

## Verification
- `wrangler secret list` shows every credential, and no credential value is in the configuration file or the repository. Run a secrets scanner over the repository.
- The custom hostname is bound. A request with the workers.dev host returns 403 or 404, never the app.
- From outside the private network, Access login, then the MFA prompt, then the app renders.
- Each block shows its fetch time and its source status.
- A forced failure from one source shows "no data" with a reason in that block only.
- A request with a modified Access token is rejected with 401.
- The cron trigger runs on schedule, as shown in the dashboard logs.
- The KV snapshot contains no personal data.
