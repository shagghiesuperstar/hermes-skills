---
name: hermes-upstream-contribution
description: Use when filing an issue or pull request upstream. The target is the Hermes upstream project. Covers ruling out local causes, deduplication, issue-first scope, small diffs and evidence.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, upstream, contribution, github, issues, pull-requests]
    category: hermes-operations
related_skills: [hermes-skill-sharing, hermes-architecture-reference]
---

# Hermes Upstream Contribution

## Overview
A flaw found on one install is worth fixing for every install, but an upstream report that blames the wrong cause costs
credibility that is hard to win back. This skill covers the order of work: rule out your own actions first, check for an
existing report, read the maintainers' acceptance criteria, file an issue before code when a behavior is a deliberate
policy, and keep the change to the smallest mechanism that fixes the measured problem.

## When to Use
- A Hermes flaw reproduces on your install and you think it affects other installs.
- You are about to file an issue, comment on an existing one, or open a pull request against the upstream repository.
- A bug report needs evidence that a stranger can reproduce.

## Features
- Local-cause check: a window of your own tool calls before the incident, to rule out self-inflicted events.
- Deduplication search across open and closed issues and pull requests.
- Acceptance-criteria review from maintainers' comments on similar changes.
- Issue-first rule for changes to deliberate policy.
- Isolated-clone workflow that keeps the live install untouched.
- Reproduction-first evidence format.

## Benefits
- Upstream reports do not blame a cause that your own automation created.
- Duplicate work is avoided, and an existing report gains evidence instead of a copy.
- Pull requests match what maintainers accept, so review cycles are short.
- Your live install is never the place where a fix is developed.

## Procedure
1. Rule out your own hands first. List the commands that ran in the minute before the incident, using your own session
   records. Look for process-stopping or service-restarting calls. If your automation stopped the process that then
   failed, the bug report must say so, and it must cite the check, not your memory of the cause:
   ```bash
   sqlite3 <hermes-home>/state.db "SELECT <columns> FROM tool_calls WHERE <time-window-and-command-filter>"
   ```
   Write the window and the result into the report.

2. Switch to the account you use for public upstream work before any write, and switch back afterwards:
   ```bash
   gh auth switch --user <public-account>
   gh api user --jq .login
   ```

3. Deduplicate. Search issues and pull requests, open and closed, with at least three keyword variants. Use the search
   command, and check the closed list separately, because the flags differ between the two. If an issue already exists,
   add your evidence as a comment, and do not open a copy.

4. Read the maintainers' close notes on similar pull requests. Their comments are the acceptance criteria. Typical criteria
   on this kind of project:
   - no hard-coded heuristic gates;
   - the fix lives inside the existing layer, not beside it;
   - a diff small enough to review in one sitting;
   - a measured improvement over the main branch;
   - no generated planning files in the diff;
   - no unexplained test-failure changes;
   - a visible human check on any AI-written change.

5. Look for an in-tree precedent. A pattern the project already merged elsewhere is the strongest argument for a new
   change. Cite the precedent by its link.

6. File an issue first when the change touches a deliberate policy, such as an ownership guard, an approval default or a
   prompt. Let a maintainer say whether the behavior is intended before you write code. You can build the change in
   parallel in an isolated clone, and hold the push until there is a signal or a set waiting period has passed.

7. Keep version one to the mechanism. Leave out prompt rewording, new configuration flags and cleanup. A prompt change
   belongs in a separate commit or a follow-up pull request, so reviewers can drop it. Reviewers reject changes that add
   more background writes.

8. Work in an isolated clone under your workspace, never in the live install. An update of the live install can discard
   local edits made there.

9. Gather evidence from real logs, with the exact command a reader can run to see the same thing. State what you could
   not measure. For example, a refused write that is not persisted anywhere cannot be audited after the fact.

10. Follow the project's own test wrapper, not a bare test runner. Add one or two invariant tests that fail on the base
    branch and pass with the change. Avoid tests that read source text or match prompt strings. Run the project's check
    command before you push.

11. Disclose AI assistance in one line, and paste real output from a throwaway home directory or profile as the
    dogfood evidence.

## Pitfalls
- **A plan that bundles a mechanism, a prompt change and documentation reads as a dump.** Trim to the smallest change
  that fixes the measured leak.
- **One power-user install can be dismissed as unusual.** Say so, and give the reproduction command instead of
  generalizing.
- **A public retraction is expensive.** Check your own actions before you file, not after.
- **Do not push before the maintainer's signal on a policy change.** Hold the branch.

## Verification
- The report cites the local-cause check, with its window and its result.
- A search shows no open or closed duplicate, or the evidence is posted on the existing issue.
- The change diff is small and touches only the layer the precedent uses.
- The test wrapper and the check command both pass on the change, and the new tests fail on the base branch.
- The account used for the write is the public one, and the switch back is confirmed.
