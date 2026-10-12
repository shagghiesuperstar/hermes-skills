---
name: live-link-audit
description: Use when auditing a live storefront for broken links, redirect chains, sitemap errors and mixed http. Read-only crawl, per-row CSV, draft PR.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [link-audit, redirects, sitemap, robots, crawl, seo]
    category: web-quality
related_skills: [storefront-code-audit, cro-baseline-audit, live-storefront-feed-parity, catalog-data-audit, data-artifact-adversarial-review]
---

# Live Link Audit (Read-Only HTTP Crawl, Per-Row CSV, Draft PR)

## Overview
A polite, read-only crawl of one live site that checks every link it can reach: status code, redirect chain, final URL, robots.txt coverage and mixed-protocol use. The output is a per-row CSV, a narrative report and one draft PR. The crawl is a probe, not a visitor: it sends no cookies, forms, cart requests or sign-ins. The report states only what the CSV contains and never claims a defect the data does not show.

## When to Use
- The request is to crawl a deployed storefront for broken links, redirect chains, sitemap 404s, mixed http/https links or orphan pages.
- The deliverable is a per-row CSV, a report and one draft docs PR.
- For a source-code review of in-app hrefs, use `storefront-code-audit`. For UX on mobile and desktop, use `cro-baseline-audit`. For feed-versus-page parity, use `live-storefront-feed-parity`.

## Features
- Robots.txt enforced on every redirect hop, with an RFC 9309 matcher (longest match, Allow wins ties, `$` anchors the end of a URL).
- Manual redirect following, one hop at a time, so every hop lands in the chain column.
- Three crawl passes: seed pages, unique target probes and sitemap children.
- Row-level flags for 4xx and 5xx, chains longer than one hop, mixed http, retired hosts and robots-blocked targets.
- Internal-link graph with inbound counts, orphans and weakly linked pages.
- Sitemap reconciliation: `<loc>` count, unique count, fetched count and a status breakdown.

## Benefits
- Every link is recorded with its source, region and status, so a reviewer can re-check any row.
- Coverage gaps from robots.txt appear first in the report, not buried in method notes.
- Counts are derived from the CSV, so the prose and the data agree.
- Bot-wall 403s and publisher redirects are separated from real site defects.
- The crawler uses only the standard library, so a re-run on another machine reproduces the same outputs.

## Procedure

1. **Confirm scope and robots.txt first.**
   - Crawl only the host named in the request. An outbound target gets one status check, with no follow-up crawl.
   - Name each seed source (an explicit list, the sitemap, or the home page plus navigation and footer targets) and count it.
   - Fetch `robots.txt` before anything else. List every `Allow` and `Disallow` line, then reconcile the seed list and the sitemap against the disallowed paths. Name every page that will not be fetched in the report's first section.

2. **Set the probe identity and pace.**
   - Send a stable, descriptive User-Agent, for example `<bot-name>/<version> (link audit; read-only)`. Browser User-Agents invite bot-wall 403s that get reported as broken links.
   - Run requests one at a time, with a floor of 0.6 s between any two requests, so the rate stays at or below about 1.67 requests per second. Use one throttle for internal and outbound requests.
   - Use the standard library (`http.client`, or `urllib` with automatic redirects turned off). Send no cookies, form data or cart or sign-in requests.

3. **Apply robots.txt on every hop.**
   - Implement the RFC 9309 matcher: the longest matching rule wins, `Allow` wins a tie, `$` anchors the end of the URL, and rules apply per user-agent group.
   - Check each redirect hop against its own host's robots.txt, then check the final URL. A redirect that lands on a disallowed path is disallowed, even when the first hop was allowed.
   - For a third-party host, a single check with the standard library robot parser is enough. Treat a 5xx or connection error on that host's robots.txt as a full disallow, as RFC 9309 specifies, and state that choice in the method section.
   - Record each blocked URL as `ROBOTS_DISALLOWED` and state in the report that its health is unknown.

4. **Crawl in three passes.**
   - *Pass 1, seed pages.* Fetch each seed. Extract `<a href>`, `<link rel="canonical">`, `<link rel="alternate">`, and absolute URLs inside JSON-LD and inline JSON payloads. Join streamed script chunks before running the regex (see Pitfalls).
   - *Pass 2, targets.* Fetch each unique target once and cache the result. Follow up to eight redirects by hand and record every hop. For outbound targets, request headers only.
   - *Pass 3, sitemap.* Fetch the sitemap index, every child sitemap it lists, and every `<loc>` in each child. Record status, chain and content type for each row.

5. **Probe hygiene redirects and soft 404s.** For each host, check `http` to `https`, `www` to the apex domain, the trailing-slash behaviour and the root. Request one nonexistent path to detect a soft 404, which is a 200 page served for a missing URL.

6. **Tag regions and fragments.** Assign each link a region with this precedence: footer, then header, then nav, then main. A nav nested in a footer reports as footer. Check same-page `#fragment` links against the ids on that page. Scan the raw HTML for `http://` attributes and for links to hosts the site has left, in addition to checking anchors.

7. **Build the internal-link graph.** Resolve each internal URL against its page, strip the query, fragment and trailing slash, and keep same-host links only. An orphan has zero inbound links from other crawled pages. List pages with four or fewer inbound links separately as weakly linked, and say which of them are linked only from an index page. An orphan's cause stays unverified until someone checks it.

8. **Write the outputs.**
   - `links.csv` columns, in this order: `source`, `target`, `status`, `chain`, `final_url`, `redirects`, `kind`, `region`, `flags`.
   - `sitemap.csv` has one row per `<loc>`.
   - `summary.json` holds counts, per-status and per-flag totals, and the sitemap reconciliation.
   - `REPORT.md` is generated from the CSV by code, so every count comes from a counter, not from typing.
   - `status` is a final HTTP code or one of `ROBOTS_DISALLOWED`, `SKIP_SCHEME`, `DNS_ERROR`, `TIMEOUT`, `EXCEPTION`. `tel:` and `mailto:` links carry `SKIP_SCHEME` and are not fetched.
   - `flags` include `REDIRECT_1HOP`, `REDIRECT_CHAIN_GT1`, `MIXED_HTTP`, `ROBOTS_DISALLOWED` and `RETIRED_HOST`, plus any others you define and document. Redact phone numbers from the output.

9. **Report in this order.**
   1. Bottom line in two to four sentences: broken count, sitemap error count, redirect count, coverage gap.
   2. Coverage gap: the blocked paths and the number of unverified pages. Put it first, not in the method section.
   3. Counts: requests made, wall time, mean rate, pages fetched, link occurrences, unique targets, internal versus outbound, per status, per flag. Define the dedupe next to each deduped count, for example `unique targets: N (fragment-stripped; probe rows and sitemap child rows excluded)`.
   4. Findings: every flagged row, sorted by flag then source, with its chain, source page and target.
   5. One fix per flag: a short paragraph each. If the URL lives in a repo file, name the file and line after reading that line. If it lives in content or a data source, name that source and state that the fix is outside the repo.
   6. Not checked: static assets, client-side navigation, transient bot-wall 403s, and third-party targets judged by a single GET.
   7. Method: User-Agent, rate, the robots matcher in one paragraph, redirect policy, the three passes, run date.
   8. Evidence: commands run, output paths, the seed list and the PR URL.

10. **Verify before the PR goes out.** A reviewer checks four things, so check them first.
    - Re-derive every count in the report from `links.csv`.
    - Byte-compare the committed artifacts against the local run with `cmp` or a checksum.
    - Diff the live `href` values on each page against the CSV targets for that page. Only static asset and icon URLs should be missing. A missing content link is a recall gap.
    - Resolve each cited repo `file:line` at the PR head, after reading that line. A guess one line off is a defect in a report whose product is the pointer.

11. **Open one draft PR.** Branch from the default branch, add only the audit directory, and open a draft. The PR body restates the bottom line, the coverage gap, scope and safety (read-only, no forms or cart), the engine or model used if any, and a line stating the diff is docs-only so the build was skipped on purpose. Do not merge.

### Sitemap status details

- Count the `<loc>` entries and the unique entries. Unescape HTML entities in the values. Report duplicates as an observation, and say each duplicate was fetched twice.
- For each URL, record the status, the final URL after redirects, the `X-Robots-Tag` header and the content type.
- Sitemap `<loc>` hosts can differ from the public domain. If the published host fails and the live host returns 200, record both and report them as one root-cause finding together with the canonical, `og:url`, alternate and robots `Sitemap:` lines.
- Zero non-200 rows is a valid result. Say so plainly; do not pad the report.
- Detection covers server-rendered HTML only. Client-injected content will not appear in the results.
- Do not speculate on why a page carries a noindex header. Report the header and ask the owner to confirm the intent.

### Internal link suggestions (optional)

- Propose links only to URLs that were fetched and returned 200. Do not invent pages.
- Anchor text names the product or category. No efficacy, medical or other claims in anchors; flag any anchor that needs compliance review.
- Never link to a page marked noindex.
- Give each suggestion a reason, and tag it as already present in the page HTML or as new.

## Pitfalls
- **Joined payloads prevent false DNS errors.** Frameworks that stream page data in script chunks, such as the Next.js `self.__next_f.push` payloads, can split a URL across two chunks. A regex over each chunk alone produces DNS errors for partial URLs. Join all chunks before extraction, then compare the DNS error count before and after.
- **Trailing slashes are different URLs under `$`.** A rule that allows `/path$` matches `/path` but not `/path/`. Note the trailing-slash behaviour in the report when a header or footer link points at the other form.
- **A first-hop robots check is not enough.** A 301 through an allowed host that lands on a disallowed host is blocked. Apply the matcher to the final URL.
- **Mixed `http://` links are a flag, not an error.** Record the link as written in the page or file. Do not rewrite it to `https://` in the report, because a 200 on `http://` is a different finding from a 200 on `https://`.
- **Contact links are not broken.** `tel:` and `mailto:` are not fetched. Redact phone numbers in the CSV.
- **Data-driven links live outside the repo.** A link from CMS or product data appears in no code file. Name the data source as the place to fix it.
- **A retired host is a finding even when it returns 200.** The site has moved away from that host, so the link should not exist.
- **Publishers and bot walls produce transient failures.** A single 403 from a third-party publisher often does not reproduce. Re-check once with a different fetcher or a real browser, then state which evidence you have.
- **Gates are findings, not crawl failures.** A signed-out redirect to a login, age or access gate is a reachability finding. Name the file that defines the rule. Do not bypass the gate to reach more pages.
- **Long crawls must survive a restart.** Run the crawl as a background process that writes a log. Persist each row as it completes, and set a hard timeout on every request. A socket timeout resets on every read, so a slow response that trickles bytes can stall for minutes.
- **Row counts and unique-target counts differ.** One link on 50 pages is 50 rows and one target. Report both.
- **Do not state a cause you did not check.** The cause of an orphan, or of a soft 404, stays unverified until someone reads the code or the CMS.

## Verification
- Every count in the report matches the value you get by re-deriving it from `links.csv`.
- `summary.json` totals equal the row counts in `links.csv`.
- A second run of the crawler produces byte-identical `links.csv` and `summary.json` for the same crawl window.
- The PR body carries the docs-only line, and `gh pr view <n> --json isDraft,files` shows a draft with every file under the audit directory.
