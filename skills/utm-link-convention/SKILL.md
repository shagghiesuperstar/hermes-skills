---
name: utm-link-convention
description: Use when publishing any outbound storefront link. Checks UTM parameters against the team's naming convention and blocks links that fail.
version: 1.0.0
author: Pixel Rainbow (shagghiesuperstar)
license: MIT
metadata:
  hermes:
    tags: [utm, campaign-tracking, links, analytics, marketing]
    category: research-content
related_skills: [regulated-catalog-content, storefront-copy-drafts]
---

# UTM Link Convention

## Overview
Every outbound link to a storefront carries UTM parameters that name the channel, the sender, the campaign and the asset in one consistent form. The convention keeps analytics comparable across channels and keeps personal data out of URLs. A link that does not meet it is not ready to publish. Run the lint on the rendered output just before anything is sent or scheduled.

## When to Use
- You draft, schedule or publish an email, SMS message, social post, affiliate placement or paid ad that links to a storefront.
- You review a campaign calendar or a set of drafts that contain links.
- You add a new channel, or a new storefront host, to a campaign.

## Features
- A fixed set of required and optional parameters, with value rules.
- A closed set of medium values.
- A campaign name format that includes the site, the year and month, and the initiative.
- Examples for each channel.
- A fail-closed lint gate that finds every link in a file.

## Benefits
- Campaigns from different channels compare directly, without manual cleaning.
- Personal data stays out of analytics URLs.
- A broken link fails before it is sent, not after.

## Procedure

1. **Set the parameters.** Four are required: `utm_source`, `utm_medium`, `utm_campaign` and `utm_content`. `utm_term` is optional, and is used for paid audience buckets. Add no other `utm_` keys, such as `utm_id`. Keys are lowercase.

2. **Choose the medium from the closed set.** Use one of `email`, `sms`, `social`, `affiliate` or `paid`. Any other value fails.

3. **Name the sender.** `utm_source` names the sending system or platform family, such as the email platform or the social network. Use lowercase, with underscores or hyphens. For an affiliate, use `aff_` followed by the partner's business or creator handle, never a person's name.

4. **Name the campaign.** Use `<site>-<yyyymm>-<initiative>`. The site is one of the storefront names the team has registered, and it must match the host the link lands on.

5. **Name the content and the term.** `utm_content` describes the asset: the template and variant, the message id, the clip id, the placement slot or the creative id. `utm_term` describes an audience bucket for a paid placement. Neither names a recipient.

6. **Check every value.** Each value matches `^[a-z0-9_-]{1,40}$`. No value contains an email address, a phone number, a person's name, or an order, customer or cart id.

7. **Keep the first touch.** The storefront must not rewrite these parameters on later visits. If it does, tell the storefront team.

8. **Run the lint on the rendered output.** Lint the final text of each draft, not the template. An unfilled placeholder, such as `{{variant}}`, fails by design. Check every http or https link in the file, including links inside CSV cells. Give the lint an expected medium for each file, so an email file cannot carry a social link.
   - Exit code 0: every link passes.
   - Exit code 1: at least one link fails. Do not send or schedule.
   - Exit code 2, or zero links found: a usage error or an empty scan. Treat it as a failure, never as a pass.
   - Exempt a host only for an unsubscribe or preference provider, and name the exemption in the review notes. Every other link is checked.

9. **Map custom domains.** When a store runs on a custom domain, map that host to its storefront name in the lint configuration, so the site check in step 4 still applies.

### Channel Examples

| Channel | utm_medium | utm_source | utm_campaign | utm_content / utm_term |
|---|---|---|---|---|
| Email | email | the email platform, e.g. `email_platform` | `<site>-202610-spring-intro` | template and variant, e.g. `intro-v1` |
| SMS | sms | the sender family, e.g. `sms_reorder` | `<site>-202610-day21-restock` | message id, e.g. `nudge-a` |
| Social | social | the platform, e.g. `tiktok` | `<site>-202610-shorts` | clip id, e.g. `clip-014` |
| Affiliate | affiliate | `aff_<partner-slug>` | `<site>-202610-newsletter` | placement, e.g. `slot-a` |
| Paid | paid | the network, e.g. `ad_network` | `<site>-202610-retarget` | creative in content; audience bucket in term |

Example links, where `<store-host>` is the storefront's host:
- Email: `https://<store-host>/?utm_source=email_platform&utm_medium=email&utm_campaign=<site>-202610-spring-intro&utm_content=intro-v1`
- Paid: `https://<store-host>/?utm_source=ad_network&utm_medium=paid&utm_campaign=<site>-202610-retarget&utm_content=creative-3&utm_term=lookalike-b`

## Pitfalls
- **A medium outside the closed set is a failure, not a new channel.** Ask the team to add the medium before you use it.
- **A recipient's name in a parameter is personal data.** Describe the asset or the audience bucket instead.
- **An empty scan hides broken drafts.** A lint that finds no links must fail. Check the scan count in its output.
- **Quote URLs in shell commands.** An unquoted ampersand ends the command early.
- **An unfilled template passes as a link.** Lint the rendered output, not the template.
- **A campaign site that differs from the host is a failure.** Check that the `<site>` part of `utm_campaign` matches the host.
- **Affiliate names are business handles.** A creator's personal name in `utm_source` is a leak.
- **Lint again after every edit.** A link added after the lint is not checked. Run the lint as the last step before sending.

## Verification
- The lint exits 0 on the rendered files, and its scan count is above zero.
- Each link has all four required keys, a medium from the closed set, and a campaign whose site matches its host.
- No parameter value contains an email address, a phone number or a personal name.
- The lint ran after the last edit to each file.
