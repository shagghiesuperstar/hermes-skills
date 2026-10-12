---
name: vendor-identity-verification
description: Use when naming a vendor, brand or sender in a reply. It also covers a corporate parent, a product family, a task record, a pull request or a message. Verify the corporate relationship with one cheap probe first, and do not call a sender suspicious from a pattern match alone.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [identity, vendors, verification, sender, corporate-parent, due-diligence]
    category: agent-discipline
related_skills: [source-grounded-investigation, deterministic-discovery-doctrine, agent-honesty]
---

# Vendor, Sender and Brand Identity Verification

## Overview
Before naming a vendor, brand, sender, corporate parent or product family, prove the relationship with one cheap probe. Do not work it out from a half-remembered list. A common failure is to see a sender domain, an email signature or a product footer, match it against memory, and speak confidently about who the sender is. The result is often wrong. Mergers and renames change the parent company, and the old name stays in signatures for a long time. The fix is one fetch of an official page, and the discipline to do it before speaking.

## When to Use
- You are about to say that an email is from a named vendor, or that it is phishing or spam.
- You are about to say that one vendor is independent of another, or a subsidiary of it.
- You are about to say that a product or service comes from a named company.
- You are about to say that a sender handle or domain belongs to a named entity.
- A user pasted a link from a vendor. Fetch it before saying what it contains.

## Features
- A rule that turns each identity claim into a probe with a quoted result.
- A ranked list of probes: an official newsroom or About page, a web search on the footer text, and the link the user supplied.
- An explicit "I haven't verified yet" wording for a claim made before its probe.
- A list of claim shapes that are banned until a probe is shown.
- A rule that a corporate relationship does not transfer account, pricing or login identity.

## Benefits
- Phishing claims are made only when the evidence supports them.
- A corrected corporate relationship is found in one fetch, not three rounds of argument.
- Partnerships and mergers do not cause wrong purchasing or integration decisions.

## Procedure
### 1. Identify the claim you are about to make
Before writing any sentence that names a vendor, check whether it is one of these:
- "This email is from X," or "this email is phishing."
- "Vendor X is independent," or "X is a subsidiary of Y."
- "This product is by company Z."
- "This handle or domain belongs to entity W."

If it is, run a probe first.

### 2. Run the cheapest probe that answers the question
In order of preference:
1. **An official page.** Fetch the vendor's About, company, or newsroom page. A single fetch usually shows the corporate parent, the brand hierarchy and any recent merger.
2. **A web search on the footer text.** Search the exact footer or signature string with the words "parent company". This shows whether a string is a brand, a product, a partner or a separate company.
3. **The link the user supplied.** Fetch it before saying anything about its content. A pasted link is an invitation to verify, not a replacement for verifying.

### 3. Quote the result
Write the probe in the reply: the page or search, the date, and the sentence that establishes the relationship. A probe with no quote does not count.

### 4. Say what is not yet verified
If you have not run the probe, say so and run it:

> I haven't verified that yet. Checking the vendor's newsroom now.

Do not write a confident assertion in its place.

### 5. Use the verified relationship exactly
State the relationship as the probe showed it: "X is the parent company after its merger with Y." If the probe shows the relationship is recent, say so. If it does not settle the question, say that it is unknown.

### When the rule does not apply
- The relationship already has a stable record from a probe earlier in the same session.
- The operator has told you who the vendor is. Treat the operator's statement as the reference point, and do not write it into durable notes or side effects, such as a pull request, a task record or a message, until the operator's correction has been re-read.
- Your claim is "I don't know who this is." That is itself a probe result.

### Claim shapes this skill bans
| Claim | Why it is banned |
|---|---|
| "This email is phishing because the address looks unfamiliar." | The address was pattern-matched, and no official page was fetched. |
| "This footer name is a separate company from the sender domain." | The footer may name the parent company after a merger. |
| "Vendor X is independent." | The vendor may have been acquired recently, and nothing re-checked it. |
| "This sender is the same as last week's vendor." | Two vendors can share product names. |
| "I'm confident the parent company is Y." | No probe is cited, so the confidence is not earned. |
| "Same parent, so the sibling brand's free API gives us the negotiated rate." | Corporate parentage does not carry over login, account or pricing. A new account gets list rates unless the negotiated terms are added in that product. |

## Pitfalls
- **Matching a signature to a memory of a vendor list.** Lists go stale. Probe.
- **Treating a footer as a rival company.** Footers often carry the post-merger name, and the sender may use an older product name.
- **Repeating a wrong claim after pushback.** Each repeat compounds the cost. When the probe contradicts you, correct the claim in the next line.
- **Assuming a relationship grants access.** Shared ownership does not give a login, a rate or a data-sharing agreement.
- **Writing a side effect on an unverified name.** A task record, pull request or message that names the vendor wrongly is harder to retract than a reply.

## Verification
- Every vendor, brand or parent named in the reply has a probe result quoted beside it, with its date.
- Every unprobed claim is marked as unverified, and the probe was run before the reply was sent.
- No phishing or independence claim appears without a fetched page or search result showing the relationship.
- No account, rate or login was assumed from a corporate relationship alone.
