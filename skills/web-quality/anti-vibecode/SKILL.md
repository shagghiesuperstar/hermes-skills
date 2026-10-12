---
name: anti-vibecode
description: Use when building, restyling or auditing a marketing page, homepage, waitlist, pricing page or SaaS landing page, to avoid generic AI-generated design. Scores the page against 30 common tells, and passes it only when no more than five are present.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [design, frontend, landing-page, anti-slop, ui, web, audit, copy]
    category: web-quality
related_skills: []
---

# Anti-Vibecode

## Overview

A marketing page that looks like every other generated page loses trust in the first three seconds. This skill is a ship gate: it scores a page against 30 common tells, each worth one point if a stranger would notice it in a three-second scan, and it passes the page only when five or fewer are present. The goal is a page that fits the actual product, not a fashionable template.

## When to Use

- Building or restyling a landing page, homepage, waitlist, pricing page or product marketing site.
- A user asks for a design that does not look generic, or asks for a review of a page's default look.
- Reviewing generated markup or styling for default-model aesthetics before a screenshot or deployment.

Skip it for internal admin screens that must match an existing kit, and for a brand system that already sets these choices on purpose.

## Features

- A scorecard of 30 named tells, scored 0 or 1 with no partial credit.
- Replacement guidance for each tell, grouped by visual, proof, copy and chrome.
- A pass rule on total hits, not per category.
- An audit-only mode that reports the scorecard without editing.
- A required output block so the score can be checked.

## Benefits

- Pages are judged against a fixed list, so reviewers agree on the result.
- Every fix is tied to a tell, so the work is bounded.
- Invented proof is caught, because proof tells are scored separately.

## Procedure

1. **Name the job in one sentence.** Say what the product does and for whom. If the sentence cannot be written, the page is not ready for a headline.

2. **Choose three locked choices before writing markup.** Pick a pairing of display and body type that is not the default sans-serif pair. Pick one accent colour from the product itself, not a purple-to-blue gradient. Pick one layout that serves the job, not a grid of equal cards.

3. **Build the page, or read the existing one.**

4. **Score all 30 tells.** Each is 0 or 1. A tell counts only when a stranger would notice it in a three-second scan.

5. **Apply the ship rule.** Five or fewer hits passes. More than five fails. Do not present a failing page as finished. List the hits, apply the replacements, and score again.

6. **In audit-only mode**, return the scorecard and stop. Do not edit the page unless the user asks.

Completion means a 30-row scorecard with a total and a verdict: either a pass at five or fewer, or a fixed page that scores a pass.

### The 30 tells

1. Purple, or purple fading into blue
2. A glowing orb behind the hero
3. A dot-grid background
4. A gradient applied to the headline text
5. A sparkle icon on anything labelled AI
6. A glass card floating over a gradient
7. An icon inside a tinted rounded square
8. An average bento grid of equal tiles
9. A clearly fake product screenshot
10. The only font is a default sans-serif
11. Default framework colours used without change
12. Testimonials from invented people with stock avatars
13. A "trusted by" logo strip with logos the business has no permission to show
14. A statistics row of large user counts and uptime figures that the business cannot back up
15. A "powered by AI" badge in the navigation
16. A waitlist form that does not store anything
17. "It's not X, it's Y"
18. Em dashes throughout the copy
19. "Fast. Simple. Powerful." descriptors
20. Feature names that are two generic nouns
21. Three feature cards of identical text length
22. "Get started" beside "Learn more"
23. Three pricing tiers with "most popular" in the middle
24. A $9, $29, $99 price structure
25. A FAQ that answers questions nobody asked
26. Generic hover and scroll animations
27. A hero that never says what the product does
28. No loading or empty state, only a blank area
29. A blog link where no blog exists
30. The default favicon

None of these is forbidden by itself. More than five is the failure.

### Replacements

- **Visual (1 to 8, 10, 11, 26).** Use one type pairing with character. Build the palette from the product's real materials, such as photography, packaging or the logo. Use a flat or lightly textured ground. Leave out orbs, dot grids, glass over gradients and sparkle icons. Animate only to show a state change.
- **Proof (9, 12 to 16, 25, 29).** Use a real screenshot or none. Use real names or no testimonials. Show logos only with permission. Show statistics only when they are true. A waitlist must store a real address. A FAQ answers real questions. A blog link needs real posts behind it.
- **Copy (17 to 22, 27).** Say what the product does in the hero, in plain words. Name features with verbs or outcomes. Card lengths may differ. Use one primary call to action that names the action. Avoid "it's not X" and empty triads of adjectives.
- **Chrome (15, 23, 24, 28, 30).** Leave out "powered by AI" chips. Show the price you actually charge. Provide loading and empty states. Use a real favicon.

**Honesty rule.** If there is no metric, testimonial, logo or screenshot, leave out that section. Invented proof scores as a hit on tells 9, 12, 13 or 14.

## Pitfalls

- **Changing purple to indigo is still tell 1.**
- **Using two default sans-serif families together** still scores tell 10 unless other choices are made.
- **A bento grid of equal tiles** is still tell 8, however it is labelled.
- **Replacing em dashes with spaced hyphens** but keeping "fast, simple, powerful" still fails tell 19.
- **The cap is on total hits, not per category.** A page can pass visual tells and still fail on copy.
- **Do not add other tells to the scorecard.** Extra style notes go in a separate paragraph, not in the score.

## Verification

Return this block with every row filled:

```
anti-vibecode score
hits: <n> / 30    verdict: PASS (<=5) | FAIL (>5)
1-10:  ...
11-20: ...
21-30: ...
fixes applied: <ids or none>
```

A verdict of PASS applies only to the page being handed back, not to the page that was started from.

## Attribution

The list of 30 tells was written by [@kloss_xyz](https://x.com/kloss_xyz). The original post is https://x.com/kloss_xyz/status/2097808934442844307. Packaging of this skill is by the Pixel Rainbow project: https://github.com/shagghiesuperstar/anti-vibecode. Credit the original post first when citing the list.
