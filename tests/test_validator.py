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


def _write_manifest(skill_dir: Path, manifest: dict, name: str = "skill.json") -> None:
    (skill_dir / name).write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def _replace_frontmatter(skill_dir: Path, old: str, new: str) -> None:
    skill_file = skill_dir / "SKILL.md"
    text = skill_file.read_text(encoding="utf-8")
    skill_file.write_text(text.replace(old, new), encoding="utf-8")


def _messages(skill_dir: Path) -> list[tuple[str, str]]:
    return [(issue.severity, issue.message) for issue in validate_skill(skill_dir)]


def test_complete_example_is_valid() -> None:
    assert validate_skill(EXAMPLE) == []


def test_unrelated_frontmatter_fields_are_out_of_scope(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    _replace_frontmatter(
        skill_dir,
        "license: MIT\n",
        "license: MIT\ncompatibility: Requires network access.\ncustom-profile: enabled\n",
    )
    _replace_frontmatter(
        skill_dir,
        f"  {MANIFEST_KEY}: skill.json\n",
        f"  {MANIFEST_KEY}: skill.json\n  custom.setting:\n    nested: value\n",
    )

    assert validate_skill(skill_dir) == []


def test_frontmatter_license_is_optional(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    _replace_frontmatter(skill_dir, "license: MIT\n", "")

    assert validate_skill(skill_dir) == []


def test_declared_frontmatter_license_must_be_non_empty(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    _replace_frontmatter(skill_dir, "license: MIT", 'license: ""')

    assert any(
        "license must be a non-empty string" in message
        for _, message in _messages(skill_dir)
    )


def test_redundant_top_level_authors_warns(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    _replace_frontmatter(
        skill_dir,
        "license: MIT\n",
        "license: MIT\nauthors:\n  - Person: Example Maintainer\n",
    )

    assert _messages(skill_dir) == [
        ("warning", "authors duplicates metadata owned by skill.json")
    ]


def test_redundant_metadata_author_warns(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    _replace_frontmatter(
        skill_dir,
        f"  {MANIFEST_KEY}: skill.json\n",
        f"  {MANIFEST_KEY}: skill.json\n  author: Example Maintainer\n",
    )

    assert _messages(skill_dir) == [
        ("warning", "metadata.author duplicates metadata owned by skill.json")
    ]


def test_matching_redundant_version_warns(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    _replace_frontmatter(skill_dir, "license: MIT\n", 'license: MIT\nversion: "1.0.0"\n')

    assert _messages(skill_dir) == [
        ("warning", "version duplicates metadata owned by skill.json")
    ]


def test_mismatched_redundant_metadata_version_is_invalid(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    _replace_frontmatter(
        skill_dir,
        f"  {MANIFEST_KEY}: skill.json\n",
        f'  {MANIFEST_KEY}: skill.json\n  version: "2.0.0"\n',
    )

    messages = _messages(skill_dir)

    assert ("warning", "metadata.version duplicates metadata owned by skill.json") in messages
    assert any(
        severity == "error" and "version must match skill.json" in message
        for severity, message in messages
    )


def test_manifest_name_must_match_frontmatter(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["name"] = "different-name"
    _write_manifest(skill_dir, manifest)

    assert any("name must match SKILL.md" in message for _, message in _messages(skill_dir))


def test_manifest_license_must_match_when_frontmatter_declares_it(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["license"] = "Apache-2.0"
    _write_manifest(skill_dir, manifest)

    assert any("license must match SKILL.md" in message for _, message in _messages(skill_dir))


def test_unknown_manifest_field_is_invalid(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["links"] = []
    _write_manifest(skill_dir, manifest)

    assert any(
        "Additional properties are not allowed" in message
        for _, message in _messages(skill_dir)
    )


def test_namespaced_extension_accepts_arbitrary_json(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["extensions"] = {
        "https://example.org/skillmeta/capabilities/v1": {
            "declares": ["network-read"],
            "advisory": True,
        }
    }
    _write_manifest(skill_dir, manifest)

    assert validate_skill(skill_dir) == []


def test_extension_key_must_be_an_absolute_uri(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["extensions"] = {"capabilities": {"declares": []}}
    _write_manifest(skill_dir, manifest)

    assert any("capabilities" in message for _, message in _messages(skill_dir))


def test_scalar_creator_is_invalid_in_v03(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["creators"] = ["Person: Example Maintainer"]
    _write_manifest(skill_dir, manifest)

    assert any(
        "is not of type 'object'" in message
        for _, message in _messages(skill_dir)
    )


def test_multiple_creator_affiliations_and_creation_contexts_are_valid(
    tmp_path: Path,
) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["creators"] = [
        {
            "type": "Person",
            "name": "Maya Chen",
            "id": "https://example.org/people/maya-chen",
            "affiliations": [
                {
                    "name": "Northstar Research",
                    "id": "https://example.org/organizations/northstar-research",
                }
            ],
            "createdUsing": [
                {
                    "harness": {"id": "openai/codex", "version": "1.2.0"},
                    "model": {"id": "openai/gpt-5.6-sol"},
                },
                {"model": {"id": "openai/gpt-5.6-terra"}},
            ],
        },
        {
            "type": "Person",
            "name": "Daniel Okafor",
            "affiliations": [{"name": "Lantern Systems"}],
            "createdUsing": [
                {
                    "harness": {"id": "google/gemini-cli", "version": "0.9.0"},
                    "model": {"id": "google/gemini-2.5-pro"},
                }
            ],
        },
    ]
    _write_manifest(skill_dir, manifest)

    assert validate_skill(skill_dir) == []


def test_software_agent_creator_is_valid(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["creators"] = [
        {
            "type": "SoftwareAgent",
            "name": "Project Auditor",
            "id": "example/project-auditor",
            "version": "1.0.0",
            "createdUsing": [
                {
                    "harness": {"id": "openai/codex", "version": "1.2.0"},
                    "model": {"id": "openai/gpt-5.6-sol"},
                }
            ],
        }
    ]
    _write_manifest(skill_dir, manifest)

    assert validate_skill(skill_dir) == []


def test_creator_fields_are_scoped_to_creator_type(tmp_path: Path) -> None:
    invalid_creators = {
        "person-version": {
            "type": "Person",
            "name": "Example Person",
            "version": "1.0.0",
        },
        "organization-affiliation": {
            "type": "Organization",
            "name": "Example Organization",
            "affiliations": [{"name": "Another Organization"}],
        },
        "software-agent-email": {
            "type": "SoftwareAgent",
            "name": "Example Agent",
            "id": "example/agent",
            "version": "1.0.0",
            "email": "agent@example.org",
        },
    }

    for directory_name, creator in invalid_creators.items():
        case_root = tmp_path / directory_name
        case_root.mkdir()
        skill_dir = _copy_example(case_root)
        manifest = _manifest(skill_dir)
        manifest["creators"] = [creator]
        _write_manifest(skill_dir, manifest)

        assert validate_skill(skill_dir)


def test_software_agent_creator_requires_scoped_id_and_version(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["creators"] = [
        {
            "type": "SoftwareAgent",
            "name": "Codex",
            "id": "codex",
        }
    ]
    _write_manifest(skill_dir, manifest)

    messages = _messages(skill_dir)
    assert any("'version' is a required property" in message for _, message in messages)
    assert any("does not match" in message for _, message in messages)


def test_created_using_harness_requires_version(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    del manifest["creators"][0]["createdUsing"][0]["harness"]["version"]
    _write_manifest(skill_dir, manifest)

    assert any("'version' is a required property" in message for _, message in _messages(skill_dir))


def test_global_created_with_is_invalid_in_v03(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["createdWith"] = manifest["creators"][0]["createdUsing"][0]
    _write_manifest(skill_dir, manifest)

    assert any(
        "Additional properties are not allowed" in message
        for _, message in _messages(skill_dir)
    )


def test_package_purl_may_use_qualifiers_and_subpath(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["requirements"][-1]["purl"] = (
        "pkg:pypi/pytest?repository_url=https%3A%2F%2Fpypi.org#src"
    )
    _write_manifest(skill_dir, manifest)

    assert validate_skill(skill_dir) == []


def test_exact_package_version_uses_vers(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["requirements"][-1]["versionRange"] = "vers:pypi/8.0.0"
    _write_manifest(skill_dir, manifest)

    assert validate_skill(skill_dir) == []


def test_package_purl_must_be_versionless(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["requirements"][-1]["purl"] = "pkg:pypi/pytest@8.0.0"
    del manifest["requirements"][-1]["versionRange"]
    _write_manifest(skill_dir, manifest)

    assert any("requirements[3]" in issue.location for issue in validate_skill(skill_dir))


def test_multiple_targets_of_supported_kinds_are_valid(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["targets"] = [
        {"kind": "harness", "id": "openai/codex"},
        {"kind": "harness", "id": "anthropic/claude-code"},
        {"kind": "package", "purl": "pkg:pypi/openai-agents"},
        {"kind": "package", "purl": "pkg:pypi/google-adk"},
        {"kind": "operating-system", "id": "macos"},
        {"kind": "operating-system", "id": "linux"},
    ]
    _write_manifest(skill_dir, manifest)

    assert validate_skill(skill_dir) == []


def test_universal_target_must_appear_alone(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["targets"] = [
        {"kind": "universal"},
        {"kind": "package", "purl": "pkg:pypi/openai-agents"},
    ]
    _write_manifest(skill_dir, manifest)

    assert any("is too long" in message for _, message in _messages(skill_dir))


def test_executable_requirement_is_valid(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["requirements"].append({"kind": "executable", "id": "git"})
    _write_manifest(skill_dir, manifest)

    assert validate_skill(skill_dir) == []


def test_removed_requirement_kinds_are_invalid(tmp_path: Path) -> None:
    for requirement in (
        {"kind": "command", "id": "git"},
        {"kind": "operating-system", "id": "linux"},
        {"kind": "capability", "id": "network-access"},
    ):
        skill_dir = _copy_example(tmp_path / requirement["kind"])
        manifest = _manifest(skill_dir)
        manifest["requirements"].append(requirement)
        _write_manifest(skill_dir, manifest)

        assert any("requirements[4]" in issue.location for issue in validate_skill(skill_dir))


def test_skill_requirement_rejects_parent_traversal(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["requirements"][0]["paths"][0] = "../outside"
    _write_manifest(skill_dir, manifest)

    assert any("../outside" in message for _, message in _messages(skill_dir))


def test_manifest_reference_must_remain_local(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    _replace_frontmatter(
        skill_dir,
        f"{MANIFEST_KEY}: skill.json",
        f"{MANIFEST_KEY}: ../skill.json",
    )

    assert any("must not escape the skill root" in message for _, message in _messages(skill_dir))


def test_nonstandard_manifest_name_warns(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    _write_manifest(skill_dir, manifest, name="manifest.json")
    _replace_frontmatter(
        skill_dir,
        f"{MANIFEST_KEY}: skill.json",
        f"{MANIFEST_KEY}: manifest.json",
    )

    assert _messages(skill_dir) == [("warning", "manifest should be named skill.json")]


def test_validator_accepts_published_v01_and_v02_schemas(tmp_path: Path) -> None:
    schema_uris = {
        "v01": (
            "https://raw.githubusercontent.com/innerlattice/skillmeta/"
            "v0.1.0/src/skillmeta/schema/v0.1/skill.schema.json"
        ),
        "v02": (
            "https://raw.githubusercontent.com/innerlattice/skillmeta/"
            "v0.2.0/src/skillmeta/schema/v0.2/skill.schema.json"
        ),
    }

    for directory_name, schema_uri in schema_uris.items():
        case_root = tmp_path / directory_name
        case_root.mkdir()
        skill_dir = _copy_example(case_root)
        manifest = {
            "manifestSchema": schema_uri,
            "name": skill_dir.name,
            "version": "1.0.0",
            "license": "MIT",
            "creators": ["Person: Example Maintainer"],
            "createdWith": {
                "harness": {"id": "openai/codex", "version": "1.2.0"},
                "model": {"id": "openai/gpt-5.6-sol"},
            },
            "targets": [{"kind": "universal"}],
            "requirements": [],
        }
        _write_manifest(skill_dir, manifest)

        assert validate_skill(skill_dir) == []


def test_unknown_manifest_schema_is_reported_as_unsupported(tmp_path: Path) -> None:
    skill_dir = _copy_example(tmp_path)
    manifest = _manifest(skill_dir)
    manifest["manifestSchema"] = "https://example.org/skillmeta/v9/schema.json"
    _write_manifest(skill_dir, manifest)

    assert _messages(skill_dir) == [
        (
            "error",
            "unsupported manifestSchema: 'https://example.org/skillmeta/v9/schema.json'",
        )
    ]
