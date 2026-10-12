---
name: interactive-cli-wizard
description: Use when a CLI setup wizard waits for menu input you must provide. Covers PTY launch, arrow-key menus, polling between steps and checking the result.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [pty, interactive, wizard, terminal, setup, menus, automation]
    category: hermes-operations
related_skills: [hermes-gateway-ops, hermes-profiles]
---

# Interactive CLI Wizard Automation

## Overview
Some setup tools are terminal wizards: they draw a selectable menu or ask a question, then wait for keyboard input. A
wizard that receives input it does not expect either ignores it or closes early. This skill covers how to drive such a
wizard from an agent shell when the operator has asked for the setup to be done rather than handed over: launch it in a
pseudo-terminal, wait for each prompt, send the right kind of input for each prompt type, poll after every step, and
check the result without relying on the wizard's own success message.

## When to Use
- A setup command renders a selectable menu and stops until a choice is made.
- A prompt asks for a value and does not proceed until one is typed.
- A text user interface ignores newline input sent through a plain pseudo-terminal writer.
- The operator has asked for the setup to be completed from the agent shell, and the wizard has no non-interactive option.

## Features
- Launch in a background pseudo-terminal with the terminal tool.
- Arrow-key navigation for selection menus, and typed input for literal prompts.
- Poll-between-steps rule, so input always matches the prompt on screen.
- Check for headless options before driving a menu.
- A terminal-automation driver for interfaces that reject plain newline input.
- Independent verification of the final state.

## Benefits
- Menus are navigated correctly on the first attempt, instead of silently confirming the default item.
- A wizard that exits early is noticed at the step where it happened.
- Setup finishes with a checked result, not with a success line from the wizard.

## Procedure
1. Check for a non-interactive path first. Read the command's help, and look for an option that accepts every answer
   as a flag or an environment variable, or a subcommand that runs without a screen. Use it if it works. Treat an option
   that the help advertises as unverified until you run it once.

2. Launch the wizard in a background pseudo-terminal, so it has a real terminal:
   ```
   terminal(background=true, pty=true, command="<interactive-cli> <args>")
   ```

3. Wait for the first prompt to render before you send anything. Sending input before the prompt appears is the most
   common cause of a silent exit. Use the process tool's wait or poll action until the expected text is in the output.

4. Navigate selection menus with arrow-key escape sequences, not typed numbers. Typing a number and pressing Enter in a
   selection menu usually confirms the item that is already highlighted, which can be the final "done" item. The
   sequences are:
   - up arrow: `\x1b[A`
   - down arrow: `\x1b[B`

   Send the sequence the number of times the target is away from the highlight. Poll the output and confirm the marker
   sits on the intended item, then send Enter.

5. Answer literal prompts by typing the value and pressing Enter, as in `Choice [1/2]:` or a yes-or-no question. Send an
   empty line with Enter to confirm a highlighted item in a menu.

6. Poll after every step, and read the prompt that is on screen before you decide the next input. A long run of
   inputs sent without polling drifts out of step with what the wizard is asking.

7. If the interface ignores Enter sent through the pseudo-terminal writer, do not try byte variations. Use a terminal
   automation driver that sends a carriage return on its own terminal. A minimal shape, with placeholders, is:
   ```
   expect -c 'set timeout 900; log_file -noappend <transcript-path>;
     spawn <interactive-cli> <args>;
     expect -re {<first-prompt-text>}; sleep 3; send "\r";
     expect { eof { puts WIZARD_EXITED } timeout { puts TIMEOUT } }'
   ```
   The transcript file records the whole session, so read it after the run. Run the driver inside the background
   pseudo-terminal, and poll it with the process tool.

8. Check the tool's minimum runtime version before you start. A wizard that fails with a version message exits at once.
   If a newer runtime is needed, install it beside the system one and prefix the path only for that command.

9. Verify the result after the wizard exits. Run the tool's status command, a service check, or the log tail. Do not
   accept the wizard's own "done" line on its own.

## Pitfalls
- **Typed numbers in a selection menu skip silently.** Navigate with arrow keys. Type numbers only into literal
  prompts that show a `[n/m]` choice or a default in brackets.
- **An empty line is Enter, not a no-op.** Use it to confirm a highlighted item.
- **Masked input is expected.** A wizard may print asterisks after a secret is entered. Do not echo the secret back.
  Confirm that it was saved, and never print its value.
- **A wizard that writes secrets to the profile's env file or config is the preferred route.** It knows the exact schema,
  so the indentation and key names are right.
- **Advertised flags are not proof.** A flag listed in the help may refuse to run in the installed build. Run it once
  before you depend on it.
- **An account-existence check can fail a signup step.** If a headless command reports that the account already exists,
  switch to the sign-in path. Do not create a new account to get past the message.
- **A service installed at the end needs a decision.** A wizard may ask whether to install a background service that
  starts at login. Ask the operator first, because the service keeps running after the session ends.
- **Poll, do not blind-send.** Each input should match the prompt that is on screen.

## Verification
- The wizard's final state matches the requested configuration, and the status command reports it.
- The transcript shows each menu step landing on the intended item.
- No secret value appears in the transcript, the output or the report.
- Any service the wizard installed is listed as installed, and its start-at-login setting matches what the operator chose.
