# Transformation Algebra

## Purpose

This document defines the semantic relations used to classify witness
transformations in SV-Witness Metamorphic Testing.

The algebra is defined over the represented-execution semantics established in
[`semantic-profile.md`](semantic-profile.md).

It does not define concrete transformation operators or validator-outcome
rules.

## Fixed Verification Task

Let

$$
\tau = (P, \varphi, M)
$$

be a verification task in the supported semantic profile.

Every transformation in this algebra keeps $\tau$ fixed. A transformation may
change a witness, but it does not change the program, checked specification, or
execution context.

For a witness $W$, the semantic profile defines

$$
E_\tau(W)
$$

as the set of feasible executions represented by $W$ for task $\tau$.

All relations below compare witnesses using this represented-execution set.

## Witness Universe

Let

$$
\mathcal{W}_\tau
$$

denote the set of witnesses that:

- are bound to the fixed task $\tau$;
- are inside the supported project profile; and
- are valid with respect to SV-Witness 2.2.

Membership in $\mathcal{W}_\tau$ therefore requires more than a supported
surface syntax. The witness must satisfy the applicable schema and guide rules.

For every $W \in \mathcal{W}_\tau$,

$$
E_\tau(W) \neq \varnothing.
$$

Non-emptiness is necessary for a supported violation witness to be valid, but
it is not by itself sufficient for SV-Witness validity.

## Semantic Inclusion

For witnesses $W_1, W_2 \in \mathcal{W}_\tau$, define

$$
W_1 \sqsubseteq_\tau W_2
\quad\Longleftrightarrow\quad
E_\tau(W_1) \subseteq E_\tau(W_2).
$$

Thus, $W_1 \sqsubseteq_\tau W_2$ means that every execution represented by
$W_1$ is also represented by $W_2$.

The relation $\sqsubseteq_\tau$ is reflexive and transitive.

It is not necessarily antisymmetric over witness syntax. Two syntactically
different witnesses may represent the same execution set.

## Semantic Equivalence

Define

$$
W_1 \equiv_\tau W_2
\quad\Longleftrightarrow\quad
E_\tau(W_1) = E_\tau(W_2).
$$

Equivalently,

$$
W_1 \equiv_\tau W_2
\quad\Longleftrightarrow\quad
W_1 \sqsubseteq_\tau W_2
\;\land\;
W_2 \sqsubseteq_\tau W_1.
$$

Semantic equivalence is an equivalence relation over
$\mathcal{W}_\tau$.

It does not require syntactic equality.

If witnesses are quotiented by $\equiv_\tau$, semantic inclusion induces a
partial order over the resulting equivalence classes.

## Strict Inclusion

Define strict semantic inclusion by

$$
W_1 \sqsubset_\tau W_2
\quad\Longleftrightarrow\quad
E_\tau(W_1) \subset E_\tau(W_2).
$$

Strict inclusion records an actual change in represented executions.

The base transformation classes below use non-strict inclusion. This allows an
operator to have the same classification across inputs even when a particular
application happens to preserve the represented set exactly.

The base classes are therefore not disjoint. Every exact transformation is both
narrowing and broadening. Conversely, any transformation that is both narrowing
and broadening is exact.

Strictness is a property of an individual transformation application. A
strictly narrowing or strictly broadening application is not exact for that
application.

## Partial Transformations

A semantic transformation for task $\tau$ is modeled as a partial function

$$
T_\tau :
\mathcal{W}_\tau
\rightharpoonup
\mathcal{W}_\tau.
$$

The transformation is partial because a concrete operator may have
operator-specific semantic preconditions.

Let

$$
\operatorname{Pre}_{T,\tau}(W)
$$

denote the precondition predicate for $T_\tau$. Its domain is

$$
\operatorname{dom}(T_\tau)
=
\left\{
W \in \mathcal{W}_\tau
\;\middle|\;
\operatorname{Pre}_{T,\tau}(W)
\right\}.
$$

A transformation specification is well-formed only if its preconditions imply
that every defined result $T_\tau(W)$ belongs to $\mathcal{W}_\tau$.

Domain membership is a semantic property determined by the operator and its
precondition predicate. Whether sufficient evidence has been established for a
particular application is a separate evidential question.

A concrete implementation may construct an intermediate witness candidate.
Such a candidate is not an admitted result of $T_\tau$ until the required
profile, validity, and semantic obligations have been established.

## Exact Transformations

A transformation $T_\tau$ is **exact** when

$$
\forall W \in \operatorname{dom}(T_\tau):
\quad
T_\tau(W) \equiv_\tau W.
$$

Equivalently,

$$
E_\tau(T_\tau(W))
=
E_\tau(W).
$$

Exactness concerns represented executions. It does not imply that the two
witnesses have identical syntax, metadata, waypoint order, or other
representation details.

## Narrowing Transformations

A transformation $T_\tau$ is **narrowing** when

$$
\forall W \in \operatorname{dom}(T_\tau):
\quad
T_\tau(W) \sqsubseteq_\tau W.
$$

Equivalently,

$$
E_\tau(T_\tau(W))
\subseteq
E_\tau(W).
$$

A particular application is **strictly narrowing** when

$$
E_\tau(T_\tau(W))
\subset
E_\tau(W).
$$

A narrowing relation alone does not establish that the transformed witness
represents any execution.

In particular,

$$
E_\tau(T_\tau(W))
\subseteq
E_\tau(W)
$$

is compatible with

$$
E_\tau(T_\tau(W))
=
\varnothing.
$$

Therefore, a narrowing transformation requires an independent argument that
its result is non-empty before the result can be admitted to
$\mathcal{W}_\tau$.

## Broadening Transformations

A transformation $T_\tau$ is **broadening** when

$$
\forall W \in \operatorname{dom}(T_\tau):
\quad
W \sqsubseteq_\tau T_\tau(W).
$$

Equivalently,

$$
E_\tau(W)
\subseteq
E_\tau(T_\tau(W)).
$$

A particular application is **strictly broadening** when

$$
E_\tau(W)
\subset
E_\tau(T_\tau(W)).
$$

Because $W \in \mathcal{W}_\tau$ implies

$$
E_\tau(W) \neq \varnothing,
$$

the broadening relation implies

$$
E_\tau(T_\tau(W)) \neq \varnothing.
$$

This establishes the non-emptiness requirement only. It does not establish all
other SV-Witness validity requirements for the transformed witness.

## Validity Obligations

A semantic relation between $W$ and a transformed candidate $W'$ does not by
itself establish that $W'$ belongs to $\mathcal{W}_\tau$.

Every admitted transformation result must separately satisfy the applicable
profile and SV-Witness validity conditions, including requirements concerning
structure, locations, expressions, waypoint forms, task binding, and other
format rules.

The represented-execution relation contributes differently to the
non-emptiness obligation:

- for an exact transformation, non-emptiness follows from equality with the
  denotation of the valid input witness;
- for a broadening transformation, non-emptiness follows from inclusion of the
  valid input witness's denotation;
- for a narrowing transformation, non-emptiness must be established
  separately.

These implications concern non-emptiness only and do not replace the remaining
validity obligations.

## Transformation Preconditions

Each concrete transformation defines explicit preconditions.

A precondition may restrict:

- the waypoint or segment structure to which the operator applies;
- source locations;
- constraint expressions;
- relationships between program locations or expressions;
- metadata fields relevant to the fixed task; or
- other properties needed by the semantic argument.

A transformation claim applies only when its stated preconditions hold.

For a concrete witness, the project admits a transformation application only
after the relevant preconditions have been established. Failure to establish
them leaves that application unadmitted; it does not by itself imply that the
mathematical precondition is false.

## Semantic Evidence

A claimed transformation relation must be justified independently of the
validator under test.

The justification may use:

- the frozen semantic profile;
- the fixed verification task;
- the input witness;
- the transformed witness;
- the transformation's stated preconditions; and
- checks or derivations that establish the local semantic side conditions of
  the transformation.

Validator outcomes are not evidence for the semantic relation.

The semantic justification must not require rerunning the full verification
task merely to determine which relation holds.

If establishing a relation requires the validator under test or full
re-verification of the task, that relation is not admitted as independently
justified by this project.

## Composition

Let $T_\tau$ and $U_\tau$ be partial transformations.

Their composition

$$
(U_\tau \circ T_\tau)(W)
=
U_\tau(T_\tau(W))
$$

is defined exactly when

$$
W \in \operatorname{dom}(T_\tau)
$$

and

$$
T_\tau(W) \in \operatorname{dom}(U_\tau).
$$

For defined compositions, the following relation classes are closed under
composition:

- exact followed by exact is exact;
- narrowing followed by narrowing is narrowing;
- broadening followed by broadening is broadening;
- composing an exact transformation with a narrowing transformation, in either
  order, is narrowing;
- composing an exact transformation with a broadening transformation, in
  either order, is broadening.

No general exact, narrowing, or broadening classification follows from
composing a narrowing transformation with a broadening transformation.

The result depends on the concrete denotations.

## Identity

The identity transformation is the total map

$$
I_\tau :
\mathcal{W}_\tau
\longrightarrow
\mathcal{W}_\tau,
\qquad
I_\tau(W) = W.
$$

It is exact.

The existence of identity and the composition properties above are ordinary
consequences of equality and set inclusion. They are algebraic properties of
the semantic model, not empirical findings.

## Relation Classes Are Not Validator Outcomes

Exact, narrowing, and broadening classify relationships between represented
execution sets.

They do not directly classify validator runs.

In particular, the algebra does not assume:

- validator completeness;
- validator monotonicity with respect to semantic inclusion;
- identical validator behavior on semantically equivalent syntax;
- successful processing of every supported witness; or
- that disagreement between related runs establishes a defect.

Any mapping from these semantic relations to constraints on validator outcomes
requires a separate operational outcome model.

## Relation Classes Are Not Transformation Correctness

Classifying the intended relation of a transformation does not establish that
an implementation realizes that relation.

For a concrete implementation, the project must separately establish that:

- its preconditions are checked correctly;
- the produced witness satisfies the required profile and validity conditions;
- the implementation performs the intended witness change; and
- the claimed relation between represented-execution sets holds.

The algebra describes the semantic contract that an implementation must meet.

## Scope

This algebra defines:

- the witness universe used for transformation reasoning;
- semantic inclusion and equivalence;
- exact, narrowing, and broadening transformation classes;
- strict forms for individual applications;
- transformation domains and preconditions;
- validity and non-emptiness obligations;
- admissible sources of semantic evidence; and
- basic composition properties.

It does not define:

- concrete witness transformations;
- algorithms for proving arbitrary witness validity;
- a general decision procedure for semantic inclusion;
- validator outcome classes;
- metamorphic oracle rules; or
- empirical classification of validator behavior.
