# Adversarial Relation Corpus

## Purpose

This document defines the initial adversarial corpus used to exercise
relation-aware testing of SV-Witness violation-witness validators.

The corpus provides deterministic semantic test inputs. It does not define
validator behavior and it does not classify validator implementations as
correct or defective.

The word adversarial refers to deliberately selected boundary and stress cases
for the supported witness profile. It does not mean that a case is known to
trigger a validator defect.

## Scope

The initial corpus is restricted to the established project profile:

- SV-Witness 2.2;
- one YAML `violation_sequence` entry;
- sequential C;
- `unreach-call`;
- one final segment, which is the last segment;
- normal follow segments;
- assumption and target waypoints only;
- follow and avoid actions only; and
- absent `thread_id` or `thread_id: 0`, both denoting the main thread.

The corpus does not extend the semantic profile.

## Corpus Unit

The semantic center of one corpus entry is a
`TransformationLocalEvidence` value.

Let

`R = (tau, W, A, W_prime, relation)`

denote that relation-bearing transformation application.

A corpus entry augments `R` with deterministic experimental metadata and the
program bytes required to materialize the verification task.

Conceptually, one entry is

`C = (case_id, description, dimensions, program_files, metadata, R)`.

The corpus does not introduce a second representation of the semantic relation.

`TransformationLocalEvidence` remains the relation object used by the
transformation and reduction layers.

## Stable Case Identity

Every corpus entry has an explicit stable `case_id`.

A case identifier:

- is unique within the corpus;
- uses a lowercase ASCII slug;
- is independent of Python object identity;
- is independent of Python `hash()`;
- is independent of filesystem enumeration order; and
- does not change merely because the corpus is evaluated by another validator.

Python hashes may be used for transient in-process collections. They are not
persistent corpus identifiers.

Corpus enumeration is ordered by `case_id`.

## Stress Dimensions

Each case records one or more descriptive stress dimensions.

A stress dimension records why the case is present. It is not a validator
expectation.

The initial vocabulary covers:

- explicit-main-thread canonicalization;
- implicit-main-thread canonicalization;
- exact relation;
- broadening relation;
- normal-segment avoid removal;
- final-segment avoid removal;
- adjacent avoid assumptions;
- repeated equal avoid assumptions;
- distinguished avoid at an early position;
- distinguished avoid at an interior position;
- distinguished avoid at a late position;
- relation cases with non-distinguished reducible avoids; and
- relation cases locally irreducible under the current reduction neighborhood.

The vocabulary may be extended when a new corpus case exercises a distinct
supported boundary.

## No Validator Ground Truth

A corpus entry does not contain an expected validator result.

In particular, it does not contain fields equivalent to:

- expected accept;
- expected reject;
- expected timeout;
- expected bug;
- known unsound;
- expected `NONEMPTY`;
- expected `EMPTY`;
- expected `NO_CLAIM`; or
- expected oracle classification.

Those observations belong to later validator-specific evaluation.

A semantic relation is not an operational validator expectation.

## Candidate-Domain Boundary

Corpus membership does not establish candidate admission.

Construction of a `TransformationLocalEvidence` object establishes only the
local transformation evidence implemented by that model.

Admission of the source witness to the candidate domain remains an independent
premise.

Materializing a witness does not establish candidate admission.

Schema conformance does not establish represented-execution non-emptiness.

Successful execution by a validator does not retroactively become semantic
evidence for the relation.

## Why Materialization Is Part of the Corpus Layer

A validator cannot consume only the internal Python model.

A concrete validation case requires bytes representing the verification task
and the two related witnesses.

The corpus layer therefore defines a narrow deterministic materialization boundary.

This boundary is intentionally smaller than a general SV-Witness serializer.

It exists only to make corpus entries reproducibly consumable by later
experiments.

## Materialized Artifact Bundle

Materializing one corpus entry produces an immutable logical bundle containing:

- every input program file required by the verification task;
- `property.prp`;
- `source.yml`; and
- `transformed.yml`.

The materializer returns relative artifact names and bytes.

It does not choose an experiment directory and does not launch a process.

Filesystem placement and validator invocation remain responsibilities of the
evaluation layer.

## Program Bytes and Task Binding

Program bytes are part of the corpus definition.

For every `ProgramInput` in the relation task:

1. a corresponding corpus program artifact exists;
2. the relative path equals the `ProgramInput.path`;
3. SHA-256 of the exact artifact bytes equals the recorded
   `ProgramInput.sha256`; and
4. witness locations use filenames belonging to the task input set.

This check establishes byte-level task correspondence.

It does not establish that every source location is semantically correct for
the referenced C construct.

## Property Artifact

`property.prp` is derived deterministically from
`VerificationTask.specification.text`.

The materialized bytes are the exact specification text followed by one newline.

The property artifact introduces no second specification value.

## Witness Artifact Metadata

The internal witness model intentionally excludes SV-Witness provenance
metadata.

Corpus materialization therefore supplies a small artifact-metadata record for
the source witness and another for the transformed witness.

The metadata required for each artifact includes:

- format version `2.2`;
- an explicit stable UUID;
- an explicit stable creation time;
- producer name;
- producer version; and
- the verification task derived from the relation case.

Source and transformed witness UUIDs are distinct.

UUIDs and timestamps are corpus data. They are not generated randomly or from
the current clock during materialization.

This makes repeated materialization byte-for-byte deterministic.

## SV-Witness 2.2 Mapping

The materializer emits exactly one `violation_sequence` entry.

Task metadata is derived from the existing `VerificationTask`:

- `input_files` from ordered program inputs;
- `input_file_hashes` from the recorded SHA-256 digests;
- `specification` from the task specification;
- `data_model` from the execution context; and
- `language` from the execution context.

The supported witness mapping is intentionally narrow.

For an assumption waypoint the materializer emits:

- type `assumption`;
- action `follow` or `avoid`;
- constraint value;
- constraint format `c_expression`;
- location; and
- `thread_id` only when it is explicitly present in the internal model.

For a target waypoint the materializer emits:

- type `target`;
- action `follow`;
- location; and
- `thread_id` only when explicitly present.

The distinction between absent `thread_id` and explicit `thread_id: 0` is
preserved in the artifact bytes.

That distinction is necessary for the exact main-thread transformations.

## Deterministic YAML Emission

The corpus layer does not add a general-purpose YAML parser.

The corpus layer also does not expose a general-purpose SV-Witness serializer.

The corpus materializer uses a deterministic emitter for the exact supported
corpus model.

The emitter:

- uses a fixed field order;
- uses fixed indentation;
- encodes strings deterministically;
- emits no comments;
- emits no aliases or anchors;
- emits no environment-dependent data; and
- terminates text artifacts with exactly one newline.

The same corpus entry therefore produces identical witness bytes across
repeated materializations.

Unsupported witness constructs are outside this emitter contract.

## Single Source of Truth

The internal relation case is the semantic source of witness content.

`source.yml` is rendered from `TransformationLocalEvidence.source`.

`transformed.yml` is rendered from
`TransformationLocalEvidence.transformed`.

The transformed artifact is not independently edited.

The task block in both witness artifacts is rendered from
`TransformationLocalEvidence.task`.

This prevents the corpus from maintaining independent handwritten semantic
copies of the same relation case.

## Relation Construction

Each initial corpus case uses one of the transformation families already
supported by transformation-local evidence:

- explicit main-thread canonicalization;
- implicit main-thread canonicalization; or
- selected avoid removal.

The transformed witness is produced by applying the corresponding existing
transformation to the source witness.

`TransformationLocalEvidence` then independently checks the local application
relationship.

The corpus must not construct a source witness and transformed witness as two
unrelated handwritten values and merely label them as related.

## Initial Task Strategy

The initial corpus prefers a small shared sequential C `unreach-call` task.

Using a common task where possible reduces unrelated experimental variation.

Different tasks are introduced only when a stress dimension cannot be expressed
faithfully with the shared task.

Every program used by the corpus is stored as deterministic bytes in the corpus
definition and is covered by task-hash checks.

## Initial Coverage Families

The initial corpus includes cases covering both exact and broadening relations.

At minimum it contains:

1. absent main-thread identifiers transformed to explicit zero;
2. explicit zero main-thread identifiers transformed to absence;
3. a selected normal-segment avoid with no non-distinguished avoid remaining;
4. a selected normal-segment avoid with earlier and later neighboring avoids;
5. a selected avoid in the final segment;
6. repeated equal avoid assumptions that exercise duplicate reduction
   neighborhoods;
7. an exact-relation case with non-distinguished avoids available for reduction;
   and
8. a relation case that is already locally irreducible under the current
   single-avoid reduction neighborhood.

These cases are chosen to exercise supported relation and reduction boundaries.

They are not claims that validators are expected to disagree on them.

## Relationship to Case Reduction

A corpus entry exposes its `TransformationLocalEvidence` directly.

The case reducer can therefore consume the relation case without conversion.

Reduction is not automatically applied to every corpus case.

When reduction is used in an experiment, the interestingness predicate and
reduction result are separate experimental records.

The original corpus identity remains the identity of the original case.

A reduced case does not silently replace its corpus source case.

## Relationship to Validator Execution

The corpus layer does not import the raw validator runner.

It does not define validator command lines.

It does not define timeouts.

It does not define validator-specific result parsers.

It does not normalize raw observations into semantic claims.

It does not call the generic metamorphic oracle.

Those concerns belong to the evaluation layer that consumes the corpus.

## Relationship to Semantic Claims

The corpus contains no `SemanticClaim` values.

The candidate universe permits a witness denotation to be empty, but the
current project has no general decision procedure that determines emptiness.

The corpus therefore does not label cases `EMPTY` or `NONEMPTY` merely from witness
syntax or construction.

A later validator-specific adapter may produce a semantic claim only under its
own justified normalization contract.

## Schema and Format Conformance

SV-Witness schema conformance and candidate-domain admission are separate
questions.

The materializer is designed to emit the pinned SV-Witness 2.2 structure for
the supported profile.

A schema-conforming artifact does not by itself prove:

- source candidate admission;
- represented-execution feasibility;
- witness non-emptiness;
- validator completeness; or
- semantic correctness of a validator result.

Likewise, corpus membership does not make those claims.

## No General Parsing Layer

The corpus layer does not parse arbitrary external SV-Witness YAML.

There is no YAML-to-model ingestion path in this corpus contract.

The direction is intentionally one way:

`CorpusCase -> deterministic artifacts`.

Adding external witness ingestion would require a separate parser, metadata
binding, profile checking, and admission architecture.

## Reproducibility

A reproducible corpus evaluation can record:

- corpus case ID;
- corpus package revision;
- exact materialized artifact hashes;
- validator identity and version;
- validator invocation;
- execution environment;
- raw process observation;
- validator-specific normalized claims, when justified; and
- generic oracle classification, when its prerequisites are met.

Only the first three belong to the corpus definition.

The remaining fields belong to later evaluation infrastructure.

## Prior-Art Boundary

Crafted validator tests and witness transformation are established prior work.

The corpus does not claim that handcrafted validator cases, witness
transformation, witness reduction, or validator comparison are new.

Its role in this project is to provide deterministic relation-bearing inputs for
the already-defined metamorphic testing structure.

## Limitations

The corpus does not claim to provide:

- a general SV-Witness parser;
- a general SV-Witness serializer;
- support outside the initial semantic profile;
- automatic candidate admission;
- automatic witness-validity checking;
- represented-execution feasibility checking;
- semantic C-expression validation;
- expected validator results;
- validator-specific normalization;
- validator completeness;
- validator defect diagnosis;
- global case minimality; or
- a general benchmark for every SV-Witness feature.

Those capabilities require separate mechanisms or empirical evidence.
