# Case Reduction Protocol

## Purpose

This document defines the model-level case-reduction procedure used to make a
relation-bearing witness-transformation case smaller while retaining the
premises needed for relation reasoning.

The procedure is intended to support reproducible investigation of a
transformation application or an externally defined interesting observation.

It does not define a new witness semantics, a validator-result semantics, or a
general witness-reduction method.

## Relation Case

The reduction target is a relation-bearing transformation application.

Conceptually, write a case as

\[
K =
(\tau, W, A, W', R),
\]

where:

- \(\tau\) is the fixed verification task;
- \(W\) is the source witness model;
- \(A\) is one concrete supported transformation application;
- \(W'\) is the transformed witness model; and
- \(R\) is the base semantic relation established for that application.

The current runtime representation corresponding to these fields is
`TransformationLocalEvidence`.

A reduction case is not a redefinition of the witness-validation case in the
research problem statement. It is an internal object used to retain the
transformation relation while reducing the witness structure.

## Admission Premise

Construction of `TransformationLocalEvidence` does not establish

\[
W \in \mathcal{C}_\tau.
\]

Source admission remains an independent premise.

The reduction protocol is therefore conditional on the source of the initial
case already having been admitted to the candidate universe.

A reduced case must not be described as independently admitted merely because
the internal witness model can be constructed.

## Supported Application Families

The current reduction protocol applies to relation cases whose application is
one of:

- explicit main-thread canonicalization;
- implicit main-thread canonicalization; or
- single selected `avoid`-assumption removal.

The corresponding base relations are:

- exact for both main-thread canonicalization applications; and
- broadening for selected `avoid` removal.

No narrowing application is currently supported.

## Reduction Atom

The only source-witness reduction atom defined by this protocol is removal of
one `avoid` assumption waypoint.

Let the current source be

\[
W.
\]

Choose a source position

\[
q = (i,j)
\]

whose waypoint is an `avoid` assumption.

Define

\[
\widehat{W}
=
R^{\mathrm{avoid}}_{\tau,i,j}(W).
\]

The existing avoid-removal theorem establishes

\[
E_\tau(W)
\subseteq
E_\tau(\widehat{W})
\]

for an admitted source candidate when the operator preconditions hold.

The same theorem establishes candidate-domain preservation for this
transformation.

The reduction procedure therefore does not introduce a separate semantic rule
for source shrinking.

## Distinguished Avoid Waypoint

When the relation case itself uses an `AvoidRemovalApplication`, its selected
`avoid` waypoint is distinguished.

That waypoint must not be removed by the case reducer.

Otherwise the reduction would destroy the concrete transformation application
whose relation the case is intended to retain.

If another `avoid` waypoint earlier in the same segment is removed, the
distinguished waypoint's runtime index shifts left by one.

The reconstructed `AvoidRemovalApplication` must use that adjusted index.

Removal in another segment, or removal later in the same segment, does not
change the distinguished waypoint index.

## Reconstructing the Relation Case

A reduced source and the old transformed witness must not simply be paired
together.

For every proposed reduced source, the original transformation family is
applied again.

The procedure is:

1. remove one eligible non-distinguished `avoid` assumption from the current
   source;
2. establish transformation-local evidence that this source reduction realizes
   the selected avoid-removal operation;
3. update the original application parameter if the distinguished avoid index
   shifted;
4. apply the original transformation family to the reduced source;
5. independently check transformation-local evidence for that reconstructed
   application; and
6. retain the candidate relation case only if the resulting base relation is
   the same base relation as the current case.

For main-thread canonicalization, the original application has no positional
parameter.

For selected avoid removal, the adjusted positional parameter identifies the
same distinguished source waypoint after earlier deletions.

The transformed witness is therefore regenerated from the reduced source
rather than independently edited.

## Semantic Evidence Boundary

The relation of a reduced case comes from the same established transformation
theorem used for an unreduced application.

The runtime evidence checker establishes transformation-local conformance.

It does not re-prove the semantic theorem.

Subject to the independent source-admission premise, the source-reduction
avoid-removal theorem transfers candidate membership to the reduced source.

The reconstructed original application can then instantiate its own exact or
broadening theorem after its local evidence has been checked.

Validator observations are not semantic evidence for either step.

## Size Measure

The current reducer measures only source-witness waypoint count.

For a witness

\[
W = (s_1,\ldots,s_n),
\]

define

\[
\operatorname{size}(W)
=
\sum_{k=1}^{n}
|s_k.\mathrm{waypoints}|.
\]

Every accepted reduction step removes exactly one `avoid` assumption and
therefore satisfies

\[
\operatorname{size}(\widehat{W})
=
\operatorname{size}(W)-1.
\]

This measure does not assign weights to:

- segments;
- expression text;
- source-location fields;
- thread identifiers; or
- serialized byte length.

Those dimensions are not reduced by the current protocol.

## Interestingness Predicate

Case reduction may be guided by an external predicate

\[
I(K) \in \{\mathrm{true},\mathrm{false}\}.
\]

The predicate states whether a candidate case retains the phenomenon the caller
wants to investigate.

The initial case must satisfy the predicate before reduction begins.

A proposed reduction is accepted only when its reconstructed relation case also
satisfies the predicate.

The predicate is an operational selection mechanism.

It is not evidence that:

- the source belongs to \(\mathcal{C}_\tau\);
- the transformation preconditions hold;
- the transformation implementation is correct;
- the exact or broadening theorem applies; or
- either witness has a particular represented-execution set.

Those premises remain independent of the predicate.

## Validator Boundary

The reducer does not define validator-result normalization.

It does not import or interpret raw process observations.

A caller may later define an interestingness predicate using reproducible
validator execution or normalized semantic claims.

If it does, preservation of that predicate means only that the caller-defined
observation remained true for the accepted reduced case.

It does not turn validator behavior into evidence for the transformation
relation.

The generic metamorphic oracle is likewise outside the structural reduction
algorithm.

An oracle classification may be part of a caller-defined interestingness
predicate only after its own relation and normalized-claim premises have been
established independently.

## Candidate Enumeration

For one current case, eligible source `avoid` waypoints are considered in
lexicographic source position order:

\[
(0,0),
(0,1),
\ldots,
(1,0),
\ldots
\]

using the zero-based runtime indices.

The distinguished waypoint of an `AvoidRemovalApplication` is skipped.

If two different selectors produce equal reconstructed relation cases, only the
first occurrence is retained for predicate evaluation.

This makes candidate ordering deterministic for a fixed current case.

## Search Procedure

Reduction uses deterministic greedy first acceptance.

Starting from a case satisfying \(I\):

1. enumerate the current single-step candidates in source position order;
2. evaluate \(I\) on each candidate in that order;
3. accept the first candidate for which \(I\) is true;
4. restart enumeration from the beginning of the accepted case; and
5. stop when no single-step candidate satisfies \(I\).

Every accepted step strictly reduces source waypoint count.

The procedure therefore terminates after finitely many accepted steps.

## Result Property

At termination, the returned case:

- satisfies the interestingness predicate;
- uses the same verification task value;
- uses the same transformation application family;
- has the same base relation class;
- has transformation-local evidence established for its reconstructed
  application; and
- has no eligible single `avoid` removal accepted by the predicate.

The last property is local irreducibility with respect to the reduction
neighborhood defined by this protocol.

It is not a claim of global minimality.

Different reduction operators, a different candidate order, or a different
interestingness predicate could produce a smaller case.

## Determinism Boundary

For a fixed initial case and a deterministic interestingness predicate, the
reducer has deterministic:

- candidate enumeration;
- duplicate suppression;
- first-accept tie breaking;
- restart behavior; and
- stopping behavior.

The reducer cannot make a stateful, randomized, time-dependent, or externally
unstable predicate deterministic.

Experimental reproducibility therefore also depends on the contract and
environment of any external predicate.

## Model-Level Boundary

The current reducer operates on immutable internal model objects.

It does not parse arbitrary SV-Witness YAML files.

It does not serialize reduced cases back to YAML.

It does not perform:

- witness metadata parsing;
- task-metadata binding;
- source-file lookup;
- source-location validation against program text; or
- arbitrary candidate admission.

Those facilities require separate mechanisms.

## Excluded Reductions

The current protocol does not reduce a case by:

- deleting normal segments;
- deleting the final segment;
- deleting a `follow` assumption;
- deleting the final target;
- deleting the distinguished avoid waypoint of the relation application;
- rewriting assumption expressions;
- rewriting source locations;
- removing optional location fields;
- rewriting `thread_id` as a size-reduction operation;
- changing the verification task;
- independently editing the transformed witness; or
- changing the transformation family.

Some of these operations may eventually admit separate semantic arguments.

They are not implied by the current case-reduction protocol.

## Prior-Art Boundary

Witness reduction is established prior work.

In particular, prior work reduces violation witnesses for the same verification
task using a sound over-approximation and evaluates validator behavior before
and after the transformation.

This protocol does not claim witness reduction, over-approximation, or
validator evaluation after reduction as new.

Its role in this project is operational: shrink a relation-bearing metamorphic
case while keeping semantic-relation evidence separate from the predicate used
to retain an observed phenomenon.

## Related Documents

The relevant project contracts are:

- [`../formal/semantic-profile.md`](../formal/semantic-profile.md) for the
  candidate and valid-witness universes;
- [`../formal/transformation-algebra.md`](../formal/transformation-algebra.md)
  for semantic relations;
- [`../formal/exact-transformations.md`](../formal/exact-transformations.md)
  for main-thread exact transformations;
- [`../formal/monotone-transformations.md`](../formal/monotone-transformations.md)
  for avoid-removal broadening;
- [`../formal/transformation-evidence.md`](../formal/transformation-evidence.md)
  for application identity and local evidence;
- [`../formal/oracle-feasibility.md`](../formal/oracle-feasibility.md) for the
  semantic-claim oracle boundary; and
- [`validator-runner.md`](validator-runner.md) for raw validator execution.
