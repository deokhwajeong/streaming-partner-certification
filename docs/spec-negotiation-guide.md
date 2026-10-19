# Partner Spec Negotiation Guide

Most certification failures that cost weeks were visible on day one in the partner's spec sheet. The job at intake is to say no early, with the platform limit attached, and to arrive with an alternative that still gets the partner what they actually need.

## When to open a negotiation

| Partner declares | Platform limit (example) | Gate it would fail | Typical root cause |
|---|---|---|---|
| Peak memory above the per-tier app limit | Entry 384 MB, mid 512 MB, premium 768 MB+ | G1.1 | Same build as their flagship device; large image caches; bundled web runtime |
| HDR or 4K required on every model | HDR pipeline only on 2160p models | G1.2 | Marketing requirement applied to the whole fleet |
| Codec or DRM level not on older SoCs | Hardware DRM and newer codecs from a given SoC onward | G2.3 | Content licensing terms written for newer devices |
| Private or undocumented platform APIs | Public SDK only | G2.1 | Workarounds carried from another platform |
| Bitrate ladder top rung above decoder ceiling | Per-SoC max bitrate | G2.3, G4.2 | Single ladder for all devices |
| Launch on models below min SDK | SDK floor for required APIs | G1.3 | Reach targets in the partner contract |

## The conversation

| Step | What you do | What you say (pattern) |
|---|---|---|
| 1. Name the limit | State the number and where it comes from | "Entry tier apps get 384 MB. That ceiling protects the tuner and the system UI on a 1.5 GB device." |
| 2. Show the gap | Put their number next to it, per tier and model count | "Your spec says 470 MB. That fails intake on 13 of 40 models in your target list." |
| 3. Ask what they need | Separate the requirement from the implementation | "Is 470 the requirement, or is it what the current build uses?" |
| 4. Offer two paths | One that changes the app, one that changes the scope | "Cap the texture cache and use the 1080p ladder on entry, or launch on mid and premium first." |
| 5. Put a date on it | Tie the decision to the gate calendar | "We need the revised spec by Oct 31 to keep the Fall train." |
| 6. Write it down | Confirm in writing the same day | Spec delta, agreed scope, owners, date |

## What not to do

| Anti-pattern | Why it hurts | Instead |
|---|---|---|
| Accept the spec and "see what QA finds" | Failure lands at G2 or G4 after weeks of test spend | Fail it at G1 with the number attached |
| Grant a one-off exception to a platform limit | Becomes the precedent every partner cites | Change the limit through architecture review, or do not change it |
| Negotiate the limit in a launch readiness review | Pressure of the date wins over the facts | Limits are closed at G1 |
| Say no without an alternative | Partner escalates to their executive sponsor | Always bring two options |
| Let business development promise models before G1 | Contract and capability diverge | Partner TPM reviews scope before any reach commitment |

## Negotiation record

| Field | Value |
|---|---|
| Partner, app, version | |
| Limit in question and source | |
| Partner declared value | |
| Models affected (count and list) | |
| Options offered | |
| Agreed resolution | |
| Spec delta and due date | |
| Approvers (partner and platform) | |
