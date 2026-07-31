# Skillmeta manifest guide

This guide explains every field in a Skillmeta v0.3 manifest. It is the
practical companion to the [normative specification](../SPECIFICATION.md) and
the [JSON Schema](../src/skillmeta/schema/v0.3/skill.schema.json).

## Contents

- [Start a manifest](#start-a-manifest)
- [Describe creators](#describe-creators)
- [Declare targets](#declare-targets)
- [Declare requirements](#declare-requirements)
- [Identify packages and versions](#identify-packages-and-versions)
- [Locate the skill repository](#locate-the-skill-repository)
- [Add extension data](#add-extension-data)
- [Validate and migrate](#validate-and-migrate)

## Start a manifest

Place `skill.json` beside `SKILL.md`, then add this pointer to the standard
frontmatter `metadata` map:

```yaml
metadata:
  skillmeta.manifest: skill.json
```

A minimal universal manifest looks like this:

```json
{
  "manifestSchema": "https://raw.githubusercontent.com/ayahohner/skillmeta/v0.3.0/src/skillmeta/schema/v0.3/skill.schema.json",
  "name": "example-skill",
  "version": "1.0.0",
  "license": "MIT",
  "creators": [
    {
      "type": "Person",
      "name": "Example Maintainer"
    }
  ],
  "targets": [
    {"kind": "universal"}
  ],
  "requirements": []
}
```

### Top-level fields

| Field | Required | Value |
| --- | --- | --- |
| `manifestSchema` | Yes | The immutable v0.3 schema URI shown above |
| `name` | Yes | The canonical Agent Skills name: 1–64 lowercase letters, numbers, or single hyphen-separated words; it must match `SKILL.md` and the skill directory |
| `version` | Yes | The skill release in Semantic Versioning form |
| `license` | Yes | An SPDX expression, SPDX identifier, or reference to bundled license terms |
| `creators` | Yes | A non-empty list of creator objects |
| `repository` | No | The Git repository and path containing this skill |
| `targets` | Yes | A non-empty list describing where the skill applies |
| `requirements` | Yes | A list of prerequisites; use `[]` when there are none |
| `extensions` | No | Namespaced data outside the core specification |

Unknown top-level fields are invalid. Put experimental or domain-specific data
under `extensions` instead.

## Describe creators

`creators` records the people, organizations, and software agents responsible
for producing the skill. Each creator carries its own identity, affiliations,
and agent-assisted creation details, so provenance does not become detached
from the participant it describes.

Skillmeta uses the three agent types defined by
[W3C PROV](https://www.w3.org/TR/prov-o/):

| `type` | Use it for |
| --- | --- |
| `Person` | An individual creator |
| `Organization` | A company, team, institution, or other organization credited directly |
| `SoftwareAgent` | An autonomous or directly credited software system |

The person and organization fields follow
[CodeMeta](https://codemeta.github.io/terms/) and
[Citation File Format](https://github.com/citation-file-format/citation-file-format/blob/main/schema-guide.md)
conventions where they fit. `createdUsing` follows
[SPDX 3 CreationInfo](https://spdx.github.io/spdx-spec/v3.0.1/model/Core/Classes/CreationInfo/)
terminology, but is nested here so a harness/model context remains attached to
the creator it describes.

Creator order is the display and credit order.

### Creator fields

| Field | Person | Organization | SoftwareAgent | Meaning |
| --- | --- | --- | --- | --- |
| `type` | Required | Required | Required | One of the three exact values above |
| `name` | Required | Required | Required | Human-readable name |
| `id` | Optional URI | Optional URI | Required product ID | Stable identity; use an ORCID, ROR, profile, or other authoritative URI when available |
| `version` | Not allowed | Not allowed | Required | Software-agent version reported by the product |
| `email` | Optional | Optional | Not allowed | Contact address; omit private information |
| `url` | Optional | Optional | Optional | Public profile, organization page, or product page |
| `affiliations` | Optional | Not allowed | Not allowed | Organizations associated with a person |
| `createdUsing` | Optional | Optional | Optional | Agent harness and model contexts associated with this creator |

A SoftwareAgent `id` uses the stable, lowercase form
`<publisher>/<product>`, such as `openai/codex`. It names the publisher's
product, not an executable filename, application bundle, installation path, or
package-manager alias.

Do not guess a SoftwareAgent or harness version. If it cannot be verified from
the product, omit that optional provenance context; a directly credited
SoftwareAgent cannot be declared until its version is known.

### Affiliations

An affiliation is an organization object nested under a `Person`:

```json
{
  "type": "Person",
  "name": "Maya Chen",
  "id": "https://example.org/people/maya-chen",
  "affiliations": [
    {
      "name": "Northstar Research",
      "id": "https://example.org/organizations/northstar-research",
      "url": "https://example.org/northstar"
    }
  ]
}
```

| Affiliation field | Required | Meaning |
| --- | --- | --- |
| `name` | Yes | Organization name |
| `id` | No | Stable absolute URI, preferably a recognized organization identifier |
| `email` | No | Public contact address |
| `url` | No | Organization website |

Affiliation records an organization associated with the person's contribution
to this skill; it does not claim a permanent relationship or give the
organization separate creator credit. Add a second `Organization` creator when
the organization itself should be credited.

### Agent-assisted creation

`createdUsing` is a list because one creator may use more than one harness or
model while producing a skill:

```json
{
  "type": "Person",
  "name": "Maya Chen",
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

Each `createdUsing` item contains at least one of:

| Field | Required | Meaning |
| --- | --- | --- |
| `harness` | No | The agent product used during creation |
| `model` | No | The model and relevant configuration used during creation |

Harness fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `id` | Yes | Stable `<publisher>/<product>` identifier |
| `version` | Yes | Product version from its version command, About screen, or publisher website |

Model fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `id` | Yes | Stable model identifier, preferably publisher-scoped |
| `configuration` | No | Provider-defined scalar settings that materially describe the run |

`configuration.reasoningEffort` should be included when the model uses such a
setting and the harness exposes it. It may be omitted when it does not apply,
is unavailable, or should be withheld for privacy or security. Values are
provider-defined and are not necessarily comparable across models.

Use a `Person` or `Organization` with `createdUsing` when that party remains
responsible for agent-assisted work. Use `SoftwareAgent` when the software
system itself is being credited as a creator. A SoftwareAgent can also carry
`createdUsing` when, for example, a custom agent ran inside another harness.

## Declare targets

Targets answer: **Where does this skill apply?** They are applicability
constraints, not installation instructions.

Matching follows five rules:

1. `universal` appears alone and adds no constraints.
2. Targets of the same kind are alternatives joined by OR.
3. Different target kinds are joined by AND.
4. An omitted kind means any value of that kind is supported.
5. An omitted `versionRange` means any version is supported.

Two harness targets and two package targets therefore mean:

```text
(first harness OR second harness) AND (first package OR second package)
```

### Universal target

```json
{"kind": "universal"}
```

| Field | Required | Value |
| --- | --- | --- |
| `kind` | Yes | `universal` |

A universal skill must be usable without a particular harness, package, or
operating system. Optional harness-specific adapters are fine as long as the
core skill does not depend on them.

### Harness target

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

| Field | Required | Meaning |
| --- | --- | --- |
| `kind` | Yes | `harness` |
| `id` | Yes | Stable `<publisher>/<product>` harness identifier |
| `purl` | No | Versionless Package URL when the harness has a package identity |
| `versionRange` | No | Accepted harness versions in VERS form |
| `model` | No | A model and configuration that narrow the target further |

### Package target

```json
{
  "kind": "package",
  "purl": "pkg:pypi/google-adk",
  "versionRange": "vers:pypi/>=2.0.0"
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `kind` | Yes | `package` |
| `purl` | Yes | Versionless identity of the library, framework, or platform the skill concerns |
| `versionRange` | No | Supported package versions |

A package target describes the subject of the skill. It does not say the
package is available where the skill runs; add a package requirement when that
is also necessary.

### Operating-system target

```json
{
  "kind": "operating-system",
  "id": "macos",
  "versionRange": "vers:generic/>=14"
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `kind` | Yes | `operating-system` |
| `id` | Yes | Stable lowercase identifier such as `linux`, `macos`, or `windows` |
| `versionRange` | No | Supported operating-system versions |

Consumers compare operating-system IDs only with the host operating system;
they do not compare an OS target with a harness or package.

## Declare requirements

Requirements answer: **What must already be available for this skill to
work?** Every requirement is mandatory, so the list is joined by AND.

| `kind` | Use it for |
| --- | --- |
| `package` | An installable artifact with a Package URL |
| `runtime` | A language or semantic execution environment |
| `executable` | A program name that must resolve in the process environment |
| `skill` | One or more Agent Skills from an immutable Git revision |

A requirement does not authorize a consumer to install, download, execute, or
grant access to anything. A human, agent, harness, installer, or other
policy-controlled tool must decide how to satisfy it.

### Package requirement

```json
{
  "kind": "package",
  "purl": "pkg:pypi/pytest",
  "versionRange": "vers:pypi/>=8.0.0"
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `kind` | Yes | `package` |
| `purl` | Yes | Versionless package identity |
| `versionRange` | No | Required versions |

### Runtime requirement

```json
{
  "kind": "runtime",
  "id": "python",
  "versionRange": "vers:semver/>=3.10.0"
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `kind` | Yes | `runtime` |
| `id` | Yes | Stable lowercase runtime identifier |
| `versionRange` | No | Required runtime versions |

Use this when the semantic runtime matters regardless of how it was installed.

### Executable requirement

```json
{
  "kind": "executable",
  "id": "git"
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `kind` | Yes | `executable` |
| `id` | Yes | Program name expected in the process environment |

The executable must be a real program, not a shell alias or function. When its
distribution or version matters, declare the corresponding package requirement
as well.

### Skill requirement

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

| Field | Required | Meaning |
| --- | --- | --- |
| `kind` | Yes | `skill` |
| `source` | Yes | Immutable Git source |
| `paths` | Yes | One or more skill-root directories in that repository snapshot |

Git source fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `type` | Yes | `git` |
| `url` | Yes | Absolute repository URI |
| `commit` | Yes | Full 40- or 64-character Git object ID; this is authoritative |
| `tag` | No | Human-readable release tag that must resolve to `commit` |

Each path is relative to the repository root and identifies a directory
containing `SKILL.md`. Paths use `/`, cannot be absolute, cannot escape through
`..`, and cannot end with `/`. One requirement can select several skills from
the same pinned repository; use another requirement for a different source.

## Identify packages and versions

Package identities use [Package URL](https://ecma-international.org/publications-and-standards/standards/ecma-427/)
(ECMA-427). Version policies use
[VERS](https://www.packageurl.org/docs/vers/introduction).

Keep the PURL versionless and put the entire version policy in `versionRange`:

| Policy | Example |
| --- | --- |
| Any version | Omit `versionRange` |
| Exact version | `vers:pypi/8.0.0` |
| Minimum version | `vers:pypi/>=8.0.0` |
| Bounded range | A valid VERS expression for that ecosystem |

Use the same ecosystem type in the PURL and VERS value when that ecosystem has
registered version semantics. Qualifiers and subpaths may remain in a
versionless PURL when they are part of package identity.

Skill dependencies do not have a Skillmeta-specific PURL type. Their identity
is the Git repository, immutable commit, and repository-relative paths.

## Locate the skill repository

`repository` tells consumers where the subject skill lives:

```json
{
  "repository": {
    "type": "git",
    "url": "https://github.com/owner/repository.git",
    "path": "skills/example-skill"
  }
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `type` | Yes | `git` |
| `url` | Yes | Absolute repository URI |
| `path` | Yes | Skill-root path relative to the repository root |

The manifest does not contain the commit of its own enclosing repository: a
commit changes when the manifest changes. Exact revisions belong in external
dependency references or installation records.

## Add extension data

`extensions` holds experimental or domain-specific data without assigning it
core meaning:

```json
{
  "extensions": {
    "https://example.org/skillmeta/capabilities/v1": {
      "declares": ["network-read"]
    }
  }
}
```

Each key must be an absolute URI controlled by the extension publisher. The
URI does not have to resolve, and each value may be any JSON value. Extensions
cannot override core fields or grant permissions. Consumers may ignore an
unknown extension or reject it under local policy, but must not invent core
semantics for it.

## Validate and migrate

Install the reference validator and check a skill directory:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install "git+https://github.com/ayahohner/skillmeta.git@v0.3.0"
.venv/bin/skillmeta validate ./example-skill --warnings-as-errors
```

The validator checks the local manifest link, canonical name and directory,
frontmatter consistency, schema structure, and redundant frontmatter fields.
It does not resolve remote tags, fetch dependencies, install packages, or run
declared executables.

### Migrate from v0.2

1. Change `manifestSchema` to the v0.3 URI.
2. Replace each SPDX Creator string with a typed creator object.
3. Move the old global `createdWith` object into the responsible creator as
   `createdUsing`, and wrap it in a list.
4. When a global creation context could belong to several creators, assign it
   explicitly; do not copy or guess.

For example:

```json
{
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
            "id": "openai/gpt-5.6-sol"
          }
        }
      ]
    }
  ]
}
```

Published v0.1 and v0.2 manifests remain valid against their immutable schemas,
and the current reference validator continues to recognize both versions.
