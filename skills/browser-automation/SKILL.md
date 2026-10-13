---
name: browser-automation
description: Use when a task needs browser control on macOS. Covers choosing between agent, managed-session and scripted approaches, reliable form and frame handling, and guardrails.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [browser, automation, playwright, macos, forms, extraction]
    category: integrations
related_skills: [tinyfish-cli, mcp-client-setup]
---

# Browser Automation

## Overview
Browser automation drives a real browser to read pages, fill forms, or capture results when no API exists. Three
approaches cover most cases: an agent that reads screenshots and decides each step, a managed cloud session that keeps
logins between runs, and a scripted browser that a person writes and reviews. Each has a different failure mode. This
skill covers how to pick one, how to handle the page controls that break naive scripts, how to make results visible
when the output channel is unreliable, and the limits that apply to any approach.

## When to Use
- A task needs a page read, a form filled, or a result captured, and no API does the job.
- A scripted step returns success but the expected output never comes back.
- A form field looks filled but the page rejects it on submit.
- You need to choose between an agent, a managed session, or a script for a browser job.

## Features
- Decision table that maps each approach to the job it fits.
- Patterns for controlled inputs, icon-only buttons and embedded frames.
- Output rules for when the wrapper does not return standard output.
- Extraction size guidance for long pages.
- Guardrails for bot protection, identity, credentials and payments.

## Benefits
- The approach matches the job, so a simple task does not need a heavy tool.
- Form and frame failures are found at the step where they happen.
- Results survive a failed output channel.
- Automation stops at the boundaries the operator has set.

## Procedure
1. Choose the approach:

   | Approach | Fits | Watch for |
   |---|---|---|
   | Agent reading screenshots | Open-ended browsing where each step needs judgment | Needs a vision-capable model; slower and less repeatable |
   | Managed cloud session | Long-lived sessions shared by a team, with stored login state | Needs an account and a paid tier; the session state is sensitive |
   | Scripted browser (Playwright or similar) | Repeatable, reviewed flows on a site you control or are authorized to automate | Breaks when the page changes; needs explicit waits |
   | Native macOS scripting | Quick control of an app already open | Limited page access; needs the operator to grant accessibility permissions |

2. Set up access legitimately. Use an account the operator owns or is authorized to use. Keep credentials in the secret store,
   never in the script. If a site asks for a verification challenge or a second factor, stop and ask the operator to complete it.

3. If the bundled browser binary is missing, point the scripted browser at an installed browser by its path, and state
   that path in the run notes. Give each run a short timeout, so a stuck page fails quickly.

4. Fill controlled inputs with the element's own value setter, then dispatch the input, change and blur events. Setting the
   value through a plain fill call can look successful while a framework that tracks the value discards it. The page then
   shows a "required" message on submit. Check the value after the fill, and read it back from the page.

5. Find icon-only buttons by a stable attribute. A button with no text can be matched by a distinctive part of its icon's
   path data, or by its position in a labelled group. Confirm the match by reading the button's attributes before you click.

6. Work with embedded payment or identity frames by locating the frame by its address, not by the parent page. Wait for the
   frame to load after the action that opens it. Do not enter payment card data unless the operator has authorized a test
   transaction on a test environment.

7. Make results visible without relying on standard output. When the wrapper does not return what the script printed, write
   the results to a file, and read that file in a separate step. Save screenshots to a folder, and list it afterwards.

8. Extract page content with a size limit that fits the page. A short article fits a small limit. A long document needs a
   larger one, and a truncated read looks like a complete one. Remove site chrome such as navigation and login prompts
   before you use the text.

9. Verify the outcome in the destination, not in the browser's last screen. Read back the saved record, the sent message,
   or the order status.

### Guardrails
- **Respect each site's terms and its robots instructions.** If the terms forbid automated access, do not automate it.
- **Do not bypass bot protection.** When a site shows a bot wall, a challenge or a rate block, record it as blocked and
  stop. Do not change the browser fingerprint, the user agent, or the request headers to get past the control.
- **Do not impersonate another client.** Use the identity the operator authorized, and do not present a different one.
- **Stop at login and payment steps unless authorized.** Enter credentials only from the operator's secret store, and only
  for the account the operator named.
- **Keep cookies and session state private.** Do not print them, do not copy them to shared locations, and do not inject
  them into another session.

## Pitfalls
- **A script that ends with success can still have done nothing.** Check the destination.
- **A fill that looks successful can be discarded by the page.** Read the value back.
- **An icon-only button has no text to match.** Match a stable attribute, and confirm before clicking.
- **A frame that loads after an action is not in the page's frame list yet.** Wait, then look for it.
- **Disabled outer buttons are common while an embedded frame loads.** Act inside the frame.
- **A truncated extraction reads as complete.** Use a limit that matches the page length.
- **Long-running browser tasks can outlive the session that started them.** Save progress to a file as you go.

## Verification
- The chosen approach matches the job, and its access is authorized by the operator.
- Each filled field reads back the value that was entered.
- The result exists in the destination, with its identifier.
- Any blocked page is recorded as blocked, with no attempt to bypass it.
- No credential, cookie or payment detail appears in the output or the saved files.
