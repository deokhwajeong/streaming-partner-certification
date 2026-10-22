"""G2 Platform compatibility."""

from __future__ import annotations

from partner_cert import Decision, Status, evaluate_cell


def _finding(test, defect="DEF-1", scope=None):
    f = {"test": test, "defect": defect, "title": f"{test} broke"}
    if scope:
        f["scope"] = scope
    return f


def test_g2_1_private_api_use_is_blocker(plan, models, make_app):
    """G2.1: private or deprecated API use fails every model it is found on."""
    app = make_app(findings=[_finding("SDK-01")])
    for m in models.values():
        assert evaluate_cell(app, m, plan).decision is Decision.NO_GO


def test_g2_2_unwaived_major_lifecycle_failure_is_no_go(plan, models, make_app):
    """G2.2: a major failure without a waiver blocks the model."""
    app = make_app(findings=[_finding("SDK-02")])
    assert evaluate_cell(app, models["mid25"], plan).decision is Decision.NO_GO


def test_g2_3_drm_defect_scoped_to_firmware_only_hits_those_models(plan, models, make_app):
    """G2.3: findings are scoped; only models on the affected firmware fail."""
    app = make_app(findings=[_finding("PB-02", scope={"soc": ["S1"], "firmware_lt": "6.4"})])
    assert evaluate_cell(app, models["entry24"], plan).decision is Decision.NO_GO
    assert evaluate_cell(app, models["entry24_new_fw"], plan).decision is Decision.GO
    assert evaluate_cell(app, models["mid25"], plan).decision is Decision.GO


def test_g2_4_hdr_conformance_only_applies_to_4k_hdr_apps(plan, models, make_app):
    """G2.4: PB-03 is n/a unless the app requires HDR and the model is 2160p."""
    sdr = make_app(findings=[_finding("PB-03")])
    outcome = next(
        o for o in evaluate_cell(sdr, models["mid25"], plan).outcomes if o.test == "PB-03"
    )
    assert outcome.status is Status.NOT_APPLICABLE
    hdr = make_app(requires_hdr=True, findings=[_finding("PB-03")])
    assert evaluate_cell(hdr, models["mid25"], plan).decision is Decision.NO_GO


def test_g2_5_minor_ux_issue_ships_as_known_issue(plan, models, make_app):
    """G2.5: minor failures do not change the decision; they are recorded."""
    app = make_app(findings=[_finding("UX-01", defect="DEF-9")])
    cell = evaluate_cell(app, models["mid25"], plan)
    assert cell.decision is Decision.GO
    assert cell.known_issues and "DEF-9" in cell.known_issues[0]


def test_g2_5_policy_can_make_minor_issues_blocking(dataset_of, models, make_app):
    """G2.5: programs late in a cycle can tighten policy so minors block."""
    from partner_cert import evaluate

    app = make_app(findings=[_finding("UX-01")])
    ev = evaluate(dataset_of(app, model_list=[models["mid25"]], minor_blocks=True))
    assert ev.cell("test-app", "T25-M").decision is Decision.NO_GO
