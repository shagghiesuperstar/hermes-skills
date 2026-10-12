---
name: terminal-tool-cwd-guard
description: Use when terminal commands fail on a removed directory. It also applies before any change to a repo you may not be in. Covers stale working directories, retry loops and preflight checks.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [terminal, cwd, working-directory, preflight, repos, debugging]
    category: hermes-operations
related_skills: [hermes-gateway-ops, hermes-profiles]
---

# Terminal Working-Directory Guard

## Overview
A terminal tool remembers a working directory between commands. If the process changes into a directory that is later
deleted, the remembered path goes stale, and every command then fails with the same "no such file" error, whatever the
command. A second risk is quieter: a command runs in a sibling repository with a similar name, or on another machine,
and the work looks successful while it lands in the wrong place. This skill covers how to recognize a stale directory,
how to stop retry loops, and the checks to run before any change to a repository.

## When to Use
- Every terminal command fails with the same "no such file or directory" error on one absolute path.
- A command fails the same way three times in a row.
- The user names a path or file that does not exist, and you are tempted to pick something similar.
- You are about to change or commit in a repository, and more than one similar repository exists on the machine.
- A session is resumed after a restart or a long pause, and you cannot say which directory and host it is working in.

## Features
- Symptom check that separates a stale working directory from a real command failure.
- Retry-loop rule that changes approach after two identical failures.
- Preflight record that must be complete before a repository change.
- Candidate listing that reports matches without picking one.
- Evidence rule: a claim about a change needs the tool output that shows it.
- Host check for sessions that may have been moved to another machine.

## Benefits
- A stale directory is fixed in one step, not by repeated retries.
- Changes land in the repository the user meant.
- Claims about verification match real output.
- A missing path becomes a question for the user, not a silent guess.

## Procedure
1. Recognize a stale working directory. Look for one absolute path in every error, and for the same error across unrelated
   commands:
   ```bash
   hermes logs errors --since 1h | grep -n "FileNotFoundError\|No such file" | tail -20
   ```
   Restarting the gateway clears the remembered directory. Confirm the path is gone before you restart.

2. Stop retrying identical failures. After two identical failures, change the approach: check the directory, try a
   different command that tests the same thing, or check that the tool you need is installed. Do not run the same command
   a third time.

3. Use absolute paths. Relative paths and a leading home-directory shorthand depend on the directory the tool remembers.
   If a shorthand fails with "no such file", write the full path instead. Pass a working-directory argument to each
   terminal call, so the directory does not depend on what came before.

4. Before any change to a repository, fill in this record and check each line:
   ```
   HOST:  <hostname>                    run: hostname
   PATH:  <absolute path>               run: ls -la <path>
   REPO:  <remote URL>                  run: git -C <path> remote -v
   FILE:  <filename>                    run: test -f <path>/<filename>
   DIFF:  <file, commit, branch or "none, show content only">
   ```
   If any line is unknown or missing, stop and ask. Do not fill a line with a best guess.

5. List candidates without choosing one. A search for a name can show several matching directories or files. Report
   the list, and let the user pick. Searching is allowed. Choosing a match and acting on it is not.

6. Show the evidence before a claim. Before you say a change was made, a test passed, or a commit landed, paste the output
   that shows it, such as the `git status` result and the listing of the file. A claim without that output is a claim
   that the check happened, not a check.

7. Check the host when the session may have moved. Run the host, user and working-directory commands at the start of any
   session that changes files. If the host is not the machine the work was meant for, stop and tell the user. Check that
   the terminal backend setting points at the local machine:
   ```bash
   hostname; whoami; pwd
   hermes -p <profile> config get terminal.backend
   ```

## Pitfalls
- **A stale directory fails every command.** Do not read each error separately. Look for the one path they share.
- **Three identical failures mean a wrong approach, not bad luck.** Stop and change the approach.
- **A missing path is a question.** Do not replace it with a similar directory, and do not create a directory to make the
  command run.
- **A similar name is not the same repository.** Two checkouts can share a name and differ in content. Check the remote
  and the file before any change.
- **A successful command can still be in the wrong place.** Check the working directory and the repository in the same
  step as the change.
- **A git pull merges into the current branch and changes its working files.** It needs the repository to be right and the operation to be approved.
  Run it only after the preflight record is complete.
- **"I verified" without output is not verification.** Paste the output, or say the check was not run.
- **A session can run on another machine after a configuration change.** The host check finds this before work starts.
- **Use absolute paths on every tool call during a multi-repository task.** Ambient state is what drifts.

## Verification
- A test command in the intended directory returns the expected output, and the error from a stale directory no longer appears.
- The preflight record is complete and every line matches the command output.
- The change shows in the repository's status command, and the status shows the intended repository.
- The host line in the record matches the machine the work was meant for.
