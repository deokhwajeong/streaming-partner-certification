"""G5 Launch readiness: sign-off, waivers, partner recommendation, blocker ranking."""

from __future__ import annotations

from datetime import date

from partner_cert import Decision, Recommendation, evaluate, evaluate_cell

ENTRY_SLOW = [
    {"metric": "cold_start_ms", "value": 2000},
    {"metric": "cold_start_ms", "value": 3900, "scope": {"tier": ["entry"]}},
    {"metric": "crash_free_pct", "value": 99.9},
]
WAIVER = {
    "test": "PERF-01",
    "scope": {"tier": ["entry"]},
    "approved_by": "Director, Partner Engineering",
    "expires": "2026-12-15",
    "mitigation": "fix in next release",
}


def test_g5_1_missing_signoff_blocks_launch(dataset_of, make_app):
    """G5.1: all four roles must sign; one missing role is NO-GO for the partner."""
    app = make_app(signoffs={"engineering": True, "qa": True, "legal": False, "partner": True})
    p = evaluate(dataset_of(app)).partner("test-app")
    assert p.recommendation is Recommendation.NO_GO
    assert any(g.gate == "G5" and g.status == "failed" for g in p.gates)


def test_g5_2_valid_waiver_makes_model_conditional(plan, models, make_app):
    """G5.2: a waiver with owner, expiry, and mitigation turns a major failure conditional."""
    app = make_app(measurements=ENTRY_SLOW, waivers=[WAIVER])
    cell = evaluate_cell(app, models["entry24_new_fw"], plan)
    assert cell.decision is Decision.CONDITIONAL
    assert "waived by Director, Partner Engineering until 2026-12-15" in cell.reasons[0]


def test_g5_2_expired_waiver_counts_as_no_waiver(plan, models, make_app):
    """G5.2: expired waivers do not carry over silently."""
    app = make_app(measurements=ENTRY_SLOW, waivers=[{**WAIVER, "expires": "2026-09-30"}])
    cell = evaluate_cell(app, models["entry24_new_fw"], plan, as_of=date(2026, 10, 19))
    assert cell.decision is Decision.NO_GO
    assert "waiver expired 2026-09-30" in cell.reasons[0]


def test_g5_2_waiver_for_one_defect_does_not_cover_another(plan, models, make_app):
    """G5.2: waivers are specific; a waiver naming DEF-1 does not hide DEF-2."""
    app = make_app(
        findings=[{"test": "SDK-02", "defect": "DEF-2", "title": "back key"}],
        waivers=[
            {
                "test": "SDK-02",
                "defect": "DEF-1",
                "approved_by": "Dir",
                "expires": "2027-01-01",
                "mitigation": "m",
            }
        ],
    )
    assert evaluate_cell(app, models["mid25"], plan).decision is Decision.NO_GO


def test_g5_3_recommendation_go_when_everything_passes(dataset_of, make_app):
    """G5.3: GO requires every targeted model to pass every gate."""
    p = evaluate(dataset_of(make_app())).partner("test-app")
    assert p.recommendation is Recommendation.GO and p.go == p.targeted == 4


def test_g5_3_recommendation_conditional_with_waivers(dataset_of, make_app):
    """G5.3: no no-go models but at least one waiver means CONDITIONAL."""
    app = make_app(measurements=ENTRY_SLOW, waivers=[WAIVER])
    p = evaluate(dataset_of(app)).partner("test-app")
    assert p.recommendation is Recommendation.CONDITIONAL
    assert (p.go, p.conditional) == (2, 2)


def test_g5_3_partial_launch_above_coverage_floor(dataset_of, make_app):
    """G5.3: some no-go models but coverage at or above the floor means PARTIAL."""
    app = make_app(
        findings=[
            {"test": "PB-02", "defect": "DEF-3", "title": "drm", "scope": {"firmware_lt": "6.4"}}
        ]
    )
    p = evaluate(dataset_of(app)).partner("test-app")
    assert p.recommendation is Recommendation.PARTIAL
    assert p.coverage == 0.75


def test_g5_3_no_go_below_coverage_floor(dataset_of, make_app):
    """G5.3: coverage below the floor means NO-GO even if some models pass."""
    app = make_app(
        findings=[
            {"test": "PB-02", "defect": "DEF-3", "title": "drm", "scope": {"model_year": [2024]}}
        ]
    )
    p = evaluate(dataset_of(app)).partner("test-app")
    assert p.coverage == 0.5
    assert p.recommendation is Recommendation.NO_GO
    assert "below the 75% launch floor" in p.rationale[0]


def test_g5_4_blocking_issues_ranked_by_model_reach(dataset_of, make_app):
    """G5.4: the issue that blocks the most models is first on the list."""
    a = make_app(
        id="a",
        findings=[
            {"test": "PB-02", "defect": "WIDE", "title": "w", "scope": {"model_year": [2024, 2025]}}
        ],
    )
    b = make_app(
        id="b",
        findings=[
            {"test": "PB-01", "defect": "NARROW", "title": "n", "scope": {"models": ["T26-P"]}}
        ],
    )
    c = make_app(
        id="c",
        findings=[
            {"test": "PB-02", "defect": "WIDE", "title": "w", "scope": {"model_year": [2025]}}
        ],
    )
    ev = evaluate(dataset_of(a, b, c))
    keys = [i.key for i in ev.blocking_issues]
    assert keys == ["WIDE", "NARROW"]
    wide = ev.blocking_issues[0]
    assert wide.reach == 3 and wide.cells == 4 and wide.partners == {"a", "c"}
