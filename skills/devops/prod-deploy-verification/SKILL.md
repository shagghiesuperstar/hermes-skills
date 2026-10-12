---
name: prod-deploy-verification
description: Use when telling anyone that a change is live or fixed. Proves that the production build contains the change, using the deployment record, the bundles the production page loads, and live behavior.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [deploy, production, verification, caching, release, leak-check]
    category: devops
related_skills: [storefront-release-publish, medusa-cloud-ops, pr-evidence-verification, review-then-ship]
---

# Production Deploy Verification

## Overview
A fix that exists only on a preview, on an unmerged branch or in the repository is not fixed for users. Saying "fixed" while production still serves the old build destroys the trust of the people who test against it. Before you claim a change is live, prove it from the deployed artifact: the platform's deployment record, the bundles the production page actually loads, and the live behavior. Do not rely on the repository, and do not rely on a version endpoint that may be cached.

## When to Use
- You are about to tell someone that a change is live, fixed or done.
- You merged a change and need to confirm that the deploy picked it up.
- A tester's screenshot shows a defect you believe is already fixed.
- You are about to say that everything is merged. List the surfaces that matter first, then verify each one. A merged change is not the same as a visible change on every site, and different sites can sit on different branches.

## Features
- A bundle check that fetches the page, extracts every script and style file it references, and searches all of them.
- A deployment-record check that matches the row's commit to the expected commit and requires the deployed status.
- A watcher pattern that does not fire on an intermediate deploy of a different commit.
- A list-surface leak check, an allow-list projection, and a backend check with the public storefront key.
- Triage steps for a build that failed in one tier, a stale browser tab, and a stale build cache.

## Benefits
- A claim of "live" carries the commit and the evidence that proves it.
- A cached version endpoint cannot make a finished deploy look stalled.
- Leaks on every list surface are found, not only on the page that was tested first.
- A build failure is diagnosed from its log before anyone retriggers it.

## Procedure

### Rules for the claim
1. "Fixed" means fixed on production. If a change is only on a preview, say so: "fixed on preview, awaiting the operator's go-ahead to deploy." A deploy to production needs a clean, pushed tree and the operator's explicit go-ahead for that deploy. Never auto-confirm a production deploy, and do not hold a confirmed fix behind a sign-off nobody required.
2. A standing instruction to ship is not an explicit go-ahead for a particular deploy. Before a production deploy, verify that the tree is clean and pushed, check the rollback and the data dependencies, and ask the operator for the go-ahead. After the deploy, report the evidence. Raise a concern in the same message only when one exists.
3. The repository's code is not evidence. Verify in the deployed bundle.
4. Before you report that production is behind the main branch, cross-check two sources: the platform's deployment record and a behaviour check on the live page. Do not rely on a self-reported version endpoint alone.

### Verify the deployed bundle
1. Fetch the production page with the audit's descriptive User-Agent. If the site refuses that User-Agent, log the refusal as a limit of the probe.
2. Extract every script and style URL it references, and remove duplicates. A page can reference several stylesheets, and a token can live in only one of them. Search all of them before you conclude that a fix did not deploy.
3. Search for the exact changed tokens: class names, values and expressions. A minifier can rewrite an expression, so search for both spellings, such as `calc(0.65 * var(--x))` and `calc(var(--x) * .65)`.
4. For a removal, scope the search to the route's own page and layout files. A deleted usage does not remove the same class from shared styles or from other components. The stronger check is the replacement: its token should appear in the route's own page.
5. A component's text can live in a client-side script rather than in the page HTML. If the HTML search finds nothing, search the page's script chunk for the same text before you conclude that the deploy missed it.
6. Search rendered text by its source case, not its displayed case. A CSS uppercase transform displays capitals while the HTML keeps the original case.

### Watch the deploy
1. Merge, then read the pull request's state. Claim the merge only when the state is merged and the merge timestamp is set. A closed pull request with no merge timestamp is not merged.
2. Read the platform's deployment record for the new build. For Medusa Cloud, list the deployments for the project and environment, and filter the rows on the commit hash. The backend and storefront have separate statuses, and they can differ by seconds. Read both columns.
3. Arm the watcher to match the expected commit, not the disappearance of the old one. A watcher that fires when the old commit goes away can fire on an intermediate deploy of a different commit.
4. A row counts as live only when its status is deployed. Building, deploying or queued is not live, even when the commit is already listed.
5. Trigger a build only after the operator's go-ahead, on a clean, pushed tree, and only when no build for the commit is in progress. A second trigger on the same environment can cancel an in-flight storefront build. A canceled status seen during a poll is not final, because it can change to deploying and then to deployed. Stop only on a failed status, or when the build finishes and the storefront never leaves canceled.
6. Quote the build identifier, the commit, the status and the search result in your message.

### Treat a version endpoint with care
Before you trust a version endpoint, read its cache headers. If the response is marked immutable, or carries a maximum age measured in years, it can keep returning an old commit after the new deploy is live. Treat it as decoration, not evidence. The platform's deployment record is authoritative, and the bundle search corroborates it. A version endpoint on a host that is not the one serving the page can also be wrong about what is served, so check which host serves which surface.

### Check every list surface for leaks
A sanitizer that strips internal fields before a product reaches a client component protects only the surfaces it is wired into. A home shelf, a related-products rail or a search page added later can skip it and expose wholesale prices or internal identifiers in the page.
1. Find every server-rendered path that ships a product object. Search the code for the components and data hooks that list products, and treat each match as a path to check.
2. For each path, fetch the live route and search the response for every internal field name. A match on any surface is a leak. The only acceptable result is zero on every surface.
3. Replace a deny-list with an allow-list projection that keeps only the fields a card shows. Apply it at every call site, and confirm that the internal field names do not appear in the projection.
4. Confirm that shoppers see the same output. Snapshot the rendered pages before and after the change, and compare them as multisets, because streamed sections can arrive in a different order.
5. Fields added later must be omitted by default unless they are added to the allow-list.

Check the backend too. Storefront filtering does not stop the backend from returning the same fields to anyone holding the public storefront key, and that key ships in the storefront's own script bundle. Request the product list with the public key and search for each internal field. If a sibling application reads a field from the public API, stop and report before you remove it from the backend. Move that reader to an authenticated route first.

### Check business-identity fields on every surface
When an address, a phone number or a legal name changes in a shared constants file, find every page that renders it: the footer, the contact page, the policy pages, the structured data and any generated text files. Count the new value on each surface, and count the old value on each. The old value must be zero everywhere. Quote the rendered text as proof, not the code. Chat tools can rewrite phone numbers when they are pasted, so count them in code rather than copying them.

### Check that design flags match production
Before you pin a feature flag to a value for production, read every branch of the code it controls, and state what each value renders. A flag that looks like a test switch can be the approved look. Quote the decision that chose the value. A release checklist should not list a design flag as "off in production" by default.

### Triage a build failure
A backend and a storefront build independently. A deployment can show the new backend live while the storefront failed. The old storefront still serves, and the live site looks healthy.
1. Read the compiler error first. For Medusa Cloud, read the storefront build log for the build identifier, and find the file and line.
2. Do not retrigger a build for a compile error in the code. The same commit fails the same way. Make a follow-up change from the base tip instead.
3. A module marked for server actions can export only async functions. A constant exported from such a module fails the build, and the failure passes review. Move constants to a sibling module without the marker, and check the export list before you merge.
4. A stray backtick in a comment inside a template literal can end the template early, and the compiler then reports an error far from the cause. Check the comments in that block for backticks.
5. If the failing commit was the tip of the environment's tracked branch, push the fix as a single commit on that branch. The push starts a production build, so get the operator's go-ahead before the push. List the deployments before you trigger one by hand.
6. Cut the fix in its own worktree when the main checkout is dirty or in use. Check that the diff stays inside any path the task locks, and confirm that the remote branch points at the new commit.

### Check the build cache
A cached build directory can carry output from an older commit into a new deploy. If a build stamp inside the compiled output names an older commit than the deployment, exclude the cache folder from the build outputs, and rebuild.

## Pitfalls
- **Searching only the first stylesheet or script.** A page can reference several, and the token can be in the second.
- **Trusting a cached version endpoint.** Check its headers first, then use the deployment record.
- **Treating a building status as live.** Only deployed counts.
- **Retriggering over a build in progress.** This cancels the build that is running.
- **Telling someone to refresh before checking.** Confirm the live artifact first. If it is correct and the tester still sees the old page, the cause is the browser's cache, and the refresh instruction goes with your fresh evidence.
- **A stale tab after several deploys.** A form that submits to a server action can fail with "not found" when the tab was opened before a deploy. Load the page fresh. If the fresh load works, the cause is the stale tab, not the code.
- **A refused User-Agent is a probe limit.** A custom domain behind bot protection can still refuse scripted requests. Check the platform host it maps to, and log the refusal as a limit of the probe, not as a failed deploy.
- **Measuring what the eye does not see.** Compare the top edges of rows, not the gaps between them. Measure before and after each change.
- **A partial ship.** When one merge claims several fixes, check the live output for each one separately.
- **A branch cut from an old local commit.** After a squash merge, branch from the current remote tip.
- **Heavy images.** Check the bytes the live page actually serves, and serve smaller renditions for list tiles. A new rendition file that no template uses does nothing.

## Verification
- The bundle search covers every referenced script and style file, and each changed token is found.
- The deployment record shows the expected commit with the deployed status for the tiers the change needs.
- The leak search returns zero for every internal field on every list surface, and on the public backend API.
- The claim quotes the build identifier, the commit, the status and the search result.
- Any claim that the site is behind is cross-checked against the deployment record and a live page check.
