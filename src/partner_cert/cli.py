"""Command line entry point.

partner-cert evaluate examples/data --out out/
partner-cert evaluate examples/data --format md
partner-cert explain examples/data --partner cinder-films --model TV24-E43A
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from . import __version__
from .engine import evaluate
from .loader import DataError, load_dataset
from .model import Recommendation, Status
from .report import to_json, to_markdown


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="partner-cert", description=__doc__.splitlines()[0])
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    ev = sub.add_parser("evaluate", help="evaluate all submissions and write the readiness report")
    ev.add_argument("data_dir", type=Path)
    ev.add_argument("--out", type=Path, help="directory for report.json and report.md")
    ev.add_argument(
        "--format",
        choices=["md", "json"],
        default="md",
        help="stdout format when --out is not given",
    )
    ev.add_argument("--as-of", type=date.fromisoformat, help="override plan as_of date")
    ev.add_argument(
        "--strict", action="store_true", help="exit 2 if any partner is NO-GO (useful as a CI gate)"
    )

    ex = sub.add_parser("explain", help="show every test outcome for one partner on one model")
    ex.add_argument("data_dir", type=Path)
    ex.add_argument("--partner", required=True)
    ex.add_argument("--model", required=True)
    ex.add_argument("--as-of", type=date.fromisoformat)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        dataset = load_dataset(args.data_dir)
    except DataError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    ev = evaluate(dataset, as_of=args.as_of)

    if args.command == "explain":
        try:
            cell = ev.cell(args.partner, args.model)
        except KeyError:
            print(f"error: no cell for {args.partner} x {args.model}", file=sys.stderr)
            return 1
        print(f"{args.partner} x {args.model}: {cell.decision.value.upper()}")
        for r in cell.reasons:
            print(f"  reason: {r}")
        for o in cell.outcomes:
            if o.status is Status.NOT_APPLICABLE:
                continue
            print(f"  {o.gate} {o.test:<12} {o.severity.value:<8} {o.status.value:<8} {o.reason}")
        return 0

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(to_json(ev), encoding="utf-8")
        (args.out / "report.md").write_text(to_markdown(ev), encoding="utf-8")
        print(f"wrote {args.out / 'report.json'} and {args.out / 'report.md'}")
        for p in ev.partners:
            print(
                f"  {p.name:<22} {p.recommendation.value.upper():<12} "
                f"{p.go + p.conditional}/{p.targeted} models"
            )
    else:
        sys.stdout.write(to_json(ev) if args.format == "json" else to_markdown(ev))

    if args.strict and any(p.recommendation is Recommendation.NO_GO for p in ev.partners):
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
