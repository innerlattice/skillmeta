# Safe Velocity: Immutable Execution, Rapid Promotion

AI agent ecosystems change too quickly for manual dependency review to be the
only update mechanism. They are also too powerful to execute mutable upstream
content safely.

The apparent trade-off is not "security versus innovation." It is a boundary
problem: discovery, evaluation, promotion, and execution have different trust
requirements and should not share one mutable reference.

## First-principles invariants

Three properties matter:

1. **Reproducibility:** the same declared input produces the same skill
   content.
2. **Trust:** executed content has known provenance and passed an explicit
   acceptance policy.
3. **Freshness:** improvements and security fixes can be adopted with low
   latency.

No system can safely guarantee all three by executing an unreviewed moving
reference. What has to give is immediate execution of arbitrary upstream
change—not freshness itself.

## Two trust planes

### Discovery plane

The discovery plane may track fast-moving sources:

- release feeds and registries;
- Git tags and branches;
- publisher advisories;
- compatibility and revocation metadata.

Its job is to notice change and assemble evidence. Discovery is not permission
to execute.

### Execution plane

The execution plane consumes immutable, reviewed identities:

- Git commits;
- content digests;
- signed release artifacts;
- a previously accepted local snapshot.

Its job is deterministic use and rollback.

## Promotion pipeline

An ideal update system promotes a discovered release to an executable pin:

```text
moving release channel
        ↓
resolve immutable commit or digest
        ↓
verify publisher identity and attestations
        ↓
inspect semantic and behavioral diff
        ↓
run schema, compatibility, security, and task evaluations
        ↓
apply trust-tier policy
        ↓
canary or sandbox
        ↓
promote new pin with previous pin retained for rollback
```

The pin can be updated within minutes when the evidence is strong. The speed
comes from automating promotion, not from allowing mutable execution.

## Risk-adjusted automation

A practical policy can distinguish:

- trusted publisher + signed patch + passing evaluations: automatic promotion;
- compatible minor release: automated canary followed by promotion;
- major release or material behavioral diff: explicit review;
- unsigned, revoked, or provenance-changing release: quarantine;
- emergency security advisory: accelerated promotion or immediate rollback.

Trust is contextual rather than permanent. Publisher history, signature
validity, evaluation coverage, requested capabilities, and behavioral change
all affect the policy.

## Feedback and recovery

Fast systems need:

- continuous update checks rather than long manual polling cycles;
- machine-readable compatibility and provenance;
- release attestations and a transparency or audit log;
- revocation signals;
- runtime monitoring against declared behavior;
- one-step rollback to a previous accepted pin.

These mechanisms turn pinning from a maintenance bottleneck into a stable
execution boundary.

## Skillmeta v0.1 boundary

Skillmeta v0.1 encodes only the durable minimum:

- optional human-readable tag;
- required immutable commit;
- repository-relative skill paths;
- direct requirements;
- machine-readable targets and package constraints.

It deliberately defers registries, signed attestations, update policy,
behavioral evaluations, lockfiles, revocation, and promotion automation. Those
systems can evolve independently without weakening the v0.1 rule that
execution resolves to immutable content.
