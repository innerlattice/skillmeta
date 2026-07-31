from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Literal

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from yaml import YAMLError

MANIFEST_KEY = "skillmeta.manifest"
ALLOWED_FRONTMATTER_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
REQUIRED_FRONTMATTER_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
}
SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class Issue:
    severity: Literal["error", "warning"]
    location: str
    message: str


def _issue(
    severity: Literal["error", "warning"],
    location: str,
    message: str,
) -> Issue:
    return Issue(severity=severity, location=location, message=message)


def _schema() -> dict[str, Any]:
    schema_resource = resources.files("skillmeta").joinpath(
        "schema",
        "v0.1",
        "skill.schema.json",
    )
    return json.loads(schema_resource.read_text(encoding="utf-8"))


def _skill_directory(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    if candidate.name == "SKILL.md":
        return candidate.parent
    return candidate


def _parse_frontmatter(skill_file: Path) -> tuple[dict[str, Any] | None, list[Issue]]:
    issues: list[Issue] = []
    try:
        text = skill_file.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [_issue("error", str(skill_file), f"cannot read SKILL.md: {exc}")]

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, [
            _issue("error", str(skill_file), "SKILL.md must begin with YAML frontmatter")
        ]

    closing_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if closing_index is None:
        return None, [
            _issue("error", str(skill_file), "SKILL.md frontmatter has no closing delimiter")
        ]

    try:
        frontmatter = yaml.safe_load("\n".join(lines[1:closing_index]))
    except YAMLError as exc:
        return None, [
            _issue("error", str(skill_file), f"invalid YAML frontmatter: {exc}")
        ]

    if not isinstance(frontmatter, dict):
        return None, [
            _issue("error", str(skill_file), "frontmatter must be a YAML mapping")
        ]
    return frontmatter, issues


def _validate_frontmatter(
    frontmatter: dict[str, Any],
    skill_dir: Path,
) -> list[Issue]:
    issues: list[Issue] = []
    skill_file = skill_dir / "SKILL.md"

    for field in sorted(REQUIRED_FRONTMATTER_FIELDS - frontmatter.keys()):
        issues.append(
            _issue("error", str(skill_file), f"missing required frontmatter field: {field}")
        )

    for field in sorted(frontmatter.keys() - ALLOWED_FRONTMATTER_FIELDS):
        issues.append(
            _issue("warning", str(skill_file), f"unknown frontmatter field: {field}")
        )

    name = frontmatter.get("name")
    if not isinstance(name, str) or not SKILL_NAME_PATTERN.fullmatch(name):
        issues.append(
            _issue(
                "error",
                f"{skill_file}:name",
                "name must contain lowercase letters, numbers, and single hyphens",
            )
        )
    elif len(name) > 64:
        issues.append(
            _issue("error", f"{skill_file}:name", "name must be at most 64 characters")
        )
    elif name != skill_dir.name:
        issues.append(
            _issue(
                "error",
                f"{skill_file}:name",
                f"name {name!r} must match parent directory {skill_dir.name!r}",
            )
        )

    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip():
        issues.append(
            _issue("error", f"{skill_file}:description", "description must be a non-empty string")
        )
    elif len(description) > 1024:
        issues.append(
            _issue(
                "error",
                f"{skill_file}:description",
                "description must be at most 1024 characters",
            )
        )

    license_value = frontmatter.get("license")
    if not isinstance(license_value, str) or not license_value.strip():
        issues.append(
            _issue("error", f"{skill_file}:license", "license must be a non-empty string")
        )

    compatibility = frontmatter.get("compatibility")
    if not isinstance(compatibility, str) or not compatibility.strip():
        issues.append(
            _issue(
                "error",
                f"{skill_file}:compatibility",
                "compatibility must be a non-empty string",
            )
        )
    elif len(compatibility) > 500:
        issues.append(
            _issue(
                "error",
                f"{skill_file}:compatibility",
                "compatibility must be at most 500 characters",
            )
        )

    allowed_tools = frontmatter.get("allowed-tools")
    if allowed_tools is not None and not isinstance(allowed_tools, str):
        issues.append(
            _issue(
                "error",
                f"{skill_file}:allowed-tools",
                "allowed-tools must be a space-separated string",
            )
        )

    metadata = frontmatter.get("metadata")
    if not isinstance(metadata, dict):
        issues.append(
            _issue("error", f"{skill_file}:metadata", "metadata must be a mapping")
        )
        return issues

    for key, value in metadata.items():
        if not isinstance(key, str) or not isinstance(value, str):
            issues.append(
                _issue(
                    "error",
                    f"{skill_file}:metadata",
                    "metadata keys and values must be strings",
                )
            )
            break

    manifest_reference = metadata.get(MANIFEST_KEY)
    if not isinstance(manifest_reference, str) or not manifest_reference.strip():
        issues.append(
            _issue(
                "error",
                f"{skill_file}:metadata.{MANIFEST_KEY}",
                f"metadata must contain the string key {MANIFEST_KEY!r}",
            )
        )
    return issues


def _manifest_path(
    frontmatter: dict[str, Any],
    skill_dir: Path,
) -> tuple[Path | None, list[Issue]]:
    metadata = frontmatter.get("metadata")
    if not isinstance(metadata, dict):
        return None, []
    reference = metadata.get(MANIFEST_KEY)
    if not isinstance(reference, str) or not reference.strip():
        return None, []

    reference_path = Path(reference)
    location = f"{skill_dir / 'SKILL.md'}:metadata.{MANIFEST_KEY}"
    if reference_path.is_absolute() or "://" in reference:
        return None, [
            _issue("error", location, "manifest reference must be a local relative path")
        ]

    skill_root = skill_dir.resolve()
    resolved = (skill_root / reference_path).resolve()
    if not resolved.is_relative_to(skill_root):
        return None, [
            _issue("error", location, "manifest reference must not escape the skill root")
        ]
    if not resolved.is_file():
        return None, [
            _issue("error", location, f"manifest does not exist: {reference}")
        ]
    return resolved, []


def _load_manifest(manifest_path: Path) -> tuple[dict[str, Any] | None, list[Issue]]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, [
            _issue("error", str(manifest_path), f"cannot read manifest: {exc}")
        ]
    except json.JSONDecodeError as exc:
        return None, [
            _issue(
                "error",
                str(manifest_path),
                f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
            )
        ]
    if not isinstance(manifest, dict):
        return None, [
            _issue("error", str(manifest_path), "manifest must be a JSON object")
        ]
    return manifest, []


def _json_location(manifest_path: Path, path: list[Any]) -> str:
    suffix = "".join(f"[{item}]" if isinstance(item, int) else f".{item}" for item in path)
    return f"{manifest_path}{suffix}"


def _validate_manifest(
    manifest: dict[str, Any],
    manifest_path: Path,
) -> list[Issue]:
    validator = Draft202012Validator(_schema(), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(manifest), key=lambda error: list(error.absolute_path))
    return [
        _issue(
            "error",
            _json_location(manifest_path, list(error.absolute_path)),
            error.message,
        )
        for error in errors
    ]


def _validate_cross_file(
    frontmatter: dict[str, Any],
    manifest: dict[str, Any],
    manifest_path: Path,
) -> list[Issue]:
    issues: list[Issue] = []
    for field in ("name", "license"):
        frontmatter_value = frontmatter.get(field)
        manifest_value = manifest.get(field)
        if frontmatter_value != manifest_value:
            issues.append(
                _issue(
                    "error",
                    f"{manifest_path}.{field}",
                    f"{field} must match SKILL.md ({frontmatter_value!r})",
                )
            )
    return issues


def validate_skill(path: str | Path) -> list[Issue]:
    skill_dir = _skill_directory(path)
    skill_file = skill_dir / "SKILL.md"
    if not skill_dir.is_dir():
        return [_issue("error", str(skill_dir), "skill directory does not exist")]
    if not skill_file.is_file():
        return [_issue("error", str(skill_file), "SKILL.md does not exist")]

    frontmatter, issues = _parse_frontmatter(skill_file)
    if frontmatter is None:
        return issues

    issues.extend(_validate_frontmatter(frontmatter, skill_dir))
    manifest_path, manifest_path_issues = _manifest_path(frontmatter, skill_dir)
    issues.extend(manifest_path_issues)
    if manifest_path is None:
        return issues

    manifest, manifest_issues = _load_manifest(manifest_path)
    issues.extend(manifest_issues)
    if manifest is None:
        return issues

    issues.extend(_validate_manifest(manifest, manifest_path))
    issues.extend(_validate_cross_file(frontmatter, manifest, manifest_path))
    return issues
