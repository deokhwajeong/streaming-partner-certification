# Escalation Matrix

Escalation is a tool for getting a decision, not for assigning blame. Every escalation names the decision needed, the options, a recommendation, and the date after which the default happens.

## Levels

| Level | Who decides | When to use | Response time | Channel |
|---|---|---|---|---|
| L1 | Functional leads in daily triage | Severity disputes, owner assignment, test environment issues | Same day | Triage thread |
| L2 | Program TPM with affected leads | Gate at risk for one partner; waiver request on a major; cross-team dependency stuck for 3 days | 24 hours | Program review or ad hoc call |
| L3 | Director, Partner Engineering and Director, Platform | Release train date at risk; partner disputes a platform limit; waiver renewal; two or more partners blocked by one platform defect | 48 hours | Written decision memo |
| L4 | VP Platform and partner executive sponsor | Contractual launch commitment at risk; legal or privacy exposure; partner threatens to withdraw | 72 hours | Executive review |

## Triggers

| Situation | Start at | Notes |
|---|---|---|
| Blocker defect with no owner after 1 business day | L1 to L2 | Program TPM assigns |
| Platform defect blocking 2+ partners or 10+ models | L2 | Ranked by reach in the readiness report |
| Partner spec exceeds a platform limit and partner refuses to change | L3 | Bring the limit, the data, and two alternatives (see negotiation guide) |
| Waiver request on a major failure | L2 | Approver must be L3 if expiry is beyond the next train |
| Waiver renewal | L3 | Original approver; written reason |
| Request to waive a blocker | Decline at L2 | Not waivable by policy. Escalate only to change policy, never for one launch |
| Legal or privacy finding (G3) | L3 | Legal owns the call; global gate |
| Missing evidence 3 days before readiness review | L2 | Default is drop from train |
| Release train date at risk | L3 | Options memo: cut scope, slip date, add capacity |

## Escalation memo (five lines)

| Field | Content |
|---|---|
| Decision needed | One sentence, phrased as a choice |
| Options | Two or three, each with cost and impact in models and dates |
| Recommendation | Which option and why |
| Default if no decision | What happens on the deadline |
| Deadline | Date and time |
