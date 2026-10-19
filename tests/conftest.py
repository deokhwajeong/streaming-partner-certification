"""Shared fixtures.

Unit tests use the real example test plan (it is the plan the playbook documents)
plus a handful of hand-built models, so each test controls exactly one variable.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
import yaml

from partner_cert.loader import Dataset, load_dataset, parse_plan, parse_submission
from partner_cert.model import Submission, TestPlan, TVModel

DATA = Path(__file__).resolve().parents[1] / "examples" / "data"


def _model(id: str, **kw: Any) -> TVModel:
    base = dict(
        series="Test",
        model_year=2025,
        tier="mid",
        soc="K6",
        firmware="7.1.4",
        sdk="7.1",
        resolution="2160p",
        hdr=True,
        app_memory_mb=512,
    )
    base.update(kw)
    return TVModel(id=id, **base)


@pytest.fixture(scope="session")
def raw_plan() -> dict[str, Any]:
    return yaml.safe_load((DATA / "test_plan.yaml").read_text())


@pytest.fixture(scope="session")
def plan(raw_plan) -> TestPlan:
    return parse_plan(raw_plan)


@pytest.fixture
def models() -> dict[str, TVModel]:
    return {
        "entry24": _model(
            "T24-E",
            model_year=2024,
            tier="entry",
            soc="K2",
            firmware="6.3.8",
            sdk="6.2",
            resolution="1080p",
            hdr=False,
            app_memory_mb=384,
        ),
        "entry24_new_fw": _model(
            "T24-E2",
            model_year=2024,
            tier="entry",
            soc="K2",
            firmware="6.4.2",
            sdk="6.4",
            app_memory_mb=384,
        ),
        "mid25": _model("T25-M"),
        "premium26": _model(
            "T26-P",
            model_year=2026,
            tier="premium",
            soc="K8",
            firmware="8.0.1",
            sdk="8.0",
            app_memory_mb=1024,
        ),
    }


GOOD_APP: dict[str, Any] = {
    "id": "test-app",
    "name": "Test App",
    "category": "svod",
    "version": "1.0.0",
    "min_sdk": "6.2",
    "memory_mb": 300,
    "has_payments": True,
    "targets": {"model_years": [2024, 2025, 2026]},
    "measurements": [
        {"metric": "cold_start_ms", "value": 2000},
        {"metric": "crash_free_pct", "value": 99.9},
    ],
    "signoffs": {"engineering": True, "qa": True, "legal": True, "partner": True},
}


@pytest.fixture
def make_app(plan):
    """Build a Submission from GOOD_APP with overrides applied."""
    test_ids = {t.id for t in plan.tests}

    def _make(**overrides: Any) -> Submission:
        raw = {**GOOD_APP, **overrides}
        return parse_submission(raw, test_ids)

    return _make


@pytest.fixture
def dataset_of(plan, models):
    def _ds(*apps: Submission, model_list: list[TVModel] | None = None, **policy) -> Dataset:
        p = replace(plan, policy=replace(plan.policy, **policy)) if policy else plan
        return Dataset(models=tuple(model_list or models.values()), submissions=apps, plan=p)

    return _ds


@pytest.fixture(scope="session")
def example() -> Dataset:
    return load_dataset(DATA)
