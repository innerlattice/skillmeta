# Skillmeta

[![Validate](https://github.com/ayahohner/skillmeta/actions/workflows/validate.yml/badge.svg)](https://github.com/ayahohner/skillmeta/actions/workflows/validate.yml)
[![Spec v0.3.0](https://img.shields.io/badge/spec-v0.3.0-7c3aed)](SPECIFICATION.md)
[![Agent Skills profile](https://img.shields.io/badge/Agent%20Skills-profile-0ea5e9)](https://agentskills.io/specification)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e)](LICENSE)

**Portable, structured metadata for Agent Skills—without bloating
`SKILL.md` frontmatter.**

[Agent Skills](https://agentskills.io/specification) defines a clean format for
teaching an agent what a skill does and how to use it. Its frontmatter is
intentionally small. Skillmeta adds a local `skill.json` for the facts that do
not fit there cleanly: release identity, human and agent provenance, supported
targets, requirements (including dependencies), repository location, and
namespaced extensions.

It is additive. Existing skills keep working, `SKILL.md` stays canonical, and
no registry or particular agent harness is required.

## Contents

- [Why Skillmeta?](#why-skillmeta)
- [Quick start](#quick-start)
- [Targets and dependencies](#targets-and-dependencies)
- [Complete manifest guide](docs/manifest-guide.md)
- [Agent quickstart](#agent-quickstart)
- [Migration](#migration)
- [Scope](#scope)

## Why Skillmeta?

`SKILL.md` sits on the agent's critical path. Its name and description help an
agent select the skill; its body guides the work. Detailed operational metadata
changes for different reasons and serves a different audience. Tooling needs
to answer questions such as:

- Which release is this, and who or what created it?
- Does it support this harness, project package, model, or operating system?
- Which packages, runtimes, executables, or other skills does it depend on?
- Which exact revision of a remote skill is being declared?

Putting those answers in prose makes them hard to check. Putting them in every
harness's private format makes the skill less portable. Skillmeta gives them a
small, versioned home beside the skill.

| File | Primary purpose | Primary readers |
| --- | --- | --- |
| `SKILL.md` | Selection and instructions | Agents |
| `skill.json` | Identity, provenance, targets, and dependencies | Tools, maintainers, and agents inspecting the package |

The manifest gives each concern an explicit home:

| Concern | Skillmeta field |
| --- | --- |
| Release identity and license | `name`, `version`, `license` |
| Human and agent provenance | `creators`, `createdUsing`, `repository` |
| Applicability | `targets` |
| Packages, runtimes, executables, and skills needed | `requirements` |
| Experimental or domain-specific data | `extensions` |

This separation pays off in three ways. A skill carries the same identity and
provenance across compatible harnesses. Tools can compare releases, match
targets, and validate requirements without interpreting prose. And reviewers
can inspect exactly which remote skill revision was declared before its
instructions enter an agent's context.

The same practical gap is being explored across the Agent Skills community;
[discussion #210](https://github.com/agentskills/agentskills/discussions/210)
captures the recurring need for portable identity, dependency declarations,
reproducibility, and a clean boundary between instructions and richer metadata.

## Quick start

A Skillmeta package is still an ordinary Agent Skill directory:

```text
agent-project-audit/
├── SKILL.md
├── skill.json
├── scripts/
└── references/
```

### 1. Link the manifest

Add one entry to the standard `metadata` map in `SKILL.md`:

```yaml
---
name: agent-project-audit
description: Audit Python agent projects for SDK misuse, brittle tests, and risky coverage gaps. Use when reviewing or improving an agent project's test suite.
license: MIT
metadata:
  skillmeta.manifest: skill.json
---
```

No other Skillmeta frontmatter is required.

### 2. Describe the package

Create `skill.json` beside `SKILL.md`:

```json
{
  "manifestSchema": "https://raw.githubusercontent.com/ayahohner/skillmeta/v0.3.0/src/skillmeta/schema/v0.3/skill.schema.json",
  "name": "agent-project-audit",
  "version": "1.0.0",
  "license": "MIT",
  "creators": [
    {
      "type": "Person",
      "name": "Aya Hohner",
      "id": "https://github.com/ayahohner",
      "createdUsing": [
        {
          "harness": {
            "id": "openai/codex",
            "version": "0.146.0-alpha.9.2"
          },
          "model": {
            "id": "openai/gpt-5.6-sol",
            "configuration": {
              "reasoningEffort": "high"
            }
          }
        }
      ]
    }
  ],
  "targets": [
    {
      "kind": "package",
      "purl": "pkg:pypi/openai-agents",
      "versionRange": "vers:pypi/>=0.9.3"
    }
  ],
  "requirements": [
    {
      "kind": "runtime",
      "id": "python",
      "versionRange": "vers:semver/>=3.10.0"
    },
    {
      "kind": "package",
      "purl": "pkg:pypi/pytest",
      "versionRange": "vers:pypi/>=8.0.0"
    },
    {
      "kind": "skill",
      "source": {
        "type": "git",
        "url": "https://github.com/openai/openai-agents-python.git",
        "tag": "v0.9.3",
        "commit": "2fee7ede4bd1c1f4e65da110ce62b05375cd14af"
      },
      "paths": [
        ".agents/skills/openai-knowledge"
      ]
    }
  ]
}
```

In plain English: this is version 1.0.0 of a skill for projects using the
OpenAI Agents SDK. It works with any harness or operating system because those
target kinds are omitted. It needs Python, pytest, and one other skill pinned
to a specific Git commit. The creator record keeps the human identity and the
agent configuration used for that contribution together.

For a larger working example, see
[`examples/openai-agents-project-audit`](examples/openai-agents-project-audit).

### 3. Validate it

The reference CLI requires Python 3.10 or newer:

```bash
python3 -m pip install skillmeta
skillmeta validate ./agent-project-audit --warnings-as-errors
```

The validator checks the local link, canonical name, cross-file consistency,
redundant frontmatter metadata, and the JSON Schema. It does not fetch or
install declared dependencies.

Validate several skills at once, scan a repository, or emit structured output:

```bash
skillmeta validate ./skills/one ./skills/two
skillmeta validate . --recursive
skillmeta validate . --recursive --format json
```

Diagnostics have stable codes so integrations do not need to parse message
text. The JSON result includes per-skill issues, aggregate counts, structural
validity, and whether the invocation passed its warning policy.

## Targets and dependencies

Targets answer **where does this skill apply?** Requirements answer **what
must already be available for it to work?**

```json
{
  "targets": [
    {"kind": "package", "purl": "pkg:pypi/google-adk"}
  ],
  "requirements": [
    {"kind": "runtime", "id": "python"},
    {"kind": "executable", "id": "git"}
  ]
}
```

Skillmeta can declare package, runtime, executable, and skill dependencies.
Packages use [Package URLs](https://ecma-international.org/publications-and-standards/standards/ecma-427/);
version policies use [VERS](https://www.packageurl.org/docs/vers/introduction).
A skill dependency can select several skill directories from one repository,
and every remote source is pinned to a full commit.

Declaring a dependency is not permission to install or execute it. The agent,
harness, installer, or human remains responsible for satisfying requirements
under its own policy.

Target matching is predictable: options of the same kind are OR choices,
different kinds are combined with AND, and an omitted kind means any value of
that kind is supported. Use `{"kind": "universal"}` alone when the core skill
has no target restrictions.

The [manifest guide](docs/manifest-guide.md) lists every target, requirement,
creator, repository, and extension field with examples and matching rules.

## Agent quickstart

If you are an agent adding Skillmeta to a skill:

1. Read the skill's `SKILL.md` and the [manifest guide](docs/manifest-guide.md)
   before changing either file; use the [v0.3 specification](SPECIFICATION.md)
   for normative details.
2. Create `skill.json` in the skill root and link it with
   `metadata.skillmeta.manifest`.
3. Copy the canonical name, declare the license, and keep it equal to the
   frontmatter license when one exists. Choose `universal` unless verified
   facts justify narrower targets.
4. Declare only load-bearing dependencies. Use versionless PURLs plus VERS,
   and use a full immutable commit for every Git skill source.
5. Record provenance you can verify, then run `skillmeta validate` with
   `--warnings-as-errors`.

Do not guess software-agent or harness versions, invent compatibility
restrictions, follow a moving branch as a dependency, or treat a requirement
as authorization to change the environment.

## Migration

### From a plain Agent Skill

Keep the existing `SKILL.md`. Add the manifest pointer, create `skill.json`,
and start with the facts already known: name, release version, license,
creators, targets, and direct requirements. If the skill has no real target
restriction, use the universal target rather than manufacturing a
compatibility statement.

### From Skillmeta v0.1 or v0.2

Update the schema URI and use typed creator objects. Each creator can now carry
its own affiliations and `createdUsing` list; the old global `createdWith`
field has been removed. When an old global context could belong to several
creators, assign it explicitly rather than guessing.

For v0.1 manifests, also replace `command` requirements with `executable`,
move operating-system applicability into targets, keep PURLs versionless, and
put version policies in VERS. The [migration guide](docs/manifest-guide.md#migrate-from-v02)
shows the v0.2-to-v0.3 transformation.

Published v0.1 and v0.2 manifests remain valid against their immutable
schemas, and the current validator recognizes both versions.

## Scope

Skillmeta is a companion profile, not part of the canonical Agent Skills
specification.

The project defines a manifest and a Python reference validator. It does not
define a registry, installer, dependency solver, lockfile, permission system,
or runtime invocation protocol. Those systems can consume Skillmeta without
being prescribed by it.

Read the [manifest guide](docs/manifest-guide.md), consult the normative
[specification](SPECIFICATION.md), inspect the
[v0.3 JSON Schema](src/skillmeta/schema/v0.3/skill.schema.json), or see
[CONTRIBUTING.md](CONTRIBUTING.md) to help refine the format. Project history
is recorded in the [changelog](CHANGELOG.md), and planned work is kept in the
[roadmap](ROADMAP.md).

## License

MIT
