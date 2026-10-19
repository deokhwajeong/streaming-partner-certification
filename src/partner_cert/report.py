"""Launch readiness report rendering: JSON (for dashboards) and Markdown (for the review)."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from .engine import Evaluation
from .model import Decision, Status

SCHEMA_VERSION = 1


def to_dict(ev: Evaluation, top_n: int | None = None) -> dict[str, Any]:
    decisions = Counter(c.decision for c in ev.cells if c.decision is not Decision.NOT_APPLICABLE)
    targeted = sum(decisions.values())
    certified = decisions[Decision.GO] + decisions[Decision.CONDITIONAL]
    recs = Counter(p.recommendation.value for p in ev.partners)
    issues = ev.blocking_issues[:top_n] if top_n else ev.blocking_issues

    by_key: dict[tuple, dict[str, Any]] = {}
    for c in ev.cells:
        for o in c.outcomes:
            if o.status is not Status.WAIVED or o.waiver is None:
                continue
            w = o.waiver
            entry = by_key.setdefault(
                (c.partner, o.test, w.approved_by, w.expires),
                {
                    "partner": c.partner,
                    "test": o.test,
                    "approved_by": w.approved_by,
                    "expires": w.expires.isoformat(),
                    "days_left": (w.expires - ev.as_of).days,
                    "mitigation": w.mitigation,
                    "models": 0,
                },
            )
            entry["models"] += 1
    waivers = list(by_key.values())

    return {
        "schema_version": SCHEMA_VERSION,
        "plan": ev.plan.name,
        "as_of": ev.as_of.isoformat(),
        "policy": {
            "min_launch_coverage": ev.plan.policy.min_launch_coverage,
            "minor_blocks": ev.plan.policy.minor_blocks,
            "waivable": [s.value for s in ev.plan.policy.waivable],
        },
        "summary": {
            "partners": len(ev.partners),
            "models": len(ev.models),
            "targeted_cells": targeted,
            "go": decisions[Decision.GO],
            "conditional": decisions[Decision.CONDITIONAL],
            "no_go": decisions[Decision.NO_GO],
            "certified_pct": round(100 * certified / targeted, 1) if targeted else 0.0,
            "recommendations": {
                k: recs.get(k, 0) for k in ("go", "conditional", "partial", "no-go")
            },
            "blocking_issues": len(ev.blocking_issues),
            "active_waivers": len(waivers),
        },
        "gates": [
            {"id": g.id, "name": g.name, "signers": list(g.signers), "global": g.global_scope}
            for g in ev.plan.gates
        ],
        "models": [
            {
                "id": m.id,
                "series": m.series,
                "model_year": m.model_year,
                "tier": m.tier,
                "soc": m.soc,
                "firmware": m.firmware,
                "sdk": m.sdk,
            }
            for m in ev.models
        ],
        "partners": [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "version": p.version,
                "recommendation": p.recommendation.value,
                "rationale": p.rationale,
                "targeted": p.targeted,
                "go": p.go,
                "conditional": p.conditional,
                "no_go": p.no_go,
                "coverage_pct": round(100 * p.coverage, 1),
                "gates": [
                    {
                        "gate": g.gate,
                        "name": g.name,
                        "status": g.status,
                        "models_failed": g.models_failed,
                        "models_conditional": g.models_conditional,
                    }
                    for g in p.gates
                ],
            }
            for p in ev.partners
        ],
        "matrix": [
            {
                "partner": c.partner,
                "model": c.model,
                "decision": c.decision.value,
                "reasons": c.reasons,
                "known_issues": c.known_issues,
            }
            for c in ev.cells
        ],
        "blocking_issues": [
            {
                "rank": i + 1,
                "key": b.key,
                "title": b.title,
                "test": b.test,
                "gate": b.gate,
                "severity": b.severity.value,
                "reach_models": b.reach,
                "cells": b.cells,
                "partners": sorted(b.partners),
            }
            for i, b in enumerate(issues)
        ],
        "waivers": sorted(waivers, key=lambda w: (w["expires"], w["partner"])),
    }


def to_json(ev: Evaluation, **kwargs: Any) -> str:
    return json.dumps(to_dict(ev, **kwargs), indent=2) + "\n"


_REC_LABEL = {"go": "GO", "conditional": "CONDITIONAL", "partial": "PARTIAL", "no-go": "NO-GO"}
_GATE_MARK = {
    "passed": "pass",
    "known_issues": "pass (known issues)",
    "conditional": "waiver",
    "failed": "FAIL",
    "n/a": "n/a",
}


def to_markdown(ev: Evaluation, top_n: int = 10) -> str:
    d = to_dict(ev)
    s = d["summary"]
    lines = [
        f"# Launch readiness report: {d['plan']}",
        "",
        f"As of {d['as_of']}. {s['partners']} partner apps across {s['models']} TV models "
        f"({s['targeted_cells']} in-scope app/model pairs).",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Certified (go + conditional) | {s['certified_pct']}% |",
        f"| Go / Conditional / No-go pairs | {s['go']} / {s['conditional']} / {s['no_go']} |",
        f"| Partner recommendations | {', '.join(f'{_REC_LABEL[k]} {v}' for k, v in s['recommendations'].items())} |",  # noqa: E501
        f"| Open blocking issues | {s['blocking_issues']} |",
        f"| Active waivers | {s['active_waivers']} |",
        "",
        "## Partner recommendations",
        "",
        "| Partner | Version | Recommendation | Coverage | Go | Cond | No-go | Rationale |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for p in d["partners"]:
        lines.append(
            f"| {p['name']} | {p['version']} | **{_REC_LABEL[p['recommendation']]}** | "
            f"{p['coverage_pct']}% of {p['targeted']} | {p['go']} | {p['conditional']} | "
            f"{p['no_go']} | {'; '.join(p['rationale'])} |"
        )

    gate_ids = [g["id"] for g in d["gates"]]
    lines += [
        "",
        "## Gate status",
        "",
        "| Partner | " + " | ".join(f"{g['id']} {g['name']}" for g in d["gates"]) + " |",
        "|---|" + "---|" * len(gate_ids),
    ]
    for p in d["partners"]:
        marks = []
        for g in p["gates"]:
            mark = _GATE_MARK[g["status"]]
            if g["models_failed"]:
                mark += f" ({g['models_failed']} models)"
            marks.append(mark)
        lines.append(f"| {p['name']} | " + " | ".join(marks) + " |")

    lines += [
        "",
        f"## Blocking issues by reach (top {min(top_n, len(d['blocking_issues']))})",
        "",
        "| # | Issue | Gate | Severity | Models | Partners |",
        "|---|---|---|---|---|---|",
    ]
    for b in d["blocking_issues"][:top_n]:
        lines.append(
            f"| {b['rank']} | `{b['key']}` {b['title']} | {b['gate']} | {b['severity']} | "
            f"{b['reach_models']} | {', '.join(b['partners'])} |"
        )

    lines += ["", "## Active waivers", ""]
    if d["waivers"]:
        lines += [
            "| Partner | Test | Approved by | Expires | Days left | Models | Mitigation |",
            "|---|---|---|---|---|---|---|",
        ]
        for w in d["waivers"]:
            lines.append(
                f"| {w['partner']} | {w['test']} | {w['approved_by']} | {w['expires']} | "
                f"{w['days_left']} | {w['models']} | {w['mitigation']} |"
            )
    else:
        lines.append("None.")

    lines += ["", "## No-go detail", ""]
    names = {p["id"]: p["name"] for p in d["partners"]}
    any_nogo = False
    for pid in names:
        rows = [c for c in d["matrix"] if c["partner"] == pid and c["decision"] == "no-go"]
        if not rows:
            continue
        any_nogo = True
        by_reason: dict[str, list[str]] = {}
        for c in rows:
            for r in c["reasons"]:
                by_reason.setdefault(r, []).append(c["model"])
        lines.append(f"**{names[pid]}** ({len(rows)} models)")
        lines.append("")
        for reason, models in by_reason.items():
            lines.append(
                f"- {reason}: {len(models)} models ({', '.join(models[:6])}"
                f"{', ...' if len(models) > 6 else ''})"
            )
        lines.append("")
    if not any_nogo:
        lines.append("None.")
    return "\n".join(lines).rstrip() + "\n"
