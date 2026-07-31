# skillmeta

`skillmeta` is an experimental, portable `skill.json` manifest profile for
[Agent Skills](https://agentskills.io/specification).

Agent Skills keeps `SKILL.md` small and broadly compatible. Skillmeta adds a
local machine-readable companion for release identity, SPDX 2.3 creators,
agent provenance, targets, package requirements, namespaced extensions, and
pinned skill dependencies.

## Status

Version `0.2.0` is experimental. It extends Agent Skills without changing the
upstream format and must not be represented as part of the canonical Agent
Skills specification.

## Minimal integration

An Agent Skill points to its local manifest through the upstream `metadata`
string map:

```yaml
---
name: example-skill
description: Performs an example workflow. Use when that workflow is requested.
license: MIT
metadata:
  skillmeta.manifest: skill.json
---
```

The referenced manifest contains the detailed metadata:

```json
{
  "manifestSchema": "https://raw.githubusercontent.com/ayahohner/skillmeta/v0.2.0/src/skillmeta/schema/v0.2/skill.schema.json",
  "name": "example-skill",
  "version": "1.0.0",
  "license": "MIT",
  "creators": ["Person: Example Maintainer"],
  "targets": [{"kind": "universal"}],
  "requirements": []
}
```

See [SPECIFICATION.md](SPECIFICATION.md) for the normative contract and
[examples/openai-agents-project-audit](examples/openai-agents-project-audit)
for a complete example.

## Validate a skill

The Python reference validator checks the manifest link, canonical name,
cross-file name/license/version consistency, redundant frontmatter metadata,
and the v0.2 JSON Schema.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/skillmeta validate examples/openai-agents-project-audit
```

Warnings do not fail validation unless requested:

```bash
.venv/bin/skillmeta validate path/to/skill --warnings-as-errors
```

## Repository layout

```text
skillmeta/
├── SPECIFICATION.md
├── examples/
├── src/skillmeta/
│   ├── schema/v0.1/skill.schema.json
│   ├── schema/v0.2/skill.schema.json
│   └── validator.py
└── tests/
```

## License

MIT
