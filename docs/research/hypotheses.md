# Research Hypotheses

## Purpose

This document states the initial hypotheses for SV-Witness Metamorphic Testing.

The hypotheses are provisional. Later semantic analysis, implementation, or
experiments may reject or narrow them.

## H1: Non-Trivial Semantic Relations Exist

There are transformations from one SV-Witness violation witness to another for
the same verification task where a non-trivial semantic relationship between
the two witnesses can be justified independently from the validator under test.

The relationship may preserve, broaden, or narrow what the witness represents.

Evidence against this hypothesis includes finding that non-trivial
transformations cannot be justified without:

- relying on the validator under test;
- rerunning the full verification task; or
- adding assumptions that fall outside the supported semantic profile.

## H2: Some Semantic Relations Constrain Validator Outcomes

At least some justified relationships between related witnesses give
non-trivial constraints on the outcomes of validator runs.

A constraint is non-trivial when it rules out at least one possible combination
of outcomes under its stated assumptions.

This hypothesis does not assume that every semantic relationship determines a
validator result.

Evidence against this hypothesis includes finding that the supported semantic
relationships rule out no validator-outcome combinations once incomplete
analysis, unsupported features, resource limits, and other run outcomes are
taken into account.

## H3: The Relations Survive Implementation

The transformations can be implemented while preserving the semantic
relationships established for them.

Evidence for this hypothesis includes transformation evidence and tests that
can be checked without trusting the validator under test.

Evidence against this hypothesis includes finding that the implementation
cannot preserve or demonstrate the claimed relationship without relying on the
validator being tested.

## H4: Some Observed Outcome Pairs Are Classifiable

When the derived constraints are applied to real validator runs, at least some
observed outcome pairs fall into a non-indeterminate class defined by the
semantic relationship and the outcome model.

The classification rules are established before the empirical evaluation.

A classification does not by itself establish a validator defect.

Evidence against this hypothesis includes finding that every observed outcome
pair remains indeterminate under the supported outcome model, including
incomplete analysis, unsupported features, resource limits, and other run
outcomes.

## Interpretation

The hypotheses address different stages of the method and can fail
separately.

For example:

- non-trivial semantic transformations may exist while placing no non-trivial
  constraints on validator outcomes;
- non-trivial constraints may exist in theory while being difficult to preserve
  in implementation; or
- the semantic and implementation stages may succeed while observed validator
  outcomes remain indeterminate.

A negative result in one of these areas remains part of the research result.

The semantic profile will define the supported witness semantics in more detail.
The transformation algebra will determine which semantic relationships can
actually be justified.
