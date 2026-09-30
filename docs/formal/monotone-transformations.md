# Monotone Transformations

## Purpose

This document defines concrete witness transformations whose semantic relation
is expressed by inclusion rather than equality.

The transformations are interpreted using the witness semantics in
[`semantic-profile.md`](semantic-profile.md) and the relation classes in
[`transformation-algebra.md`](transformation-algebra.md).

The first operator removes one selected `avoid` assumption waypoint from a
supported violation witness.

This document defines a semantic relation between witnesses. It does not define
validator outcome rules.

## Scope

Let

\[
\tau = (P, \varphi, M)
\]

be a fixed verification task and let

\[
W \in \mathcal{W}_\tau.
\]

Write the ordered segments of \(W\) as

\[
W = (s_1, s_2, \ldots, s_n).
\]

For segment \(s_i\), write its ordered waypoints as

\[
s_i =
(w_{i,1}, w_{i,2}, \ldots, w_{i,m_i}).
\]

The indices in this document are mathematical positions and begin at one.

The verification task remains unchanged by every transformation defined here.

## Avoid-Removal Operator

For a fixed pair of positions \((i,j)\), define

\[
R^{\mathrm{avoid}}_{\tau,i,j}
:
\mathcal{W}_\tau
\rightharpoonup
\mathcal{W}_\tau
\]

as the transformation that removes exactly waypoint \(w_{i,j}\) from segment
\(s_i\).

Every other waypoint is retained.

Every other segment is retained.

The transformation does not rewrite any remaining waypoint field.

### Preconditions

The operator is defined exactly when:

1. \(1 \le i \le n\);
2. \(1 \le j \le m_i\); and
3. \(w_{i,j}\) is an `assumption` waypoint whose action is `avoid`.

Equivalently, define

\[
\operatorname{Pre}^{\mathrm{avoid}}_{i,j,\tau}(W)
\]

to mean that the selected position exists and contains an `avoid` assumption
waypoint.

Then

\[
\operatorname{dom}
\left(
R^{\mathrm{avoid}}_{\tau,i,j}
\right)
=
\left\{
W \in \mathcal{W}_\tau
\;\middle|\;
\operatorname{Pre}^{\mathrm{avoid}}_{i,j,\tau}(W)
\right\}.
\]

The operator is therefore partial.

A witness containing no `avoid` assumption at the selected position is outside
the domain of that operator instance.

## Structural Preservation

The supported profile permits zero or more `avoid` assumption waypoints in
both normal and final segments. [1]

A supported normal segment also contains exactly one `follow` assumption
waypoint.

A supported final segment contains exactly one `target` waypoint.

Because the selected waypoint is required to be an `avoid` assumption, it is
neither the normal segment's required `follow` waypoint nor the final
segment's required target waypoint.

Removing it therefore preserves:

- the number and order of segments;
- whether each segment is normal or final;
- the unique `follow` waypoint of every normal segment;
- the unique target waypoint of the final segment;
- every remaining waypoint's type;
- every remaining waypoint's action;
- every remaining waypoint's constraint;
- every remaining waypoint's source location;
- every remaining waypoint's `thread_id`;
- the relative order of every remaining waypoint; and
- the verification task.

The selected segment remains non-empty because its required `follow` or target
waypoint remains present.

No waypoint is moved between segments.

## Avoid-Waypoint Semantics

SV-Witness 2.2 defines an `avoid` waypoint as a waypoint that must never be
passed. It may be evaluated any number of times, including zero times. [1]

Within the supported profile, an `avoid` assumption constrains an execution
only while its containing segment is current.

Removing one selected `avoid` waypoint therefore removes one waypoint-passing
obligation from that segment.

It does not introduce a new obligation.

Waypoint order within a segment does not itself impose evaluation order. [1]

## Broadening Theorem

For every

\[
W
\in
\operatorname{dom}
\left(
R^{\mathrm{avoid}}_{\tau,i,j}
\right),
\]

the avoid-removal operator is broadening:

\[
W
\sqsubseteq_\tau
R^{\mathrm{avoid}}_{\tau,i,j}(W).
\]

Equivalently,

\[
E_\tau(W)
\subseteq
E_\tau
\left(
R^{\mathrm{avoid}}_{\tau,i,j}(W)
\right).
\]

### Proof

Let

\[
e \in E_\tau(W).
\]

By the supported violation-sequence semantics, there exists a decomposition

\[
e =
\pi_1
\cdot
\pi_2
\cdots
\pi_n
\]

such that each execution part \(\pi_k\) matches segment \(s_k\).

Consider the selected segment \(s_i\).

Because \(\pi_i\) matches \(s_i\), the waypoint-passing semantics of every
waypoint in \(s_i\) are satisfied during \(\pi_i\).

In particular, the selected `avoid` waypoint is never passed while \(s_i\) is
current.

The transformed segment removes only this selected `avoid` waypoint.

Every remaining waypoint-passing obligation of \(s_i\) is unchanged and was
already satisfied by \(\pi_i\).

For a normal segment, the same unique `follow` waypoint remains present.
Therefore the condition determining the end of \(\pi_i\) is unchanged.

For the final segment, the same target waypoint remains present. Therefore the
required `unreach-call` violation condition is unchanged.

Hence the same execution part \(\pi_i\) matches the transformed segment.

Every segment \(s_k\) with \(k \ne i\) is unchanged, so each corresponding
execution part \(\pi_k\) still matches it.

The same decomposition therefore establishes that

\[
e
\in
E_\tau
\left(
R^{\mathrm{avoid}}_{\tau,i,j}(W)
\right).
\]

Since \(e\) was arbitrary,

\[
E_\tau(W)
\subseteq
E_\tau
\left(
R^{\mathrm{avoid}}_{\tau,i,j}(W)
\right).
\]

Thus the transformation is broadening.

## Strictness

Avoid removal is not claimed to be strictly broadening for every application.

The removed waypoint may impose no additional restriction on the executions
already represented by the witness.

For example, its evaluation point may not be reached while its segment is
current for any execution already admitted by the other segment conditions.

Therefore an individual application may satisfy

\[
E_\tau(W)
=
E_\tau
\left(
R^{\mathrm{avoid}}_{\tau,i,j}(W)
\right)
\]

or may satisfy strict inclusion

\[
E_\tau(W)
\subset
E_\tau
\left(
R^{\mathrm{avoid}}_{\tau,i,j}(W)
\right).
\]

The base classification is broadening in both cases.

Determining strictness requires additional semantic evidence and is not part of
the operator definition.

## Validity Preservation

The input witness belongs to \(\mathcal{W}_\tau\), so it is already a valid,
profile-supported witness with non-empty represented-execution set.

The transformation preserves all required `follow` and target waypoints and
removes only one optional `avoid` assumption.

SV-Witness 2.2 permits an arbitrary number of `avoid` waypoints in a segment,
including zero. [1]

The transformation therefore preserves the segment forms required by the
supported profile.

All retained waypoint fields come unchanged from the valid input witness.

Because the transformation is broadening,

\[
E_\tau(W)
\subseteq
E_\tau
\left(
R^{\mathrm{avoid}}_{\tau,i,j}(W)
\right)
\]

and

\[
E_\tau(W)
\ne
\varnothing,
\]

so

\[
E_\tau
\left(
R^{\mathrm{avoid}}_{\tau,i,j}(W)
\right)
\ne
\varnothing.
\]

Thus removal does not create an empty represented-execution set.

This argument is specific to removal of a selected `avoid` assumption in the
supported profile. It is not a general rule that deleting arbitrary witness
elements preserves validity.

## Repeated Removal

A sequence of avoid-removal transformations is broadening when each operator is
defined on the witness produced by the preceding operator.

This follows from transitivity of semantic inclusion.

No claim is made here that raw positional selectors commute.

Removing one waypoint changes later waypoint positions within the same segment,
so a subsequent implementation-level position must refer to the current
witness representation.

## Implementation Boundary

A concrete implementation may operate directly on the internal
`ViolationSequence` model without receiving \(\tau\) as a runtime argument.

The runtime implementation may use zero-based Python indices even though the
formal positions in this document begin at one.

The implementation must reject or otherwise leave undefined applications in
which:

- the segment position does not exist;
- the waypoint position does not exist;
- the selected waypoint is not an assumption waypoint; or
- the selected assumption does not have action `avoid`.

Implementation tests must establish at least that:

- exactly the selected `avoid` waypoint is removed;
- removal works in normal segments;
- removal works in the final segment;
- all other waypoints are retained unchanged;
- segment order is preserved;
- remaining waypoint order is preserved;
- the required normal `follow` waypoint is retained;
- the final target is retained;
- the input witness is not mutated; and
- out-of-domain selections are rejected.

Unit tests establish implementation behavior. They do not by themselves prove
the semantic inclusion theorem above.

## Exclusions

This document does not classify the following operations:

- insertion of an `avoid` waypoint;
- removal of a `follow` waypoint;
- removal of a target waypoint;
- removal of an arbitrary assumption waypoint;
- assumption-expression rewriting;
- source-location rewriting;
- `thread_id` rewriting;
- segment insertion;
- segment deletion;
- segment splitting;
- segment merging; or
- segment reordering.

In particular, insertion of an `avoid` waypoint is not included here as a
narrowing operator. A narrowing result requires an independent non-emptiness
argument before it can be admitted to \(\mathcal{W}_\tau\).

## References

[1]: https://gitlab.com/sosy-lab/benchmarking/sv-witnesses/-/blob/2.2/user-guide/Witness-Format.md
