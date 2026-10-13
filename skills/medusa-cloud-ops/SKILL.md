---
name: medusa-cloud-ops
description: Use when Medusa Cloud auth expires or a build is needed. It also triggers storefront or backend builds and proves a deploy runs a specific commit. Covers auth refresh, build triggers, commit verification, tracking branches, variables, domains, backups, and triage.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [medusa, medusa-cloud, mcloud, deployments, builds, storefront, verification]
    category: devops
related_skills: [medusa-docs-first, medusa-api-verification, storefront-release-publish, prod-deploy-verification]
---

# Medusa Cloud Operations (mcloud)

## Overview
Medusa Cloud builds and deploys a backend and a storefront from a tracked branch. The CLI reports build rows, and each row has a status for the backend and for the storefront. A build is not proof of what is live. The proof is the backend's version endpoint, which reports the commit that actually booted. This skill covers the operating procedure: keep the CLI authenticated, trigger a build only when none is in flight, verify the live commit, and handle variables, domains, backups, and failures without exposing secrets or breaking a live site.

## When to Use
- The CLI reports an expired login, or a command returns 401.
- A build must be triggered for an environment, or a redeploy must be proven for a commit.
- A domain, a sender domain, a variable, or a tracking branch must change.
- A build or a storefront fails, and the cause must be found.

## Features
- An auth gate that runs a real read after the identity check, because the identity check can pass with an expired token.
- Environment resolution by type and exact name, with preview environments kept separate from long-lived ones.
- A commit check that reads the backend version endpoint and compares it with the tracked branch tip.
- Deploy-rule and tracking-branch checks that use a before-and-after snapshot.
- Two-round domain procedures that avoid repeated verification posts.
- Triage recipes for storefront errors, payment setup errors, and failed migration scripts.

## Benefits
- No secret value appears in the transcript.
- A build row that reports success is never mistaken for a live deploy.
- Live sites are not broken by a DNS change or a rule change that was not checked first.
- Each failure is traced to the layer that caused it: auth, configuration, code, or vendor.

## Procedure
### Always-on rules
- Check auth before any command, with a real read. Run `mcloud whoami --json` for the identity, and then one read command such as `mcloud projects list --json`. Treat a 401 on the read as an auth failure even when `whoami` looks fine.
- Never list variables with values in the output. Use `mcloud variables list` with the names only, and do not reveal values in a transcript. Some JSON output includes values, even for rows marked secret. Write any such output to a file, and print only the key names.
- Never run a trigger while a build for the same commit is still in progress. The API cancels the live build and starts over. List the deployments first, and filter the rows on the commit hash. The list has no commit filter flag.
- Read a build's commit from its `commit_hash`. Field names such as `commit`, `sha`, or `git_sha` are not in the list or get output, so a query on them returns null and suggests a wrong commit when there is none.
- Derive a preview URL from the environment's `default_domain` field. Never type a domain by hand, and never guess a host name and probe it.
- Some operations need a person. A two-factor code, a browser sign-in, and a dashboard-only step belong to the operator. Ask the operator for the one action, and never type a code on their behalf.

### Step 1: Check authentication
Run the identity check and one read:
```zsh
mcloud whoami --json | jq -e '.auth.kind != "none" and .organization.id != null'
mcloud projects list --json > /dev/null
```
An expired token reports the old expiry date in `auth.expires_at`, and API calls return 401. Refresh before you start a ship day, not after the first failure.

To refresh, back up the credentials file first. Then run the login in a background terminal that has a TTY, and wait for the success line. The login opens the default browser, where an existing session can complete the sign-in. The login times out after about three minutes, so ask the operator to be at the machine before you start it. After the login, decode the new token's expiry and confirm it is about a day away.

If the browser session has also expired, the sign-in asks for a second-factor code. That code is for the operator only. Ask the operator to enter it in the open browser tab, then continue.

### Step 2: Resolve the environment
```zsh
mcloud environments get <name-or-handle> --organization <org-id> --project <project-handle> --json
```
Record the identifier, the handle, the default domain, and the status. A preview environment for a branch is not the long-lived target. Match on `type: long-lived` or on the exact environment name.

### Step 3: Check for a build in flight
List the deployments, and filter on the target commit hash. A cancelled build can still show a successful storefront column, so read both status columns before you decide what shipped.

### Step 4: Trigger a build only when needed
```zsh
mcloud environments trigger-build <env-id> -p <project-handle>
```
The trigger command returns an empty object on success. The new build identifier appears in the next deployment list, not in the trigger output.

Use a redeploy only for a runtime variable change. A redeploy reuses the active build image, so a build that never started will not start this way. For a source change, or for a build-time variable, trigger a new build.

### Step 5: Verify the commit that is live
A build is done when its row reads deployed on both the backend and the storefront columns. The build is proven when the backend's version endpoint reports the commit you expected:
```zsh
mcloud deployments get <build-id> --json | jq -r '.commit_hash'
curl -fsS "<backend-url>/version"
```
The `commit_sha` in the version response must equal the full tip of the tracked branch, all 40 characters. A short preview hash is not enough. A mismatch means the build did not boot the commit you think it did. Report both values, and do not claim the tip is live.

The storefront's own version page can be a stamp committed at build time, so it can show a stale commit. Use the backend's version endpoint as the deploy check.

Poll the deployment list at intervals, and stop when both columns read deployed. A loop that reads the first row, and exits on success, is enough:
```zsh
for i in 1 2 3 4 5 6 7 8; do
  mcloud deployments list --json > deployments.json
  python3 -c "import json,sys; top=json.load(open('deployments.json'))[0]; sys.exit(0 if top['backend_status']=='deployed' and top['storefront_status']=='deployed' else 1)" && break
  sleep 25
done
```
The list output is a bare array of rows, not an object with an items key.

### Step 6: Report with a live artifact
Report the build identifier, the commit, the environment, the preview URL from the default domain, and when to check back. A build takes about ten to fifteen minutes. Use a field block:
```text
BUILD=<build-id>
COMMIT=<full sha from the build row>
LIVE_SHA=<commit_sha from the backend version endpoint>
ENV=<environment handle>
URL=<default domain>
STATUS=DONE|BLOCKED
BLOCKER=<one line, or none>
```

### Deploy rules and tracking branches
- An environment can track a branch, and it can have a deploy rule that gates a deploy by commit-message text. A rule gates the deploy step, not the build. Builds still start on every push to the tracked branch, so a new building row does not show that a rule failed.
- The deciding test is the backend's version endpoint. Before a merge that a rule should hold back, record the current commit and build time. After the build settles, read the version endpoint again. An unchanged commit means the rule held. Any change means it did not.
- A marker string in a commit message can match a rule anywhere in the full message, including a squash body. Do not write the marker in commit text or pull request text unless you intend to deploy. Write it in prose instead, such as "release marker".
- Read rules with a plain read command or the environment's JSON output. A nested field can read as null even when a rule is set. Confirm a rule with a second read before you rely on it.
- If a live environment is tracking a working branch and not the main branch, merges to main will not deploy. Check the tracked branch with `mcloud environments get <env> --json | jq -r '.external_id'` before you plan a ship.

#### Repointing an environment to a working branch
When `main` carries changes that must not ship yet, do not merge to main. Cut a working branch from the live commit, add only the change, and point the long-lived environment at that branch:
1. Read the live commit from the backend version endpoint, not from the storefront stamp.
2. Create the branch from that commit, add the change, and push.
3. Repoint the long-lived environment to the branch, and trigger one build.
4. Verify that the backend version endpoint reports the branch tip.
5. Before you repoint, write a restore note with the previous branch, the previous commit, and the previous build identifier, so a later step can return the environment to main.

### Variables
- List variable names with `mcloud variables list -p <project> --type <backend|storefront>`. Probe a variable with `get` only when you know its type. A storefront variable read with the backend type returns "not found", and that does not mean the variable is missing.
- Set variables with `mcloud variables set <KEY> <VALUE>`. For a value that must not appear in a transcript, pipe it from a generator, and do not echo it.
- A variable change does not apply by itself. A runtime variable needs a redeploy. A variable that the storefront reads at build time needs a new build. Storefront variables with the public prefix are baked into the bundle at build time, so a missing one produces a bundle that calls localhost, and a redeploy does not fix it.
- A deleted variable needs an explicit confirmation flag. Check before you run it.

### Domains and sender domains
- Add a domain through the API with the entity's identifier and the domain type. Types include sender, storefront, and backend. The response lists the verification records to create at the registrar.
- Verify a domain with one POST after the records are live. Poll the domain with GET only. Each verification post on a failed domain can issue new verification values, and the values you gave the operator then go stale.
- For a storefront domain, plan two rounds of DNS work. Round one is the ownership record and the proxy record. Round two is the certificate challenge record, which the service returns only after the proxy records point at it. Between the two rounds, the old host can fail TLS, so send the operator the round-one and round-two records together, with a clear window.
- Before a DNS switch away from an old host, check that no live asset is served from that host. Count the product images and document URLs by host on the live API. A non-zero count on the old host means the switch deletes assets, so hold the switch.
- Adding a storefront domain can add origin-allow regexes without an anchor. Replace them with exact origins at cutover.
- If an apex on a flattening alias record sits in a finalizing state for hours, moving the nameservers to a provider that flattens CNAME records is a known fix. Plan the rollback before you start.
- Verify DNS with the registry's own data and a public DNS-over-HTTPS query. A local resolver can return a stale cached answer that lacks the authoritative flag.

### Backups and destructive imports
- Create a manual database dump through the API, and poll for the new backup row. Verify a downloaded dump with the PostgreSQL list command before you rely on it.
- A database import in REPLACE mode deletes existing rows in the target. Treat it as destructive. Take a fresh backup first, get explicit approval, and have a rollback plan that includes the admin accounts.

### Logs and incident triage
- Pull logs for each layer with a bounded time window, and write them to files:
  ```zsh
  mcloud logs -p <project> -e <env-id> --type storefront --from <ISO-time> --limit 2000 --json > sf.json
  mcloud logs -p <project> -e <env-id> --type backend --from <ISO-time> --limit 2000 --json > be.json
  ```
- Production error pages redact the error digest. Search by the path, the time window, and the status code. The digest number does not appear in the logs.
- Correlate the storefront and backend logs by time. A storefront error from a null read is usually a missing optional-chain check in the code.
- A storefront that shows an idle status after a deploy usually means the build artifact is uploaded but the runtime did not start. Trigger a new build. If the same status persists, read the first line of the storefront build log, which names the directory the build used. A wrong directory means the storefront root path is wrong.
- A storefront that returns a redirect to the same path on every request is a middleware loop in the application code. A new build does not fix it, so route the code fix to the application's developers. A redirect from the root to a locale path is normal routing.
- A build that fails in the font loader with a null read can be a transient fetch failure. Retry once after no build is in flight. If it fails twice, switch to local font files.
- A build can show a failed storefront after a clean build log. Retry once. Diagnose only if the retry fails too.

### Payment and shipping triage
- A checkout error on a preview with a payment-session failure usually means a missing provider key. Compare the key names on the backend and on the storefront with the names the provider module reads. Use the backend log line to tell a configuration gap from a code gap.
- A custom shipping provider needs three things. The constructor's dependency lookup throws on unregistered keys, so read optional dependencies inside a try block. The provider must be added to the stock location before an option can use it. The products must be linked to the option's shipping profile, or the provider receives an empty item list and returns its base price.
- Prove shipping prices with live store cart calls, not with unit tests alone.

### Migration scripts
- A one-time migration script runs once per environment on deploy, and it is not retried if it reports success. A step that logs and returns on error makes the failure silent. Let the script exit non-zero on a real failure, and collect the step errors at the end.
- A deletion that finds the row already gone is a success for a partial rerun, not a failure.
- The deploy command can exit with success even when a script threw. Read the affected rows through the admin API or a database read after each deploy, and do not trust the build status alone.
- Test the actual script under the real migration runner against a side database, and check the exit code, the row state, and the log message.

## Pitfalls
- **Trusting the identity check.** A token can report a valid identity and still fail every read. Run a real read.
- **Printing variable values.** Structured output can include secret values. Write it to a file and print only the names.
- **Triggering over a running build.** The running build is cancelled and restarted from zero.
- **Declaring a deploy live from the build row.** Check the backend version endpoint for the commit.
- **Assuming a preview hostname.** Read the default domain from the environment.
- **Looping a verification post.** Poll with GET, and post once per round.
- **Sending a test email to a shared admin address.** Use an address that a person checks, and never copy an admin address into notes.
- **Restarting a shared gateway to fix one site.** Restart only the service that has the problem.
- **Reusing a repointing note after the environment changes.** Read the live tracking branch again before each ship.

## Verification
- The identity check and a real read both succeed, and no variable value appears in the transcript.
- The build row shows deployed on both columns, and the backend version endpoint reports the tracked commit.
- Each domain record and each rule change was read back after it was made.
- Any repointed environment has a restore note, and it returns to its previous branch once the change is verified.
- Each incident report names the layer that failed, with the log line that shows it.
