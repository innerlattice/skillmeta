# Contributing

Skillmeta is an experimental profile. Changes should preserve compatibility
with canonical Agent Skills and keep the core contract small.

## Development

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/ruff check .
.venv/bin/pytest
.venv/bin/python -m build
.venv/bin/skillmeta validate examples/openai-agents-project-audit --warnings-as-errors
```

## Schema changes

- Add fields only when they change resolution, compatibility, provenance, or
  validation behavior.
- Do not add harness-specific behavior to the universal core.
- Published schema URIs are immutable.
- Any change to accepted documents or field meaning requires a new versioned
  schema directory and URI.
- Add valid and invalid tests for every contract change.

## Pull requests

Explain the interoperability problem, the smallest contract change that solves
it, the compatibility impact, and the verification evidence.
