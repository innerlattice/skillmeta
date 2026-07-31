# skillmeta

`skillmeta` is an experimental, portable `skill.json` manifest profile for
[Agent Skills](https://agentskills.io/specification).

Agent Skills keeps `SKILL.md` small and broadly compatible. `skillmeta` adds a
local, machine-readable companion for release identity, SPDX creators,
provenance, targets, package requirements, and pinned skill dependencies.

## Status

Version `0.1.0` is experimental. It extends Agent Skills without changing the
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
compatibility: Universal; exact targets and requirements are declared in skill.json.
metadata:
  skillmeta.manifest: skill.json
---
```

The referenced `skill.json` contains the detailed profile:

```json
{
  "manifestSchema": "https://raw.githubusercontent.com/ayahohner/skillmeta/v0.1.0/src/skillmeta/schema/v0.1/skill.schema.json",
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
for a complete example with multiple skills from multiple repositories.

## Validate a skill

The reference validator checks the Agent Skills frontmatter profile, warns on
unknown frontmatter fields, validates `skill.json`, and enforces cross-file
name and license consistency.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/skillmeta validate examples/openai-agents-project-audit
```

Warnings do not fail validation unless requested:

```bash
.venv/bin/skillmeta validate path/to/skill --warnings-as-errors
```

## Safe velocity

Pinning does not require slow updates. Discovery can follow fast-moving release
channels while execution remains bound to a reviewed immutable commit.
Automated provenance checks, compatibility tests, policy, canaries, and
rollback can promote new pins within minutes without executing mutable
upstream state. The first-principles model is described in
[docs/safe-velocity.md](docs/safe-velocity.md).

## Repository layout

```text
skillmeta/
├── SPECIFICATION.md
├── docs/safe-velocity.md
├── examples/
├── src/skillmeta/
│   ├── schema/v0.1/skill.schema.json
│   └── validator.py
└── tests/
```

## License

MIT
