"""G1 Intake and spec review. Criteria ids refer to docs/certification-playbook.md."""

from __future__ import annotations

import pytest

from partner_cert import Decision, evaluate_cell
from partner_cert.engine import eligibility
from partner_cert.loader import DataError, parse_submission


def test_g1_1_memory_over_platform_limit_is_no_go(plan, models, make_app):
    """G1.1: declared footprint above the model's app memory limit fails intake."""
    app = make_app(memory_mb=450)
    cell = evaluate_cell(app, models["entry24_new_fw"], plan)
    assert cell.decision is Decision.NO_GO
    assert any("exceeds the 384 MB app memory limit" in r for r in cell.reasons)
    # Same app fits the mid tier limit.
    assert evaluate_cell(app, models["mid25"], plan).decision is Decision.GO


def test_g1_1_memory_failure_cannot_be_waived(plan, models, make_app):
    """G1.1: platform limits are blockers; a waiver on INT-01 is rejected."""
    app = make_app(
        memory_mb=450,
        waivers=[
            {
                "test": "INT-01",
                "approved_by": "VP",
                "expires": "2027-01-01",
                "mitigation": "trust us",
            }
        ],
    )
    cell = evaluate_cell(app, models["entry24_new_fw"], plan)
    assert cell.decision is Decision.NO_GO
    assert any("waiver rejected" in r for r in cell.reasons)


def test_g1_2_hdr_requirement_on_non_hdr_model(plan, models, make_app):
    """G1.2: an app that requires HDR cannot certify on a model without HDR output."""
    app = make_app(requires_hdr=True)
    cell = evaluate_cell(app, models["entry24"], plan)
    assert cell.decision is Decision.NO_GO
    assert any("INT-02" in r for r in cell.reasons)
    assert evaluate_cell(app, models["mid25"], plan).decision is Decision.GO


def test_g1_3_below_min_sdk_is_out_of_scope_not_failed(plan, models, make_app):
    """G1.3: models below the declared minimum SDK are excluded, not counted as failures."""
    app = make_app(min_sdk="7.0")
    cell = evaluate_cell(app, models["entry24"], plan)
    assert cell.decision is Decision.NOT_APPLICABLE
    assert "below app minimum 7.0" in cell.reasons[0]


def test_g1_3_untargeted_model_year_is_out_of_scope(models, make_app):
    """G1.3: the partner declares target model years; others are out of scope."""
    app = make_app(targets={"model_years": [2026]})
    assert eligibility(app, models["mid25"]) == "model year 2025 not targeted"
    assert eligibility(app, models["premium26"]) is None


@pytest.mark.parametrize(
    "override, message",
    [
        ({"findings": [{"test": "NOPE-1", "defect": "D1", "title": "x"}]}, "unknown test"),
        (
            {
                "findings": [
                    {"test": "PB-01", "defect": "D1", "title": "x", "scope": {"chipset": ["K2"]}}
                ]
            },
            "unknown scope key",
        ),
        ({"evidence_missing": ["NOPE-2"]}, "unknown test"),
    ],
)
def test_g1_4_malformed_submission_is_rejected(plan, override, message):
    """G1.4: a submission that references unknown tests or scope keys fails loudly."""
    from tests.conftest import GOOD_APP

    with pytest.raises(DataError, match=message):
        parse_submission({**GOOD_APP, **override}, {t.id for t in plan.tests})
