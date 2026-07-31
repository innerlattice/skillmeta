from __future__ import annotations

from pathlib import Path

from skillmeta.cli import main

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = REPOSITORY_ROOT / "examples" / "openai-agents-project-audit"


def test_cli_accepts_complete_example(capsys) -> None:
    assert main(["validate", str(EXAMPLE)]) == 0
    assert "valid: 0 warning(s)" in capsys.readouterr().out
