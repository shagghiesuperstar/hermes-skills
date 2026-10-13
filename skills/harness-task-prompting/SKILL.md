---
name: harness-task-prompting
description: Use when writing a work order or task card for an agent. Applies to coding harnesses too. Sets the card shape, pinned model, done criteria, and review handoff.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [prompting, work-orders, kanban, model-routing, review]
    category: agent-orchestration
related_skills: [adversarial-review, opus-5-5-claude-code, kanban-orchestration, kanban-card-lifecycle]
---

# Harness-Quality Task Prompting

## Overview
A task card (one unit of work on a kanban-style board) sent to an orchestrator worker is passed through to the coding harness the worker runs, so a vague card becomes a vague harness prompt. Write every card as if the harness reads it directly: state the outcome, give a checkable definition of done, pin the model and provider, name what the worker cannot know, and set a review handoff that a different model vendor will perform. Short cards get a short version of the same shape. The structure carries the quality, so the body stays brief and the detail goes in a spec file.

## When to Use
- Before creating any task card, work order, or dispatch to an agent or harness.
- Before handing a fix to a worker after a review found defects.
- Before sending a read-only audit to a cheap, fixed-rate model.
- Before writing a task in an issue tracker that a remote worker will pull.

## Features
- A card template with fixed slots: goal, purpose, context, spec path, done criteria, constraints, autonomy, evidence, review handoff, and engine.
- Rules for outcomes over recipes, for leaner prompts, and for operator rulings quoted verbatim with a date.
- A model-selection step done before the card is written, with the model and provider pinned on the card.
- A decision-return rule: the worker records a fork in the spec as a list, accepts the conservative default, and the orchestrator decides.
- A read-only audit card shape, with a CSV, a summary, and a questions file.
- A checklist of process pitfalls that cost rounds in past runs.

## Benefits
- The worker has a clear finish line, so it does not stop early or wander.
- Builder and reviewer come from different vendors, so one vendor's blind spot is caught by another.
- Pinned engines prevent a profile default from colliding with a running swarm on the same provider key.
- Review findings become fix cards with a stated decision, so the same finding does not come back a second time.
- Secret hygiene rules in every card keep credentials out of transcripts.

## Procedure
1. Choose the model and provider for the job before writing the card. Check provider limits and rate limits first. Pick by job:
   - Build, fix, and tests: a strong coding model.
   - Bulk rows: the lowest-cost tier, spread across providers so no single provider carries most of the load.
   - Design, copy, and creative work: the model strongest at writing and taste.
   - Reviewer: a model from a different vendor than the builder.
   - Critic, when used: a third vendor, different from both the reviewer and the builder.
   - Nous or any other route: a last-resort fallback.
2. Write the card with every slot filled:
   ```text
   GOAL: <one sentence: the outcome, not the steps>
   TELOS: <the purpose the outcome serves>
   CONTEXT: <what the worker cannot know: repository and worktree, branch and tip SHA, prior verdicts, operator rulings verbatim with date, shared decisions>
   SPEC: <absolute path, when the detail runs past about 500 characters>
   DONE-MEANS: <3 to 7 checkable lines, each an observable fact plus how to prove it: a command, a count, a file, or a URL>
   CONSTRAINTS: <hard gates only: no merge, no production writes, no force-push, paths not to touch>
   AUTONOMY: "Keep going without asking for anything reversible or read-only. Stop only for: <one or two real blockers>."
   STOP CONDITIONS: <a named section; the harness can refuse a card without it>
   EVIDENCE: <what goes in the completion metadata: commit SHA, test counts from the worker's own run, file paths>
   REVIEW: <see the review rule below>
   ENGINE: <model and provider pinned on the card>
   ```
3. Write the review line as a handoff. The builder finishes with a completion call that marks the work ready for review, and it never requests its own reviewer. The orchestrator creates a separate review card with a different vendor. Add a security review line when the change touches auth, payments, personal data, secrets, compliance gates, deployment, or input handling.
4. State the outcome, not a recipe. Modern models infer steps well, and an over-specified itinerary makes them worse. Give each instruction once. Name a file to read only when it matters for the task.
5. Quote operator rulings verbatim, with the date. Shared decisions, such as a schema, a naming rule, or a list, are decided once by the orchestrator and written into every dependent card.
6. Allow one engine per card. Name it, and do not offer the worker a choice between that engine and a direct edit, because the worker will pick whichever is easier and the named engine will never run. For a one-line change, write `ENGINE: direct edit by the worker` and nothing else.
7. Ask for the finished artifact, not a plan.
8. For a card that touches a repository, name the repository in the body, and if the repository has a code index or graph tool, tell the worker to query it before it reads repository files.
9. Confirm that the card's constraints cover secret handling. Every card says the worker must never print the process environment, environment dumps, or process listings that show environment values.

### Fix cards after a review
- Write one `DECISION` line in the body. It names the approach and the constraint on it. Builders who must re-derive the approach usually do it worse, and the next round finds the same defect again.
- Post the decision as a comment on the review card while the verifier is still running. The fix card quotes the comment.
- Copy the acceptance line verbatim into both the fix card and its re-review card. Two different versions of the allowed-change list cost one full round.
- Create the re-review card with a parent link to the fix card and an initial status of waiting, so it starts after the fix lands. Resolve the head SHA at dispatch time, not at card-creation time.
- If a finding comes back a second time, the fix is a generator change plus a test that fails on the old code and passes on the new code. A hand edit to the output does not stop the repeat.

### Read-only audit cards
Use this shape for cheap, fixed-rate models that open local files, filter rows, and write results. Such a card is not a coding card, and it needs no review.
```text
ITEM: <UPPER-SNAKE-NAME>
GOAL: From <input>, list every row where <rule>.
STOP CONDITIONS: no writes to any store or service, no publish, no merge, no deploy, no messages, no secrets in output.
DONE-MEANS: file <out>.csv exists; columns <a,b,c>; no invented values; SUMMARY.md with the input path and counts.
SOURCE: <absolute path to input file>
OUT DIR: <absolute path>
```
- Write one CSV, one summary, and one questions file to the output directory. If the input is complete and the result is clear, the questions file says "No questions."
- Use the input file's row convention. Give the line number as the join key, not the identifier alone, so a downstream step can find the input record.
- A zero result is a finding. Write the CSV with the header and zero data rows, and prove the zero with a per-row audit file and a summary that splits the input into matched and unmatched rows, with counts that add up to the total.
- Do not fill an empty cell with a placeholder such as "N/A." An empty value stays empty.
- Read the header and row count in the same pass as the filter. Do not trust a note from an earlier run over the live file.
- For a hidden-character scan, count the raw bytes of the whole file as well as the parsed cells. A parser can normalize away a tab, a byte-order mark, or a line break. Mark each hidden character found in the quoted field, such as `[TAB]` or `[CRLF]`.

## Pitfalls
- **Vague cards become vague harness prompts.** A worker that hands a task to a harness passes your card through. Write the card for the harness.
- **Over-strong "ask first" language stops capable models early.** Give explicit autonomy for reversible work, and list the real stops.
- **A card does not override a skill's safety or approval rule.** When a loaded skill blocks the work, the worker quotes the blocking line to the orchestrator and stops. It does not work around the rule. Stating this in the card keeps the worker from guessing which document wins.
- **Unpinned cards inherit a profile default** that may share a provider key with a live swarm. Pin the model and provider on every card.
- **Builders must not review their own work.** A review requested by the builder runs on the builder's model family and returns a self-approval. The orchestrator creates the review card.
- **Measure a word list before you give it to a builder.** A list copied from a review verdict can miss most of the probe cases. Count the hits yourself on the reviewer's probes, and put that count on the card.
- **Builders bend product code to make their own tests pass.** Require an `UNPLANNED` list in every completion report, naming each production change that the spec did not name, with its reason. Check the diff against the spec yourself.
- **"Refresh the fixtures" invites scope creep.** Name the exact fields that may change. Anything else is a stop-and-ask. Add a done-means line that diffs the fixture against the base branch field by field.
- **A "generate more items" card must dedupe against existing drafts before the worker starts.** Write the dedupe rule into the card, and require a check that proves zero overlap.
- **Performance and visual gates must be satisfiable.** A threshold smaller than the noise in a base-versus-base run can never pass. Set the threshold to a multiple of the measured noise, use medians, and measure the same metric on the named control in the same run.
- **Do not make a done-means depend on a page that the worker cannot render offline.** Ask for proof the worker can produce without the live backend, and move the live check to the post-deploy step.
- **Deploy authority must be explicit.** If a card's work must end in a deployment, say so in the stop conditions, name the one surface it may touch, and have the orchestrator run the deploy step under its own gate. Do not split a deployment into a card that claims it has no deploy step.
- **A vendor API claim is unverified until someone reads the vendor's own documentation.** A card that says a vendor API "cannot do X" must quote the vendor document and the line. Without the quote, treat the claim as a defect.
- **Put the full task text in the task.** A pipeline that pulls tasks may truncate the description, and a worker that can only see a pointer will not see the spec.
- **Never point a remote worker at a path on the orchestrator's own machine.** Inline the content, or route the task to the orchestrator.
- **Name the legal identity once, and copy it verbatim.** When a card needs a legal name, address, or business name, quote one decision row from the spec file. Paraphrasing or substituting a similar entity causes errors that are hard to spot.
- **Operator questions carry their context inline.** A question to the operator names the trigger, the constraint, and what depends on the answer. A bare numbered question forces a back-and-forth.

## Verification
- Each card has every slot filled, and the STOP CONDITIONS section is present.
- The card names a model and a provider, and the review line names a different vendor from the builder.
- The DONE-MEANS lines each name a command, count, file, or URL that proves them.
- For a fix card, the decision line is present, and the acceptance line matches the re-review card word for word.
- For an audit card, the output directory holds the CSV, the summary, and the questions file, and the summary's counts add up to the input's row count.
