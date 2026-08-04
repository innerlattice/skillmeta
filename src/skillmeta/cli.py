from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from skillmeta import __version__
from skillmeta.validator import Issue, validate_skill

IGNORED_SCAN_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "__pycache__",
    "node_modules",
    "venv",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillmeta",
        description="Validate Agent Skills using the Skillmeta manifest profile.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate one or more skill directories.",
    )
    validate_parser.add_argument(
        "paths",
        nargs="+",
        help="Skill directories or paths to SKILL.md files.",
    )
    validate_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Find and validate every SKILL.md below each directory.",
    )
    validate_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        dest="output_format",
        help="Output format (default: text).",
    )
    validate_parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Return a failure status when validation emits warnings.",
    )
    return parser


def _skill_directory(path: Path) -> Path:
    return path.parent if path.name == "SKILL.md" else path


def _recursive_skills(path: Path) -> list[Path]:
    if not path.is_dir():
        return [_skill_directory(path)]

    skills: list[Path] = []
    for root, directories, files in os.walk(path):
        directories[:] = sorted(
            directory
            for directory in directories
            if directory not in IGNORED_SCAN_DIRECTORIES
        )
        if "SKILL.md" in files:
            skills.append(Path(root))
    return skills or [path]


def _validation_paths(paths: Sequence[str], recursive: bool) -> list[Path]:
    candidates: list[Path] = []
    for value in paths:
        path = Path(value).expanduser()
        candidates.extend(_recursive_skills(path) if recursive else [_skill_directory(path)])

    unique: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        identity = candidate.resolve()
        if identity not in seen:
            seen.add(identity)
            unique.append(candidate)
    return unique


def _counts(results: list[tuple[Path, list[Issue]]]) -> tuple[int, int]:
    issues = [issue for _, path_issues in results for issue in path_issues]
    errors = sum(issue.severity == "error" for issue in issues)
    warnings = sum(issue.severity == "warning" for issue in issues)
    return errors, warnings


def _print_text(
    results: list[tuple[Path, list[Issue]]],
    warnings_as_errors: bool,
) -> None:
    for _, issues in results:
        for issue in issues:
            print(f"[{issue.severity}] {issue.code} {issue.location}: {issue.message}")

    errors, warnings = _counts(results)
    if errors:
        print(f"invalid: {errors} error(s), {warnings} warning(s)")
    elif warnings and warnings_as_errors:
        print(f"invalid: 0 error(s), {warnings} warning(s) treated as errors")
    elif len(results) == 1:
        print(f"valid: {warnings} warning(s)")
    else:
        print(f"valid: {len(results)} skill(s), {warnings} warning(s)")


def _print_json(
    results: list[tuple[Path, list[Issue]]],
    warnings_as_errors: bool,
) -> None:
    errors, warnings = _counts(results)
    payload = {
        "valid": errors == 0,
        "passed": errors == 0 and (warnings == 0 or not warnings_as_errors),
        "summary": {
            "skills": len(results),
            "errors": errors,
            "warnings": warnings,
        },
        "results": [
            {
                "path": str(path.resolve()),
                "valid": not any(issue.severity == "error" for issue in issues),
                "issues": [asdict(issue) for issue in issues],
            }
            for path, issues in results
        ],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != "validate":
        raise AssertionError(f"unhandled command: {args.command}")

    results = [
        (path, validate_skill(path))
        for path in _validation_paths(args.paths, args.recursive)
    ]
    errors, warnings = _counts(results)

    if args.output_format == "json":
        _print_json(results, args.warnings_as_errors)
    else:
        _print_text(results, args.warnings_as_errors)

    return int(errors > 0 or (warnings > 0 and args.warnings_as_errors))
