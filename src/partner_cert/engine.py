"""Certification engine: turns test evidence into per-model decisions.

Decision rules (mirrors docs/certification-playbook.md, "Decision rules"):

* A model is in scope for an app only if its model year is targeted and its SDK is
  at or above the app's minimum SDK. Out-of-scope cells are ``n/a``.
* Any failing blocker, any unwaived failing major, or missing evidence for a
  blocker or major test makes the model ``no-go``.
* Blockers are never waivable. An expired waiver counts as no waiver.
* A valid waiver turns a failure into ``waived``; any waived test makes the model
  ``conditional``.
* Minor failures are recorded as known issues and do not change the decision
  unless the policy sets ``minor_blocks``.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import date

from .loader import Dataset
from .model import (
    Decision,
    Gate,
    Recommendation,
    Severity,
    Status,
    Submission,
    TestCase,
    TestKind,
    TestPlan,
    TVModel,
    Waiver,
)
from .scope import app_matches, matches, version_lt


@dataclass(frozen=True)
class Outcome:
    test: str
    gate: str
    severity: Severity
    status: Status
    reason: str = ""
    issue_key: str = ""
    issue_title: str = ""
    waiver: Waiver | None = None


@dataclass
class Cell:
    partner: str
    model: str
    decision: Decision
    reasons: list[str] = field(default_factory=list)
    known_issues: list[str] = field(default_factory=list)
    outcomes: list[Outcome] = field(default_factory=list)
    blocking: list[Outcome] = field(default_factory=list)


@dataclass
class GateResult:
    gate: str
    name: str
    status: str  # passed | known_issues | conditional | failed | n/a
    models_failed: int = 0
    models_conditional: int = 0


@dataclass
class PartnerResult:
    id: str
    name: str
    category: str
    version: str
    recommendation: Recommendation
    rationale: list[str]
    targeted: int
    go: int
    conditional: int
    no_go: int
    gates: list[GateResult]

    @property
    def coverage(self) -> float:
        return (self.go + self.conditional) / self.targeted if self.targeted else 0.0


@dataclass
class BlockingIssue:
    key: str
    title: str
    test: str
    gate: str
    severity: Severity
    partners: set[str] = field(default_factory=set)
    models: set[str] = field(default_factory=set)
    cells: int = 0

    @property
    def reach(self) -> int:
        return len(self.models)


@dataclass
class Evaluation:
    plan: TestPlan
    as_of: date
    models: tuple[TVModel, ...]
    submissions: tuple[Submission, ...]
    cells: list[Cell]
    partners: list[PartnerResult]
    blocking_issues: list[BlockingIssue]

    def cell(self, partner: str, model: str) -> Cell:
        for c in self.cells:
            if c.partner == partner and c.model == model:
                return c
        raise KeyError((partner, model))

    def partner(self, partner_id: str) -> PartnerResult:
        for p in self.partners:
            if p.id == partner_id:
                return p
        raise KeyError(partner_id)


# Spec checks compare what the partner declared against platform limits. They run
# without device evidence, which is why they belong in the intake gate.
SpecCheck = Callable[[Submission, TVModel], str | None]


def _memory_budget(app: Submission, model: TVModel) -> str | None:
    if app.memory_mb > model.app_memory_mb:
        return (
            f"declared {app.memory_mb} MB exceeds the {model.app_memory_mb} MB app memory "
            f"limit on {model.tier} tier"
        )
    return None


def _hdr_capability(app: Submission, model: TVModel) -> str | None:
    if app.requires_hdr and not model.hdr:
        return "app requires HDR output; model has no HDR pipeline"
    return None


SPEC_CHECKS: dict[str, SpecCheck] = {
    "memory_budget": _memory_budget,
    "hdr_capability": _hdr_capability,
}


def eligibility(app: Submission, model: TVModel) -> str | None:
    """Return why the model is out of scope for this app, or None if in scope."""
    if app.target_years and model.model_year not in app.target_years:
        return f"model year {model.model_year} not targeted"
    if version_lt(model.sdk, app.min_sdk):
        return f"SDK {model.sdk} below app minimum {app.min_sdk}"
    return None


def _applies(test: TestCase, app: Submission, model: TVModel) -> bool:
    cond = test.applies_if
    return matches(cond.get("model"), model) and app_matches(cond.get("app"), app)


def _find_waiver(app: Submission, test: TestCase, model: TVModel, defect: str | None):
    for w in app.waivers:
        if w.test != test.id or not matches(w.scope, model):
            continue
        if w.defect and defect and w.defect != defect:
            continue
        return w
    return None


def _raw_outcomes(test: TestCase, app: Submission, model: TVModel) -> list[Outcome]:
    """Evaluate one test before waivers are considered."""
    base = {"test": test.id, "gate": test.gate, "severity": test.severity}
    if not _applies(test, app, model):
        return [Outcome(status=Status.NOT_APPLICABLE, **base)]

    if test.id in app.evidence_missing and test.kind is not TestKind.SPEC:
        return [
            Outcome(
                status=Status.NOT_RUN,
                reason=f"{test.id} no evidence submitted ({test.evidence or 'required'})",
                issue_key=f"{test.id}/no-evidence",
                issue_title=f"Missing evidence: {test.title}",
                **base,
            )
        ]

    if test.kind is TestKind.RESULT:
        hits = [f for f in app.findings if f.test == test.id and matches(f.scope, model)]
        if not hits:
            return [Outcome(status=Status.PASS, **base)]
        return [
            Outcome(
                status=Status.FAIL,
                reason=f"{test.id} {f.defect}: {f.title}",
                issue_key=f.defect,
                issue_title=f.title,
                **base,
            )
            for f in hits
        ]

    if test.kind is TestKind.METRIC:
        value = None
        for m in app.measurements:  # later, narrower entries override earlier ones
            if m.metric == test.metric and matches(m.scope, model):
                value = m.value
        if value is None:
            return [
                Outcome(
                    status=Status.NOT_RUN,
                    reason=f"{test.id} no measurement for {test.metric}",
                    issue_key=f"{test.id}/no-evidence",
                    issue_title=f"Missing measurement: {test.title}",
                    **base,
                )
            ]
        too_high = test.max is not None and value > test.max
        too_low = test.min is not None and value < test.min
        if too_high or too_low:
            bound = f"max {test.max:g}" if too_high else f"min {test.min:g}"
            return [
                Outcome(
                    status=Status.FAIL,
                    reason=f"{test.id} {test.metric} {value:g} vs {bound}",
                    issue_key=f"{test.id}/{model.tier}",
                    issue_title=f"{test.title} out of threshold on {model.tier} tier",
                    **base,
                )
            ]
        return [Outcome(status=Status.PASS, **base)]

    if test.kind is TestKind.SPEC:
        check = SPEC_CHECKS.get(test.check or "")
        if check is None:
            raise ValueError(f"unknown spec check {test.check!r} in {test.id}")
        problem = check(app, model)
        if problem:
            return [
                Outcome(
                    status=Status.FAIL,
                    reason=f"{test.id} {problem}",
                    issue_key=f"{test.id}/{app.id}/{model.tier}",
                    issue_title=f"{test.title}: {app.name} on {model.tier} tier",
                    **base,
                )
            ]
        return [Outcome(status=Status.PASS, **base)]

    # SIGNOFF
    missing = [r for r in test.roles if not app.signoffs.get(r)]
    if missing:
        return [
            Outcome(
                status=Status.FAIL,
                reason=f"{test.id} missing sign-off: {', '.join(missing)}",
                issue_key=f"{test.id}/{app.id}",
                issue_title=f"Sign-off outstanding ({', '.join(missing)}) for {app.name}",
                **base,
            )
        ]
    return [Outcome(status=Status.PASS, **base)]


def _apply_waiver(
    outcome: Outcome, test: TestCase, app: Submission, model: TVModel, plan: TestPlan, as_of: date
) -> Outcome:
    if outcome.status is not Status.FAIL:
        return outcome
    defect = outcome.issue_key if test.kind is TestKind.RESULT else None
    waiver = _find_waiver(app, test, model, defect)
    if waiver is None:
        return outcome
    if test.severity not in plan.policy.waivable:
        note = f" (waiver rejected: {test.severity} is not waivable)"
        return replace(outcome, reason=outcome.reason + note)
    if waiver.expires < as_of:
        note = f" (waiver expired {waiver.expires.isoformat()})"
        return replace(outcome, reason=outcome.reason + note)
    note = f" (waived by {waiver.approved_by} until {waiver.expires.isoformat()})"
    return replace(outcome, status=Status.WAIVED, reason=outcome.reason + note, waiver=waiver)


def _is_blocking(o: Outcome, plan: TestPlan) -> bool:
    if o.status is Status.FAIL:
        return o.severity is not Severity.MINOR or plan.policy.minor_blocks
    if o.status is Status.NOT_RUN:
        return o.severity is not Severity.MINOR
    return False


def evaluate_cell(
    app: Submission, model: TVModel, plan: TestPlan, as_of: date | None = None
) -> Cell:
    as_of = as_of or plan.as_of
    why_not = eligibility(app, model)
    if why_not:
        return Cell(app.id, model.id, Decision.NOT_APPLICABLE, reasons=[why_not])

    outcomes: list[Outcome] = []
    for test in plan.tests:
        for raw in _raw_outcomes(test, app, model):
            outcomes.append(_apply_waiver(raw, test, app, model, plan, as_of))

    blocking = [o for o in outcomes if _is_blocking(o, plan)]
    waived = [o for o in outcomes if o.status is Status.WAIVED]
    known = [
        o.reason for o in outcomes if o.status is Status.FAIL and not any(o is b for b in blocking)
    ]

    if blocking:
        decision, reasons = Decision.NO_GO, [o.reason for o in blocking]
    elif waived:
        decision, reasons = Decision.CONDITIONAL, [o.reason for o in waived]
    else:
        decision, reasons = Decision.GO, []
    return Cell(app.id, model.id, decision, reasons, known, outcomes, blocking)


def _gate_results(cells: list[Cell], gates: tuple[Gate, ...]) -> list[GateResult]:
    results = []
    for gate in gates:
        failed = conditional = known = applicable = 0
        for c in cells:
            outs = [o for o in c.outcomes if o.gate == gate.id]
            if any(o.status is not Status.NOT_APPLICABLE for o in outs):
                applicable += 1
            if any(o is b for o in outs for b in c.blocking):
                failed += 1
            elif any(o.status is Status.WAIVED for o in outs):
                conditional += 1
            elif any(o.status is Status.FAIL for o in outs):
                known += 1
        if not applicable:
            status = "n/a"
        elif failed:
            status = "failed"
        elif conditional:
            status = "conditional"
        elif known:
            status = "known_issues"
        else:
            status = "passed"
        results.append(GateResult(gate.id, gate.name, status, failed, conditional))
    return results


def _recommend(
    app: Submission, cells: list[Cell], gates: list[GateResult], plan: TestPlan
) -> tuple[Recommendation, list[str]]:
    targeted = [c for c in cells if c.decision is not Decision.NOT_APPLICABLE]
    if not targeted:
        return Recommendation.NO_GO, ["no TV models in scope for this submission"]
    no_go = sum(c.decision is Decision.NO_GO for c in targeted)
    cond = sum(c.decision is Decision.CONDITIONAL for c in targeted)
    coverage = (len(targeted) - no_go) / len(targeted)
    global_fail = [g for g in gates if g.status == "failed" and plan.gate(g.gate).global_scope]
    if global_fail:
        names = ", ".join(f"{g.gate} {g.name}" for g in global_fail)
        return Recommendation.NO_GO, [f"global gate failed: {names}"]
    if no_go == 0:
        if cond:
            return Recommendation.CONDITIONAL, [
                f"all {len(targeted)} models certifiable; {cond} under time-boxed waiver"
            ]
        return Recommendation.GO, [f"all {len(targeted)} targeted models pass every gate"]
    pct = f"{coverage:.0%}"
    floor = f"{plan.policy.min_launch_coverage:.0%}"
    if coverage >= plan.policy.min_launch_coverage:
        return Recommendation.PARTIAL, [
            f"launch on {len(targeted) - no_go} of {len(targeted)} models ({pct}); "
            f"hold {no_go} until blockers clear"
        ]
    return Recommendation.NO_GO, [f"coverage {pct} is below the {floor} launch floor"]


def evaluate(dataset: Dataset, as_of: date | None = None) -> Evaluation:
    plan = dataset.plan
    as_of = as_of or plan.as_of
    severity_of = {t.id: t.severity for t in plan.tests}
    all_cells: list[Cell] = []
    partners: list[PartnerResult] = []
    issues: dict[str, BlockingIssue] = {}
    issue_cells: dict[str, int] = defaultdict(int)

    for app in dataset.submissions:
        cells = [evaluate_cell(app, m, plan, as_of) for m in dataset.models]
        all_cells.extend(cells)
        gates = _gate_results(cells, plan.gates)
        rec, rationale = _recommend(app, cells, gates, plan)
        partners.append(
            PartnerResult(
                id=app.id,
                name=app.name,
                category=app.category,
                version=app.version,
                recommendation=rec,
                rationale=rationale,
                targeted=sum(c.decision is not Decision.NOT_APPLICABLE for c in cells),
                go=sum(c.decision is Decision.GO for c in cells),
                conditional=sum(c.decision is Decision.CONDITIONAL for c in cells),
                no_go=sum(c.decision is Decision.NO_GO for c in cells),
                gates=gates,
            )
        )
        for c in cells:
            for o in c.blocking:
                issue = issues.setdefault(
                    o.issue_key,
                    BlockingIssue(o.issue_key, o.issue_title, o.test, o.gate, severity_of[o.test]),
                )
                issue.partners.add(app.id)
                issue.models.add(c.model)
                issue_cells[o.issue_key] += 1

    for key, n in issue_cells.items():
        issues[key].cells = n
    ranked = sorted(issues.values(), key=lambda i: (-i.reach, -i.cells, i.severity.rank, i.key))
    return Evaluation(plan, as_of, dataset.models, dataset.submissions, all_cells, partners, ranked)
