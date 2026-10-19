# OS and SDK Migration Revalidation Plan

When the platform moves to a new OS generation or SDK major version, every partner app that ran on the old stack must re-pass certification on the new one. No grandfathering: a certificate is for an app version on a platform version, and the platform version just changed.

## Scope

| Item | Rule |
|---|---|
| Apps in scope | Every app live on any model that will receive the new OS or SDK |
| Models in scope | Every model on the new stack, plus old-stack models that receive the compatibility layer |
| Gates re-run | G1 (limits may change), G2, G4, G5. G3 re-runs if the payments or account APIs changed |
| Evidence reuse | None for G2 and G4. Prior evidence is reference only |
| Exit | Every in-scope app certified on the new stack, or formally delisted on it with partner agreement |

## Phases

| Phase | Weeks (indicative) | Platform side | Partner side | Exit criteria |
|---|---|---|---|---|
| 0. Announce | T-26 | Publish migration guide, API diff, deprecations, new limits, dates | Acknowledge, name a migration owner | 100% of partners acknowledged in writing |
| 1. Impact assessment | T-24 to T-20 | Static API scan of every live app against the new SDK | Review scan, estimate effort | Each app rated: no change, minor, major, rewrite |
| 2. Early access | T-20 to T-12 | Developer firmware and SDK on reference boards; office hours twice weekly | Port and self-test | Partner build boots and plays on new stack |
| 3. Certification wave 1 | T-12 to T-8 | Certify top apps by active usage first | Submit with full evidence | Top apps (covering most usage hours) certified |
| 4. Certification wave 2 | T-8 to T-4 | Remaining apps | Submit | All apps certified, waived, or delist agreed |
| 5. Staged rollout | T-4 to T | OTA in rings: internal, 1%, 10%, 50%, 100% with hold points | On call for launch issues | Crash and start-failure rates at or below the old stack at each ring |
| 6. Close out | T+4 | Retire compatibility shims on schedule | Remove old code paths | Revalidation report published |

## Tracking

Track the migration as a matrix: apps x model groups on the new stack. Each cell is one of: not started, in test, certified, conditional, blocked, delisted. The engine models the same shape: add the new firmware and SDK rows to `models.yaml`, re-run `partner-cert evaluate`, and the report shows which apps have not re-passed.

| Metric | Target | Reviewed |
|---|---|---|
| Apps acknowledged | 100% by T-24 | Weekly |
| Apps with scan rating | 100% by T-20 | Weekly |
| Usage hours covered by certified apps | 95% by T-8 | Weekly |
| Apps certified or with agreed outcome | 100% by T-4 | Weekly, then daily from T-4 |
| Rollout ring health | No regression vs old stack | Per ring |

## Risks specific to migrations

| Risk | Mitigation |
|---|---|
| A top partner cannot staff the port | Engage at T-26 with their executive sponsor; platform engineering offers embedded support for top apps |
| Deprecated API with no replacement | Compatibility shim with a published removal date; never an indefinite shim |
| Old-stack models stranded mid-migration (mixed firmware in the field) | Certify against both trains until OTA reaches the agreed threshold; findings scoped by `firmware_lt` |
| Partner ships a new feature during the port | Feature freeze on the migration build; features land after certification |
| Rollout ring shows regression in one app | Hold the ring, not the platform; app-level pin to the last good version |
