# Security Policy

Skill manifests and required skills can influence agent behavior and may
reference executable resources. Treat untrusted skills as untrusted code and
instructions.

Report suspected vulnerabilities privately through GitHub's security advisory
workflow for this repository.

Version `0.3.x` receives security fixes.

Consumers should:

- execute only immutable commits or verified content digests;
- verify tags against declared commits;
- review targets, extensions, and package requirements;
- retain a previous known-good pin;
- never place credentials in `skill.json`.
