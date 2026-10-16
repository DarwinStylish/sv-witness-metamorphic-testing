# Multi-Validator Evaluation

## Purpose

This document describes how relation-bearing corpus cases are evaluated across
multiple SV-Witness validators without collapsing process observations,
validator-specific interpretation, and semantic relation reasoning into one
layer. The evaluation record connects those layers while preserving the evidence
that each layer contributes.

The input is a deterministic `CorpusCase`. Its transformation evidence supplies
the source witness, transformed witness, fixed verification task, and established
base relation. Materialization supplies the exact program, property, and witness
bytes used by a concrete experiment. Validator execution then produces raw
`ValidatorRun` records, while validator-specific adapters may interpret those
records as semantic claims under separately justified normalization contracts.

The generic evaluation model records these objects and applies the existing
relation-aware oracle. It does not define concrete validator output semantics,
discover validators, launch processes, or infer semantic truth from agreement
between implementations.

## Evaluation Record

A multi-validator evaluation is tied to one corpus case and therefore to one
verification task and one transformation relation. The materialized artifact
bundle is represented by ordered SHA-256 records so that the evaluation can be
connected to the exact bytes of `example.c`, `property.prp`, `source.yml`, and
`transformed.yml`, or to the corresponding artifact names of another supported
case.

Candidate-domain admission remains an independent premise. The corpus model and
the materializer deliberately do not establish that the source witness belongs
to the candidate universe. Before this evaluation layer invokes the generic
oracle, it therefore requires a `CandidateAdmissionEvidence` record. That record
binds an external admission basis to the corpus case identifier and to the
SHA-256 digest of the materialized source witness. The record preserves the
premise used by the experiment; its construction does not itself prove the
premise.

Each validator observation carries two kinds of identity. `ValidatorIdentity`
records the implementation and version being studied. `AdapterIdentity` records
the adapter name, adapter version, and the normalization contract under which
raw output is interpreted. Keeping these identities separate makes it possible
to change an adapter without pretending that the validator changed, and to
change a validator version without silently reusing evidence justified for a
different version.

A `NormalizedValidatorRun` combines those identities with an unchanged
`ValidatorRun` and one `SemanticClaim`. Source and transformed observations form
a `NormalizedValidatorPair`; both sides must use the same validator identity and
the same adapter identity. A `ValidatorPairEvaluation` retains the raw runs,
normalized claims, relation, and oracle classification. The complete
`MultiValidatorEvaluation` contains the artifact digests, admission evidence,
and one pair evaluation for each validator implementation.

Conceptually, for validator implementation \(v\), the retained record is

\[
E_v =
(V_v, A_v, R_v^{src}, c_v^{src}, R_v^{dst}, c_v^{dst}, o_v),
\]

where \(V_v\) identifies the validator, \(A_v\) identifies the normalization
contract, each \(R\) is a raw run, each \(c\) is a normalized semantic claim, and
\(o_v\) is the relation-aware classification. The aggregate keeps the
per-validator records separate rather than deriving a combined claim.

## Normalization and Relation Classification

A raw validator run is a process observation. Return codes, standard output,
standard error, timeouts, and process-spawn failures remain exactly as recorded
by the runner. None of those observations has a generic mapping to `NONEMPTY`,
`EMPTY`, or `NO_CLAIM`.

A concrete adapter may emit `NONEMPTY` or `EMPTY` only when its documented
normalization contract justifies that interpretation for the concrete validator
version, witness format, and verification-task profile. Unsupported features,
ambiguous output, unrecognized output, timeouts, and process failures remain
`NO_CLAIM` unless a stronger interpretation is independently justified. This
preserves the distinction between lack of information and a semantic statement
that the represented execution set is empty.

Once source admission has been supplied independently and both runs have been
normalized, the evaluation layer delegates classification to
`classify_claim_pair`. It does not reproduce or modify the oracle truth table.
For an exact relation, mixed informative emptiness claims contradict equality.
For a broadening relation, a non-empty source claim paired with an empty
transformed claim contradicts inclusion. Any pair containing `NO_CLAIM` remains
indeterminate under the current oracle.

The resulting classification constrains the pair of claims, not the validator as
a whole. `COMPATIBLE` means that the claims can both hold under the established
relation; it does not prove either claim. `CONTRADICTION` means that both claims
cannot simultaneously be sound if the relation and its premises are sound; it
does not identify the faulty component. `INDETERMINATE` records that the
available claim strength is insufficient for either conclusion.

## Multi-Validator Interpretation

A multi-validator record contains observations from at least two distinct
validator implementations. Each implementation is evaluated independently with
its own adapter and raw process records. Versions remain part of validator
identity, but two versions of the same implementation do not by themselves
satisfy the requirement for multiple implementations.

Agreement between validators is useful empirical information, but it is not a
semantic voting rule. The aggregate therefore has no majority result, consensus
claim, validator ranking, or preferred implementation. A contradiction reported
for one validator is not repaired by agreement among the others, and agreement
among several validators does not establish that their normalized claims are
true.

Negative and inconclusive outcomes are valid experimental results. An
evaluation may contain only compatible pairs, only indeterminate pairs, or a
mixture of the two. It may also reveal that current adapter contracts cannot
justify informative claims for the selected profile. The experiment does not
need to produce a contradiction or a validator defect in order to be
interpretable.

## Artifact and Process Provenance

Artifact hashes bind the evaluation record to the deterministic bytes produced
by corpus materialization. The source-witness digest is also used to bind
candidate-admission evidence to the evaluated source artifact. Recomputing these
hashes is a byte-level integrity check; it does not establish semantic
correctness, witness feasibility, or candidate admission.

Each normalized run retains the complete `ValidatorRun`, including the exact
`ValidatorInvocation` and raw process observation. This preserves the argument
vector, working directory, explicit environment, timeout, return code when one
exists, and captured output bytes. The evaluation layer does not rewrite those
records and does not infer which artifact a validator actually consumed from
the command line. A concrete execution harness is responsible for placing the
materialized bytes in a workspace and constructing the validator-specific
invocation.

These records provide useful provenance but are not a complete reproducibility
package. They do not establish executable digests, operating-system identity,
container identity, linked-library identity, CPU or kernel identity, scheduler
behavior, or stronger resource isolation. Those properties require additional
reproducibility evidence.

## Concrete Validator Adapters

A validator-specific adapter should be introduced only when its interpretation
can be tied to a concrete validator release or revision. The supporting
documentation needs to identify the witness format and verification-task
profile accepted by that validator, the invocation used for validation, the
documented result semantics, and the rule that maps observable validator
behavior to the project semantic-claim vocabulary.

The normalization contract is part of experimental provenance rather than a
generic property of the validator name. Evidence for one validator release
cannot be silently generalized to another release, and an adapter should fall
back to `NO_CLAIM` when its stated contract does not cover an observed result.

The generic evaluation layer is defined without a concrete adapter. This keeps
model-level tests separate from empirical validator results and prevents
unit-test fixtures from being presented as observations of real validators.

## Limitations

The evaluation layer assumes that transformation-local evidence and independent
source admission are already available. It does not provide a candidate-admission
decision procedure, a general SV-Witness parser, validator installation or
discovery, validator-version discovery, executable hashing, workspace
management, process scheduling, or a validator-specific normalizer.

The model also does not establish validator correctness, validator completeness,
or defect attribution. A relation-level contradiction narrows the set of claims
that can simultaneously be sound, but further evidence is required to determine
whether the cause lies in validator behavior, normalization, admission,
transformation evidence, or another experimental premise.

## Related Documents

The semantic and operational boundaries used here are defined in
`../formal/oracle-feasibility.md`,
`../formal/transformation-evidence.md`,
`validator-runner.md`, `adversarial-corpus.md`, and `case-reduction.md`.
