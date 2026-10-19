"""G3 Commerce and legal. A global gate: failure anywhere blocks the launch."""

from __future__ import annotations

from partner_cert import Decision, Recommendation, Status, evaluate, evaluate_cell


def test_g3_1_payments_test_skipped_for_apps_without_purchases(plan, models, make_app):
    """G3.1: PAY-01 applies only when the app sells something."""
    app = make_app(has_payments=False)
    out = next(o for o in evaluate_cell(app, models["mid25"], plan).outcomes if o.test == "PAY-01")
    assert out.status is Status.NOT_APPLICABLE


def test_g3_1_payment_flow_failure_is_no_go(plan, models, make_app):
    """G3.1: a broken purchase or restore flow is a blocker."""
    app = make_app(findings=[{"test": "PAY-01", "defect": "DEF-7", "title": "restore fails"}])
    assert evaluate_cell(app, models["mid25"], plan).decision is Decision.NO_GO


def test_g3_3_kids_app_without_parental_gate_evidence_is_no_go(plan, models, make_app):
    """G3.3: missing evidence is not a pass. No record, no certification."""
    app = make_app(category="kids", evidence_missing=["LGL-02"])
    cell = evaluate_cell(app, models["mid25"], plan)
    assert cell.decision is Decision.NO_GO
    assert any("no evidence submitted" in r for r in cell.reasons)


def test_g3_4_scoped_legal_failure_still_blocks_whole_launch(dataset_of, make_app):
    """G3.4: G3 is global. Even one failing model makes the partner NO-GO."""
    app = make_app(
        findings=[
            {
                "test": "LGL-01",
                "defect": "DEF-8",
                "title": "stale notice",
                "scope": {"model_year": [2026]},
            }
        ]
    )
    ev = evaluate(dataset_of(app))
    p = ev.partner("test-app")
    assert p.no_go == 1 and p.coverage == 0.75
    assert p.recommendation is Recommendation.NO_GO
    assert "global gate failed" in p.rationale[0]
