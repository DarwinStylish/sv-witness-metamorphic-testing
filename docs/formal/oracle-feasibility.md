# Metamorphic Oracle Feasibility

## Purpose

This document states the semantic premises under which the project can derive
relation-aware constraints over normalized validator claims.

It separates:

- witness semantics;
- transformation relations;
- candidate and validity admission;
- raw validator execution;
- validator-specific result normalization; and
- the generic metamorphic oracle.

The oracle does not assume validator completeness, semantic extensionality, or
operational monotonicity unless a concrete experiment states and justifies such
an additional contract.

## Semantic Universes

For a fixed verification task

\[
\tau = (P,\varphi,M),
\]

the semantic profile defines the candidate universe

\[
\mathcal{C}_\tau.
\]

Every

\[
W \in \mathcal{C}_\tau
\]

has a defined represented-execution set

\[
E_\tau(W).
\]

That set may be empty.

The valid-witness universe is

\[
\mathcal{W}_\tau
=
\left\{
W \in \mathcal{C}_\tau
\;\middle|\;
E_\tau(W) \neq \varnothing
\right\}.
\]

The transformation algebra is defined over
\(\mathcal{C}_\tau\), not only over already-valid witnesses.

This distinction is necessary for emptiness and non-emptiness claims to
participate in a non-trivial pairwise oracle.

## Current Transformation Relations

The current transformation set contains:

- exact main-thread canonicalization; and
- broadening by removal of one selected `avoid` assumption.

For an admitted exact application,

\[
W,W' \in \mathcal{C}_\tau
\]

and

\[
E_\tau(W') = E_\tau(W).
\]

For an admitted avoid-removal application,

\[
W,W' \in \mathcal{C}_\tau
\]

and

\[
E_\tau(W) \subseteq E_\tau(W').
\]

Neither relation requires the source denotation to be non-empty.

If the source is additionally known to belong to
\(\mathcal{W}_\tau\), exactness and broadening both preserve validity for the
currently defined transformations.

That validity consequence is separate from the relation itself.

## Raw Runs Are Not Semantic Claims

A raw validator run records process behavior.

Process exit, timeout, spawn failure, stdout, and stderr are not by themselves
semantic witness claims.

Any semantic interpretation of a raw run requires a validator-specific
normalization rule justified from that validator's documented interface or
another independently stated contract.

The generic oracle must not derive a semantic claim directly from:

- process return code alone;
- timeout;
- spawn failure;
- diagnostic output without a validator-specific interpretation rule;
- unsupported input;
- parse failure; or
- absence of successful confirmation.

## Semantic Claim Vocabulary

The generic oracle uses three claim-strength classes.

`NONEMPTY`
: the normalized validator result asserts that the candidate represents at
  least one violating execution for the fixed task.

`EMPTY`
: the normalized validator result asserts that the candidate represents no
  violating execution for the fixed task.

`NO_CLAIM`
: the normalized result establishes neither of the preceding semantic claims.

These labels describe semantic claim strength.

They do not define how any concrete validator output maps to the labels.

A validator-specific adapter may emit `NONEMPTY` or `EMPTY` only when its
independently justified contract supports that interpretation.

Otherwise it must emit `NO_CLAIM`.

## Exact-Relation Constraint

Suppose

\[
E_\tau(W) = E_\tau(W').
\]

Then the following claim pairs are semantically compatible with the exact
relation:

| Source claim | Result claim | Relation classification |
| --- | --- | --- |
| `NONEMPTY` | `NONEMPTY` | compatible |
| `EMPTY` | `EMPTY` | compatible |

The following claim pairs contradict equality of the represented-execution
sets:

| Source claim | Result claim | Relation classification |
| --- | --- | --- |
| `NONEMPTY` | `EMPTY` | contradiction |
| `EMPTY` | `NONEMPTY` | contradiction |

If either side is `NO_CLAIM`, the exact relation alone does not determine a
contradiction.

The pair is therefore indeterminate under the current claim model.

This does not assume that a complete validator must emit the same operational
result for semantically equivalent witness syntax.

It constrains only explicit semantic claims that have already been normalized
under a justified validator-specific contract.

## Broadening-Relation Constraint

Suppose

\[
E_\tau(W) \subseteq E_\tau(W').
\]

The pair

| Source claim | Result claim | Relation classification |
| --- | --- | --- |
| `NONEMPTY` | `EMPTY` | contradiction |

is impossible if both semantic claims are sound.

A non-empty subset cannot be contained in an empty set.

The following combinations are compatible with the broadening relation:

| Source claim | Result claim | Relation classification |
| --- | --- | --- |
| `NONEMPTY` | `NONEMPTY` | compatible |
| `EMPTY` | `EMPTY` | compatible |
| `EMPTY` | `NONEMPTY` | compatible |

The last case is permitted because an empty source denotation is a subset of a
non-empty result denotation.

If either side is `NO_CLAIM`, inclusion alone does not require a claim on the
other side.

Such a pair is therefore indeterminate under the current claim model.

## Why the Constraints Are Relation-Aware

Candidate admission to

\[
\mathcal{C}_\tau
\]

does not establish represented-execution non-emptiness.

Therefore neither an `EMPTY` nor a `NONEMPTY` claim is ruled out merely by
candidate admission.

For an exact application, the contradictory mixed pairs arise from semantic
equality.

For a broadening application, the
`NONEMPTY`-source / `EMPTY`-result contradiction arises from semantic
inclusion.

These are therefore non-trivial pairwise constraints under the definition in
the research hypotheses: the relationship rules out combinations that the
candidate-admission premises alone do not rule out.

## Relation Classification Is Not a Defect Verdict

A relation-level contradiction means that the two normalized semantic claims
cannot both be sound under the independently established candidate admission
and transformation theorem.

It does not by itself identify which component is wrong.

Possible causes include:

- an unsound validator claim;
- an incorrect validator-specific normalization rule;
- incorrect candidate admission;
- incorrect transformation-local evidence;
- an implementation that does not realize the intended transformation; or
- an error in the semantic theorem or its stated assumptions.

The generic oracle therefore classifies consistency with the established
relation.

It does not directly label a validator implementation defective.

## Validator Incompleteness Remains Permitted

The candidate-domain redesign does not introduce a completeness assumption.

A validator may still:

- return an unknown result;
- fail to confirm a valid witness;
- reject unsupported input;
- time out;
- fail internally; or
- expose no semantic claim usable by this oracle.

Such cases remain `NO_CLAIM` unless a validator-specific contract establishes
something stronger.

For an exact relation, incompleteness may still yield operationally asymmetric
runs.

For a broadening relation, incompleteness may still prevent the validator from
making a claim on either side.

The oracle constrains claim content, not the validator's obligation to produce
a claim.

## Validity Consequences

For a candidate

\[
W \in \mathcal{C}_\tau,
\]

a sound `NONEMPTY` claim is consistent with the non-emptiness condition required
for

\[
W \in \mathcal{W}_\tau.
\]

A sound `EMPTY` claim establishes that the candidate does not satisfy the
violation-sequence non-emptiness requirement and therefore cannot belong to
\(\mathcal{W}_\tau\).

The generic relation oracle does not need to perform this validity
classification in order to compare a source/result pair.

Validity and relation consistency remain separate conclusions.

## Outcome Normalization Requirement

Validator-specific normalization must preserve distinctions that affect claim
strength.

A normalizer must not silently collapse:

- timeout;
- unsupported input;
- parse failure;
- internal error;
- process failure;
- unrecognized output; or
- generic non-confirmation

into `EMPTY`.

Likewise, a normalizer must not emit `NONEMPTY` merely because a process exited
successfully.

Each semantic mapping requires an independently justified validator-specific
contract.

## Generic Oracle Boundary

The generic metamorphic oracle may depend on:

- independent admission of the source and result to
  \(\mathcal{C}_\tau\);
- independently established transformation-local evidence;
- the resulting exact or broadening semantic relation;
- normalized semantic claims whose strength is explicit; and
- any additional validator contract stated by the experiment.

It must not depend directly on:

- raw subprocess return codes;
- validator-specific text parsing;
- undocumented output conventions;
- majority agreement between validators;
- full re-verification used merely to infer the transformation relation; or
- assumptions introduced solely to force a non-indeterminate result.

Validator-specific adapters belong below the generic oracle.

The raw validator runner remains below both layers.

## Gate C

Gate C is satisfied at the semantic-design level when the implementation can
apply the predefined relation tables above to:

1. an admitted candidate-domain transformation application; and
2. two normalized semantic claims.

For exact relations:

- mixed `EMPTY` / `NONEMPTY` claims are contradictions;
- equal informative claims are compatible; and
- any pair containing `NO_CLAIM` is indeterminate.

For broadening relations:

- `NONEMPTY` source with `EMPTY` result is a contradiction;
- the other informative combinations are compatible; and
- any pair containing `NO_CLAIM` is indeterminate.

A concrete validator adapter is still required before raw validator output can
supply these semantic claims.

The adapter contract must be justified separately for the concrete validator,
validator version, witness-format version, and supported task profile.

## Research Interpretation

The candidate-domain correction does not guarantee that current validators
expose sufficiently strong semantic claims.

It establishes only that the transformation relations themselves now admit a
non-trivial semantic oracle when such claims are available.

If no concrete validator can justify an `EMPTY` or `NONEMPTY` mapping strong
enough to exercise these constraints, that remains a valid negative empirical
result.

The project must not strengthen a validator result merely to make Gate C
produce contradictions.
