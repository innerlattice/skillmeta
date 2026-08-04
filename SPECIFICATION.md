# Skillmeta Specification

- Version: `0.3.0`
- Profile of: [Agent Skills](https://agentskills.io/specification)

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT**,
and **MAY** are to be interpreted as described by
[BCP 14](https://www.rfc-editor.org/info/bcp14) when they appear in uppercase.

## 1. Purpose and boundary

Skillmeta defines a local `skill.json` companion manifest for an Agent Skill.
It keeps selection-critical `SKILL.md` frontmatter small while providing
machine-readable release, license, creator, provenance, applicability, and
dependency metadata.

Skillmeta does not define a registry, installer, dependency solver, lockfile,
permission system, execution protocol, or update process.

## 2. Definitions

- **Agent Skill**: the directory format defined by the Agent Skills
  specification.
- **skill package**: one Agent Skill directory, including `SKILL.md`, its
  manifest, and any bundled resources.
- **manifest**: the Skillmeta JSON document describing a skill package.
- **subject skill**: the skill package described by a particular manifest.
- **consumer**: an agent, harness, validator, catalog, or other software that
  reads a manifest.
- **creator**: a person, organization, or software agent responsible for
  producing the subject skill.
- **creation context**: a harness and/or model configuration associated with a
  particular creator's contribution.
- **harness**: the product that loads a model, skills, and tools to operate an
  agent.
- **target**: an applicability constraint used to decide whether the subject
  skill supports a particular environment or project.
- **requirement**: a resource that must already be available for the subject
  skill to work.

## 3. Package layout and discovery

A conforming skill package is an Agent Skill directory containing `SKILL.md`
and a local manifest:

```text
example-skill/
├── SKILL.md
├── skill.json
├── scripts/
├── references/
└── assets/
```

`SKILL.md` MUST comply with the Agent Skills specification. It links the
manifest through the upstream string-valued `metadata` map:

```yaml
metadata:
  skillmeta.manifest: skill.json
```

Keeping the manifest local makes it part of the same versioned skill package,
allows offline validation, and avoids making metadata availability depend on a
remote service. The explicit pointer lets existing packaging conventions place
the file differently when necessary.

The manifest reference:

- MUST be a path relative to the skill package root;
- MUST NOT resolve outside the skill package root;
- MUST resolve to a regular JSON file;
- SHOULD be named `skill.json`.

Skillmeta adds no other frontmatter requirements. In particular, the upstream
`compatibility` field remains optional.

## 4. Manifest format

A v0.3 manifest MUST be UTF-8 JSON and MUST validate against:

```text
https://raw.githubusercontent.com/innerlattice/skillmeta/v0.3.0/src/skillmeta/schema/v0.3/skill.schema.json
```

The `version` field identifies the subject skill release and MUST follow
Semantic Versioning 2.0.0.

| Required field | Meaning |
| --- | --- |
| `manifestSchema` | Immutable URI identifying the Skillmeta schema |
| `name` | Canonical Agent Skills name |
| `version` | Semantic version of the subject skill release |
| `license` | SPDX expression, license identifier, or bundled license reference |
| `creators` | One or more typed creator agents and their provenance |
| `targets` | Supported environments or project contexts |
| `requirements` | Resources required for the skill to work |

Unknown top-level fields are invalid. Extension data belongs in `extensions`.

## 5. Creators and creation provenance

A creator is an agent that bears responsibility for producing the subject
skill. The creator model uses the W3C PROV agent categories `Person`,
`Organization`, and `SoftwareAgent`; its person and organization properties
follow the common CodeMeta and Citation File Format conventions where they fit
the Skillmeta contract. The `createdUsing` name follows SPDX 3 CreationInfo,
while Skillmeta nests the relationship so each context stays attached to the
creator it describes.

Each creator MUST be an object with `type` and `name`. Creator order is the
display and credit order.

| Field | Person | Organization | SoftwareAgent |
| --- | --- | --- | --- |
| `type` | REQUIRED: `Person` | REQUIRED: `Organization` | REQUIRED: `SoftwareAgent` |
| `name` | REQUIRED | REQUIRED | REQUIRED |
| `id` | Optional absolute URI | Optional absolute URI | REQUIRED `<publisher>/<product>` ID |
| `version` | Prohibited | Prohibited | REQUIRED product version |
| `email` | Optional | Optional | Prohibited |
| `url` | Optional absolute URI | Optional absolute URI | Optional absolute URI |
| `affiliations` | Optional list | Prohibited | Prohibited |
| `createdUsing` | Optional list | Optional list | Optional list |

A person or organization `id` SHOULD be a stable public identity URI when one
is available, such as an ORCID, ROR, or authoritative profile. Contact fields
MUST NOT contain private information without the subject's consent.

A SoftwareAgent `id` is the stable, lowercase, publisher-scoped product
identifier `<publisher>/<product>`. It names the publisher's product, not an
executable filename, application bundle, installation path, or package-manager
alias. Its version MUST come from the product's version command, About screen,
or authoritative publisher website; consumers MUST NOT invent a missing
version.

### 5.1 Affiliations

Each `affiliations` item is an organization object with a REQUIRED `name` and
optional `id`, `email`, and `url`. `id` and `url` MUST be absolute URIs.

An affiliation relates an organization to a person's contribution to the
subject skill; it does not assert a permanent relationship or make that
organization a separate creator. An organization that should receive direct
credit MUST also appear as its own `Organization` creator.

### 5.2 Creation contexts

`createdUsing` is nested under the creator whose contribution it describes. It
MUST be a non-empty list of creation contexts; the same creator MAY declare
more than one context. A context MUST contain at least one of `harness` or
`model`.

```json
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
```

A harness requires a stable `<publisher>/<product>` `id` and a non-empty
`version`. A model requires a stable `id`; its optional `configuration` object
MAY contain provider-defined string, number, or boolean values.

`model.configuration.reasoningEffort` SHOULD be included when the model uses
such a setting and the harness exposes it. It MAY be omitted when the setting
is inapplicable, unavailable, or withheld for privacy or security. Its
vocabulary is provider-defined; values are not necessarily comparable between
models or providers.

Use a `Person` or `Organization` with `createdUsing` when that party remains
responsible for agent-assisted work. Use `SoftwareAgent` when the software
system itself is directly credited. A SoftwareAgent MAY also declare
`createdUsing`, for example when a custom agent ran inside another harness.

## 6. Targets

`targets` describes where the subject skill is applicable. Consumers match
each target only against the corresponding kind of environment information:
harness targets against the active harness, package targets against the
subject project's packages, and operating-system targets against the host
operating system.

Target matching follows these rules:

1. `{"kind": "universal"}` MUST appear alone and imposes no target
   constraints.
2. Multiple targets of the same kind are alternatives joined by logical OR.
3. Present target kinds are joined by logical AND.
4. Omission of a target kind means any value of that kind is supported.
5. Omission of `versionRange` means any version is supported.

For example, two harness targets and two package targets mean:

```text
(first harness OR second harness) AND (first package OR second package)
```

An omitted operating-system kind means any operating system is supported.

### 6.1 Universal target

```json
{"kind": "universal"}
```

A universal skill's core instructions MUST NOT require a particular harness,
package, or operating system. It MAY contain optional adapters for particular
harnesses, but those adapters cannot be required to use the core skill.
Universality describes applicability, not identical performance across every
model or future model version.

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

Harness IDs use the same stable `<publisher>/<product>` form as SoftwareAgent
creator identifiers. `purl` SHOULD be supplied when the harness has a registered
package identity. An optional model narrows the harness target further.

### 6.3 Package target

```json
{
  "kind": "package",
  "purl": "pkg:pypi/google-adk",
  "versionRange": "vers:pypi/>=2.0.0"
}
```

A package target identifies a library, framework, or platform that is the
subject of the skill. It does not state that the package is installed in the
skill's execution environment; use a package requirement for that contract.

### 6.4 Operating-system target

```json
{
  "kind": "operating-system",
  "id": "macos",
  "versionRange": "vers:generic/>=14"
}
```

Common IDs include `linux`, `macos`, and `windows`. Consumers compare IDs
exactly and evaluate `versionRange` using its declared VERS scheme.

## 7. Requirements

All entries in `requirements` are hard requirements joined by logical AND.
Requirements declare prerequisites only: they do not authorize a consumer to
install packages, download skills, execute programs, change the environment,
or grant permissions. Installation and authorization remain the responsibility
of the skill, agent, harness, package manager, or another policy-controlled
tool.

| Kind | Meaning |
| --- | --- |
| `package` | A particular installable artifact identified by PURL |
| `runtime` | A semantic execution environment such as Python or Node.js |
| `executable` | A program name that must resolve in the process environment |
| `skill` | One or more Agent Skills from an immutable Git revision |

Use a package requirement when the distribution identity matters. Use a
runtime requirement when the contract is the language environment regardless
of how it was installed. An executable requirement identifies a real program,
not a shell alias or function; if its package or version matters, declare the
corresponding package requirement as well.

Examples:

```json
[
  {"kind": "package", "purl": "pkg:pypi/pytest", "versionRange": "vers:pypi/>=8.0.0"},
  {"kind": "runtime", "id": "python", "versionRange": "vers:semver/>=3.10.0"},
  {"kind": "executable", "id": "git"}
]
```

Operating-system applicability belongs in `targets`. Experimental capability
vocabularies belong in namespaced extensions until a stable ontology emerges;
capability declarations never grant authority.

### 7.1 Skill requirements

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

Dependency names are read from each referenced `SKILL.md` and are not repeated
beside the paths.

`source.commit` is REQUIRED and MUST be the repository's full Git object ID.
`source.tag` is an optional human-readable release selector. When both are
present, a resolver MUST verify that the tag resolves to the declared commit.
The commit is authoritative. Branches are not valid immutable identities.

Directory paths are relative to the pinned snapshot. An upstream directory
change cannot alter an existing pin; a dependency update MAY change both the
commit and paths.

## 8. Package identity and version ranges

Package identities MUST use [Package URL](https://ecma-international.org/publications-and-standards/standards/ecma-427/)
(ECMA-427). Version ranges MUST use
[VERS](https://www.packageurl.org/docs/vers/introduction).

PURLs in targets and requirements MUST be versionless. `versionRange` carries
all version policy:

| Policy | Representation |
| --- | --- |
| Any version | Omit `versionRange` |
| Exact version | `vers:pypi/8.0.0` |
| Minimum version | `vers:pypi/>=8.0.0` |

Use the PURL ecosystem type for VERS when it has a registered version scheme.
Use another registered VERS scheme only when no package ecosystem determines
the version semantics. Qualifiers and subpaths MAY remain in the versionless
PURL when they are part of package identity.

Skillmeta does not define a PURL type for Agent Skills. Git source, immutable
commit, and repository-relative paths provide the skill dependency identity.

## 9. Repository provenance

The optional `repository` object locates the subject skill:

```json
{
  "repository": {
    "type": "git",
    "url": "https://github.com/owner/repository.git",
    "path": "skills/example-skill"
  }
}
```

The subject skill cannot embed the commit hash of its own containing revision
because changing the manifest would change that hash. Exact commits belong in
external dependency references or installation records.

## 10. Extensions

The optional `extensions` object carries namespaced experimental or
domain-specific data without claiming that it is part of the core vocabulary.
Each key MUST be an absolute URI controlled by the extension's publisher; the
URI does not need to resolve. Each value MAY be any JSON value.

```json
{
  "extensions": {
    "https://example.org/skillmeta/capabilities/v1": {
      "declares": ["network-read"]
    }
  }
}
```

Extensions MUST NOT override core fields or grant permissions. A consumer that
does not recognize an extension MUST ignore it or reject it according to local
policy, without assigning it core semantics.

## 11. Updates

Skill dependencies SHOULD use immutable commits. Agents and maintainers are
encouraged to build update tooling that finds newer revisions, runs security
and compatibility checks, and proposes a new commit pin; Skillmeta does not
define that update process.

## 12. Validation

A conforming Skillmeta validator MUST:

1. validate the canonical Agent Skills name and its directory match;
2. require `metadata.skillmeta.manifest` to identify a local manifest inside
   the skill package;
3. validate the manifest against its declared Skillmeta schema;
4. require manifest `name` to match `SKILL.md`;
5. require manifest `license` to match `SKILL.md` when frontmatter declares a
   license;
6. warn when frontmatter duplicates metadata owned by the manifest;
7. require a duplicated `version` to match the manifest version.

Redundancy warnings apply to `version`, `author`, `authors`, `creators`,
`createdWith`, `createdUsing`, `repository`, `targets`, `requirements`, and
`extensions` when they appear either at the top level or inside the
frontmatter `metadata` map.
The intentional `name`, optional `license`, and manifest pointer are not
redundancy warnings. Other frontmatter fields are outside Skillmeta validation
and MUST NOT produce unknown-field warnings.

Warnings are non-blocking by default. Validators SHOULD offer a mode that
treats warnings as errors. Network resolution of tags, commits, packages, and
remote skill paths is outside structural validation and SHOULD be opt-in.

## 13. Evolution

Published schema URIs are immutable. A change that alters accepted documents
or field meaning requires a new versioned schema URI. Consumers encountering
an unknown `manifestSchema` MUST report it as unsupported.

## References

- [Agent Skills specification](https://agentskills.io/specification)
- [W3C PROV-O](https://www.w3.org/TR/prov-o/)
- [SPDX 3.0.1 CreationInfo](https://spdx.github.io/spdx-spec/v3.0.1/model/Core/Classes/CreationInfo/)
- [CodeMeta terms](https://codemeta.github.io/terms/)
- [Citation File Format schema guide](https://github.com/citation-file-format/citation-file-format/blob/main/schema-guide.md)
- [SPDX license expressions](https://spdx.github.io/spdx-spec/v2.3/SPDX-license-expressions/)
- [Package URL / ECMA-427](https://ecma-international.org/publications-and-standards/standards/ecma-427/)
- [VERS](https://www.packageurl.org/docs/vers/introduction)
- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12)
- [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)
