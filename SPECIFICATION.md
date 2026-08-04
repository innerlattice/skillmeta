# Skillmeta Specification

- Version: `0.1.0`
- Status: Experimental
- Profile of: [Agent Skills](https://agentskills.io/specification)

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT**,
and **MAY** are to be interpreted as described by
[BCP 14](https://www.rfc-editor.org/info/bcp14) when they appear in uppercase.

## 1. Purpose and boundary

Skillmeta defines a local `skill.json` companion manifest for an Agent Skill.
It provides machine-readable metadata that does not belong in the
selection-critical `SKILL.md` frontmatter.

Skillmeta:

- preserves canonical Agent Skills discovery and progressive disclosure;
- identifies the skill release, license, and creators;
- records agent-assisted creation provenance without conflating it with human
  identity;
- declares supported targets and hard requirements;
- identifies packages with Package URLs and ranges with VERS;
- pins Git-hosted skill requirements to immutable commits.

Skillmeta does not define a registry, installer, transitive dependency solver,
lockfile, permission system, or execution protocol.

## 2. Package layout and discovery

A conforming package is an Agent Skill directory containing `SKILL.md` and a
local Skillmeta manifest:

```text
example-skill/
├── SKILL.md
├── skill.json
├── scripts/
├── references/
└── assets/
```

`SKILL.md` MUST comply with the Agent Skills specification. The Skillmeta
profile additionally requires:

- `license`: a non-empty scalar;
- `compatibility`: a non-empty scalar human summary;
- `metadata.skillmeta.manifest`: a string URI-reference resolving to the local
  manifest.

The manifest reference:

- MUST be relative to the skill root;
- MUST NOT resolve outside the skill root;
- MUST resolve to a regular JSON file;
- SHOULD be `skill.json`.

Skillmeta does not add `authors` or any other new top-level frontmatter field.
Creator metadata belongs in `skill.json`. The upstream experimental
`allowed-tools` field remains valid Agent Skills frontmatter, but is omitted
from the Skillmeta default example.

Validators MUST warn about unknown top-level `SKILL.md` frontmatter fields.
Unknown keys inside the upstream open `metadata` map MUST NOT warn when their
values are strings.

## 3. Manifest schema and format version

A manifest MUST be UTF-8 JSON and MUST validate against:

```text
https://raw.githubusercontent.com/innerlattice/skillmeta/v0.1.0/src/skillmeta/schema/v0.1/skill.schema.json
```

The manifest uses `manifestSchema` rather than JSON Schema's `$schema`
keyword. `$schema` declares the dialect of a schema document; `skill.json` is
an instance document.

The versioned, immutable `manifestSchema` URI identifies the manifest format.
A separate `manifestVersion` field is therefore prohibited as redundant.

The manifest's `version` field identifies the skill release, not the manifest
format, and MUST follow Semantic Versioning 2.0.0.

## 4. Required fields

| Field | Meaning |
| --- | --- |
| `manifestSchema` | Immutable URI identifying the Skillmeta schema |
| `name` | Agent Skills name; must match `SKILL.md` and its directory |
| `version` | Semantic version of the skill release |
| `license` | License expression or identifier; must match `SKILL.md` |
| `creators` | One or more SPDX creator strings |
| `targets` | One or more supported target alternatives |
| `requirements` | Zero or more conjunctive hard requirements |

Unknown top-level manifest fields are invalid. Future vocabulary requires a
new schema version rather than ungoverned top-level extensions.

## 5. Creators and creation provenance

Each `creators` entry MUST use an SPDX Creator prefix:

- `Person: <name>`
- `Organization: <name>`
- `Tool: <toolidentifier>-<version>`

Example:

```json
{
  "creators": [
    "Person: Aya Hohner",
    "Tool: codex-cli-0.146.0-alpha.9.2"
  ]
}
```

The optional `createdWith` object records structured tool configuration.
`createdWith.harness` identifies the agent harness. `createdWith.model`
identifies the model and MAY contain provider-defined scalar configuration:

```json
{
  "createdWith": {
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
}
```

Reasoning effort belongs to model configuration. Its vocabulary is
provider-defined; consumers MUST NOT assume that values are comparable across
models or providers.

## 6. Targets

`targets` states where the skill is applicable.

- Target entries are alternatives joined by logical OR.
- Conditions inside one target are joined by logical AND.
- `{"kind": "universal"}` MUST appear alone.
- Omitting `versionRange` means any version.

### 6.1 Universal target

```json
{"kind": "universal"}
```

### 6.2 Harness target

```json
{
  "kind": "harness",
  "id": "openai/codex",
  "purl": "pkg:npm/%40openai/codex",
  "versionRange": "vers:npm/>=0.146.0",
  "model": {
    "id": "openai/gpt-5.6-sol",
    "configuration": {
      "reasoningEffort": "high"
    }
  }
}
```

`id` is a profile-defined, lowercase, namespaced harness identifier. `purl`
SHOULD be supplied when the harness has a registered package identity.

### 6.3 Package target

```json
{
  "kind": "package",
  "purl": "pkg:pypi/google-adk",
  "versionRange": "vers:pypi/>=2.0.0"
}
```

## 7. Requirements

All entries in `requirements` are hard requirements joined by logical AND.
Version ranges are retained for package, runtime, command, and operating-system
requirements where a resolver may select a compatible installed release.
Skill requirements do not use version ranges in v0.1.

### 7.1 Package requirement

```json
{
  "kind": "package",
  "purl": "pkg:pypi/pytest",
  "versionRange": "vers:pypi/>=8.0.0"
}
```

PURLs in targets and requirements MAY retain qualifiers or a subpath when
those are part of the package identity. A versioned PURL declares one exact
package release and MUST NOT be combined with `versionRange`.

### 7.2 Runtime, command, operating-system, and capability requirements

```json
{"kind": "runtime", "id": "python", "versionRange": "vers:semver/>=3.10.0"}
{"kind": "command", "id": "git"}
{"kind": "operating-system", "id": "linux"}
{"kind": "capability", "id": "network-access"}
```

Use a package PURL instead when a particular package distribution is the real
contract.

### 7.3 Skill requirements

A skill requirement groups one or more skill-root paths from one immutable Git
source:

```json
{
  "kind": "skill",
  "source": {
    "type": "git",
    "url": "https://github.com/dotnet/skills.git",
    "tag": "v1.0.0",
    "commit": "cb7c10bd32b250459632df9e6fa1350cdaf00b18"
  },
  "paths": [
    "plugins/dotnet-test/skills/test-anti-patterns",
    "plugins/dotnet-test/skills/coverage-analysis"
  ]
}
```

Each path:

- is relative to the repository root;
- identifies a directory containing `SKILL.md`;
- uses `/` separators;
- MUST NOT be absolute, contain `..`, contain `\`, or end in `/`.

The resolver obtains each dependency's name from its `SKILL.md`; requirements
do not duplicate names beside paths.

`source.commit` is REQUIRED and MUST be the repository's full Git object ID.
`source.tag` is an optional human-readable release selector. When both are
present, a resolver MUST verify that the tag resolves to the declared commit.
The commit is authoritative for execution.

A source record intentionally has no branch field. Moving branches are
discovery inputs, not safe execution identities.

Directory paths are coupled to the pinned repository snapshot. Upstream path
changes cannot break an existing pin; changing the source commit is an
explicit dependency upgrade that MAY also update paths.

## 8. Repository provenance

The optional top-level `repository` object locates the current skill:

```json
{
  "repository": {
    "type": "git",
    "url": "https://github.com/owner/repository.git",
    "path": "skills/example-skill"
  }
}
```

It does not contain the commit hash of its own containing revision. Embedding
that hash would be self-referential: modifying the manifest changes the commit
hash. Exact commits belong in external dependency references or installation
receipts.

## 9. Package identity and version ranges

Package identities MUST use
[Package URL](https://ecma-international.org/publications-and-standards/standards/ecma-427/)
(ECMA-427). Version ranges MUST use the companion
[VERS](https://www.packageurl.org/docs/vers/introduction) syntax.

The three common policies are:

| Policy | Representation |
| --- | --- |
| Any version | Versionless PURL; omit `versionRange` |
| Exact version | Versioned PURL such as `pkg:pypi/pytest@8.0.0`; omit `versionRange` |
| Minimum version | Versionless PURL plus `vers:pypi/>=8.0.0` |

Use the PURL ecosystem type for VERS when it has a registered version scheme.
Use another registered VERS type, such as `semver`, only when no package
ecosystem determines the version semantics.

Skillmeta does not define a new PURL type for Agent Skills. Until such a type
is standardized, Git source plus pinned path is the portable skill dependency
identity.

## 10. Manifest versus lockfile

`skill.json` is the authored declarative manifest. Version 0.1 does not define
a `skill-lock.json` because:

- skill dependencies are already pinned to exact commits;
- only direct requirements are declared;
- each depended-on skill owns its own transitive requirements;
- language packages retain their native manifests and lockfiles.

A future lockfile MAY be specified if Skillmeta gains ranges for skills,
automatic conflict resolution, or a generated flattened transitive graph.
That lockfile would record resolver output; it would not replace
`skill.json`.

## 11. Resolution and update safety

Discovery and execution are separate trust planes:

- discovery MAY follow moving channels, tags, feeds, or registries;
- execution MUST use the declared immutable commit;
- promotion to a new commit SHOULD verify provenance, schema conformance,
  compatibility, tests, and policy;
- consumers SHOULD retain the previous known-good pin for rollback.

Pinning controls what executes; it need not control how quickly verified
updates are discovered or promoted. See
[docs/safe-velocity.md](docs/safe-velocity.md).

## 12. Validation

A conforming validator MUST:

1. validate canonical Agent Skills name and description constraints;
2. require the Skillmeta frontmatter profile fields;
3. warn on unknown top-level frontmatter fields;
4. resolve the local manifest without escaping the skill root;
5. validate `skill.json` against the declared schema;
6. require `name` and `license` to match across both files.

Warnings are non-blocking by default. Validators SHOULD offer a mode that
treats warnings as errors for profile-controlled repositories.

Network resolution of tags, commits, packages, and remote skill paths is
outside structural validation and SHOULD be an explicit opt-in operation.

## 13. Evolution

Published schema URIs are immutable. A change that alters accepted documents
or field meaning requires a new versioned schema URI. Consumers encountering
an unknown `manifestSchema` MUST report that the format is unsupported rather
than silently interpreting it as a known version.

## References

- [Agent Skills specification](https://agentskills.io/specification)
- [SPDX Creator](https://spdx.github.io/spdx-spec/v2.3/document-creation-information/)
- [Package URL / ECMA-427](https://ecma-international.org/publications-and-standards/standards/ecma-427/)
- [VERS](https://www.packageurl.org/docs/vers/introduction)
- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12)
- [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)
