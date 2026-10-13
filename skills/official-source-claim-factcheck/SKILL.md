---
name: official-source-claim-factcheck
description: Use when checking claims against official sources. Uses verbatim quotes a script can re-fetch and a per-claim verdict.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [research, fact-check, compliance, citations, official-sources]
    category: research-content
related_skills: [regulated-catalog-content, data-artifact-adversarial-review]
---

# Official-Source Claim Fact-Check (Verbatim, Re-Fetchable Quotes)

## Overview
Every claim in a published page is checked against the official text it cites, and each verdict comes with a quote that a later script can re-fetch and find in the live page. A claim is judged only on what the official text says. Quotes are copied from fetched text, never retyped. The output is one row per claim with a verdict, the URL, the quote and a note on scope, dates and gaps. The skill reports what official sources say and does not draw legal conclusions or give advice.

## When to Use
- A page makes factual claims (numbers, dates, requirements, eligibility) and each one needs checking against an official source.
- A later script will re-fetch every cited URL and search for every quote, so every quote must come from the live text.
- The check covers many jurisdictions or agencies, and each jurisdiction's rules must be checked against its own official text.

Skip when the claim is a marketing judgement with no official source, or when the claim is about a private party's own records.

## Features
- A claim parser that reads the claims from the repository file with code, not by retyping them.
- A verdict set of AGREES, DISAGREES and NO_SOURCE_FOUND, with a rule for each.
- Quote selection rules, and a verification step that tests each quote under more than one text extraction.
- A change check that records the publication date, the last-modified header and any later notice.
- A report that orders disagreements first.

## Benefits
- A reviewer can re-fetch any row and find the quote.
- Disagreements are visible at the top, with the scope and date needed to judge them.
- Missing sources are recorded with the searches that were tried, so a gap is not mistaken for a result.

## Procedure

1. **Parse the claims with code.** Extract each claim, its page text and its cited URL from the repository file with a parser, not by copying. At the end, assert that each page text appears verbatim in the file.

2. **Fetch every cited URL.** Make a plain GET for each distinct URL, follow redirects, and record the status code. Stay at or below two requests per second. Fetch the current official page for each topic too (the agency's program page, the statute, the register notice), so that you check the live rule, not only the cited snapshot.

3. **Compare every number and date.** List every number and date in each claim, and compare each one exactly with the fetched text. Give the verdict DISAGREES only when a specific value differs. Put scope, wording nuance and tense in the note, without changing the verdict.

4. **Select the quote, then verify it.** Follow the quote rules below. Write each row with the exact key set, then verify every row against fresh fetches.

5. **Keep wording to the official text.** Restate what the official text says, and quote its words. Do not state legal conclusions ("legal" or "illegal"), and do not give advice.

6. **Check for changes since review.** Compare the HTTP `Last-Modified` header, any visible "last updated" date, and any notice published after the review date. Report what was checked, not only "unchanged".

7. **Assemble the report by code.** Write `table.csv`, and a report that lists DISAGREES rows first, then NO_SOURCE_FOUND, then AGREES. Compute the verdict counts from the data. Add scope notes for classes with no rule to compare, and the date of the review.

### Verdict rules

- **AGREES**: the official text states the claim in the same terms.
- **DISAGREES**: the official text states a different value, date or requirement. Note the direction (the page says more permissive, or more restrictive, than the official text).
- **NO_SOURCE_FOUND**: no official source states the claim. Leave the URL and quote empty, and list in the note which domains and searches were tried.
- An absence from a schedule or a list is not a quotable source. Say so in the note, and do not mark the claim AGREES on that basis alone.
- Cite the enacted or signed record for a bill, not the introduced text. Check whether a bill died in committee, was passed but not signed, or expired.
- Check effective dates against the review date. A rule that is not yet in force gets "not yet in force" in the note.
- Official but non-general sources (settlement orders, attorney-general opinions, staff summaries) are official, but not rules of general application. Say so in the note.
- Federal sources are used only when no official sub-national source exists, and the note says so.
- Third-party summaries can point you to the official page. Never cite them as evidence.

### Quote rules

- Take the quote from one element: one paragraph, one list item, one table cell. Do not cross list items, headings, table cells, inline links, bold or italic markers, or PDF line breaks.
- Prefer ASCII. Replace or avoid curly quotes, dashes and section signs, which extractors render inconsistently.
- Keep quotes at or under 350 characters, with no ellipses. Cut at a clause boundary.
- If the best sentence crosses a boundary, quote the shorter single-line piece, and put the rest of the sentence in the note.
- Test each candidate against the tag-stripped HTML (entities decoded), against a second text extraction of the same page, and against whitespace-normalised copies of both. Accept the quote only if every variant contains it.
- For PDFs, test two text extractors, because extractors split or join words differently. Avoid quotes that span a page break or margin line numbers.
- Do not paraphrase a quote until it matches. Fix the extraction, or pick a different sentence.

## Pitfalls
- **HTTP 200 is not content.** A JavaScript application shell returns 200 with no text. Find the real file host in the page's configuration or its network calls, fetch that host directly, and say so in the note.
- **A 403 from object storage with a "not found" body is a missing key.** Changing the user agent does not help. Report the status as found.
- **Do not work around bot challenges.** A "just a moment" challenge page blocks plain fetchers. Record the status as the cited status, explain it in the note, and confirm the page in a normal browser. Do not change headers or identities to get past the challenge.
- **Image-only PDFs have no text layer.** No quote is possible from them. Find a text source that quotes the same document, such as the agency's press release or a register notice.
- **Future tense after the date has passed.** Agencies often leave "will take effect on" wording after the date. Note it, and confirm the date on the agency's schedule or the register notice.
- **Rolling archives drop old issues.** Use the recent issues and the agency's current pages.
- **Scripted quote checks reject a row if the string is missing.** A quote that fails because of a line wrap, a curly quote or a script-rendered page is a fix to make in the extraction, not a reason to paraphrase.
- **Grep chunks for config strings only.** Read the single configuration value you need, and never paste a bundle into your context.
- **Never claim a verdict you did not check.** A row keeps its verdict only if its quote was found in the live text.

## Verification
- Every row has the exact key set: claim number, page text, cited URL, cited URL status, verdict, direction, URL, quote and note.
- Every quote is found in the live text under each extraction, when a fresh fetch is run.
- The report's counts equal the counts of rows in the table.
- The text of each claim is found verbatim in the repository file.
- Before the report ships, a search of its text for advice wording ("should", "must", "legal to", "safe to") returns no hits, or each hit is a quoted source word.
