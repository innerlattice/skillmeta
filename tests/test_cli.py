from __future__ import annotations

import json
import shutil
from pathlib import Path

from skillmeta.cli import main

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = REPOSITORY_ROOT / "examples" / "openai-agents-project-audit"


def test_cli_accepts_complete_example(capsys) -> None:
    assert main(["validate", str(EXAMPLE)]) == 0
    assert "valid: 0 warning(s)" in capsys.readouterr().out


def test_cli_emits_machine_readable_results(capsys) -> None:
    assert main(["validate", str(EXAMPLE), "--format", "json"]) == 0

    payload = json.loads(capsys.readouterr().out)

    assert payload == {
        "passed": True,
        "results": [
            {
                "issues": [],
                "path": str(EXAMPLE.resolve()),
                "valid": True,
            }
        ],
        "summary": {"errors": 0, "skills": 1, "warnings": 0},
        "valid": True,
    }


def test_cli_reports_stable_diagnostic_codes(tmp_path: Path, capsys) -> None:
    missing = tmp_path / "missing-skill"

    assert main(["validate", str(missing)]) == 1
    assert "skill.directory.not_found" in capsys.readouterr().out


def test_cli_recursively_validates_skills_and_ignores_dependencies(
    tmp_path: Path,
    capsys,
) -> None:
    first = tmp_path / "first" / EXAMPLE.name
    second = tmp_path / "second" / EXAMPLE.name
    ignored = tmp_path / "node_modules" / EXAMPLE.name
    shutil.copytree(EXAMPLE, first)
    shutil.copytree(EXAMPLE, second)
    shutil.copytree(EXAMPLE, ignored)

    assert main(["validate", str(tmp_path), "--recursive", "--format", "json"]) == 0

    payload = json.loads(capsys.readouterr().out)

    assert payload["summary"] == {"errors": 0, "skills": 2, "warnings": 0}
    assert {result["path"] for result in payload["results"]} == {
        str(first.resolve()),
        str(second.resolve()),
    }


def test_cli_accepts_multiple_skill_paths(capsys) -> None:
    assert main(["validate", str(EXAMPLE), str(EXAMPLE / "SKILL.md")]) == 0
    assert "valid: 0 warning(s)" in capsys.readouterr().out
