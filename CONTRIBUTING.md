# Contributing

Skillmeta is a profile of Agent Skills. Changes should preserve compatibility
with the canonical format and keep the core contract small.

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

- Add core fields only when they change resolution, applicability, provenance,
  or validation behavior. Use a namespaced extension for experimental data.
- Do not add harness-specific behavior to the universal core.
- Published schema URIs are immutable.
- Any change to accepted documents or field meaning requires a new versioned
  schema directory and URI.
- Add valid and invalid tests for every contract change.

## Releases

The manifest format version appears in `SPECIFICATION.md` and its schema URI.
The reference tool version is reported by `skillmeta --version`. They may
advance independently: tooling changes do not require a new schema version.

Create a GitHub release for each published tool version. The release workflow
builds and publishes the matching Python package through PyPI Trusted
Publishing. Release notes summarize the corresponding changelog entries.

## Pull requests

Explain the interoperability problem, the smallest contract change that solves
it, the compatibility impact, and the verification evidence.
