# Problem Definition

## Context

SV-Witnesses are software-verification (SV) witnesses exchanged between
verification tools and witness validators. They include correctness witnesses
for proofs and violation witnesses for reported property violations.

This project studies the validation of violation witnesses. SV-Witness version
2.2 is the first semantic reference used by the project. Support for older
witness versions and specific validator implementations will be handled
separately.

## Research Question

Can we transform SV-Witness violation witnesses in ways that give known
semantic relationships between the original and transformed witnesses, and use
those relationships to test witness validators?

The method does not treat one validator as ground truth or depend on agreement
between several validators.

## Research Object

The project studies a witness-validation case made from:

- a fixed verification task;
- a violation witness; and
- a validator under test.

The verification task contains:

- the program;
- the property being checked; and
- the execution or machine assumptions needed by the task.

A witness transformation changes the witness but keeps the verification task
fixed.

The project studies transformations whose semantic relationship between the
original and transformed witnesses can be justified without relying on the
validator being tested.

The validator can then be run on both witnesses. Its results can be compared
with the semantic relationship between the witnesses.

A difference between the validator results does not by itself prove that the
validator is wrong. It may also come from incomplete analysis, unsupported
features, resource limits, or other validator behavior.

## Initial Scope

The first stage of the project is limited to:

- SV-Witness version 2.2 as the semantic reference;
- violation witnesses;
- sequential C programs;
- reachability-safety tasks based on `unreach-call`;
- transformations justified by the supported witness semantics; and
- validator results that can be reproduced through local execution.

The first stage does not cover:

- concurrency;
- termination properties;
- memory-safety properties;
- correctness witnesses; or
- GraphML witness format version 1.0.

The semantic profile may narrow this scope further if some features need extra
assumptions that the project cannot justify clearly.

## Validation Problem

A witness validator checks a witness in the context of its verification task and
reports whether it can validate the reported violation.

Testing a validator with only a fixed set of known witnesses gives limited
information about how it behaves on related witnesses.

A transformed witness may describe the relevant executions differently while
preserving, broadening, or narrowing what the original witness represents.

The project asks whether these relationships can be derived from the supported
SV-Witness semantics, implemented as controlled transformations, and used to
test validator behavior.

A difference between the results for related witnesses is not automatically a
defect. Its interpretation depends on the semantic relationship between the
witnesses and on how each validator run ended.

## Approach Under Study

The project studies a semantics-guided metamorphic-testing method for
SV-Witness violation-witness validators.

The method starts with a seed witness-validation case. It then:

1. creates a related witness;
2. records the semantic relationship between the two witnesses;
3. runs the validator on both witnesses; and
4. compares the validator results with that relationship.

Whether this method adds useful testing capability beyond existing
witness-validation methods is still a research question. The prior-art review
will define that boundary.

## Non-Goals

The first stage does not aim to:

- define a new witness format;
- replace or change the SV-Witness standard;
- build a general-purpose software verifier;
- build a new reference witness validator;
- prove that existing validators are fully correct;
- treat majority agreement between validators as proof of correctness;
- build a general-purpose metamorphic-testing framework;
- support every SV-Witness property or programming language; or
- treat every validator disagreement as a software defect.

## Success Criteria

The approach is useful if the project can:

- find non-trivial witness transformations whose semantic relationships can be
  justified within the supported semantic profile;
- implement those transformations without changing their intended
  relationships; and
- use the resulting relations to build reproducible checks over real validator
  runs.

The project does not need to find a validator defect to succeed.

If the tested validators satisfy the generated relations, that result can still
tell us something about the method and the scope that was tested.

## Failure Criteria

The approach may not be useful if:

- useful transformation relationships cannot be justified without relying on
  the validator being tested;
- establishing the semantic relationship requires running full verification
  again; or
- the resulting relationships do not place useful constraints on validator
  results.

Negative results are still part of the study. If the scope changes later, those
changes should be kept separate from results produced under the earlier scope.

## Open Questions

The next research stages need to answer:

- What semantic condition should mean that a violation witness is successfully
  confirmed?
- Which SV-Witness 2.2 features should be included in the first semantic
  profile?
- Which witness transformations preserve, broaden, or narrow the executions
  represented by a witness?
- What evidence is needed to justify each transformation?
- How should validator-specific results be normalized without losing important
  differences?
- Which validator and witness-format versions can be compared without assuming
  that different versions have the same semantics?
