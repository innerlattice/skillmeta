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
MANIFEST_SCHEMA_URI = (
    "https://raw.githubusercontent.com/ayahohner/skillmeta/"
    "v0.3.0/src/skillmeta/schema/v0.3/skill.schema.json"
)
MANIFEST_SCHEMA_URIS = {
    (
        "https://raw.githubusercontent.com/ayahohner/skillmeta/"
        "v0.1.0/src/skillmeta/schema/v0.1/skill.schema.json"
    ): "v0.1",
    (
        "https://raw.githubusercontent.com/ayahohner/skillmeta/"
        "v0.2.0/src/skillmeta/schema/v0.2/skill.schema.json"
    ): "v0.2",
    MANIFEST_SCHEMA_URI: "v0.3",
}
REDUNDANT_FRONTMATTER_FIELDS = {
    "author",
    "authors",
    "createdWith",
    "createdUsing",
    "creators",
    "extensions",
    "repository",
    "requirements",
    "targets",
    "version",
}
SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class Issue:
    code: str
    severity: Literal["error", "warning"]
    location: str
    message: str


def _issue(
    code: str,
    severity: Literal["error", "warning"],
    location: str,
    message: str,
) -> Issue:
    return Issue(code=code, severity=severity, location=location, message=message)


def _schema(manifest_schema: str) -> dict[str, Any]:
    schema_version = MANIFEST_SCHEMA_URIS[manifest_schema]
    schema_resource = resources.files("skillmeta").joinpath(
        "schema",
        schema_version,
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
        return None, [
            _issue(
                "frontmatter.read_failed",
                "error",
                str(skill_file),
                f"cannot read SKILL.md: {exc}",
            )
        ]

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, [
            _issue(
                "frontmatter.missing",
                "error",
                str(skill_file),
                "SKILL.md must begin with YAML frontmatter",
            )
        ]

    closing_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if closing_index is None:
        return None, [
            _issue(
                "frontmatter.unclosed",
                "error",
                str(skill_file),
                "SKILL.md frontmatter has no closing delimiter",
            )
        ]

    try:
        frontmatter = yaml.safe_load("\n".join(lines[1:closing_index]))
    except YAMLError as exc:
        return None, [
            _issue(
                "frontmatter.invalid_yaml",
                "error",
                str(skill_file),
                f"invalid YAML frontmatter: {exc}",
            )
        ]

    if not isinstance(frontmatter, dict):
        return None, [
            _issue(
                "frontmatter.not_mapping",
                "error",
                str(skill_file),
                "frontmatter must be a YAML mapping",
            )
        ]
    return frontmatter, issues


def _validate_frontmatter(
    frontmatter: dict[str, Any],
    skill_dir: Path,
) -> list[Issue]:
    issues: list[Issue] = []
    skill_file = skill_dir / "SKILL.md"

    for field in sorted(frontmatter.keys() & REDUNDANT_FRONTMATTER_FIELDS):
        issues.append(
            _issue(
                "frontmatter.redundant",
                "warning",
                f"{skill_file}:{field}",
                f"{field} duplicates metadata owned by skill.json",
            )
        )

    name = frontmatter.get("name")
    if not isinstance(name, str) or not SKILL_NAME_PATTERN.fullmatch(name):
        issues.append(
            _issue(
                "frontmatter.name.invalid",
                "error",
                f"{skill_file}:name",
                "name must contain lowercase letters, numbers, and single hyphens",
            )
        )
    elif len(name) > 64:
        issues.append(
            _issue(
                "frontmatter.name.too_long",
                "error",
                f"{skill_file}:name",
                "name must be at most 64 characters",
            )
        )
    elif name != skill_dir.name:
        issues.append(
            _issue(
                "frontmatter.name.directory_mismatch",
                "error",
                f"{skill_file}:name",
                f"name {name!r} must match parent directory {skill_dir.name!r}",
            )
        )

    license_value = frontmatter.get("license")
    if "license" in frontmatter and (
        not isinstance(license_value, str) or not license_value.strip()
    ):
        issues.append(
            _issue(
                "frontmatter.license.invalid",
                "error",
                f"{skill_file}:license",
                "license must be a non-empty string when declared",
            )
        )

    metadata = frontmatter.get("metadata")
    if not isinstance(metadata, dict):
        issues.append(
            _issue(
                "frontmatter.metadata.invalid",
                "error",
                f"{skill_file}:metadata",
                "metadata must be a mapping",
            )
        )
        return issues

    for field in sorted(metadata.keys() & REDUNDANT_FRONTMATTER_FIELDS):
        issues.append(
            _issue(
                "frontmatter.redundant",
                "warning",
                f"{skill_file}:metadata.{field}",
                f"metadata.{field} duplicates metadata owned by skill.json",
            )
        )

    manifest_reference = metadata.get(MANIFEST_KEY)
    if not isinstance(manifest_reference, str) or not manifest_reference.strip():
        issues.append(
            _issue(
                "frontmatter.manifest.missing",
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
            _issue(
                "frontmatter.manifest.external",
                "error",
                location,
                "manifest reference must be a local relative path",
            )
        ]
    if reference_path.suffix.lower() != ".json":
        return None, [
            _issue(
                "frontmatter.manifest.not_json",
                "error",
                location,
                "manifest reference must identify a JSON file",
            )
        ]

    skill_root = skill_dir.resolve()
    resolved = (skill_root / reference_path).resolve()
    if not resolved.is_relative_to(skill_root):
        return None, [
            _issue(
                "frontmatter.manifest.outside_root",
                "error",
                location,
                "manifest reference must not escape the skill root",
            )
        ]
    if not resolved.is_file():
        return None, [
            _issue(
                "frontmatter.manifest.not_found",
                "error",
                location,
                f"manifest does not exist: {reference}",
            )
        ]
    issues: list[Issue] = []
    if reference_path.name != "skill.json":
        issues.append(
            _issue(
                "frontmatter.manifest.nonstandard_name",
                "warning",
                location,
                "manifest should be named skill.json",
            )
        )
    return resolved, issues


def _load_manifest(manifest_path: Path) -> tuple[dict[str, Any] | None, list[Issue]]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, [
            _issue(
                "manifest.read_failed",
                "error",
                str(manifest_path),
                f"cannot read manifest: {exc}",
            )
        ]
    except json.JSONDecodeError as exc:
        return None, [
            _issue(
                "manifest.invalid_json",
                "error",
                str(manifest_path),
                f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
            )
        ]
    if not isinstance(manifest, dict):
        return None, [
            _issue(
                "manifest.not_object",
                "error",
                str(manifest_path),
                "manifest must be a JSON object",
            )
        ]
    return manifest, []


def _json_location(manifest_path: Path, path: list[Any]) -> str:
    suffix = "".join(f"[{item}]" if isinstance(item, int) else f".{item}" for item in path)
    return f"{manifest_path}{suffix}"


def _validate_manifest(
    manifest: dict[str, Any],
    manifest_path: Path,
) -> list[Issue]:
    manifest_schema = manifest.get("manifestSchema")
    if manifest_schema not in MANIFEST_SCHEMA_URIS:
        return [
            _issue(
                "manifest.schema.unsupported",
                "error",
                f"{manifest_path}.manifestSchema",
                f"unsupported manifestSchema: {manifest_schema!r}",
            )
        ]

    validator = Draft202012Validator(
        _schema(manifest_schema),
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(manifest), key=lambda error: list(error.absolute_path))
    return [
        _issue(
            "manifest.schema.invalid",
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
    skill_file: Path,
) -> list[Issue]:
    issues: list[Issue] = []
    frontmatter_name = frontmatter.get("name")
    if manifest.get("name") != frontmatter_name:
        issues.append(
            _issue(
                "manifest.name.mismatch",
                "error",
                f"{manifest_path}.name",
                f"name must match SKILL.md ({frontmatter_name!r})",
            )
        )

    frontmatter_license = frontmatter.get("license")
    if (
        isinstance(frontmatter_license, str)
        and frontmatter_license.strip()
        and manifest.get("license") != frontmatter_license
    ):
        issues.append(
            _issue(
                "manifest.license.mismatch",
                "error",
                f"{manifest_path}.license",
                f"license must match SKILL.md ({frontmatter_license!r})",
            )
        )

    manifest_version = manifest.get("version")
    if isinstance(manifest_version, str):
        version_locations: list[tuple[str, Any]] = []
        if "version" in frontmatter:
            version_locations.append(
                (f"{skill_file}:version", frontmatter["version"])
            )
        metadata = frontmatter.get("metadata")
        if isinstance(metadata, dict) and "version" in metadata:
            version_locations.append(
                (
                    f"{skill_file}:metadata.version",
                    metadata["version"],
                )
            )
        for location, value in version_locations:
            if value != manifest_version:
                issues.append(
                    _issue(
                        "manifest.version.mismatch",
                        "error",
                        location,
                        f"version must match skill.json ({manifest_version!r})",
                    )
                )
    return issues


def validate_skill(path: str | Path) -> list[Issue]:
    skill_dir = _skill_directory(path)
    skill_file = skill_dir / "SKILL.md"
    if not skill_dir.is_dir():
        return [
            _issue(
                "skill.directory.not_found",
                "error",
                str(skill_dir),
                "skill directory does not exist",
            )
        ]
    if not skill_file.is_file():
        return [
            _issue(
                "skill.file.not_found",
                "error",
                str(skill_file),
                "SKILL.md does not exist",
            )
        ]

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
    if manifest.get("manifestSchema") in MANIFEST_SCHEMA_URIS:
        issues.extend(
            _validate_cross_file(frontmatter, manifest, manifest_path, skill_file)
        )
    return issues
