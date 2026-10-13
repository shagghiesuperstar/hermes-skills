---
name: repo-sanitization-publishing
description: Use when publishing code or docs publicly on GitHub. It must carry no personal identifiers, machine identity, network details or secrets. Covers maintaining that public repository afterwards.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [github, privacy, pii, sanitization, publishing, repository, stewardship]
    category: devops
related_skills: [repo-backup, repo-ssot-hygiene, git-remote-hygiene, pr-evidence-verification]
---

# Repository Sanitization and Publishing

## Overview
Anything committed to a public repository is copied, indexed and cached, and it cannot be fully withdrawn. Internal work carries identifiers that are easy to miss: user names in paths, machine and network names, private addresses, model nicknames and commit identities. This skill builds each publishable artifact clean from the start, runs a sweep over the text before any push, sets a no-reply commit identity, confirms visibility by reading it back, and runs a landing gate before the work is called done. After publication it covers how to keep the public repository clean and correct.

## When to Use
- The operator asks to commit a folder to a repository, create a repository, make one public or private, or open-source a tool.
- Files must be added to a repository that already exists.
- An internal skill or document needs a generic published copy.
- You maintain a public repository and must review changes to it.

## Features
- A neutral build folder, so no identity-bearing tree is used as the origin of the artifact.
- Sanitized-by-construction defaults: relative paths, environment variables for hosts, and generic names for group identifiers.
- A pattern sweep that runs before the first commit and before every later push.
- Removal and ignore rules for macOS folder-metadata files.
- A visibility read-back after creation.
- A landing gate that runs the tests, re-checks the most sensitive settings, and reconciles the file list.
- Stewardship rules for a public repository: one pull request per change, live probes before any claim, and fresh installs for behaviour that changes outside the repository.

## Benefits
- Identity is removed before the first commit, not patched later.
- The sweep checks the documents that describe sanitization, not only the code.
- Visibility is never changed by guesswork.
- Each publish ends with a checked result that a reviewer can repeat.

## Procedure

### Operator rules
1. **No identifiers in committed content.** No user names, machine names, host names, private addresses, absolute paths under a home folder, email addresses, real names, credentials, key prefixes or internal model nicknames.
2. **A no-reply commit identity every time.** Set the commit name and email to the account's no-reply address. Never use the real identity.
3. **Visibility is an explicit instruction.** If the request says private, create it private, even when the stated goal is a later public release. When visibility is ambiguous, create the repository private, and change it later with an explicit edit.
4. **Confirm the account first.** Check which account is signed in before creating anything.

### 1. Build in a neutral folder
Build the artifact in a folder that is not inside a tool's configuration tree. If the material arrives as an archive, extract it straight into the neutral folder:
```zsh
mkdir -p ~/src/<repo-name>
unzip <archive>.zip -d ~/src/<repo-name>
```

### 2. Write it clean from the start
- Make every path relative to the home variable or the project root.
- Make every host `localhost` or an environment variable.
- Make every credential an environment variable with a generic default.
- Clean the defaults too. A default group identifier that contains a user name leaks identity even when the code is clean. Use a generic default, and document the local override in a private note outside the repository.

### 3. Run the sweep before the first commit
Run a sweep script over the working tree. Write it in Python rather than as one grep with lookahead patterns, because some lookaheads silently match nothing on the default macOS grep. The script should:
- Load the identity strings from a list kept outside the repository.
- Skip build output, dependency folders, environment files and cache folders.
- Match plain substrings, and print the hit count for each pattern.
- Exit non-zero on any hit.

Fix every hit, and run the sweep again until it reports clean. Whitelist the account's own handle, so that only other identifiers cause a failure. The handle appears in license lines and clone addresses, and that is expected.

### 4. Remove folder metadata files
On macOS, the folder-metadata file must not be committed. Remove it from tracking, and add both ignore rules in the same step, so that it does not return on the next add:
```zsh
find . -name .DS_Store -exec git rm --cached {} +
printf '\n.DS_Store\n**/.DS_Store\n' >> .gitignore
```
Commit the ignore change immediately afterward.

### 5. Initialize, commit and create the repository
```zsh
git init
git config user.name "<no-reply-name>"
git config user.email "<no-reply-address>"
git add -A
git commit -m "<descriptive message>"
gh repo create <account>/<repo-name> --private --source . --push --description "<description>"
```
Read the visibility back. Do not rely on the create output alone:
```zsh
gh repo view <account>/<repo-name> --json name,visibility,isPrivate,url
```

### 6. Add files to an existing repository
When the task is to add files to a repository that already exists, do not create a new one:
1. Stage the files in a separate scratch folder, written clean from the start.
2. Run the sweep on the scratch folder, before the target repository is touched.
3. Remove any old local clone, and clone the repository fresh. Do not reuse a checkout that may have diverged.
4. Set the no-reply identity in the clone. A fresh clone does not always inherit the global setting.
5. Copy the staged files into a subfolder of the clone, add them, commit and push.
6. Check the result with `git log --oneline -3` and `git ls-files <subfolder>/`. Confirm that only the intended files landed and that nothing existing was overwritten.
7. Leave the repository's visibility as it is. The private-by-default rule applies only to new repositories. If the new content is more sensitive than the current visibility, stop and ask.

To publish a generic version of an internal document, write a new derivative file in the scratch folder. Do not edit the internal copy in place.

### 7. Publish through a secondary account
When the target is an account other than the one the command-line tool is signed in to, create the repository through the REST API, using a token kept in a credential store. Do not embed the token in a remote URL, because a token in a remote URL appears in `git remote -v` and is stored in the repository's configuration. After the first push, confirm that the remote URL has no credential in it:
```zsh
curl -s -X POST https://api.github.com/user/repos \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "<repo-name>", "private": true}'
git remote set-url origin "https://github.com/<account>/<repo-name>.git"
git remote -v
```
Confirm that the response includes a clone address before you continue. Apply the same landing gate to this account.

### 8. Use SSH for private operator repositories
When a remote must use SSH, use a dedicated key for the repository host, and add the public key through the host's settings page. The command-line key-add command needs a token scope for public keys. If that scope is missing, have the operator paste the public key in the browser.

Check the remote-rewrite settings. A global rule that rewrites SSH addresses to HTTPS makes `git remote -v` show the wrong transport. Find the rule, and remove it only after confirming with the operator:
```zsh
git config --global --get-regexp '^url\.'
```
Verify with `ssh -T <git-user>@<git-host>` and `git ls-remote origin`. Commit as the no-reply identity, never commit the private key, and publish only the public key.

### 9. Run the landing gate
After the repository exists and has been pushed, run these checks before the task is called done:
1. **Run the tests.** If the repository has a test command, run it and require every test to pass. If the test count differs from the count the operator expected, flag it. If there are no tests, say so. Never report a suite as green when none exists.
2. **Read the most sensitive checks raw.** Find the check that proves the core contract, and run its assertions directly, not only through the suite. A test that passes against a changed rule set proves nothing.
3. **Reconcile the file list.** Compare the tracked files with the repository's own file map. Every file in the map must exist. Every other file must be explained, apart from known exceptions such as the ignore file, the readme and the license. No environment file and no folder-metadata file may be tracked:
   ```zsh
   git ls-files | sort
   ```
4. **Record the landing.** Write the repository address, the commit, the test result and the date to the operator's notes. Do not write the operator's own identifiers into any public file.

### 10. Steward the public repository afterwards
- **Probe the live repository before describing it.** Fetch the current files and the repository tree, and read them. Do not describe the public repository from a local clone or from memory.
- **One pull request per change.** Keep each change small, with a title that names the change and a body that states what changed and why.
- **Run the sweep on every commit,** not only the first.
- **Test behaviour that changes outside the repository.** For an installer, install from a fresh clone. For a file mode, check the mode in the pull request's branch.
- **Re-check each open pull request after a merge.** After each squash merge, update the next branch from the base, resolve any conflict, push, wait for checks and then merge. Do not force-merge a dirty base.
- **Attribute adapted public work.** Name the authors and link their public project for any idea or text that came from them. Use a concept only when its licence allows it, and never copy code into a repository under an incompatible licence.
- **Shadow-test risky behaviour before merging.** Run it in an isolated copy for a stated period, and check that the isolated copy is really running the new code before you rely on the result.

## Pitfalls
- **A readme that names what it removed.** A sentence such as "no references to this machine's name or user path" is itself a leak. Sweep the documents that describe sanitization as well.
- **Hardware lines that name a machine.** Describe the class instead, such as "Apple silicon with 128 GB of unified memory."
- **Internal model or server names.** Describe the class, such as "a quantized mixture-of-experts model" or "a local OpenAI-compatible server."
- **Local-override instructions in the repository.** Keep machine-specific settings in a private note outside the repository.
- **A folder-metadata file that comes back.** Removing it from tracking without an ignore rule lets it return on the next add.
- **A sweep that passes once and never runs again.** Run it before every push, including after documents are added later.
- **A token in a remote URL.** It is stored in the repository's configuration and shown by `git remote -v`. Use a credential store.
- **A fine-grained token missing a permission.** It can work for clone and push, and still return an empty result for workflow runs. Check what the token can read before you read an empty result as "no runs".
- **Instruction files written into a protected path.** If a write to an agent instruction file is blocked by a permission gate, do not retry through another route. Put the onboarding text in a documentation file and link it from the readme.
- **Sweeping build output.** Skip build output, dependency folders and environment files, or the sweep reports false hits from generated files. Sweep the staged tracked content.
- **An installer script that is not executable in version control.** The file mode must be executable in the commit, not only on the local disk. Set it with `git update-index --chmod=+x <file>`, and check the mode in the pull request's branch, not only on the main branch.
- **Path roots computed from a test file.** Compute the repository root from the test file's location, and assert that a known file exists there.
- **Keyword arguments that drift after a merge.** Check every call site against the current function signature.
- **An open pull request is not done.** Done means merged, with the merge commit confirmed and the checks green.
- **Branch names are live facts.** Copy a branch name from the remote listing, not from memory.
- **Shipped is not deployed.** A green pull request and an isolated test do not prove that the installed copy runs the new code. Compare the commit, the installed hash and the running process before you call it live.

## Verification
- The sweep reports clean on the staged content, and it ran after the last document was added.
- The repository's visibility matches the operator's instruction, as read back from the host.
- The commits use the no-reply identity.
- The tracked file list has no environment file, no folder-metadata file and no unexplained extra file.
- The test result is reported as run and passed, as not run because none exists, or as failed with its output.
- No remote URL contains a credential.
