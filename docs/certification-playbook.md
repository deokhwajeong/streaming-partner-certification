# Partner App Certification Playbook

How a third-party streaming app earns the right to ship on the platform, model by model. This is the operating contract between the platform program office, engineering, QA, legal, payments, and the partner. The engine in `src/partner_cert` implements the decision rules below; the tests in `tests/` are named after the exit criteria.

## Principles

1. **The decision is per model, not per app.** A TV matrix spans model years, SoCs, firmware trains, and SDK versions. "Certified" means certified on a named list of models.
2. **No evidence, no pass.** A test without a record is a failed test. QA does not certify from memory or a partner's assurance.
3. **Platform limits are not negotiable at the gate.** Memory, codec, and DRM ceilings are settled at intake (see `spec-negotiation-guide.md`). By G4 it is too late to argue about them.
4. **Waivers are time-boxed debt.** Every waiver has an owner, an expiry, and a mitigation. Blockers are never waived.
5. **Say the date out loud.** Every gate has a scheduled review and a named signer. Slips are announced at the review, not discovered after it.

## Roles

| Role | Accountable for | Signs |
|---|---|---|
| Program TPM (chair) | Operating rhythm, readiness review, final go/no-go call | G5 |
| Partner TPM | Partner relationship, intake package, spec negotiation | G1 |
| Platform architect | Platform limits and SDK roadmap | G1 |
| QA lead | Test execution, evidence integrity, defect triage | G2, G4 |
| Platform engineering | SDK and firmware fixes, API guidance | G2 |
| Payments lead | Purchase, restore, refund, subscription flows | G3 |
| Legal | Terms, privacy notices, regional and child-safety requirements | G3 |
| Partner engineering lead | Fixes, evidence, measurements, commitments on waivers | G5 (partner sign-off) |

## Gates

| Gate | Purpose | Entry criteria | Exit criteria (ids used by tests) | Evidence | Signers | Scope |
|---|---|---|---|---|---|---|
| **G1 Intake and spec review** | Catch platform-limit conflicts before any testing money is spent | Partner agreement executed; intake form with target model years, min SDK, declared resource footprint | **G1.1** declared memory within the app limit on every targeted model (blocker, never waivable). **G1.2** declared output requirements (HDR) supported by the model. **G1.3** scope declared; models below min SDK or outside target years are out of scope, not failures. **G1.4** submission data validates (no unknown tests or scope keys). | Spec sheet; resource profile; scope declaration | Partner TPM, platform architect | Per model |
| **G2 Platform compatibility** | Prove the app behaves on real firmware | G1 passed; build on certification channel; test accounts provisioned | **G2.1** no private or deprecated APIs (blocker). **G2.2** lifecycle: launch, suspend, resume, back, exit (major). **G2.3** playback start, seek, DRM license acquisition and renewal (blocker); defects scoped to the affected firmware or SoC. **G2.4** HDR signaling only on 2160p models for HDR apps. **G2.5** minor UX issues ship as known issues unless policy tightens. | API scan; lifecycle log; playback and DRM logs incl. 90 min renewal soak | QA lead, platform eng | Per model |
| **G3 Commerce and legal** | Protect users and the platform's legal position | G2 in progress (can run in parallel) | **G3.1** purchase, restore, refund (if the app sells). **G3.2** terms and privacy notice current in every launch region. **G3.3** parental gate for kids apps. **G3.4** global gate: a failure on any model blocks the whole launch. | Payments sandbox transcript; legal review record; parental gate record | Payments lead, legal | Global |
| **G4 Performance and stability** | Make sure the app is good enough on the weakest model | G2 functionally complete | **G4.1** median cold start at most 3500 ms per tier (major, waivable). **G4.2** crash-free sessions at least 99.5% over 24 h soak (blocker). **G4.3** a missing measurement is a not-run, which blocks. | 20 cold starts per tier; soak report per model year | QA lead | Per model |
| **G5 Launch readiness** | One decision, one record | G1 to G4 closed or under valid waiver | **G5.1** engineering, QA, legal, partner sign-offs recorded. **G5.2** waivers valid (owner, expiry, mitigation; expired waiver counts as none; blockers never waived). **G5.3** partner recommendation computed (below). **G5.4** blocking issues ranked by model reach with owners and dates. | Readiness review minutes; report from `partner-cert evaluate` | Program TPM | Global |

## Decision rules

Per model:

| Condition | Decision |
|---|---|
| Model year not targeted, or model SDK below app minimum | `n/a` (out of scope) |
| Any blocker failing; any major failing without a valid waiver; any blocker or major without evidence | `no-go` |
| No blocking failures, at least one valid waiver | `conditional` |
| Otherwise (minor failures recorded as known issues) | `go` |

Per partner:

| Condition | Recommendation | What happens |
|---|---|---|
| A global gate (G3, G5) failed on any model | **NO-GO** | Nothing ships. Fix and re-enter at the failed gate. |
| Every targeted model `go` | **GO** | Ship on the full list. |
| No `no-go`, some `conditional` | **CONDITIONAL** | Ship; waiver owners report at each weekly sync until closed. |
| Some `no-go`, coverage at or above 75% | **PARTIAL** | Ship on certified models; hold the rest with a dated fix plan. |
| Coverage below 75% | **NO-GO** | A launch that skips a quarter of the fleet creates more support load and partner friction than it saves. |

The 75% floor is a policy value in `test_plan.yaml`. Tighten it for flagship partners or a hero launch; never loosen it during a review to make a date.

## Operating rhythm

| Cadence | Forum | Attendees | Output |
|---|---|---|---|
| Daily (during G2 to G4) | Defect triage, 20 min | QA lead, platform eng, partner eng | Severity confirmed, owner and date per defect |
| Weekly | Partner sync | Partner TPM, partner leads, QA lead | Evidence status, risk register delta, waiver check-ins |
| Weekly | Program review | Program TPM, all functional leads | Gate status per partner, top blockers by reach, escalations |
| Per release train | Launch readiness review | Signers of all gates | Go / conditional / partial / no-go, recorded in minutes |
| After launch or slip | Postmortem | Anyone involved | Actions with owners (see `postmortem-template.md`) |

## Re-entry

A fix re-enters at the earliest gate it touches. A new build re-runs G2 and G4 on every in-scope model; G1 re-runs only if the declared footprint or scope changed. Firmware or SDK changes on the platform side trigger the revalidation plan in `migration-revalidation-plan.md`.
