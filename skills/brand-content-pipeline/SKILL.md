---
name: brand-content-pipeline
description: Use when generating AI brand video or image content. Covers regulated or character-led brands whose logo and characters must stay fixed.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [content-pipeline, brand, video, image, character-lock, regulated-brand]
    category: research-content
related_skills: [regulated-catalog-content, storefront-visual-acceptance]
---

# Brand-Locked AI Content Pipeline

## Overview
A content pipeline that produces AI-generated video and images for a brand that must keep its logo, its characters and its regulatory wording fixed across every output. Identity drifts when a model is asked to describe a character again in text, and a logo drifts when a model redraws it. The pipeline prevents both by starting each generation from approved reference files, and by keeping logos and text cards out of the model's hands.

## When to Use
- The brand has a logo, a mascot or a character roster that every output must match.
- The brand sells regulated products, so claims, depiction and age wording need fixed rules.
- Output is produced both interactively, in a desktop director tool, and in unattended batches through an API.

Skip when you need a one-off image with no brand constraints, or narration with no characters.

## Features
- Three production lanes, chosen by the decision being made: interactive direction, unattended API batches, and a local model for private assets.
- Character locks: approved transparent reference images that every shot starts from.
- Logo lock: approved logo files are composited in, never redrawn.
- A brand skill file that every generation inherits, with a fixed section list.
- A provider content-filter probe before any spend.
- A spend and provenance record for each batch.

## Benefits
- Characters and logos stay recognisable across a whole series.
- Regulated wording and depiction rules apply to every output, not only to the ones a reviewer happens to check.
- Private assets stay on the operator's machine when the lane is local.
- A provider's filter is found early, before budget is spent.

## Procedure

1. **Pick the lane for each decision.** Use an interactive director tool for final cuts and creative direction. Use an API for drafts, variants and batch work. Use a local model for high-volume iteration on private or regulated assets, because the files never leave the machine.

2. **Write the brand skill file first.** Store it at a canonical path on disk, so you can diff and regenerate it. Use this section order:
   1. Who the brand is: two or three sentences on tone, audience and what is sold.
   2. Voice cast: each voice with its role, language and cadence.
   3. Visual grammar: aspect ratio, length, grade, lens and camera verbs.
   4. Character lock rule: point at the approved folder and require motion-only prompts.
   5. Logo lock rule.
   6. Hard bans: regulated claims that are never allowed, legal limits (minors, hate symbols, real people without rights), and competitor marks.
   7. Compliance framing: lifestyle framing, no depiction of consumption, and age-gated wording such as "adults only", not "for everyone".
   8. Prompt structure: subject, action, setting, camera, lighting and sound, with a reference tag for each attached file.
   9. Episode structure and the naming convention for outputs.

3. **Lock characters with reference images.** Keep approved character art as transparent PNG files in an approved folder, with a short index file that says which set is the default reference. Start every shot from one of those files. Prompts describe what moves, not what the character looks like. A text description of a character drifts from shot to shot; a reference image does not.

4. **Lock logos outside the model.** Approved logo files are never regenerated or redrawn. When an image tool needs the logo, pass the file as an edit input, not as part of a new-generation prompt, because generation ignores the reference and invents a mark. Composite the logo into the first frame before any motion is generated. Build outro cards and text cards with ordinary image or video tools, not with the model.

5. **Probe the provider's content filter.** Before a batch, send a small set of prompts that use the most explicit approved wording, and record each response. If the filter blocks approved wording, report that the lane is blocked for that wording. Do not rephrase to get past the filter. Choosing a framing the provider's policy allows is a copy decision for the brand owner.

6. **Record voice consent.** Clone a voice only from recordings the speaker has agreed to be used that way. Keep the consent record in the batch file next to the voice.

7. **Check every output against the locks.** A reviewer rejects any shot where the logo drifts, warps or is reinterpreted, or where the character's identity changes. Re-run a failed shot from the same reference. Do not patch it by describing the character differently.

8. **Record spend and provenance.** For each batch, record the task identifiers, the cost, the remaining balance, the reference files used and the output files. Keep the record in a file beside the outputs.

9. **Hand off with paths.** End each session with the next steps the operator can run without you, and the exact path for each.

## Pitfalls
- **A text description of a character drifts within a few generations.** Keep the reference-image rule and the motion-only prompt rule, even when they seem repetitive.
- **A model-generated logo is never a final logo.** Logos come from the approved files, composited by a non-AI tool.
- **Blocked wording is a finding, not a puzzle.** A filter that blocks approved copy blocks that lane. Report it and stop that lane.
- **Desktop app credits and API billing are separate pools.** A free credit balance in an app does not pay for API calls. Track each pool separately.
- **Do not paste credentials into chat.** Stage keys in a file the operator reads on their own machine, and print only prefixes and lengths.
- **Workspace paths can disappear mid-session.** Re-check a file before you claim it exists, and report the gap if it has gone.
- **Adapt third-party skills rather than installing them directly.** An adapt step validates the file's structure and flags issues before install.
- **One clip is not a pipeline.** Test one full run (reference still, motion, poll, download) with real assets before committing to a batch.
- **Mandated regulated wording is a legal question.** It comes from the brand's compliance owner, not from the pipeline.

## Verification
- A probe batch passed with at least three brand-safe prompts, including the most explicit one you plan to use.
- A reference test passed: a transparent character still as the first frame, with a motion-only prompt, produced an output that keeps the character's identity on review.
- The brand skill file exists at its canonical path, and is imported where the tool reads it.
- Voice consent is recorded for every cloned voice.
- The batch record lists task identifiers, costs, remaining balance, reference files and outputs.
