---
name: overnight-housekeeping
description: Use when running a scheduled overnight health pass. It is a health and hygiene pass on a Hermes agent host. Covers gateway health, memory store hygiene, skills and cron checks, config review, tool dependencies, and backups.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [housekeeping, health-check, memory, skills, cron, backups, maintenance]
    category: fleet-infrastructure
related_skills: [infrastructure-guardian-agent, hermes-host-operations, incident-forensics]
---

# Overnight Housekeeping

## Overview
An agent host accumulates small problems: duplicate memory entries, stale configuration, skill files that no longer load, scheduled jobs that report errors they did not have, dependency warnings that are cosmetic, and backups that pile up. A nightly pass catches these while nobody is working. The pass is read-only by default. It reports what it found, makes only the reversible fixes that the runbook allows, and leaves anything destructive for the operator.

## When to Use
- A scheduled nightly job should check a Hermes host and produce a report.
- The operator asks for a health and cleanup pass before a busy day.
- A reported problem might be a false alarm, and you need to check the logs before acting.

## Features
- A gateway check that reads the runtime's own status and doctor output.
- A memory-store check for size, exact duplicates, and stale directives, with a dry-run before any removal.
- A skills audit for missing or empty skill files and unreadable frontmatter.
- A cron check that reads the logs before trusting a job's status field.
- A configuration review that lists settings to compare rather than changing them.
- Dependency checks that separate real vulnerabilities from cosmetic warnings.
- A backup policy with dated names and archiving of old copies.

## Benefits
- Problems are found while they are small.
- False alarms are not chased, because each claim is checked against a log.
- Nothing destructive happens without a backup and an operator's approval.
- The report gives the operator a short list of decisions, not a long list of observations.

## Procedure
### Gateway and providers
1. Read the runtime's status and doctor output:
   ```zsh
   hermes status
   hermes doctor
   ```
2. Check that each provider the host relies on can answer a one-token request. Treat a provider as healthy only when a real request succeeds, not when a listing does.
3. Read the gateway log for recent provider errors. A small-tier provider can reject requests above its token cap with a payment or quota error. That is expected for the tier, so report it as a limit, not an outage. Check whether the error is the cause before you change any routing.
4. A "not found" response to a metadata listing on one endpoint can be cosmetic when the model call itself works. Confirm with a real call before raising an alert.
5. If a private-network resolver fails for a hostname that works elsewhere, test with the same client library the agent uses. A resolver problem on the private network is not a key problem.

### Memory store
6. Count the entries and check the bank exists before any analysis:
   ```zsh
   hindsight memory list <bank>
   ```
7. Find exact duplicates: entries with the same text and different identifiers. Report the count and a sample. Do not delete entries in the nightly pass.
8. Check for stale directives, such as a rule that retires a model or a setting. Compare each directive with the live configuration. Report the stale ones, and let the operator decide on removal.
9. Confirm that retrieval works with two or three known queries. A healthy store returns relevant entries for each one.

### Skills
10. Find skill files that are empty, that lack frontmatter, or that do not parse. Report each one with its path:
    ```zsh
    find <skills-dir> -name 'SKILL.md' -empty
    ```
11. Compare the installed skill count from the runtime's own listing with the number of skill files on disk. A difference can come from nested folders or non-standard file names, so report it without assuming an error.

### Scheduled jobs
12. For each job whose status shows an error, read the job's output log before believing the status. A status can carry an error string that a job printed as text, while the job completed. Report the real failures separately from the embedded strings.
13. Run the scheduler's pre-flight check, if the runtime has one, before declaring the job set healthy.

### Configuration
14. Read the profile's configuration file and list the settings that matter for operation: the primary provider, the fallback chain, the context-compression settings, the memory provider, and the tool servers. Compare them with the values in the last report. Report changes. Do not edit the file in the nightly pass.

### Tool servers and dependencies
15. List the configured tool servers and confirm each process is running:
    ```zsh
    hermes mcp list
    ```
16. Run the package manager's audit for each tool directory. Read each finding before acting. Some findings are in nested copies that the runtime does not load, and a forced upgrade can change major versions. Do not run a forced fix in the nightly pass.

### Backups and disk
17. Check the backup folder for copies older than the retention window (for example, five days). Rename old copies to a `.stale` suffix, and keep the most recent copy of each file. Do not delete anything.
18. Confirm that new backups use the dated naming pattern before any risky change. Report the disk use of the profile directory, and find the largest subfolders, since cache directories can dominate it.

## Pitfalls
- **A status field is not a log.** A job can show an error that it printed as text, while the job itself completed.
- **Dependency audit findings are not all live.** Check whether the flagged copy is the one the runtime loads.
- **A forced dependency fix can change major versions.** Read the change, then plan the upgrade in daylight.
- **A profile directory can hold a large cache.** Do not assume it is data. Check the subfolders first.
- **Deduplication needs review.** Two entries with the same text can record different events. Report, then decide.
- **Config paths depend on the profile.** Resolve the live path with the runtime's own command.
- **Stale is not wrong.** A directive can be old and still correct. Compare it with the live state before retiring it.

## Verification
- The report lists each check with its result and the command or log that supports it.
- No file was changed by the pass, except renaming old backups to the stale suffix.
- Each reported failure has a log line or command output attached.
- Each recommended change is listed with its reason, for the operator to approve.
