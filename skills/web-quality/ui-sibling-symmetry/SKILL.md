---
name: ui-sibling-symmetry
description: Use when a storefront page adds or changes a control. Match the sibling controls on the same page.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [ui, consistency, design-system, storefront, review]
    category: web-quality
related_skills: [storefront-visual-acceptance, storefront-accessibility-audit]
---

# UI Sibling Symmetry (Match the Controls Beside It)

## Overview
When a filter, selector, list, nav or control appears on a page, every parallel control on that page should share its visual language. A small, regular-weight control next to a bold one reads as broken, and two inputs that collect the same fact make a visitor type twice. This skill is a checklist for UI diffs that catches these mismatches before they ship.

## When to Use
- You add or change a filter, sort, selector, navigation item, list or control on a page that already has sibling controls.
- You add a second input for a fact that another input on the same view already collects.
- You review a UI diff before it ships.
- You design a dense table, histogram or dashboard that has to work on a phone.

## Features
- A shared-grammar checklist: one family per role, matched size and weight, one casing, one active-state treatment, icons sized to the text.
- A duplicate-input rule for facts collected twice on one view.
- Narrow-width rules for charts and tables, with the overlap check that proves them.
- Layout gate for dense boards, run at full and missing data.

## Benefits
- Controls look like they belong together, so the page reads as one design.
- Visitors type a fact once, and merge conflicts between two versions of one control are caught early.
- Charts and tables stay legible on a phone.
- Reviews rest on measured layout checks, not on a builder's own view of the layout.

## Procedure

1. **List the sibling controls.** On the page you are changing, list every control with the same role (every filter group, every selector, every item in a rail). Record each one's font family, size, weight, casing, active-state colour and icon size. Read these from the computed styles, not from the stylesheet.

2. **Match the family, size, weight and casing.** Use one typeface per role. If one rail uses large bold capitals, a sort group under it uses the same size, weight and casing. Do not make the second one smaller, lighter or sentence-case.

3. **Use one active-state treatment.** Pick one pattern for the current selection and use it across the page. Mark the active item with coloured text, and leave the rest in white, with no radio dots, underlines or mixed signals. A thin accent bar can join the colour when the rail already uses one.

4. **Size icons to the text.** An icon or avatar placed beside text is legible at a glance. As a rule of thumb, a profile icon is about twice the text height. Never shrink it to the height of a letter.

5. **Check for duplicate inputs.** When two features collect the same fact in the same visual section (two postal-code fields, a search box and a filter that filters by the same field, two contact fields for one contact), ship one input. Make the other a fallback, for example a "use my location" link under the postal-code field, rather than a peer input.

6. **Plan merges so they replace controls.** When a ported change and a feature each add a version of the same control, the merge must replace the old control, not sit beside it. The merge spec names the surviving control before the work starts.

7. **Check headings.** Use the site's heading case everywhere. Use all-caps headings, with body copy in sentence case. Break two-sentence display headings after the first sentence, so a single word never sits alone at the end of a line.

8. **Check narrow widths.** Load the page at 360, 375 and 390 px. For each pair of adjacent text labels, the bounding boxes must not overlap. A check at one desktop width does not catch these bugs.

9. **Compare with the sibling control.** Take a screenshot of the new control next to the sibling it must match, and confirm they look like they belong to one page.

### Narrow-width charts and tables

A vertical bar chart with bucket labels and currency labels under the axis is illegible on a phone. Labels run together, and currency labels collide, because each label is wider than its bar's column. Changing the font size does not fix that, because the layout is the problem.

- Use one row per bucket, with the columns: bucket label, bar, count, amount and percentage.
- Size each bar by the dimension that matters most to the reader, which is often the amount rather than the count.
- Use bold capitals for group headers that carry subtotals (for example, a range of days that groups several buckets).
- Right-align numbers, use tabular figures, and never truncate them.
- Use one component on every device size. A compact type scale is fine; dropping rows is not.

### Dense dashboards

- Give each location or store one column with the same section order and the same row heights. A row that does not apply to a column shows an aligned, muted placeholder, not a gap.
- Put the two most important sections, the items that need action now and the reorder list, in the most space. Show real lists with a "plus N more" line. Summary tiles alone are not enough.
- Put secondary totals in a separate column, so the main view stays readable.
- Keep the main view to the questions a user must answer at a glance. Anything else belongs on a details page. Every new tile replaces an existing one.
- Keep every item clickable, including on TV browsers. Do not remove links for a TV mode.
- Run one page-wide layout test at two large widths, once with full data and once with missing data. The test fails on any text overlap, any element spilling out of its section, and any ellipsis. Sibling-pair checks miss overlaps across sections. When a column has fixed height, use a priority-ordered space budget and compact the lowest-priority block first.
- A builder's own visual judgement is not proof. The test output is.

### Brand colours and tokens

- Take brand colours from the current brand kit. When older design documents disagree with it, the kit wins.
- Check a hex value against the live token file before you quote it.
- Never copy another site's palette.

### Brand media

- Defer heavy media; do not remove it on a device class. Show the poster first, and start the media when it is in view.
- Before you approve a change that drops media on phones or desktops, check the sections below. If a lower section keeps its media, the hero keeps its media too.

## Pitfalls
- **A smaller sibling reads as a leftover.** Matched size, weight and casing are what make two controls look designed together. A regular-weight control next to a bold one looks unfinished.
- **Two inputs for one fact make visitors guess.** Visitors type into both and then have to pick the one that counts. Ship the input the main flow expects, and make the other a fallback.
- **A merge that keeps both versions ships two controls.** When two branches each add the same control, the rebase must remove one. Name the survivor in the spec before the work starts.
- **Checks at one width miss legibility bugs.** Labels that look fine at 1440 can collide at 360. Run the overlap check at the narrow widths.
- **An icon at letter height is a finding.** It is too small to read at a glance, even if it is technically present.
- **Removing media to speed up a phone is a regression.** Deferring it keeps the page fast and the brand intact.
- **A builder's claim that a layout is fine is not evidence.** Run the layout test with full and missing data, and read the failures.
- **Old design docs carry retired colours.** Quoting a retired hex value gives a reviewer a wrong palette. Check the current kit first.

## Verification
- Every sibling control on the page has the same family, size, weight and casing, as recorded from the computed styles.
- Only one control collects each fact in each visual section.
- The active state uses the one treatment chosen for the page, and nothing else.
- Each icon beside text is at least as tall as the text, and the avatar is about twice the text height.
- Adjacent labels do not overlap at 360, 375 and 390 px. The bounding-box check passes, not only a visual check.
- For a dense board, the page-wide layout test passes with full data and with missing data at both large widths.
