# Transformation Evidence

## Purpose

This document defines evidence for concrete applications of the witness
transformations formalized by this project.

Transformation evidence records facts that connect:

- a fixed verification task;
- a source witness;
- a concrete transformation application;
- a transformed witness; and
- the semantic theorem already established for that transformation.

It does not redefine witness validity, transformation semantics, or validator
behavior.

The semantic profile is defined in
[`semantic-profile.md`](semantic-profile.md).

The general transformation relations are defined in
[`transformation-algebra.md`](transformation-algebra.md).

The currently supported concrete transformations are defined in
[`exact-transformations.md`](exact-transformations.md) and
[`monotone-transformations.md`](monotone-transformations.md).


## Evidence Is Not Admission by Construction

The internal `ViolationSequence` model establishes local structural invariants
of the supported profile.

Construction of that model does not establish that a witness candidate belongs
to the semantic candidate universe

\[
\mathcal{C}_\tau.
\]

Likewise, construction of a `VerificationTask` establishes only the local
verification-task representation.

It does not by itself prove that a witness is bound to that task or that the
task and witness satisfy the complete candidate-domain requirements.

Transformation evidence must therefore not infer

\[
W \in \mathcal{C}_\tau
\]

merely from the presence of a `ViolationSequence` and a `VerificationTask`
object.

Membership of the source witness in \(\mathcal{C}_\tau\) is an independent
premise of application admission.

It does not require the source to have a non-empty represented-execution set.

## Evidence Layers

The project distinguishes three kinds of facts.

### Source-Admission Facts

Source-admission facts establish that the source belongs to

\[
\mathcal{C}_\tau.
\]

They include the applicable requirements for:

- support by the project semantic profile;
- binding to the fixed verification task;
- the applicable SV-Witness 2.2 schema and guide conditions retained by the
  candidate universe;
- valid source locations and interpretable expressions as required by the
  supported profile; and
- every other candidate-domain condition except represented-execution
  non-emptiness.

Source admission therefore does not establish

\[
E_\tau(W) \neq \varnothing.
\]

The current local witness and task constructors do not establish this complete
set of candidate-admission facts.

This document does not define a general source-candidate admission algorithm.

### Transformation-Local Facts

Transformation-local facts concern one concrete application of one defined
operator.

They may include:

- the concrete operator being applied;
- operator parameters;
- whether the selected source structure satisfies the operator's stated
  preconditions;
- whether the transformed witness has the syntactic effect defined by that
  operator;
- whether all fields required to remain unchanged are preserved; and
- whether the transformation-specific structural obligations are preserved.

These facts can be checked using the immutable internal witness representation
for the transformations currently supported.

### Semantic Theorems

The relation between represented-execution sets comes from the previously
established semantic theorem for the transformation.

A runtime evidence checker does not re-prove the theorem for each application.

Instead, after the source-admission premise and transformation-local
preconditions have been established, the appropriate theorem can be
instantiated for that application.

The theorem determines the base semantic relation.

## Application Identity

Evidence for one transformation application must be tied to the exact
application for which it was established.

Conceptually, an application identity contains

\[
A =
(\tau, W, O, p, W'),
\]

where:

- \(\tau\) is the fixed verification task;
- \(W\) is the source witness;
- \(O\) is the concrete transformation operator;
- \(p\) is the operator parameter value, if any; and
- \(W'\) is the transformed witness.

For the two main-thread canonicalization operators, \(p\) is empty.

For avoid removal,

\[
p = (i,j),
\]

where the runtime representation may use zero-based indices even though the
formal transformation document uses one-based mathematical positions.

Evidence established for one application identity must not be reused as
evidence for an application with a different task, source witness, operator,
parameter, or transformed witness.

The current task and witness models are immutable. An implementation can
therefore retain the actual immutable values in an evidence record rather than
relying on mutable object identity.

## Relation Classes Used by Evidence

The current transformation set requires two base relation classes:

- exact; and
- broadening.

The main-thread canonicalization operators are exact.

Single selected avoid removal is broadening.

Strict broadening is not part of the current application-evidence contract.

An evidence record must not upgrade broadening to strict broadening merely
because a syntactic change occurred.

No narrowing transformation is currently implemented.

## Explicit Main-Thread Evidence

Let \(W'\) be a candidate result for explicit main-thread canonicalization.

Transformation-local evidence for that application establishes that:

1. the source and result have the same number of segments;
2. corresponding segments have the same kind;
3. corresponding segments have the same number of waypoints;
4. every result waypoint has `thread_id = 0`;
5. every non-`thread_id` field of each corresponding waypoint is unchanged;
6. waypoint order is unchanged;
7. segment order is unchanged.

There is no additional operator-specific semantic precondition beyond the
independent premise

\[
W \in \mathcal{C}_\tau.
\]

Once that premise and these local facts hold, the exactness theorem in
`exact-transformations.md` applies:

\[
E_\tau(W')
=
E_\tau(W).
\]

The equality theorem applies whether the source denotation is empty or non-empty.
If the source is later established to belong to \(\mathcal{W}_\tau\),
exactness also transfers represented-execution non-emptiness to the result.

## Implicit Main-Thread Evidence

Let \(W'\) be a candidate result for implicit main-thread canonicalization.

Transformation-local evidence establishes that:

1. the source and result have the same number of segments;
2. corresponding segments have the same kind;
3. corresponding segments have the same number of waypoints;
4. every result waypoint has absent `thread_id`;
5. every non-`thread_id` field of each corresponding waypoint is unchanged;
6. waypoint order is unchanged;
7. segment order is unchanged.

There is no additional operator-specific semantic precondition beyond the
independent premise

\[
W \in \mathcal{C}_\tau.
\]

The exactness theorem then gives

\[
E_\tau(W')
=
E_\tau(W).
\]

## Avoid-Removal Evidence

Let

\[
R^{\mathrm{avoid}}_{\tau,i,j}
\]

be the selected avoid-removal operator and let \(W'\) be a candidate result.

Transformation-local evidence must first establish the operator precondition:

1. the selected segment position exists;
2. the selected waypoint position exists; and
3. the selected source waypoint is an `assumption` waypoint whose action is
   `avoid`.

It must then establish the intended syntactic effect:

1. the result has the same number of segments as the source;
2. every segment except the selected segment is unchanged;
3. the selected result segment has exactly one fewer waypoint;
4. the removed source waypoint is exactly the selected waypoint;
5. every remaining waypoint in the selected segment is unchanged;
6. the relative order of the remaining waypoints is unchanged;
7. the normal segment's required `follow` waypoint remains present when the
   selected segment is normal;
8. the final target remains present when the selected segment is final.

Given the independent source-admission premise

\[
W \in \mathcal{C}_\tau,
\]

these local facts satisfy the preconditions of the broadening theorem from
`monotone-transformations.md`.

The theorem gives

\[
E_\tau(W)
\subseteq
E_\tau(W').
\]

It does not establish strict inclusion.


## Candidate Result and Validity Consequence

Transformation-local evidence alone does not establish source admission to
\(\mathcal{C}_\tau\).

For the currently defined transformations, once candidate source admission is
established independently, the transformation theorems and local structural
facts provide the transformation-specific argument needed to retain the result
inside \(\mathcal{C}_\tau\).

For the exact main-thread transformations:

- required structural relationships are preserved;
- the changed main-thread representations are both admitted by the profile;
  and
- their denotations are equal.

For avoid removal:

- the removed waypoint is optional in the supported segment structure;
- all required `follow` and target waypoints are preserved; and
- the broadening theorem applies independently of source non-emptiness.

These arguments establish candidate-domain preservation.

They do not assume that either candidate is already valid.

If the source is separately established to belong to

\[
\mathcal{W}_\tau,
\]

then exactness or broadening transfers represented-execution non-emptiness to
the result.

That is a derived validity consequence, not a prerequisite for recording the
semantic relation.


## Application Admission Criterion

A concrete transformation application is admitted for relation reasoning only
when all of the following have been established:

1. the source witness belongs to \(\mathcal{C}_\tau\);
2. the transformation-local preconditions hold;
3. the candidate result realizes the syntactic transformation defined by the
   operator;
4. the transformation-specific candidate-preservation argument applies; and
5. the operator's semantic theorem applies to the application.

For an admitted application, the project may then record:

- the application identity;
- the established base relation; and
- the transformation-local evidence used to instantiate the theorem.

Admission of the relation application does not establish

\[
W \in \mathcal{W}_\tau
\]

or

\[
W' \in \mathcal{W}_\tau.
\]

Those validity facts require represented-execution non-emptiness.

Failure to establish any required application-admission item leaves the
relation application unadmitted.

Failure to establish an item is not equivalent to proving that the
corresponding mathematical property is false.

## Independent Evidence Checking

Transformation-local evidence should be checked independently from the
transformation implementation being assessed.

For example, evidence that an implementation removed exactly one selected
`avoid` assumption should not be established merely by invoking the same
removal implementation a second time and comparing the results.

A checker may inspect the source and result witness structures directly and
derive the expected structural relationship independently.

This separation supports the distinction between:

- the intended semantic transformation;
- the implementation under test; and
- the evidence that a concrete implementation result conforms to the intended
  transformation.

The checker may share immutable model types with the transformation
implementation.

It should not depend on the transformation function whose output it is
checking.

## Validator Independence

Validator outcomes are not admissible evidence for transformation semantics.

In particular, evidence must not be based on:

- whether one validator confirms either witness;
- whether two validator runs agree;
- whether several validators agree;
- confirmation rates;
- validator error messages; or
- validator-specific success or failure classifications.

Validator execution occurs after transformation evidence has been established.

## No Full Re-Verification Requirement

Application evidence must not require rerunning the full verification task
merely to determine whether the transformation relation holds.

If determining the relation requires the validator under test or full
re-verification of the task, the relation is not independently justified under
the current method.

This restriction does not prohibit later experiments from executing validators
on already-related witnesses.

## Runtime Evidence Boundary

An initial runtime evidence implementation may support only:

- explicit main-thread canonicalization;
- implicit main-thread canonicalization; and
- single selected avoid removal.

It may define immutable descriptors for these concrete application forms and an
immutable transformation-local evidence record.

The evidence record should retain:

- the fixed verification task;
- the source witness;
- the transformed witness;
- the concrete application descriptor; and
- the established base relation.

Retaining the task in the record binds the evidence to the semantic context in
which the relation is interpreted.

Retention of the task is not itself evidence that the source witness is
correctly bound to that task.

The runtime evidence implementation must not claim to establish source
admission until an independent source-admission mechanism exists.

## Exclusions

This evidence model does not currently provide:

- a general SV-Witness validity checker;
- a source-witness parser;
- task-metadata parsing or binding;
- source-file lookup;
- source-location validation against program text;
- semantic validation of arbitrary C expressions;
- represented-execution feasibility checking;
- strict-broadening evidence;
- narrowing evidence;
- validator-result evidence;
- a validator outcome model;
- a generic proof system; or
- a general decision procedure for semantic inclusion.

Those concerns require separate mechanisms.

## References

The evidence rules in this document depend on the canonical semantic and
transformation documents linked above. Upstream SV-Witness semantics and source
pins remain defined by `semantic-profile.md`.
