---
name: storefront-copy-drafts
description: Use when drafting storefront copy as files for review. Every claim cites a live page or source file.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [copy, storefront, citations, compliance, drafts, draft-pr]
    category: research-content
related_skills: [regulated-catalog-content, storefront-code-audit, cro-baseline-audit]
---

# Storefront Copy Drafts (Cited, Linted, Files Only)

## Overview
Copy drafts for a regulated storefront, delivered as files in a docs-only draft PR. Five jobs share one method: category intro copy with FAQs, product field text (alt text and meta descriptions), recovery-screen copy (404, empty cart, empty search, sold-out product, empty order list), lifecycle messages, and an inventory of the copy the storefront already ships. Every claim cites a live page or a source file. Every draft passes a banned-claim lint with a negative control. Nothing is published, sent or configured.

## When to Use
- A review asks for draft copy for category pages, product fields, recovery screens or messages, as files for a human to approve.
- A review asks what copy the storefront ships today, before a rewrite.
- The copy has to follow a compliance floor that bans effect or health claims.

Skip for a live-site UX audit (use `cro-baseline-audit`) or a catalog-level data audit.

## Features
- One method for five job types, each with a Markdown or CSV format that a checker can parse.
- A citation rule: every factual sentence has an excerpt, a URL or file path, and a verbatim quote.
- A banned-claim lint with a stricter effect-word list, run with a mutation test.
- Recovery-screen copy checked against the code file it renders from.
- An inventory of hard-coded strings from the repository, with a completeness check.

## Benefits
- Reviewers can re-find every quoted sentence.
- A passing checker is shown to be capable of failing.
- Drafts never claim behaviour the site does not show.
- Nothing reaches a customer or a provider without a human decision.

## Procedure

1. **Read the existing work first.** Find earlier copy files and open pull requests for the same surfaces. Quote the earlier wording in a dedupe list, and do not copy it. If a rival draft for the same surface is open, that is a finding: ask which draft wins before you write another.

2. **Collect facts from the live site.** Fetch each page with a descriptive User-Agent that names the audit, and strip script and style blocks. If a page is empty without JavaScript, read its rendered text once in a browser, then cite only text you can re-find with a plain fetch. Keep a page map that records which page supports which claim.

3. **Write every draft from one data structure.** Hold each draft as copy, citations and metadata in one place. Generate the Markdown and the CSV from it. Write the CSV with a CSV writer, because subjects and previews contain commas.

4. **Format each job.**
   - **Category intro (answer first).** An intro of 60 to 90 words in three sentences: what the category is, who it suits, and how to choose. The lead names the product. A brand line can follow it. Then three FAQ pairs, each a question and a one- or two-sentence answer.
   - **Product fields (alt text and meta descriptions).** Alt text is a noun phrase of 125 characters or fewer, with no full stop at the end. A meta description is 155 characters or fewer and contains a verb. Use third-person wording, not "our" or "we". When the page has no per-image source data, state the position ("photo 2 of 5") and do not guess the view.
   - **Recovery screens (404, empty cart, empty search, sold-out product, empty order list).** One section per screen, with the file path, the quoted current copy, the proposed copy, and a table of CTA labels and URLs. Keep button labels to two or three words.
   - **Lifecycle messages (welcome, abandoned cart, post-purchase).** Metadata lines (flow, message id, trigger, delay, subject, preview, CTA), then the body and a SOURCES block. Each SOURCES line is `excerpt :: live URL :: verbatim quote`, or `excerpt :: VOICE` for short brand wording that makes no factual claim.
   - **Copy inventory (what the storefront ships).** One row per string, with file, line, kind and area. The report lists flagged rows first and caveats last.

5. **Run the lint with a negative control.** The lint strips URL lines, and the identifier lines on the reviewed exemption list, before it scans the prose. It then scans the prose. Print the raw hit count and the residual after stripping, and require the residual to be zero. Then inject a banned phrase into a clean draft, confirm that the lint fails with the expected hits, restore the draft, and confirm the lint passes again.

6. **Check the numbers and the agreement.** Check the limits as numbers: subject 60 characters or fewer, preview 90 or fewer, body 200 words or fewer, including the footer. Every handle in the CSV must appear in the Markdown, and the reverse. Quote the exact checker output in the PR.

7. **Check the links.** Request every cited URL from the host that serves the storefront. Test each call-to-action target with redirects turned off, and record the status. A 404 on a call-to-action target is a defect of that screen.

8. **Confirm the diff is docs-only.** `git diff --cached --name-only | grep -v '^docs/' | wc -l` must return 0. The build is not run. The PR body states `build skipped: docs-only diff`, and gives the proof and the checker output.

9. **Push with an explicit refspec, and open a draft.** Run `git push -u origin HEAD:<branch>`, then `gh pr create --draft`. The PR body lists the dedupe list, the counts, the lint and negative-control output, the file list, the head commit, and a "Not done, by design" line: nothing was merged, published, sent or scheduled.

### Rules That Apply to Every Job
- **Cite every factual sentence.** A quote is a verbatim sentence from the cited page or file. Search the fetched text for each quote before you ship it.
- **Do not invent behaviour.** Do not claim cart persistence, order tracking in the account, one-click unsubscribe, response-time promises, price guarantees, restock alerts, age checks at sign-up, or shipping rules that no page states.
- **Keep the hedges.** "Where we have one on file", "may be required" and "typically" stay in the copy. Do not turn a conditional into an absolute.
- **Avoid figures that drift.** Prefer category names and behaviours to counts that change.
- **Use mandated lines verbatim.** A required disclaimer is copied exactly. Do not delete it to satisfy a lint. Flag it for review instead.
- **Stay in scope.** No sends, no scheduling, no provider configuration, no setting changes, and no merges.

## Pitfalls
- **Headings and slugs can carry a banned word.** A category slug may contain a word the lint bans. The lint skips only the identifier lines on an explicit exemption list, which the compliance owner approves; it never skips a line by default. A display-name line lets the storefront show a permitted name, and it does not hide a banned word from the lint. Name each exemption in the PR body.
- **Product titles can carry effect words.** Do not repeat a title that contains an effect word as a heading. Write the heading as the product type.
- **Do not duplicate live FAQs.** Read the storefront's own FAQ source first, and skip any question it already answers.
- **A lint that never fails is a broken gate.** Run the injected-phrase test every time.
- **Mutation tests edit only the body.** A global search-and-replace also edits the line the checker reads, and that hides the failure.
- **The checker must pass its own scan.** Keep the banned-word list in a reviewed file, exclude that file by path from the folder scan, and phrase the checker's messages as "banned-claim words".
- **Answer first means the product leads.** A default brand-first paragraph misses the requirement. Check the lead sentence of each intro.
- **Word counts overstate with tables and code.** Strip code spans and table rows before counting, in the lint and in review alike.
- **Buttons wrap on phones.** Keep CTA labels to two or three words, and put longer text in a table column.
- **Empty states have more than one surface.** An order list and an order dashboard tile are separate components. Cite both, or name the one the draft covers.
- **Mobile and desktop actions are separate files.** Update both, or name the one the draft covers.
- **Inventory line numbers drift.** A multi-line text node reports its first line. Print the cited line before you rely on it.
- **A copy inventory is not a copy rewrite.** Keep them in separate pull requests, and say "no code changes" in the inventory PR.
- **Keep personal paths and identities out of the diff.** Use placeholders for home and work directories, and the repository's committer identity.

## Verification
- Every draft passes the lint with a residual of zero, and the negative control shows that the lint can fail.
- Every quote in a SOURCES block appears verbatim in the cited page or file.
- Every CSV handle appears in the Markdown, in the same order.
- The diff is docs-only, and the head commit and file list match the PR body.
- Every call-to-action URL returns 200 without a redirect from the storefront host.
