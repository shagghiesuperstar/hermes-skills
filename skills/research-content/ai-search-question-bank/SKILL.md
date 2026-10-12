---
name: ai-search-question-bank
description: Use when building a sourced question bank for AI search. Covers buyer questions for answer-engine coverage, mapped to a site's live pages.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [seo, aeo, question-bank, content-gaps, research]
    category: research-content
related_skills: [ai-answer-presence-audit, ai-discoverability-max, git-remote-hygiene]
---

# AI-Search Question Bank

## Overview
A question bank is the list of questions real buyers ask before they buy. Each question is tied to where it was seen, and to the live page that answers it, or to a GAP row when no page does. The bank is the input for answer-presence audits and for content planning. This skill builds the list and the gap matrix. It does not write copy: a human reviewer decides what to publish.

## When to Use
- You need a sourced list of buyer questions for one or more sites, before any content is drafted.
- You want to know which buyer questions a site's live pages already answer, and which they do not.
- The output must be a reviewable folder and a draft PR.

Skip when you need a citation audit of answer engines (use `ai-answer-presence-audit`), or when the job is writing the content itself.

## Features
- Per-site question CSVs with the observed URL and either the answering page or `GAP`.
- A gap ranking grouped by topic cluster, with no proposed copy.
- An evidence file of response headers for each cited page.
- A dedupe step against question lists already in the repository.

## Benefits
- Questions come from real buyer phrasing, so the bank matches how people search.
- Every answered row points to a live page that was checked in this session.
- Gaps are listed, not filled, so a human decides what to write.
- Topic spread keeps the bank from becoming many versions of one question.

## Procedure

1. **Set up a clean worktree.** Create it from the default branch. Run a token scan before any push (see `git-remote-hygiene`). Push with an explicit refspec, `git push -u origin HEAD:<branch>`. A worktree that tracks the default branch sends a bare push to that branch.

2. **Inventory existing lists.** Search the repository for earlier question files (`questions*.json`, `queries.json`, FAQ headings, `gaps.md`). Quote each matched path in the README, so a reviewer sees what was skipped. Confirm each path exists on the default branch (`git ls-tree <branch> <path>`) before you treat it as a skip list.

3. **Collect questions per site.** Seed each site with its brand name, its top three product categories, and three to five buyer phrases such as "where to buy", "online", "ship to <region>" or "reviews". Use these sources, in order of reliability:

| Source | Why | Method |
|---|---|---|
| Search-engine autocomplete | Real buyer phrasing, no script wall | Request `https://suggestqueries.google.com/complete/search?client=firefox&hl=en&q=<urlencoded seed>` |
| Public forum or community search | Phrasing plus intent context | Search the community for the seed, sorted by relevance |
| Niche community forums | Long-tail intent for the category | Read the thread pages your search returns |

Spread questions across clusters (product, price, shipping, rules and legality, trust, usage, comparison), so the list is not variants of one question.

4. **Map each question.** Record the URL where you saw the question as `source_url`. Then look for a live page that answers it:
   - Fetch the candidate with a clearly identified User-Agent, and follow redirects with a timeout.
   - If the page returns 200 and contains a token that answers the question (a shipping fact, a product name, an FAQ sentence), cite that URL.
   - Otherwise write `GAP`.
   - Append the response headers for every cited URL to `evidence/`.

5. **Handle trade-name mismatches.** When the buyer uses a trade name and the page heading uses a chemical or canonical name, a literal text check fails even though the page is right. Cite the canonical page, and note the exception in the README. Do not turn the row into a GAP for that reason.

6. **Leave sensitive gaps open.** Questions about dosing, effects or legality need a human's review. Keep those rows as GAP and rank them. Do not write an answer for them, even when a draft would be easy to produce.

7. **Rank the gaps.** Write `GAPS.md` as a ranked reading list, grouped by cluster and then by the number of rows in each cluster. Propose no page titles, headings or copy.

8. **Ship a draft.** Stage only the output folder. Keep scratch files, seed lists and builder scripts out of the commit. Use a conventional docs commit message. Write the PR body to a file, open the PR as a draft with `--body-file`, and never merge.

### Deliverable layout

```
docs/marketing/<bank-id>/
├── README.md                      # dedupe list, mapping rule, counts
├── GAPS.md                        # ranked gaps, no proposed copy
├── questions-<site>.csv           # one per site: question, source_url, our_url_or_GAP
└── evidence/curl-our-urls.txt     # response headers for each cited URL
```

## Pitfalls
- **A bare push can publish to the default branch.** Always use an explicit refspec to a named branch.
- **Autocomplete endpoints change and throttle.** Record the exact URL and the date you used it, and keep request rates low.
- **"People also ask" panels are unreliable.** Engines return interstitials, geo-varied results, or no such panel at all. Cite a panel question only when a second source carries the same question.
- **Cite where the buyer asked, not your own FAQ.** `source_url` is where the question was observed. Citing your own FAQ for "is this legitimate?" hides where the phrasing came from.
- **Do not fill dosing, effect or legality gaps.** Regulated stores often publish no such guidance, and a disclaimer does not answer a legal question. Those rows stay GAP for a human.
- **Identify your User-Agent honestly.** Copying another crawler's user-agent string to get past a block misreports your requests. If a site blocks the request, record the block as a limit of the audit.
- **Index and graph hits are pointers.** Confirm any path on the default branch before you use it, and do not use an unconfirmed path as a skip list.
- **Keep contact details and tokens out of output.** Do not print them into logs, the CSVs or the PR body.

## Verification
- Each CSV row has a non-empty question, a source URL, and either a cited URL or the word `GAP`.
- Every cited URL has its response headers in `evidence/`, from this session.
- The README's counts match the CSV row counts, derived by counting, not from memory.
- `GAPS.md` contains no proposed copy.
- The draft PR changes only files under the output folder.
