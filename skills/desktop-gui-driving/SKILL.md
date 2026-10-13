---
name: desktop-gui-driving
description: Use when driving a desktop GUI with several windows open. Confirm the target window is in front and the input reached its field, and hand the keyboard back when it did not.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [desktop, gui, automation, safety, focus, multi-window]
    category: agent-discipline
related_skills: [agent-honesty, execution-discipline, ask-before-assuming]
---

# Desktop GUI Driving

## Overview
Driving a graphical desktop with several windows open fails quietly. A click or keystroke goes to whichever window is in front at that moment, and that is not always the window the plan named. The usual result is input that lands in a browser tab, a chat window or a password manager that nobody meant to touch. This skill adds a verification layer to the basic capture-act-capture loop: confirm the target is in front, confirm the input reached its field, and stop the moment it did not.

## When to Use
- The task drives a native application or a browser through screen capture, an accessibility tree, clicks or keystrokes.
- More than one window or tab is open, and the target might not be the one in front.
- A form or field could be shared by two windows that look alike.
- A verification read after an action reports "unverifiable" or shows no expected change.

## Features
- An inventory of running apps and windows before the first action, with the front-most window identified.
- Element-based actions preferred over screen coordinates.
- A post-action check that reads the field back, rather than trusting the delivery status.
- A bail-out rule: one verifiably wrong-window input stops the run.
- A hand-back script for the operator when focus or the surface is unsafe to drive.

## Benefits
- Input lands in the field the operator meant, or the run stops before it leaves the target.
- Sensitive windows (banking, password managers, mail, chat, admin consoles) are not driven without permission.
- The operator gets a clear next step instead of an unexplained failure.

## Procedure
### 1. Inventory the desktop before the first action
List the running apps and their windows. Identify the front-most window on the active desktop or space. A capture of a background window does not show where the next click will land. Capture the target app only after confirming it is front-most.

### 2. Capture first, then act by element
Capture an indexed element list for the target, then act on an element index. Element-based actions are more reliable than coordinates. Coordinates are screen-relative, and a pixel click does not confirm which window is in front. Use coordinates only when the element tree has no entry for the control, and say so in the plan.

### 3. Verify after every state-changing action
Re-capture and read the field value, or compare pixels. Ask one question: did the change appear in the field that was targeted? An "unverifiable" result means the tool delivered the event but could not read the outcome. It is not a success.

### 4. Stop when input reaches the wrong window
If input landed in a window the plan did not name, stop. Do not try once more, and do not type to undo it. Report what landed where, and ask the operator to bring the right window forward.

### 5. Confirm focus before typing long text
For a multi-field form, click the field, capture, and confirm the caret or value moved. If the next capture shows no change, the field never took focus. Do not type a long string to find out. Type one short character, capture once more, and only then enter the full value.

### 6. Use a set-value action only from the latest capture
Some tools bind an element index to one snapshot. Use an index only from the most recent capture. If the tool refuses a stale index, capture again and retry once. If the retry fails, click the element and type the text instead of looping on the set-value action.

### 7. Hand the keyboard back when the surface is wrong
Stop driving and ask the operator to act when any of these is true:
- The target window is not front-most, and bringing it forward would disturb the operator.
- Two input attempts on the same control both returned unverifiable results with no visible change.
- The window that would receive input is a personal or sensitive surface the operator did not authorize.
- A field is shared by two windows and the accessibility tree cannot tell them apart.

### 8. Write the hand-back plainly
Name the action (for example, "click Create"), and any short text the operator should enter, word for word. Do not paste the operator's secrets or personal data into the chat. Wait for the operator to confirm before resuming.

## Pitfalls
- **Reading "unverifiable" as "probably landed".** The most common silent failure on a busy desktop is that focus shifted before the input. The only proof is the post-action read of the targeted field.
- **Trusting coordinates for forms.** A click at a screen position lands in whatever window is in front at that position.
- **Typing to test focus.** A long string typed into the wrong field is the costly outcome. Test with one character.
- **Driving a surface the operator is reading.** Even a correct target looks like a takeover to someone at the keyboard. For banking, password managers, OAuth prompts and SMS codes, do not type at all.
- **Retrying the same rung.** Two unverifiable results on one control mean the surface is the problem. Stop, re-list the windows, and hand back if the target is still not clearly in front.
- **Undoing a wrong input by typing more.** A second wrong input on top of the first makes the damage harder to find.

## Verification
- The front-most window was confirmed before the first input, and the reply names it.
- Every state-changing action has a post-action read of the targeted field showing the expected value.
- No input reached a window outside the plan. If one did, the run stopped and the operator was told which window.
- Every hand-back step names the action, the window and the expected result, with no secrets in the text.
