"""G4 Performance and stability."""

from __future__ import annotations

from partner_cert import Decision, evaluate_cell


def _metrics(cold=2000, crash=99.9, extra=()):
    return [
        {"metric": "cold_start_ms", "value": cold},
        {"metric": "crash_free_pct", "value": crash},
        *extra,
    ]


def test_g4_1_cold_start_over_threshold_is_no_go(plan, models, make_app):
    """G4.1: median cold start above 3500 ms fails (major)."""
    app = make_app(measurements=_metrics(cold=3600))
    cell = evaluate_cell(app, models["mid25"], plan)
    assert cell.decision is Decision.NO_GO
    assert "cold_start_ms 3600 vs max 3500" in cell.reasons[0]


def test_g4_1_tier_specific_measurement_overrides_default(plan, models, make_app):
    """G4.1: measurements are per tier; the narrower scope wins."""
    app = make_app(
        measurements=_metrics(
            extra=[{"metric": "cold_start_ms", "value": 3900, "scope": {"tier": ["entry"]}}]
        )
    )
    assert evaluate_cell(app, models["entry24_new_fw"], plan).decision is Decision.NO_GO
    assert evaluate_cell(app, models["mid25"], plan).decision is Decision.GO


def test_g4_2_crash_free_below_floor_is_blocker(plan, models, make_app):
    """G4.2: crash-free sessions below 99.5% is a blocker."""
    app = make_app(measurements=_metrics(crash=99.4))
    cell = evaluate_cell(app, models["premium26"], plan)
    assert cell.decision is Decision.NO_GO
    assert any("PERF-02" in r for r in cell.reasons)


def test_g4_3_missing_measurement_is_not_a_pass(plan, models, make_app):
    """G4.3: no soak data means the test was not run, which blocks."""
    app = make_app(measurements=[{"metric": "cold_start_ms", "value": 2000}])
    cell = evaluate_cell(app, models["mid25"], plan)
    assert cell.decision is Decision.NO_GO
    assert any("no measurement for crash_free_pct" in r for r in cell.reasons)
