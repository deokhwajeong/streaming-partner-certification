"""Scope matching: which TV models a finding, waiver, measurement, or test applies to.

A scope is a small dict. An empty scope matches every model. All keys must match.

    {"tier": ["entry"], "soc": ["K2"], "firmware_lt": "6.4"}
"""

from __future__ import annotations

from typing import Any

from .model import Submission, TVModel

LIST_KEYS = {
    "models": "id",
    "model_year": "model_year",
    "tier": "tier",
    "soc": "soc",
    "resolution": "resolution",
    "series": "series",
}
VERSION_KEYS = {"sdk_lt", "sdk_gte", "firmware_lt", "firmware_gte"}
SCOPE_KEYS = frozenset(LIST_KEYS) | VERSION_KEYS
APP_KEYS = frozenset({"category", "requires_hdr", "has_payments"})


def parse_version(text: str | int | float) -> tuple[int, ...]:
    """'6.4.1' -> (6, 4, 1). Missing parts compare as zero."""
    parts = [int(p) for p in str(text).strip().split(".") if p != ""]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


def version_lt(a: str, b: str) -> bool:
    return parse_version(a) < parse_version(b)


def validate_scope(scope: dict[str, Any], where: str) -> None:
    unknown = set(scope) - SCOPE_KEYS
    if unknown:
        raise ValueError(f"{where}: unknown scope key(s) {sorted(unknown)}")


def matches(scope: dict[str, Any] | None, model: TVModel) -> bool:
    if not scope:
        return True
    for key, expected in scope.items():
        if key in LIST_KEYS:
            allowed = expected if isinstance(expected, list) else [expected]
            if getattr(model, LIST_KEYS[key]) not in allowed:
                return False
        elif key in VERSION_KEYS:
            attr, op = key.split("_")
            actual = getattr(model, attr)
            below = version_lt(actual, str(expected))
            if (op == "lt" and not below) or (op == "gte" and below):
                return False
        else:
            raise ValueError(f"unknown scope key {key!r}")
    return True


def app_matches(conditions: dict[str, Any] | None, app: Submission) -> bool:
    if not conditions:
        return True
    for key, expected in conditions.items():
        actual = getattr(app, key)
        if isinstance(expected, list):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return True
