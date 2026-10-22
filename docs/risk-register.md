# Risk Register: Template and Worked Example

Reviewed weekly at the program review. A risk without an owner and a trigger date is a worry, not a risk; it does not go on the register until it has both.

## Scoring

| Score | Likelihood | Impact |
|---|---|---|
| 1 | Unlikely (<20%) | Single model or cosmetic |
| 2 | Possible (20 to 50%) | One tier or one partner partially held |
| 3 | Likely (50 to 80%) | One partner held, or a model year affected |
| 4 | Near certain (>80%) | Multiple partners held, or the release train slips |

Exposure = likelihood x impact. 9 and above is reviewed every week with a named mitigation in flight. 12 and above goes on the escalation matrix.

## Template

| ID | Risk (cause, event, effect) | Gate | L | I | Exp | Owner | Trigger / date | Mitigation | Contingency | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| R-__ | Because ___, ___ may happen, which would ___ | | | | | | | | | Open / Watching / Closed |

## Worked example: Fall partner release train

Uses the fictional data in `examples/data`. Numbers come straight from `partner-cert evaluate`.

| ID | Risk (cause, event, effect) | Gate | L | I | Exp | Owner | Trigger / date | Mitigation | Contingency | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| R-01 | Because Fathom Originals declared 470 MB against a 400 MB entry tier limit, 13 entry models fail intake, which drops coverage to 68% and makes the launch NO-GO | G1 | 4 | 3 | 12 | Partner TPM | Revised spec by Oct 31 | Spec negotiation: offer 1080p ladder and texture cache cap on entry tier; platform shares its memory profiling tool | Launch mid and premium only next train, with partner sign-off on the reduced scope | Open |
| R-02 | Because DRM renewal fails on pre-6.4 firmware (DEF-4471), Cinder Films is held on 4 models from the 2024 line, which leaves users on the old firmware without the app | G2 | 3 | 2 | 6 | Platform eng | Firmware 6.4 rollout reaches 95% by Nov 15 | Accelerate 6.4 OTA to affected SoCs; partner adds renewal retry | Ship PARTIAL; hold list published to support | Watching |
| R-03 | Because the Driftwood Kids parental gate record was never submitted and legal has not signed, a global gate fails, which blocks the entire kids launch | G3 | 4 | 3 | 12 | Legal | Evidence by Oct 24 or drop from train | Daily check-in with partner compliance lead; pre-review their gate design | Move to next train; communicate to partner leadership now, not at the review | Open, escalated |
| R-04 | Because Brightline Sports cold start is 3920 ms on entry tier, it ships under waiver; if 5.1.0 slips past Dec 15, the waiver lapses and 9 models flip to no-go during peak sports season | G4 | 2 | 3 | 6 | Partner eng lead | 5.1.0 in certification by Dec 1 | Weekly waiver check-in; pre-book QA slot for 5.1.0 | Approver decides renewal one week before expiry, in writing | Watching |
| R-05 | Because 2026 mid tier changed back-key handling, Cinder Films' ad break exits the app (DEF-4492), which may affect other ad-supported partners not yet tested | G2 | 2 | 3 | 6 | QA lead | Regression sweep by Oct 28 | Add ad-break back-key case to SDK-02 for all partners | Platform compatibility shim if more than one partner is hit | Open |
