---
name: hermes-skill-sharing
description: Use when publishing a Hermes skill to GitHub or a hub. Publishing goes to a public GitHub repo and a community hub. Covers account checks, credit, install URL proof and the hub submission.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [hermes, skills, publish, community, github, sharing]
    category: hermes-operations
related_skills: [hermes-upstream-contribution]
---

# Hermes Skill Sharing

## Overview
Sharing a skill means three separate publications: a public repository that holds the skill, a raw-file install URL that
works without a login, and a submission to a community hub that reviews it. Each step can publish under the wrong
account or with the wrong content, and a leftover token in the environment can make the hub submission use a different
identity. This skill sets the order of work so each step is checked before the next one starts.

## When to Use
- You want a skill of your own published to a public repository and offered to a community hub.
- You are packaging someone else's post, list or idea as a skill. Credit the original author in the skill.
- Do not use it for changes to the upstream project's own repository (see the upstream contribution skill), or for a
  skill that only lives in your personal skills folder.

## Features
- Account check before any repository is created or pushed.
- Skill folder layout with a license, a readme and a credited attribution section.
- Public-visibility and raw-URL checks.
- Hub submission from the skill folder, with the environment token cleared.
- Attribution in three places: the skill, the readme and the submission comment.

## Benefits
- A skill is never published under the wrong owner.
- An install command is proven to work before it is shared.
- Original authors keep their credit.
- A share message is only drafted, never posted, unless the operator asks for it.

## Procedure
1. Confirm the publishing account before anything else:
   ```bash
   gh auth switch --user <community-account>
   gh api user --jq .login
   ```
   If the printed login is not the community account, stop. Work repositories and community repositories belong to
   different owners.

2. Gather the material. If it is a public post, read its text from a public page or API, and record its author.
   Do not reconstruct a list from memory.

3. Write the skill at `skills/<name>/SKILL.md`, where the folder name equals the skill name. Put the original author in
   an Attribution section. The skill's own author line follows the library's contract. Keep the trigger sentence
   self-contained in its first line.

4. Lay out the repository with a readme that holds the install command and the credit, a license file, and the
   `skills/<name>/` folder. Work in a dedicated folder under your workspace.

5. Also write a local copy into your own skills folder, so this machine can load the skill.

6. Commit with a single-line message. Multi-line messages built with nested shell quoting break in some agent shells, so
   use a plain `-m` argument.

7. Create the repository from that folder and push it. Then confirm its visibility:
   ```bash
   gh repo create <community-account>/<name> --public --source . --remote origin --description "<one line>" --push
   gh repo view <community-account>/<name> --json url,visibility,isPrivate
   ```
   The visibility must be public.

8. Prove the install URL. The raw file must return HTTP 200 without a login:
   ```bash
   curl -s -o /dev/null -w '%{http_code}\n' https://raw.githubusercontent.com/<community-account>/<name>/main/skills/<name>/SKILL.md
   hermes skills install https://raw.githubusercontent.com/<community-account>/<name>/main/skills/<name>/SKILL.md
   ```

9. Submit to the hub from the skill folder, not the repository root. Clear any token variable in the same command, so the
   hub uses the account you just switched to:
   ```bash
   env -u GITHUB_TOKEN hermes skills publish <abs-path-to-skill-folder> --to github --repo <hub-owner>/<hub-repo>
   ```
   The safety scan must return a safe verdict. Note the pull request URL that comes back.

10. Add a comment to the hub pull request that credits the original author and links the public repository. The
    automatic description does not include the credit.

11. If the operator asked for a share message, draft one of at most 280 characters, with the credit and the repository
    link. Do not post it unless the operator says to post it.

12. Switch back to the account you normally use, and confirm the login.

## Pitfalls
- **Check the account before creating a repository.** The default account is often the wrong owner for a community
  repository.
- **A hub submission from a repository root is the wrong shape.** Publish the skill folder itself.
- **Do not publish a repository through the hub command and expect it to be your own.** The hub command forks the target
  and opens a pull request. Push your own public repository directly, then submit the skill to the hub.
- **Do not drop the original author's credit.** Packaging a post does not make the idea yours.
- **A stale token in the environment can publish as the wrong user.** Clear it for the submission command.
- **Related skills in a hub entry must exist in the hub's own catalog.** A link to a skill that exists only on your
  machine is a broken reference for everyone else.

## Verification
- The account login was the community account at create, push and submission time, and back to your usual account at the end.
- The repository is public, and the raw skill file returns HTTP 200.
- The install command installs the skill on a clean profile.
- The hub returns a pull request URL with a safe verdict.
- The attribution appears in the skill, the readme and the submission comment.
