# Exact Transformations

## Purpose

This document defines the first concrete witness transformations used by
SV-Witness Metamorphic Testing.

The operators are interpreted using the witness semantics in
[`semantic-profile.md`](semantic-profile.md) and the relation classes in
[`transformation-algebra.md`](transformation-algebra.md).

This document defines transformation semantics. It does not define validator
outcome rules or claim that a particular validator must behave identically on
the transformed syntax.

## Scope

The operators in this document apply to the supported sequential
SV-Witness 2.2 violation-witness profile.

Let

\[
\tau = (P, \varphi, M)
\]

be a fixed verification task and let

\[
W \in \mathcal{W}_\tau.
\]

The verification task remains unchanged by every transformation defined here.

The only witness field modified by these operators is `thread_id`.

## Main-Thread Representation

Within the supported profile, every waypoint belongs to the main thread.

SV-Witness 2.2 assigns the same thread denotation to:

- an absent `thread_id`; and
- an explicit `thread_id: 0`.

The internal witness model deliberately retains these two representations as
distinct syntax.

This makes it possible to transform between the two representations without
changing which thread a waypoint denotes.

## Explicit Main-Thread Operator

Define

\[
T^0_\tau :
\mathcal{W}_\tau
\longrightarrow
\mathcal{W}_\tau
\]

as the whole-witness transformation that replaces every absent supported
waypoint `thread_id` with `0`.

For every waypoint:

- `thread_id = None` becomes `thread_id = 0`;
- `thread_id = 0` remains `thread_id = 0`.

All other waypoint fields are retained unchanged.

Waypoint order, segment structure, and segment order are retained unchanged.

### Domain

The operator is total on \(\mathcal{W}_\tau\).

It has no additional operator-specific semantic precondition beyond membership
of the input witness in the supported witness universe.

A particular application need not change the witness syntax. A witness whose
waypoints already all use explicit `thread_id: 0` remains syntactically
unchanged.

### Idempotence

For every

\[
W \in \mathcal{W}_\tau,
\]

\[
T^0_\tau(T^0_\tau(W))
=
T^0_\tau(W)
\]

at the witness-representation level.

## Implicit Main-Thread Operator

Define

\[
T^\varnothing_\tau :
\mathcal{W}_\tau
\longrightarrow
\mathcal{W}_\tau
\]

as the whole-witness transformation that removes explicit main-thread
identifiers from every supported waypoint.

For every waypoint:

- `thread_id = 0` becomes absent;
- an absent `thread_id` remains absent.

All other waypoint fields are retained unchanged.

Waypoint order, segment structure, and segment order are retained unchanged.

### Domain

The operator is total on \(\mathcal{W}_\tau\).

It has no additional operator-specific semantic precondition beyond membership
of the input witness in the supported witness universe.

A particular application need not change the witness syntax. A witness whose
waypoints already all omit `thread_id` remains syntactically unchanged.

### Idempotence

For every

\[
W \in \mathcal{W}_\tau,
\]

\[
T^\varnothing_\tau(T^\varnothing_\tau(W))
=
T^\varnothing_\tau(W)
\]

at the witness-representation level.

## Exactness

Both operators are exact.

Consider any waypoint in a supported witness. Replacing an absent `thread_id`
with `0`, or replacing `0` with absence, does not change the thread denoted by
that waypoint: both representations denote the main thread.

The operators do not change:

- waypoint type;
- waypoint action;
- assumption constraint;
- source location;
- waypoint order;
- segment structure;
- segment order; or
- the verification task.

Therefore an execution reaches and evaluates each transformed waypoint under
the same thread condition as before.

The conditions for matching every segment are consequently unchanged.

Thus, for every

\[
W \in \mathcal{W}_\tau,
\]

\[
E_\tau(T^0_\tau(W))
=
E_\tau(W)
\]

and

\[
E_\tau(T^\varnothing_\tau(W))
=
E_\tau(W).
\]

Hence

\[
T^0_\tau(W) \equiv_\tau W
\]

and

\[
T^\varnothing_\tau(W) \equiv_\tau W.
\]

## Validity Preservation

The transformations preserve the witness fields and structural relationships
other than the two equivalent main-thread representations.

Both resulting `thread_id` forms are admitted by the supported profile and by
SV-Witness 2.2.

For an input witness in \(\mathcal{W}_\tau\), exactness preserves
represented-execution non-emptiness.

The operators therefore introduce no new validity obligation concerning
`thread_id`.

This statement does not turn construction of the project's internal witness
model into a general proof of SV-Witness validity. The exactness claim applies
to inputs already established to belong to \(\mathcal{W}_\tau\).

## Composition of the Two Operators

The operators choose opposite canonical representations.

For every supported witness,

\[
T^0_\tau(T^\varnothing_\tau(W))
=
T^0_\tau(W)
\]

and

\[
T^\varnothing_\tau(T^0_\tau(W))
=
T^\varnothing_\tau(W)
\]

at the witness-representation level.

Both compositions remain exact because exact transformations are closed under
composition.

The two operators are not inverses over witness syntax because each discards
the previous choice between absent and explicit main-thread representation.

## Implementation Boundary

A concrete implementation may operate on the internal `ViolationSequence`
model without receiving \(\tau\) as a runtime argument.

This does not make the semantic transformation task-independent.

The notation \(T_\tau\) records that the exactness claim is interpreted for a
fixed task and for witnesses in \(\mathcal{W}_\tau\). The implementation itself
does not need to inspect the task because the changed field has the same
denotation throughout the supported profile.

Implementation correctness remains separate from the semantic classification.

Tests must establish at least that the implementation:

- changes only `thread_id`;
- handles assumption and target waypoints;
- applies across every segment;
- preserves waypoint and segment ordering;
- preserves already canonical witnesses;
- is idempotent; and
- realizes the stated composition behavior.

## Exclusions

This document does not classify any other syntax edit as exact.

In particular, it makes no exactness claim for:

- assumption-expression rewriting;
- addition or removal of assumption waypoints;
- waypoint reordering;
- source-location rewriting;
- removal of optional location fields;
- segment insertion, deletion, reordering, splitting, or merging;
- target relocation; or
- non-zero thread identifiers.

Those cases require separate semantic arguments.
