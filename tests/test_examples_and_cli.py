"""End to end: the shipped example data, report formats, CLI, and loader guards."""

from __future__ import annotations

import json

import pytest

from partner_cert import evaluate
from partner_cert.cli import main
from partner_cert.loader import DataError, parse_models, parse_plan
from partner_cert.report import to_dict, to_markdown
from partner_cert.scope import parse_version, version_lt
from tests.conftest import DATA


def test_example_matrix_shape(example):
    assert len(example.models) == 40
    assert {m.model_year for m in example.models} == {2024, 2025, 2026}
    assert len(example.submissions) == 6


def test_example_recommendations_cover_every_outcome(example):
    recs = {p.id: p.recommendation.value for p in evaluate(example).partners}
    assert recs == {
        "aurora-stream": "go",
        "brightline-sports": "conditional",
        "cinder-films": "partial",
        "driftwood-kids": "no-go",
        "ember-music": "go",
        "fathom-originals": "no-go",
    }


def test_report_json_is_consistent(example):
    d = to_dict(evaluate(example))
    s = d["summary"]
    assert s["go"] + s["conditional"] + s["no_go"] == s["targeted_cells"]
    assert len(d["matrix"]) == 6 * 40
    reach = [b["reach_models"] for b in d["blocking_issues"]]
    assert reach == sorted(reach, reverse=True)
    assert d["waivers"][0]["days_left"] == 57
    json.dumps(d)  # serializable


def test_report_markdown_has_review_sections(example):
    md = to_markdown(evaluate(example))
    for heading in (
        "## Summary",
        "## Partner recommendations",
        "## Gate status",
        "## Blocking issues by reach",
        "## Active waivers",
        "## No-go detail",
    ):
        assert heading in md
    em_dash, en_dash = chr(0x2014), chr(0x2013)
    assert em_dash not in md and en_dash not in md


def test_cli_writes_reports(tmp_path, capsys):
    assert main(["evaluate", str(DATA), "--out", str(tmp_path)]) == 0
    assert (tmp_path / "report.json").exists() and (tmp_path / "report.md").exists()
    assert "Cinder Films" in capsys.readouterr().out


def test_cli_strict_mode_fails_when_any_partner_is_no_go():
    assert main(["evaluate", str(DATA), "--format", "json", "--strict"]) == 2


def test_cli_explain(capsys):
    assert main(["explain", str(DATA), "--partner", "cinder-films", "--model", "TV24-E43A"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("cinder-films x TV24-E43A: NO-GO")
    assert "DEF-4471" in out


def test_cli_reports_bad_data_dir(tmp_path, capsys):
    assert main(["evaluate", str(tmp_path)]) == 1
    assert "missing input file" in capsys.readouterr().err


def test_versions_compare_numerically():
    assert parse_version("6.10") > parse_version("6.9")
    assert parse_version("7.0.0") == parse_version("7")
    assert version_lt("6.3.8", "6.4")


def test_duplicate_model_ids_rejected():
    row = {
        "id": "X",
        "series": "s",
        "model_year": 2025,
        "tier": "mid",
        "soc": "K6",
        "firmware": "7.1",
        "sdk": "7.1",
        "resolution": "2160p",
        "hdr": True,
        "app_memory_mb": 512,
    }
    with pytest.raises(DataError, match="duplicate model ids"):
        parse_models({"models": [row, row]})


def test_plan_cannot_make_blockers_waivable(raw_plan):
    with pytest.raises(DataError, match="blockers cannot be waivable"):
        parse_plan({**raw_plan, "policy": {"waivable": ["blocker", "major"]}})
