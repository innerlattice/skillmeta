# Changelog

This file records user-visible changes to the Skillmeta specification and
reference tooling.

## Unreleased

## 0.3.0 - 2026-08-04

### Added

- Typed `Person`, `Organization`, and `SoftwareAgent` creator records.
- Creator-scoped `createdUsing` provenance for harnesses, models, and model
  configuration.
- Stable validator diagnostic codes and JSON output.
- Validation of multiple skill paths and recursive repository scanning.
- Trusted-publishing workflow for PyPI releases.

### Changed

- Creator affiliations and creation contexts are attached to the creator they
  describe.
- Immutable schema tags are separate from reference-tool release tags.
- Project ownership moved to `innerlattice/skillmeta`.

## 0.2.0 - 2026-07-31

### Added

- Target matching across harnesses, packages, and operating systems.
- Package, runtime, executable, and skill requirements.
- Package URL and VERS identifiers for cross-ecosystem dependencies.
- Namespaced extensions and repository provenance.

## 0.1.0 - 2026-07-31

### Added

- Initial `skill.json` manifest profile, JSON Schema, validator, and guide.
