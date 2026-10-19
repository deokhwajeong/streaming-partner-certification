# Launch Readiness Review: Template

One meeting, one decision, one record. Pre-read goes out 24 hours ahead with the output of `partner-cert evaluate`. If a signer has not read it, the review moves; it does not proceed on summaries.

**Release train:** ______ **Review date:** ______ **Chair:** Program TPM ______

## 1. Decision requested

| Partner app | Version | Engine recommendation | Coverage | Proposed decision | Ship date |
|---|---|---|---|---|---|
| | | GO / CONDITIONAL / PARTIAL / NO-GO | __ of __ models | | |

## 2. Gate sign-off

| Gate | Status | Signer | Signed (Y/N) | Notes |
|---|---|---|---|---|
| G1 Intake and spec review | | Partner TPM, platform architect | | |
| G2 Platform compatibility | | QA lead, platform eng | | |
| G3 Commerce and legal | | Payments lead, legal | | |
| G4 Performance and stability | | QA lead | | |
| G5 Launch readiness | | Program TPM | | |
| Partner acceptance | | Partner engineering lead | | |

## 3. Open blocking issues (top 5 by reach)

| Rank | Issue | Gate | Models blocked | Owner | Fix ETA | Ship without it? |
|---|---|---|---|---|---|---|
| 1 | | | | | | No: hold these models |

## 4. Waivers in effect

| Partner | Test | Approved by | Expires | Mitigation | Check-in cadence |
|---|---|---|---|---|---|
| | | | | | Weekly sync |

A waiver expiring before the next release train is flagged red. Renewal requires the original approver and a new date, not a silent extension.

## 5. Launch scope

| Partner | Models in scope | Models held | Reason held | Re-test window |
|---|---|---|---|---|
| | | | | |

## 6. Operational readiness

| Item | Owner | Ready (Y/N) |
|---|---|---|
| Store listing, artwork, and regional metadata approved | Partner TPM | |
| Support runbook and known-issues list delivered to support | QA lead | |
| Staged rollout plan (percent and hold points) agreed | Program TPM | |
| Rollback path tested (delist, version pin, or kill switch) | Platform eng | |
| Partner on-call contact for launch week confirmed | Partner TPM | |
| Launch-week metrics dashboard live (crash rate, start failures, purchase errors) | QA lead | |

## 7. Record

| Field | Value |
|---|---|
| Decision | |
| Conditions attached | |
| Dissent recorded | |
| Next checkpoint | |

Decisions are final when the chair reads them back and no signer objects. Dissent is written down with the name attached, then the meeting moves on.
