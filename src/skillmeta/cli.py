from __future__ import annotations

import argparse
from collections.abc import Sequence

from skillmeta import __version__
from skillmeta.validator import validate_skill


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillmeta",
        description="Validate Agent Skills using the Skillmeta manifest profile.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a skill directory.")
    validate_parser.add_argument("path", help="Skill directory or path to its SKILL.md.")
    validate_parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Return a failure status when validation emits warnings.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != "validate":
        raise AssertionError(f"unhandled command: {args.command}")

    issues = validate_skill(args.path)
    for issue in issues:
        print(f"[{issue.severity}] {issue.location}: {issue.message}")

    error_count = sum(issue.severity == "error" for issue in issues)
    warning_count = sum(issue.severity == "warning" for issue in issues)

    if error_count:
        print(f"invalid: {error_count} error(s), {warning_count} warning(s)")
        return 1
    if warning_count and args.warnings_as_errors:
        print(f"invalid: 0 error(s), {warning_count} warning(s) treated as errors")
        return 1

    print(f"valid: {warning_count} warning(s)")
    return 0
