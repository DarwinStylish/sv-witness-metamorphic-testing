# Metamorphic Oracle Feasibility

## Purpose

This document determines which validator-outcome constraints follow from the
currently established witness semantics and transformation relations.

The purpose is to prevent operational observations from being assigned stronger
semantic meaning than the current model supports.

This document does not define a validator-specific result parser.

It also does not assume validator completeness, semantic extensionality, or
monotonicity unless such a property is introduced separately and justified.

## Existing Semantic Premises

For a fixed verification task

\[
\tau = (P,\varphi,M),
\]

the current transformation algebra uses the witness universe

\[
\mathcal{W}_\tau.
\]

Membership in this universe requires the witness to be valid for the fixed task
and supported by the current semantic profile.

In particular, for

\[
W \in \mathcal{W}_\tau,
\]

the represented-execution set is non-empty:

\[
E_\tau(W) \ne \varnothing.
\]

The current transformation set contains:

- exact main-thread canonicalization; and
- broadening by removal of one selected `avoid` assumption.

For an admitted exact application,

\[
E_\tau(W') = E_\tau(W).
\]

For an admitted avoid-removal application,

\[
E_\tau(W) \subseteq E_\tau(W').
\]

The current transformation-specific validity arguments preserve result
admission once source admission has been established independently.

Consequently, for every currently admitted transformation application,

\[
E_\tau(W) \ne \varnothing
\]

and

\[
E_\tau(W') \ne \varnothing.
\]

This fact exists before validator outcomes are considered.

## Outcome Information Must Be Separated from Process Observations

A raw validator run records only process behavior.

Process exit, timeout, and spawn failure are not semantic witness claims.

Any interpretation of a raw run therefore requires a separate
validator-specific normalization rule.

Such a rule must be justified from the validator's documented interface or
another independently stated contract.

The generic oracle must not derive a semantic claim directly from:

- process return code alone;
- timeout;
- spawn failure;
- diagnostic output without a validator-specific interpretation rule; or
- absence of successful confirmation.

## Candidate Semantic Claims

Consider the following abstract claim vocabulary:

`NONEMPTY`
: the normalized validator result asserts that the witness represents at least
  one violating execution for the fixed task.

`EMPTY`
: the normalized validator result asserts that the witness represents no
  violating execution for the fixed task.

`NO_CLAIM`
: the normalized result establishes neither of the preceding semantic claims.

These labels describe claim strength.

They do not define how any concrete validator output maps to the labels.

## Admission Makes Non-Emptiness an Individual Fact

For a currently admitted transformation application, both source and result
already have non-empty represented-execution sets.

Therefore an `EMPTY` claim about the source conflicts with source admission
independently of the transformation relation.

Likewise, an `EMPTY` claim about the transformed witness conflicts with result
admission independently of whether the relation is exact or broadening.

Thus a pair containing `EMPTY` does not become contradictory because of the
relationship between the two witnesses.

The individual admission facts are already sufficient.

This distinction matters for a relation-aware oracle.

A relation-aware constraint is non-trivial only when the relation rules out an
outcome combination that the other stated premises do not already rule out.

## Exactness with Non-Emptiness Claims

Suppose an admitted application is exact:

\[
E_\tau(W) = E_\tau(W').
\]

Because admission already gives

\[
E_\tau(W) \ne \varnothing
\]

and

\[
E_\tau(W') \ne \varnothing,
\]

the equality does not add a new non-emptiness fact.

If both normalized results make `NONEMPTY` claims, they are compatible with
the established semantics.

If one result makes an `EMPTY` claim, that claim already conflicts with the
individual admission of the corresponding witness.

If either result is `NO_CLAIM`, exactness alone gives no rule requiring the
validator to make a claim on the other witness.

Therefore exactness does not currently provide a non-trivial pairwise
constraint over the claim vocabulary

\[
\{
\text{NONEMPTY},
\text{EMPTY},
\text{NO\_CLAIM}
\}
\]

once application admission is included among the premises.

## Broadening with Non-Emptiness Claims

Suppose an admitted application is broadening:

\[
E_\tau(W) \subseteq E_\tau(W').
\]

Source admission already gives

\[
E_\tau(W) \ne \varnothing.
\]

The broadening theorem therefore provides result non-emptiness:

\[
E_\tau(W') \ne \varnothing.
\]

For the currently defined transformation, this result is already part of the
transformation-specific result-admission argument.

Consequently an `EMPTY` claim for the transformed witness is inconsistent with
the established application premises before a pairwise validator-outcome rule
is considered.

A source `EMPTY` claim is likewise inconsistent with source admission.

If either result is `NO_CLAIM`, set inclusion alone does not require the
validator to make a corresponding claim on the other run.

Thus the current broadening relation also provides no additional pairwise
constraint over this claim vocabulary for an admitted application.

## Confirmation Is Not Completeness

A validator may successfully confirm a valid violation witness.

Failure to confirm the witness does not, without an additional contract, imply

\[
E_\tau(W) = \varnothing.
\]

A validator can fail to confirm a valid witness because of:

- incomplete analysis;
- unsupported features;
- resource limits;
- internal failure;
- timeout; or
- other implementation behavior.

Therefore the operational abstraction

`CONFIRMED`
: the validator successfully established its supported confirmation condition.

`NO_CONFIRMATION`
: the run did not establish that confirmation condition.

must not be identified with

`NONEMPTY`
and
`EMPTY`

respectively.

At most, a validator-specific contract may establish that `CONFIRMED` entails
a `NONEMPTY` claim.

`NO_CONFIRMATION` remains semantically weaker unless the validator contract
explicitly establishes otherwise.

## Exactness Does Not Imply Equal Operational Results

For an exact application,

\[
E_\tau(W) = E_\tau(W').
\]

This equality does not imply that an incomplete validator must behave
identically on the two witness representations.

Without an additional semantic-extensionality or completeness contract, each
of the following operational pairs remains possible:

    CONFIRMED / CONFIRMED
    CONFIRMED / NO_CONFIRMATION
    NO_CONFIRMATION / CONFIRMED
    NO_CONFIRMATION / NO_CONFIRMATION

The asymmetric cases may result from syntax sensitivity, unsupported features,
resource behavior, internal heuristics, or incomplete analysis.

Exactness alone therefore does not classify either asymmetric pair as a
validator defect.

## Broadening Does Not Imply Operational Monotonicity

For a broadening application,

\[
E_\tau(W) \subseteq E_\tau(W').
\]

This inclusion does not imply that an incomplete validator that confirms the
source must confirm the transformed witness.

Such an implication would require an additional behavioral property of the
validator.

In particular, it would require some form of monotonicity or completeness with
respect to the represented-execution relation.

No such property is part of the current transformation algebra.

Therefore the pair

    CONFIRMED / NO_CONFIRMATION

is not contradictory merely because the transformation is broadening.

The reverse pair

    NO_CONFIRMATION / CONFIRMED

is also operationally possible.

## Strict Broadening Does Not Resolve the Issue

Knowing that

\[
E_\tau(W) \subset E_\tau(W')
\]

would establish that the transformed witness represents at least one execution
not represented by the source.

It would still not require an incomplete validator to confirm either witness.

Strictness therefore does not by itself create a confirmation-level
metamorphic constraint.

A validator-behavior contract would still be required.

## Current Constraint Result

Under all of the following premises:

1. transformation applications are admitted using the current
   \(\mathcal{W}_\tau\) universe;
2. source admission establishes source non-emptiness;
3. the current transformations preserve result admission;
4. validator incompleteness is permitted;
5. semantic extensionality of validator behavior is not assumed;
6. validator monotonicity is not assumed; and
7. non-confirmation is not interpreted as a semantic emptiness proof;

the current exact and broadening relations do not rule out any pair of
`CONFIRMED` and `NO_CONFIRMATION` outcomes.

Adding an `EMPTY` semantic claim does not by itself solve this problem because
emptiness is already ruled out individually for both witnesses in an admitted
application.

This is a limitation of the current oracle premises, not a failure of the
transformation theorems.

## Consequence for Relation-Aware Testing

The current semantic relations remain useful descriptions of related
witnesses.

However, semantic equality or inclusion alone is insufficient to derive a
non-trivial operational oracle over confirmation and non-confirmation while
validator incompleteness and representation-sensitive behavior remain
permitted.

A difference between validator outcomes therefore remains observational data
unless additional justified premises provide a stronger interpretation.

## Conditions That Could Produce a Non-Trivial Oracle

A non-trivial relation-aware oracle would require at least one additional
source of information not present in the current admitted-witness,
confirmation-only model.

Possible directions include the following.

### Broader Semantic Domain

The transformation relation could be established over a broader universe of
profile-supported candidate witnesses that may have empty represented-execution
sets.

Such a redesign would separate:

- structural/profile admissibility;
- semantic equality or inclusion; and
- witness validity as non-emptiness.

The existing transformation theorems would need to be restated and re-proved
over that broader universe.

The current theorems must not simply be assumed to have this larger domain.

### Stronger Validator Claims

A concrete validator may expose a documented result that has semantic meaning
stronger than failure to confirm.

For example, a validator-specific result might, if its documented contract
supports such an interpretation, assert that no execution represented by the
witness establishes the violation.

Such an interpretation must be justified separately for that validator and
version.

A generic `EMPTY` result must not be invented merely to make the oracle
non-trivial.

### Explicit Validator Behavioral Contract

An experiment could state and test an additional validator property such as:

- semantic extensionality over an exact transformation;
- monotonicity over a broadening relation; or
- completeness over a defined supported subdomain.

Such a property would be an explicit contract under test.

It would not follow from the witness semantics alone.

The experimental conclusion would therefore concern conformance to that
contract rather than an unconditional consequence of semantic equality or
inclusion.

### Richer Semantic Outputs

A validator may provide independently meaningful artifacts or claims beyond
binary confirmation.

If such claims have documented semantics that interact with witness equality or
inclusion, they may support stronger relation-aware constraints.

This requires separate analysis of the concrete validator interface.

## Outcome Normalization Requirement

Validator-specific normalization must preserve distinctions that affect claim
strength.

In particular, a normalizer must not silently collapse:

- timeout;
- unsupported input;
- internal error;
- process failure;
- unrecognized output; and
- unsuccessful confirmation

into a semantic `EMPTY` claim.

A normalized result should expose only semantic information justified by the
validator-specific contract.

Operational information may be retained separately.

## Oracle Dependency Boundary

A generic metamorphic oracle may depend on:

- an independently established semantic relation;
- normalized validator results whose claim strength is explicit; and
- any additional validator contract stated by the experiment.

It must not depend directly on:

- raw subprocess return codes;
- validator-specific text parsing;
- undocumented output conventions; or
- assumptions introduced solely to force a non-indeterminate classification.

Validator-specific adapters belong below the generic oracle.

The raw validator runner remains below both layers.

## Research Interpretation

The absence of a non-trivial constraint under the current premises is a valid
research outcome.

It does not show that relation-aware validator testing is impossible in
general.

It shows only that the currently established relation classes, application
admission rules, and confirmation-level outcome information are insufficient
by themselves to produce a non-trivial pairwise oracle without adding further
justified premises.

Any later oracle must state those premises explicitly.
