"""Load and validate the model matrix, partner submissions, and test plan from YAML.

Validation is strict on purpose: a typo in a scope key or a test id should fail the
run loudly, not silently certify a model that was never tested.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from .model import (
    Finding,
    Gate,
    Measurement,
    Policy,
    Severity,
    Submission,
    TestCase,
    TestKind,
    TestPlan,
    TVModel,
    Waiver,
)
from .scope import APP_KEYS, validate_scope


class DataError(ValueError):
    """Raised when input data is malformed or inconsistent."""


@dataclass(frozen=True)
class Dataset:
    models: tuple[TVModel, ...]
    submissions: tuple[Submission, ...]
    plan: TestPlan


def _read(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except FileNotFoundError as exc:
        raise DataError(f"missing input file: {path}") from exc


def _date(value: Any, where: str) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise DataError(f"{where}: invalid date {value!r}") from exc


def _scope(raw: dict[str, Any], where: str) -> dict[str, Any]:
    scope = dict(raw.get("scope") or {})
    try:
        validate_scope(scope, where)
    except ValueError as exc:
        raise DataError(str(exc)) from exc
    return scope


def parse_models(raw: Any) -> tuple[TVModel, ...]:
    rows = raw.get("models") if isinstance(raw, dict) else raw
    if not rows:
        raise DataError("model matrix is empty")
    models = []
    for row in rows:
        try:
            models.append(
                TVModel(
                    id=str(row["id"]),
                    series=str(row["series"]),
                    model_year=int(row["model_year"]),
                    tier=str(row["tier"]),
                    soc=str(row["soc"]),
                    firmware=str(row["firmware"]),
                    sdk=str(row["sdk"]),
                    resolution=str(row["resolution"]),
                    hdr=bool(row["hdr"]),
                    app_memory_mb=int(row["app_memory_mb"]),
                )
            )
        except KeyError as exc:
            raise DataError(f"model {row.get('id', '?')}: missing field {exc}") from exc
    ids = [m.id for m in models]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise DataError(f"duplicate model ids: {dupes}")
    return tuple(models)


def parse_plan(raw: dict[str, Any]) -> TestPlan:
    gates = tuple(
        Gate(
            id=g["id"],
            name=g["name"],
            signers=tuple(g.get("signers", ())),
            global_scope=bool(g.get("global", False)),
        )
        for g in raw["gates"]
    )
    gate_ids = {g.id for g in gates}
    tests = []
    for t in raw["tests"]:
        where = f"test {t.get('id', '?')}"
        if t["gate"] not in gate_ids:
            raise DataError(f"{where}: unknown gate {t['gate']!r}")
        applies = dict(t.get("applies_if") or {})
        unknown = set(applies) - {"model", "app"}
        if unknown:
            raise DataError(f"{where}: applies_if supports 'model' and 'app', got {unknown}")
        if "model" in applies:
            _scope({"scope": applies["model"]}, where)
        if set(applies.get("app") or {}) - APP_KEYS:
            raise DataError(f"{where}: unknown app condition(s)")
        kind = TestKind(t.get("kind", "result"))
        if kind is TestKind.METRIC and (not t.get("metric") or ("max" not in t and "min" not in t)):
            raise DataError(f"{where}: metric tests need 'metric' and 'max' or 'min'")
        if kind is TestKind.SPEC and not t.get("check"):
            raise DataError(f"{where}: spec tests need 'check'")
        if kind is TestKind.SIGNOFF and not t.get("roles"):
            raise DataError(f"{where}: signoff tests need 'roles'")
        tests.append(
            TestCase(
                id=t["id"],
                gate=t["gate"],
                title=t["title"],
                severity=Severity(t["severity"]),
                kind=kind,
                evidence=t.get("evidence", ""),
                applies_if=applies,
                metric=t.get("metric"),
                max=t.get("max"),
                min=t.get("min"),
                check=t.get("check"),
                roles=tuple(t.get("roles", ())),
            )
        )
    ids = [t.id for t in tests]
    if len(ids) != len(set(ids)):
        raise DataError("duplicate test ids in plan")
    pol = raw.get("policy") or {}
    policy = Policy(
        min_launch_coverage=float(pol.get("min_launch_coverage", 0.75)),
        minor_blocks=bool(pol.get("minor_blocks", False)),
        waivable=tuple(Severity(s) for s in pol.get("waivable", ["major", "minor"])),
    )
    if Severity.BLOCKER in policy.waivable:
        raise DataError("policy: blockers cannot be waivable")
    return TestPlan(
        name=raw.get("name", "certification plan"),
        as_of=_date(raw["as_of"], "plan.as_of"),
        gates=gates,
        tests=tuple(tests),
        policy=policy,
    )


def parse_submission(raw: dict[str, Any], test_ids: set[str]) -> Submission:
    sid = raw["id"]

    def check_test(test_id: str, where: str) -> str:
        if test_id not in test_ids:
            raise DataError(f"submission {sid}: {where} references unknown test {test_id!r}")
        return test_id

    findings = tuple(
        Finding(
            test=check_test(f["test"], "finding"),
            defect=str(f["defect"]),
            title=f["title"],
            scope=_scope(f, f"submission {sid} finding {f['defect']}"),
        )
        for f in raw.get("findings") or ()
    )
    measurements = tuple(
        Measurement(
            metric=m["metric"],
            value=float(m["value"]),
            scope=_scope(m, f"submission {sid} measurement"),
        )
        for m in raw.get("measurements") or ()
    )
    waivers = tuple(
        Waiver(
            test=check_test(w["test"], "waiver"),
            approved_by=w["approved_by"],
            expires=_date(w["expires"], f"submission {sid} waiver"),
            mitigation=w["mitigation"],
            scope=_scope(w, f"submission {sid} waiver"),
            defect=w.get("defect"),
        )
        for w in raw.get("waivers") or ()
    )
    missing = tuple(check_test(t, "evidence_missing") for t in raw.get("evidence_missing") or ())
    targets = raw.get("targets") or {}
    return Submission(
        id=sid,
        name=raw["name"],
        category=raw["category"],
        version=str(raw["version"]),
        min_sdk=str(raw["min_sdk"]),
        memory_mb=int(raw["memory_mb"]),
        has_payments=bool(raw.get("has_payments", False)),
        requires_hdr=bool(raw.get("requires_hdr", False)),
        target_years=tuple(int(y) for y in targets.get("model_years", ())),
        evidence_missing=missing,
        findings=findings,
        measurements=measurements,
        waivers=waivers,
        signoffs={str(k): bool(v) for k, v in (raw.get("signoffs") or {}).items()},
    )


def load_dataset(data_dir: str | Path) -> Dataset:
    """Load ``models.yaml``, ``test_plan.yaml`` and every file in ``submissions/``."""
    root = Path(data_dir)
    models = parse_models(_read(root / "models.yaml"))
    plan = parse_plan(_read(root / "test_plan.yaml"))
    test_ids = {t.id for t in plan.tests}
    sub_dir = root / "submissions"
    files = sorted(sub_dir.glob("*.yaml")) if sub_dir.is_dir() else []
    if not files:
        raise DataError(f"no submissions found in {sub_dir}")
    submissions = tuple(parse_submission(_read(p), test_ids) for p in files)
    ids = [s.id for s in submissions]
    if len(ids) != len(set(ids)):
        raise DataError("duplicate submission ids")
    return Dataset(models=models, submissions=submissions, plan=plan)
