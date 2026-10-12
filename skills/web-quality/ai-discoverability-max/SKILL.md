---
name: ai-discoverability-max
description: Use when a website must be made as readable as possible to search engines, AI answer engines, generative engines and AI agents, without changing what human visitors see. Covers crawlability, structured data, agent files, accessibility for agent browsers, bot access and a verification gate.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [seo, aeo, geo, mcp, llms-txt, json-ld, robots, accessibility]
    category: web-quality
related_skills: [ai-answer-presence-audit, medusa-docs-first]
---

# AI Discoverability (Search, Answer Engines and Agents)

## Overview

Search engines, answer engines and AI agents read a site through its HTML, its structured data, its agent files and its accessibility tree. This skill makes all four complete and consistent, from one source of facts, while leaving the visual design unchanged. Accessibility fixes are allowed when they are invisible or strictly additive. Everything published must be true. Anything that cannot be verified is recorded as not tested.

## When to Use

- A site needs search and agent readability work, or an audit and fix pass on its discoverability.
- Any task touches head tags, structured data, robots rules, sitemaps, agent files, feeds, markdown copies or accessibility on a public site.

Skip it for visual redesign, for payment, authentication or deployment changes, and for measuring presence in answers (use ai-answer-presence-audit).

## Features

- One data module that every output reads from, so titles, structured data, agent files and feeds cannot drift.
- Crawl and sitemap rules, with separate sitemaps and accurate last-modified dates.
- Structured data validated against the vocabulary and checked against the visible page.
- Agent files (a site summary, a full-text file, per-page markdown copies and a product feed) generated at build time.
- Accessibility rules for agent browsers, and a verification gate with numbers.

## Benefits

- Each fact appears once in one place and is reproduced everywhere it is needed.
- Agents receive the same answer as human visitors, including why a login or gate exists.
- Every claim in the output can be checked against the live site.

## Procedure

### 0. Discover before changing anything

- Identify the framework, the routing, the rendering mode, the content sources and the hosting. Read every route and content collection.
- Work out what the business is, who it serves, what it sells, where, and which legal rules apply: age, region, licence or trade-only access.
- Build one data module that holds the business name, description, contact details, policies, rules and catalog access. Every output below reads from it.
- Record open questions in a file and proceed with safe defaults.
- Write a plan as a checklist that maps to each section below.
- Take baseline screenshots of the main page types, for a visual comparison at the end.

### 1. Crawlability and technical search

- Put the important content in the first HTML response. Essential content must not depend on client-side code.
- Give each page one title (60 characters at most), one meta description (155 characters at most), one canonical link, a language attribute, a character set and a viewport.
- Add Open Graph and social card tags with a per-page image of 1200 by 630 pixels, plus the site name, type and locale.
- Robots file: allow the search and assistant crawlers by name, disallow only private paths such as cart, checkout, account and internal interfaces, and link every sitemap. Never disallow a URL that a sitemap lists.
- Sitemaps: an index that points to split sitemaps for pages, products, categories and articles, with real last-modified dates and only pages that return 200.
- URLs: stable and readable, with a consistent trailing slash, permanent redirects for changed paths, and a real 404 status for unknown paths.
- Filtered and sorted addresses point their canonical link at the clean page, and parameter variants stay out of the sitemaps. Paginated lists use real links between pages.
- Use alternate language links with a default when more than one language or region exists.
- Keep the Core Web Vitals in the good range: largest contentful paint under 2.5 seconds, interaction delay under 200 milliseconds, layout shift under 0.1. Use modern image formats with dimensions set, and load below-the-fold images lazily.
- Add security headers where the host allows them.
- Provide feeds for articles, and submit sitemaps to the search consoles as an owner step.

### 2. Structured data

- Generate one structured-data graph per page from a shared component. Use only the types that match visible content:
  - Organization and website, with a search action only when site search exists.
  - Web page and breadcrumb list.
  - Product and offer, with price, currency, availability and URL, and identifiers only when they are real. Include shipping and return policies.
  - Item list on category pages.
  - Article with a real author, a published date and a modified date.
  - FAQ and how-to only for content that is visible on the page.
  - Local business only with a real location.
  - Reviews and ratings only when they are real and visible.
- Do not publish a price behind a login. Describe how to obtain pricing instead.
- Add a build-time test that fails when the structured data's name, price or availability differs from the rendered page.

### 3. Content for answer engines

- Open each key page with a direct answer of one or two sentences: what it is, who it is for, and what it costs or how to buy it.
- Use question-shaped headings that match real queries, each followed by a 40-to-60-word answer, then more detail.
- Use tables and definition lists for specifications and comparisons, not images.
- Use one consistent name for each entity. Add a glossary page where the domain has technical terms.
- Show who is behind the site: an about page, author biographies, contact details, shipping, returns, privacy and terms pages, and last-updated dates. Cite primary sources for factual claims.
- Make every page reachable within three clicks, with descriptive link text and a hub page for each topic.
- State age, region and trade rules in plain text, so that agents can explain them correctly.

### 4. Agent files

- A site summary file in the standard format: a level-one heading with the site name, a short summary, then sections of links with one-line descriptions. Include an agent-context section that explains who can buy, the age and region limits, why any gate exists, how to apply or contact the business, and what agents may and may not do.
- A full-text file with the markdown of the key pages, generated at build time from the same data.
- A markdown copy of each content page, linked from the page with an alternate link. Where the host allows it, also return markdown when a request asks for it.
- A product feed, if products exist, with the same fields and values as the pages.
- A security contact file under the well-known path. Do not publish well-known files that describe capabilities the site does not have.
- Optional, and only when the feature is detected: expose real site actions to in-browser agents through navigator.modelContext (the WebMCP interface), behind a feature check. Expose only actions the site really has.
- Every agent file returns 200 with the right content type, is linked from the robots file or the summary, and is not blocked by the host's bot protection.

### 5. Accessibility for agent browsers

Agents read the accessibility tree, so:

- Use landmarks (header, navigation, main, footer), one first-level heading and a logical heading order, with a skip link.
- Every control is a real link or button with an accessible name, reachable by keyboard. No clickable divs and no actions that only work on hover.
- Forms have labels, correct input types, autocomplete hints and visible errors linked to their fields.
- Images have useful alternative text, or empty alternative text when decorative. Icon-only buttons have labels.
- Dialogs for age checks, consent and pop-ups are real dialogs, with focus trapped, dismissable by keyboard, and clearly named buttons. Content under them stays in the HTML.
- Key elements have stable identifiers: search, price, add to cart, quantity, navigation and the main action.
- Price, availability and key facts are text in the page, never inside images or canvas.
- Respect reduced-motion preferences, and make sure animation does not hide content.
- Run an accessibility checker with zero serious or critical findings.

### 6. Bot access at the edge

- Check the hosting provider's bot rules for blocks on AI crawlers, bot-fight modes or challenge pages. Agent files and public pages must be reachable by the crawlers the robots file allows.
- Confirm access by reading the rules and by requesting the pages with your own client, and report what your client can observe. Do not send crawler user-agent strings to test whether a challenge can be avoided. List what cannot be tested from outside.
- If analytics exist, label AI and bot traffic rather than dropping it, so the owner can see agent visits.

### 7. Verification gate

Wire these checks into the build or continuous integration where possible, and paste the numbers into the report:

- The build succeeds, and the production build is served locally.
- Every route returns 200, no internal link is broken, every sitemap address returns 200, and no sitemap address is disallowed.
- Structured data validates against the schema vocabulary and matches the visible content.
- A mobile performance and accessibility audit on key pages reaches the target scores set by the team.
- An accessibility checker reports zero serious or critical issues.
- The agent files, the sitemaps, the feeds and the markdown copies return the right status, content type and content.
- The main content, prices and headings are present in the raw HTML, without running client code.
- Visual comparison with the baseline screenshots shows no change beyond accessibility fixes.

### 8. Deliverables

- Small, well-named commits on a new branch. Do not push to the main branch and do not deploy.
- A report: what was added, where each file lives, the test results with numbers, anything skipped and why, and open questions.
- A maintenance note: how the agent files, sitemaps, feeds, markdown copies and structured data stay in sync when content changes, and how to rerun the checks.
- A list of owner steps: submit sitemaps to the search consoles, confirm the robots choices, confirm what gated prices agents may see, and approve the deployment.

### 9. Audit mode (read-only, no changes)

When the request is an audit rather than a fix:

- Make GET requests only, signed out, one at a time, at least 0.6 seconds apart, with a descriptive User-Agent that names the audit. A HEAD request is not a GET.
- Fetch the robots file, the summary file, the full-text file, every sitemap the robots file names, the feeds, the well-known files and a sample of pages. Judge each against its specification, and cite the specification in the report.
- Mark each item PASS, GAP, INFO or NOT TESTED. Give each gap a fix and the generator file that owns it.
- Check every link in the agent files. List every dead link with the file and line where it appears, and treat placeholder patterns explicitly.
- Compare structured-data price and stock for every variant with the feed and the summary file.
- Check canonical links and robots headers for each page type. Flag a gated route that is neither disallowed nor set to noindex.
- Verify every number in the report against the data before it ships.

## Pitfalls

- **Speed work should target one element per page.** Raising the priority of several images at once can slow the real largest element. Measure which element is the largest, prioritise only that one, and compare before and after.
- **A "no visual change" performance fix must not re-encode or crop an image people see.** Changing the pixels is a visual change. Use preloading and fetch priority on the existing file instead, and check with a pixel comparison at threshold zero.
- **Name the largest element from the performance report before naming a cause.** Read the element's selector and its timing breakdown first.
- **Do not measure under heavy host load and call the result a benchmark.** Note the load, use simulated throttling, and take the median of several runs.
- **Catch-all responses fake the agent layer.** Some hosts return 200 with HTML for unknown feed paths. Check the content type, and return a real 404 for unknown paths.
- **Canonical links can point at an old host after a domain change.** Check that the canonical host equals the serving host on every page type.
- **A gate that redirects every unknown path turns missing pages into soft 404s.** Exempt unknown paths and the version endpoint from the gate.
- **A build timestamp used as the last-modified date** makes every page look updated at once. Omit the date when no real one exists.
- **Model-context tools must be honest.** Do not expose an add-to-cart tool to visitors who cannot buy.
- **Markdown copies need one per page.** A single site-wide link to one file is not a copy of each page.
- **An agent file that contradicts a live policy page is a hard defect.** Quote both sides, and fix the template that generates the file rather than individual pages.
- **A one-byte range request** proves that a linked file exists without downloading it. Use it for linked certificates and images.
- **Product label-and-value rows can render with a line break and a dash.** When matching a fact, use a pattern that allows for this.
- **Audits without fixes waste the cycle.** Turn each finding into a fix task, rather than commissioning another audit.

## Verification

- The verification gate numbers are in the report, with the command or check that produced each one.
- Each agent file, feed and markdown copy returns the right status and content type.
- Structured data matches the visible page for every product checked.
- No visible design change beyond accessibility fixes, shown by the visual comparison.
- The report lists everything that could not be tested from outside.

## Attribution

The structure follows the public llms.txt proposal (https://llmstxt.org) and the schema.org vocabulary (https://schema.org).
