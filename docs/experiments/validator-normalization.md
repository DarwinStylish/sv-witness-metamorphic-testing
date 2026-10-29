# Validator Normalization

## Purpose

Concrete validator output must be interpreted before the relation-aware oracle can use it. This
document defines that boundary for CPAchecker and Theta under the SV-Witness 2.2 sequential C
`unreach-call` profile. The rule is deliberately narrow: only a confirmed reachability violation
produces an informative semantic claim.

The normalizers do not execute validators and do not parse arbitrary console output. They consume
a standardized result produced by a pinned BenchExec tool-info implementation and retain the
original `ValidatorRun` beside that result evidence. Process evidence and semantic interpretation
therefore remain separate.

## Pinned Evidence

The CPAchecker contract is tied to version `4.2.2-3728-g5c33b8d955`, whose development line
contains unified YAML 2.x violation-witness parsing with format 2.2 support. The Theta contract is
tied to source revision `f30b2fb88f9345df07878b0363c2bf1f8e76c604`, where the source tree contains
explicit 2.2 witness handling and 2.2 witness-validation fixtures.

Result interpretation is pinned independently to BenchExec revision
`2a1a063fea57af414f2b80c89009a958183498e6`, using `benchexec.tools.cpachecker` and
`benchexec.tools.theta`. The validator revision and result-parser revision remain separate pieces
of provenance.

WitnessLint is not included as a semantic validator. Its 2.2 schema support is useful for syntax
and metadata checking, but schema acceptance does not establish feasibility of the executions
represented by a violation witness.

## Normalization Rule

`BenchExecResultEvidence` records the tool-info revision, tool-info module, and standardized
BenchExec result string. The record is supplied by an execution harness; constructing it does not
prove that BenchExec produced the value.

For this profile, the only informative accepted result is `false(unreach-call)`. When that status
accompanies a normal process exit with return code zero, the normalizer emits `NONEMPTY`. All other
statuses emit `NO_CLAIM`.

In particular, `true`, `unknown`, invalid-witness errors, unsupported input, timeout, spawn failure,
and nonzero process exit do not become `EMPTY`. Failure to confirm a witness may reflect
incompleteness or an operational limitation rather than an empty witness denotation.

## Validator Identity

The CPAchecker adapter identifies `CPAchecker 4.2.2-3728-g5c33b8d955` and accepts only evidence
from the pinned CPAchecker BenchExec tool-info module. The Theta adapter identifies the exact
source revision above and accepts only evidence from the pinned Theta tool-info module. Neither
contract is silently generalized to another validator release or another BenchExec revision.

Both adapters return `NormalizedValidatorRun`, so the existing multi-validator model can pair
source and transformed observations and apply the generic oracle without validator-specific logic.

## Limitations

These contracts cover only the selected sequential C `unreach-call` profile. They do not establish
support for other witness versions, concurrency, other properties, or unpinned validator builds.
Unit-test result values demonstrate model behavior but are not empirical validator observations.

Executable hashes, build provenance, workspace construction, resource isolation, and archived
experiment outputs remain reproducibility concerns rather than normalization semantics.
