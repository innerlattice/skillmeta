from __future__ import annotations

import json
import shutil
from pathlib import Path

from skillmeta.validator import MANIFEST_KEY, validate_skill

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = REPOSITORY_ROOT / "examples" / "openai-agents-project-audit"


def _copy_example(tmp_path: Path) -> Path:
    target = tmp_path / EXAMPLE.name
    shutil.copytree(EXAMPLE, target)
    return target


def _manifest(skill_dir: Path) -> dict:
    return json.loads((skill_dir / "skill.json").read_text(encoding="utf-8"))


def _write_manifest(skill_dir: Path, manifest: dict) -> None:
    (skill_dir / "skill.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def test_complete_example_is_valid() -> None:
    assert validate_skill(EXAMPLE) == []


def test_unknown_frontmatter_field_warns(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    skill_file = skill_dir / "SKILL.md"
    text = skill_file.read_text(encoding="utf-8")
    skill_file.write_text(
        text.replace("license: MIT\n", "license: MIT\nauthors: []\n"),
        encoding="utf-8",
    )

    issues = validate_skill(skill_dir)

    assert [(issue.severity, issue.message) for issue in issues] == [
        ("warning", "unknown frontmatter field: authors")
    ]


def test_manifest_name_must_match_frontmatter(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["name"] = "different-name"
    _write_manifest(skill_dir, manifest)

    issues = validate_skill(skill_dir)

    assert any("name must match SKILL.md" in issue.message for issue in issues)


def test_unknown_manifest_field_is_invalid(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["links"] = []
    _write_manifest(skill_dir, manifest)

    issues = validate_skill(skill_dir)

    assert any("Additional properties are not allowed" in issue.message for issue in issues)


def test_package_purl_may_use_qualifiers_and_subpath(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["requirements"][-1]["purl"] = (
        "pkg:pypi/pytest?repository_url=https%3A%2F%2Fpypi.org#src"
    )
    _write_manifest(skill_dir, manifest)

    assert validate_skill(skill_dir) == []


def test_package_purl_may_pin_an_exact_version(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["requirements"][-1]["purl"] = "pkg:pypi/pytest@8.0.0"
    del manifest["requirements"][-1]["versionRange"]
    _write_manifest(skill_dir, manifest)

    assert validate_skill(skill_dir) == []


def test_versioned_package_purl_cannot_have_a_range(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["requirements"][-1]["purl"] = "pkg:pypi/pytest@8.0.0"
    _write_manifest(skill_dir, manifest)

    issues = validate_skill(skill_dir)

    assert any(".requirements[3]" in issue.location for issue in issues)


def test_universal_target_must_appear_alone(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["targets"] = [
        {"kind": "universal"},
        {"kind": "package", "purl": "pkg:pypi/openai-agents"},
    ]
    _write_manifest(skill_dir, manifest)

    issues = validate_skill(skill_dir)

    assert any("is too long" in issue.message for issue in issues)


def test_skill_requirement_rejects_parent_traversal(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["requirements"][0]["paths"][0] = "../outside"
    _write_manifest(skill_dir, manifest)

    issues = validate_skill(skill_dir)

    assert any("../outside" in issue.message for issue in issues)


def test_manifest_reference_must_remain_local(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    skill_file = skill_dir / "SKILL.md"
    text = skill_file.read_text(encoding="utf-8")
    skill_file.write_text(
        text.replace(f"{MANIFEST_KEY}: skill.json", f"{MANIFEST_KEY}: ../skill.json"),
        encoding="utf-8",
    )

    issues = validate_skill(skill_dir)

    assert any("must not escape the skill root" in issue.message for issue in issues)
