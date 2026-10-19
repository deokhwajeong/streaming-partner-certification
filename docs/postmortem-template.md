# Postmortem: Template

Blameless, written within 5 business days of a launch slip, a launch-week incident, or a certification escape (a defect that passed the gates and reached users). The goal is a gate that would have caught it next time.

**Title:** ______ **Date:** ______ **Author:** ______ **Reviewers:** ______

## 1. Summary

Three sentences: what happened, who was affected (partners, models, users), and what changed as a result.

## 2. Impact

| Dimension | Value |
|---|---|
| Partners affected | |
| Models affected (count) | |
| Duration (detect to mitigate) | |
| User-facing symptom | |
| Launch date impact | |
| Contract or partner relationship impact | |

## 3. Timeline

| Time | Event | Source |
|---|---|---|
| | First signal | |
| | Detected by us | |
| | Escalated (level) | |
| | Mitigated | |
| | Resolved | |

## 4. Gate analysis

The core question: which gate should have caught this, and why did it not?

| Gate | Should it have caught this? | What it checked | Why it missed |
|---|---|---|---|
| G1 Intake | | | |
| G2 Compatibility | | | |
| G3 Commerce and legal | | | |
| G4 Performance | | | |
| G5 Readiness | | | |

Common answers: test not in plan; test in plan but not applied to this model scope; evidence accepted without the full matrix; waiver hid a related defect; measurement taken on the wrong tier.

## 5. Contributing factors

| Factor | Category (process, tooling, spec, communication, capacity) |
|---|---|
| | |

## 6. Actions

| ID | Action | Type (prevent, detect, mitigate) | Owner | Due | Tracking |
|---|---|---|---|---|---|
| A-1 | | | | | |

Every "prevent" action should land as a change to `test_plan.yaml` (new test, wider `applies_if`, tighter threshold) or to the playbook. Actions without an owner and a date are not accepted.

## 7. What went well

Keep it. It tells the next program what to protect.
