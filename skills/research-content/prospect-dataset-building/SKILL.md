---
name: prospect-dataset-building
description: Use when building a deduplicated, verified list of business prospects from public registries and map data, delivered as a CSV with a source link on every row.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [prospects, dataset, open-data, deduplication, verification]
    category: research-content
related_skills: [data-artifact-adversarial-review, official-source-claim-factcheck, competitor-site-teardown]
---

# Prospect Dataset Building (Verified, Deduplicated, Files Only)

## Overview
Build a list of unique business rows for one region and one category from public data. Each row carries a source link that re-resolves to the same business. The list ships with its builder, its raw snapshots, an exclusion log and a verifier. The list is research data. It does not decide whether any business may be sold to, and it does not contact anyone.

## When to Use
- The request is for N unique business rows in a region, drawn from public registries, open-data portals or map data.
- Each row must have a source link that a reviewer can open and check.
- The output is a CSV, a summary and a draft PR.

Skip when the list needs personal contact data, when a source's terms forbid the use, or when the job is outreach. Outreach needs its own review.

## Features
- Source priority: official registry first, open-data portal second, map data as enrichment.
- A row-resolving source link on every row, checked against the live source.
- Four dedupe keys, plus a same-premises check across sources.
- Chain and non-retail filters, with every exclusion logged and its reason recorded.
- Pool arithmetic that must add up before any count is reported.
- A live verifier with a fixed-seed sample, a full run and seeded-bad probes.

## Benefits
- A reviewer can open any row and confirm it.
- A shortfall is reported with its reasons, not padded.
- A rebuild from the committed snapshots gives the same bytes.
- Personal contact data stays out of the deliverable.

## Procedure

1. **Resume before rebuilding.** Check the remote branches for earlier attempts at the same list (`git ls-remote --heads origin | grep <topic>`). If a checkpoint exists, reuse its builder and snapshots in a worktree, and build on top of it. Do not start from scratch or open a second branch for the same work.

2. **Check the rules before any fetch.** Read the restrictions that apply to the target category in the jurisdiction, from the files on the default branch (`git show <branch>:<path>`), not from a stale local copy. Record each restriction per class, with the commit hash you read. If the category is blocked for the requested purpose, stop and report it. Otherwise proceed, and put the full per-class table in the report so a reader can see what was checked.

3. **Triage every source.** A source is a row source only when each row has its own URL or record id, and a fresh fetch of that URL returns that record. Examples: a per-record query by object id, a map element URL, or a registry detail page. A list page, a search form, a PDF without record anchors, or a single dashboard page is a signal file. Use it for cross-checks, not to produce rows.

4. **Snapshot the inputs.** Save raw responses compressed (`*.json.gz`), with a fetch timestamp for each file. The builder reads only these snapshots, so a rebuild runs offline and gives the same result.

5. **Re-read map elements before using them.** A map-data snapshot can be stale. Re-read each element by id from the map API, in bulk requests of a bounded size, falling back to single-id requests when a bulk request returns a 4xx. Drop an element that now returns 404 or 410, or has no tags, with the reason `deleted_or_untagged`.

6. **Classify the type from tags first, then from the name.** Use the type tag the data carries before any name pattern, so a misspelled name cannot change the type. Use a name-only type only when the name carries a clear store word. Record the basis for each type (tag, cross-reference, name, or licence class), and count each basis. The weakest basis needs its own line in the report.

7. **Filter in order, and log every exclusion.** Filters run in this order: type, chain blocklist, non-retail names (repair shops, storage, schools and similar), state and ZIP range, required fields, then dedupe. Each exclusion goes to `excluded.csv` with its reason and its evidence. Match chain names as whole words and also in squashed form (spaces removed), so both `Example Express` and `EXAMPLEEXPRESS` are caught.

8. **Dedupe on four keys, then across sources.** The keys are: normalised name plus ZIP; normalised address plus ZIP; house number plus street core plus ZIP; and a name-independent same-premises check (same house number, same street after abbreviation normalisation, same ZIP). Normalise by removing punctuation and spacing, expanding abbreviations (`TRL` to `TRAIL`), and stripping unit markers before punctuation is removed. When two sources describe the same premises, keep the record with the richer contact fields. Carry a phone or website onto the kept row only from a record at the same premises.

9. **Check the pool arithmetic.** The build prints `delivered + excluded == fetched`, and the report repeats the equation. A mismatch means a filter dropped rows silently. Fix it before reading the count.

10. **Verify live, then prove the verifier can fail.**
    - *Sample.* Use a fixed random seed and about two percent of rows (at least 20). Re-resolve each sampled `source_url` against the live source. Record the seed and the count.
    - *Full run.* Re-resolve every row. Only a full run supports a claim of N of N verified.
    - *Seeded-bad probe.* Copy the CSV and mutate a few fields per row to plausible wrong values (a wrong ZIP, a wrong digit, a wrong street suffix, a transposed name). Run the verifier on the copy. It must exit non-zero, and its failure count must equal the number of seeded defects.
    - *Determinism.* Build twice from the same snapshots and compare the checksums. Report the second build's checksum, since that is the file that gets committed.

11. **Report any shortfall honestly.** If the build returns fewer rows than the target after all filters, report the real count, the cap, the gap, the held-back counts by reason, and one line naming how a later run could close the gap. Do not loosen filters, widen source types or add non-matching rows to reach the number.

12. **Deliver as a draft.** Work in a worktree created from the default branch, so a dirty working copy is untouched. Commit only the research directory. Before pushing, scan `git remote -v` and the Git rewrite rules for embedded tokens, and remove any you find. Push with an explicit refspec (`git push -u origin HEAD:<branch>`), and open the PR as a draft. Never merge.

## Pitfalls
- **Lowercasing is not a dedupe key.** `Example Mart` and `Examplemart` both survive `lower()`. Remove everything except letters and digits before comparing.
- **A search URL is not a row link.** A link that runs a query returns whatever the query matches today. A row link contains the record's id.
- **A PDF fragment is not a row link.** Anything after `#` is ignored by static file servers, so every row can resolve to the same bytes. Keep such rows out of the deliverable, or verify them by extracting the text from the downloaded PDF.
- **Count the records a per-record query returns.** Exactly one record must come back. Zero means the record moved or was renewed; more than one means the query did not narrow enough. Fail the row, and do not relax the query to make it pass.
- **Encode every interpolated value.** An unencoded quote in a query string returns an error, and a builder can quietly count that as zero rows.
- **Parse dates as dates.** Compare expiry dates with a date parser, not with a string comparison, and compare them with the snapshot date, not today's date.
- **Fallback sources rarely carry contacts.** A state filing usually has no phone or website. Take contacts only from a record at the same premises, and count the rows that still have neither.
- **A phone field may hold several numbers.** Split on the first separator, keep only a 10-digit number, and blank the field otherwise. State the rule and the fill counts in the report.
- **A licence holder's phone is not the storefront's counter line.** Say which kind of number the report counts. Report duplicate phone numbers separately, because one number shared by many rows usually means one operator.
- **A mailing city is not a premises city.** Take the physical city from the row's own source, cross-check it against a second source, and never use the mailing city.
- **A reverse-geocoded ZIP is not corroboration.** A verifier that repeats the same lookup only confirms itself. Corroborate a derived ZIP against an independent dataset, such as the nearest records in a retailer layer, and drop the row if they disagree.
- **Chain blocklists miss variants.** Match each brand token as a whole word and in squashed form. Re-scan the delivered names for brands the blocklist missed. Report each blocklist entry with its hit count and one example name.
- **A regional-chain rule needs a documented threshold.** Count distinct premises per brand after normalising the name. State the threshold, and list the multi-store brands that were kept.
- **A top-N slice is biased.** Taking the first N rows of a sorted file favours one area. Allocate the picks by area in proportion to the pool, and state the rule.
- **Keep personal data out.** Do not store owner names, personal emails or home contacts in snapshots, provenance or the CSV, unless the build needs them. If matching needs an owner, keep only a numeric identifier.
- **Keep tokens out of output.** Do not print a credential. Export one inline only for the command that needs it.
- **Stop probe browsers.** A headless browser left on a fixed debugging port keeps running after its script exits. End each probe run by stopping that browser.
- **Verify the file that gets committed.** Any change after a verify pass, including a new column, invalidates that pass. Re-run the full verifier on the final file.

## Verification
- The build prints `delivered + excluded == fetched`, and the report repeats the equation.
- The full live run reports N of N re-resolved, or names each failing row.
- The seeded-bad probe exits non-zero, and its failure count equals the seeded count.
- Two builds from the same snapshots produce the same checksum.
- The report states the cap, the delivered count, the gap, and each exclusion reason with its count.
- The draft PR touches only the research directory, and `gh pr view <n> --json isDraft,files` confirms it is a draft.

## Attribution

Map data comes from OpenStreetMap. Any deliverable with OpenStreetMap rows carries this line in its report and PR body, with the count of OpenStreetMap-derived rows: "Contains data from OpenStreetMap, (c) OpenStreetMap contributors, ODbL 1.0 (https://www.openstreetmap.org/copyright)."
