"""Domain types for the certification engine.

Everything here is plain data. Loading and validation live in ``loader.py``;
decision logic lives in ``engine.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    BLOCKER = "blocker"
    MAJOR = "major"
    MINOR = "minor"

    @property
    def rank(self) -> int:
        return {"blocker": 0, "major": 1, "minor": 2}[self.value]


class Status(StrEnum):
    """Outcome of one test case on one (partner app, TV model) pair."""

    PASS = "pass"
    FAIL = "fail"
    WAIVED = "waived"
    NOT_RUN = "not_run"
    NOT_APPLICABLE = "n/a"


class Decision(StrEnum):
    """Per-model certification decision."""

    GO = "go"
    CONDITIONAL = "conditional"
    NO_GO = "no-go"
    NOT_APPLICABLE = "n/a"


class Recommendation(StrEnum):
    """Per-partner launch recommendation across all targeted models."""

    GO = "go"
    CONDITIONAL = "conditional"
    PARTIAL = "partial"
    NO_GO = "no-go"


class TestKind(StrEnum):
    RESULT = "result"  # pass unless a finding is filed against it
    METRIC = "metric"  # measured value checked against a threshold
    SPEC = "spec"  # computed from the partner's declared spec vs platform limits
    SIGNOFF = "signoff"  # named roles must have signed


@dataclass(frozen=True)
class TVModel:
    id: str
    series: str
    model_year: int
    tier: str
    soc: str
    firmware: str
    sdk: str
    resolution: str
    hdr: bool
    app_memory_mb: int


@dataclass(frozen=True)
class Gate:
    id: str
    name: str
    signers: tuple[str, ...]
    global_scope: bool = False  # failure anywhere blocks the whole launch


@dataclass(frozen=True)
class TestCase:
    id: str
    gate: str
    title: str
    severity: Severity
    kind: TestKind = TestKind.RESULT
    evidence: str = ""
    applies_if: dict[str, Any] = field(default_factory=dict)
    metric: str | None = None
    max: float | None = None
    min: float | None = None
    check: str | None = None
    roles: tuple[str, ...] = ()


@dataclass(frozen=True)
class Policy:
    min_launch_coverage: float = 0.75
    minor_blocks: bool = False
    waivable: tuple[Severity, ...] = (Severity.MAJOR, Severity.MINOR)


@dataclass(frozen=True)
class TestPlan:
    name: str
    as_of: date
    gates: tuple[Gate, ...]
    tests: tuple[TestCase, ...]
    policy: Policy = field(default_factory=Policy)

    def gate(self, gate_id: str) -> Gate:
        for g in self.gates:
            if g.id == gate_id:
                return g
        raise KeyError(gate_id)


@dataclass(frozen=True)
class Finding:
    test: str
    defect: str
    title: str
    scope: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Measurement:
    metric: str
    value: float
    scope: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Waiver:
    test: str
    approved_by: str
    expires: date
    mitigation: str
    scope: dict[str, Any] = field(default_factory=dict)
    defect: str | None = None


@dataclass(frozen=True)
class Submission:
    id: str
    name: str
    category: str
    version: str
    min_sdk: str
    memory_mb: int
    has_payments: bool = False
    requires_hdr: bool = False
    target_years: tuple[int, ...] = ()
    evidence_missing: tuple[str, ...] = ()
    findings: tuple[Finding, ...] = ()
    measurements: tuple[Measurement, ...] = ()
    waivers: tuple[Waiver, ...] = ()
    signoffs: dict[str, bool] = field(default_factory=dict)
