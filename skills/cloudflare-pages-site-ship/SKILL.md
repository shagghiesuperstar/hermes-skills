---
name: cloudflare-pages-site-ship
description: Use when deploying a static site to Cloudflare Pages. The deploy runs headlessly. Covers a token-safe deploy script, a content-verification gate that an HTTP 200 alone does not satisfy, custom-domain order, cache busting, and rollback from a backup.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [cloudflare, pages, deploy, wrangler, static-site, dns, verification]
    category: devops
related_skills: [cloudflare-worker-app, chat-safe-secret-staging, bitwarden-secrets-manager-hermes]
---

# Cloudflare Pages Site Ship

## Overview
Cloudflare Pages can deploy a static site from the command line, with no browser login and no interactive `wrangler login`. The token comes from the organization's secrets store and is passed to the deploy tool only in its environment. A deploy is not done when the upload command succeeds. The site is done when the live URLs return the expected content. An HTTP 200 alone cannot tell a new design from a stale cached one, so this skill adds a content check on the live response, and it writes artifacts that record what was verified.

## When to Use
- A static site needs to be published or updated on Cloudflare Pages without a browser.
- A site already on Pages is being redeployed, and its custom domain must keep working.
- A deploy must be verified against the live response, and the result recorded.

## Features
- A deploy flow that reads the token from the secrets store at run time and sets it only in the deploy process's environment.
- A content-verification gate on the live pages and assets.
- A custom-domain sequence that avoids a verification stall.
- Artifacts that record the live URLs, the file sizes, and the verification results, without any token value.
- A rollback path that redeploys the previous source from a dated backup.

## Benefits
- No token value appears in a chat, a log, or a command line.
- A stale cache or an unchanged design is caught before the deploy is reported as done.
- Redeploys keep the existing project and custom domain.
- Every deploy leaves a record that a reviewer can check.

## Procedure
### Always-on rules
- Never print a Cloudflare or secrets-store value in chat or in logs. The deploy script resolves the token in memory and passes it to the deploy tool through the environment only.
- Never report a site as live based on the deploy tool's output. Live means a GET on the real URL returns 200 and the response body contains the expected content.

### Step 1: Stage the source folder
Put the site's files in one folder: the HTML, the assets, the headers file, the robots file, and the favicon. Keep no secrets in it.

### Step 2: Back up the previous deploy
Copy the previous source to a dated backup folder before you overwrite it. Rollback is then one command: redeploy the backup.

### Step 3: Write the deploy script
Write the script in a scratch folder. It does four things:
1. Lists the secrets in the store and finds the token by its key name.
2. Reads that secret's value into a variable.
3. Sets `CLOUDFLARE_API_TOKEN` in the environment of the deploy process only.
4. After the operator gives the go-ahead for this release, run the deploy from a clean tree that is committed and pushed. Use a pinned version of the tool. Do not pass `--yes` to `npx` or `--commit-dirty=true` to the deploy:
   ```zsh
   npx wrangler@<pinned-version> pages deploy <source-dir> --project-name <project-name> --branch main
   ```

Reuse the existing project name on every redeploy. Do not recreate the project or the custom domain.

If the project does not exist yet, create it through the API first. A GET that returns 404 is the check, and the create call takes the project name and the production branch:
```zsh
curl -sS -X POST -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.cloudflare.com/client/v4/accounts/<account-id>/pages/projects" \
  -d '{"name": "<project-name>", "production_branch": "main"}'
```
A deploy to a project that does not exist fails with "project does not exist".

### Step 4: Verify the live site in one pass
- GET every page and every asset URL. Record the status, the content type, and the byte count. Compare each byte count with the file on disk.
- Parse the live HTML for the required strings: the brand name, the contact address, the slogan, and the page title.
- Search the live HTML for the forbidden strings: old colors, retired addresses, and any name removed in this release.

Some default HTTP clients receive a 403 from Cloudflare. Send a descriptive User-Agent that names the check, and follow redirects. If the site still refuses it, record the 403 as a limit and let the operator change the site's bot rule. Do not change the User-Agent to pass as a browser.

### Step 5: Apply the content-verification gate
An HTTP 200 cannot tell a new design from a stale cached one. Before you report the deploy as done, confirm these on the live response:
- **Required:** the exact colors, the contact address, the slogan, and the title.
- **Forbidden:** retired addresses, old color values, and anything removed in this release.
- **Assets:** the images are served from the live host, with the right content type, and with the byte count on disk. A 404 fails the gate.

### Step 6: Write the artifacts
Write two files next to the source:
- A result file for this version. It holds the live URLs, the deployment alias URL, the source paths, the slogan, the contact address, the names of the tokens used (never the values), the style reference, the verification time, and the full probe table.
- A deploy manifest in JSON. It holds the project name, the live URL, the alias URL, the token's name, a map of each file to its byte size, the contact address, and the verification time.

### Custom domains
- Attach the domain to the Pages project first, through the project's domains endpoint. Then create the DNS records.
- Create the records as DNS-only, with the proxy off and a TTL of automatic. They verify within a few minutes when the zone is already on Cloudflare. The domain status moves from initializing to pending to active.
- After the domain status is active, turn the proxy on for the existing records with a PATCH on the DNS record. Enabling the proxy before verification can leave Pages reporting "CNAME record not set", and turning it on afterward fixes that.
- Do not change existing MX, SPF, or DKIM records when you add site records. Mail routing depends on them.
- Public resolvers can lag the authoritative name servers by several minutes for a new record. Check the authoritative name server first, for example `dig @<name-server> <host>`, and test with `curl --resolve <host>:443:<ip>` while caches catch up.

#### Redirect the www host to the apex
Use a single redirect rule with a wildcard request pattern and a target that keeps the path and the query:
- Request URL: `https://www.<domain>/*`. Cloudflare requires the protocol in the request URL.
- Target: `https://<domain>/${1}`. A target without `${1}` drops the path.
- Preserve the query string, and set the status to 301.
- Turn on "Always Use HTTPS" in the SSL/TLS edge settings, so that plain `http://www` requests are sent to HTTPS first.

A request pattern for `https://` alone misses plain HTTP requests. Test both ports with `curl --resolve www.<domain>:443:<ip>` and `curl --resolve www.<domain>:80:<ip>`, and check that the path and query survive.

### Tokens and scopes
- Use a scoped API token, not a global key.
- `GET /user/tokens/verify` can return 401 for a valid token that lacks the user-token read permission. Confirm the token with `GET /zones?name=<domain>` or `GET /accounts` instead.
- A Pages deploy token needs Pages edit, account settings read, DNS edit, and zone read, scoped to the domain's zone. Access-protected apps need a separate permission, and a Pages token does not have it.
- Test each endpoint before you promise an operation. A token that works on accounts and zones does not necessarily work on Access, on email routing, or on DNS settings.
- If an operation needs a permission the token lacks, paste the exact endpoint and the exact error into the report, and ask the operator to make that one change. Do not ask the operator to do steps the API can do.

### Cache busting
If the headers file marks CSS or JavaScript as `immutable` with a long `max-age`, a returning visitor can keep the old file for that whole window, even after the deploy. Add a version query to every link to a changed stylesheet or script, and to any import inside a stylesheet. A date-based value such as `?v=YYYYMMDD` works. Do not version the HTML file itself.

## Pitfalls
- **Declaring a deploy live from the upload output.** Verify the live response.
- **Treating a custom-domain DNS delay as a deploy failure.** Check the authoritative name server first, and report the URL that actually returned 200 as the proof URL.
- **Assuming a custom domain survives a redeploy.** Read the previous manifest before you redeploy, because a changed project can drop a domain.
- **Auto-creating a git repository to silence the deploy tool.** Commit the change, push it, and deploy from that clean tree.
- **Pages cannot send mail.** A Pages project cannot bind a mail-sending binding, and a contact form that sends mail needs a Worker that owns its route.
- **Identity mix-ups in the shell.** A token variable that is exported in the shell can override the identity a CLI uses. Clear it for identity-sensitive commands, for example with `env -u <variable-name> <command>`.
- **Sending a private-network address to a client.** Private-network addresses are not reachable from outside the network. Send the Pages URL or the custom domain instead.
- **Serving the site from a quick tunnel.** A quick tunnel stops when the machine sleeps. Pages does not.

## Verification
- Each page and asset returns 200, with the expected content type and byte count.
- The required strings are present, and the forbidden strings are absent, in the live HTML.
- The custom domain returns 200 on its own address, and the redirect keeps the path and query.
- The result file and the deploy manifest exist, and neither contains a token value.
- The previous source is in a dated backup folder, so rollback is one redeploy.
