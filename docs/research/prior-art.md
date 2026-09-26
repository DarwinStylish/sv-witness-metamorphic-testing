# Prior Art and Research Boundary

## Purpose

This document records the work closest to this project and the current boundary
of the research question.

The boundary is provisional and may change if later searches find closer work.

## SV-Witnesses and Witness Validation

SV-Witnesses are an exchange format for software-verification results [2, 6].

Correctness witnesses support reported proofs. Violation witnesses describe
reported property violations [2, 6].

The semantics of a violation witness describe a set of program executions that
violate the property. The witness is valid when this set is not empty [6].

Witness validation provides a way to check verification results independently
from the verifier that produced the witness [1, 2, 3].

SV-Witness version 2.2 is the latest tagged release at the time of this review
[7]. This project uses version 2.2 as its first semantic reference.

SV-COMP 2026 used witness formats 1.0, 2.0, and 2.1 [8]. Results from that
competition therefore do not by themselves establish validator support for
version 2.2.

## Existing Validator Evaluation

Witness validators have already been studied as software systems that can
produce incorrect results.

A 2022 case study tested several validators using witnesses produced by many
verification tools. It found cases where validators confirmed invalid witnesses
and proposed regular comparative evaluation of witness validators [1].

A witness-validation track was later added to SV-COMP [2, 8].

This work shows that testing witness validators is not a new research problem.

## Crafted Validation Tasks

SV-COMP includes validation tasks made specifically to test witness validators
[8].

The validation benchmarks include a `ValidationCrafted` category with crafted
tasks for correctness and violation witnesses [8].

These benchmarks provide fixed validation cases with expected results.

This project therefore does not claim that crafted testing of witness validators
is new.

## WitnessLint

The SV-Witness project provides WitnessLint [6].

WitnessLint checks whether a witness follows the syntax and format rules of the
SV-Witness standard [6].

Its role is different from the question studied here. This project focuses on
semantic relationships between related witnesses and the results reported by
witness validators.

## Validation via Verification

MetaVal introduced validation via verification [3].

Its method takes a program, specification, and witness and transforms the
verification problem so that an existing software verifier can take part in
witness validation [3].

This is close prior work because transformation is part of the validation
method.

The transformation has a different purpose from the one studied here. MetaVal
constructs a validation procedure from an existing verifier [3]. This project
studies transformations between related witnesses and the relationships they may
imply between validator results.

## Metamorphic and Related-Input Testing

Testing through relationships between related inputs is already established.

Equivalence Modulo Inputs creates related program variants and uses them to test
compilers [4].

STATFIER generates program variants through semantics-preserving
transformations and looks for inconsistent static-analysis results between the
original programs and their variants [5].

Skeletal Approximation Enumeration, implemented by Sparrow, tests SMT solvers
using mutations that under-approximate or over-approximate formulas [9]. The
known relationship between the original and mutated formulas gives a constraint
on the solver results [9].

This is especially close to the structure studied here. It shows that
metamorphic testing based on inclusion or approximation relationships, rather
than only equivalence, already exists.

Metamorphic testing has also been applied to formal-methods tools such as logic
theorem provers [10].

This project therefore does not claim a new general form of relation-based
metamorphic testing.

## Witness-Domain Transformations

Earlier work already transforms and reduces verification witnesses.

Stepwise testification uses a witness from one verifier as input to another
verification step [11].

Tests from Witnesses derives executable tests from violation witnesses [12].

Work on cooperative verification gives a common semantic view of verification
artifacts exchanged between tools [13].

Fault Localization on Verification Witnesses is especially close to this
project [14]. It takes a violation witness and produces a reduced violation
witness for the same verification task.

The reduction is proved to be a sound over-approximation. The reduced witness
describes a superset of the program paths described by the original witness
[14].

The study also measures how validators behave before and after the
transformation. Confirmation rates increase for some validator and witness
combinations and decrease for others [14].

This result is important here because it separates a semantic relationship
between witnesses from the operational behavior of a validator.

The Transformation Game treats witness transformers as a general kind of
verification component and surveys several uses of transformed witnesses [16].

More recent work also transforms test cases into violation witnesses so that
test generators can take part in formal-verification workflows [15].

TransVer provides modular transformations between verification tasks. Its tool
also supports witness transformations for results produced on transformed tasks
[17].

Recent work on termination witnesses also uses transformation-based workflows
for witness generation and validation [18].

In these transformation-based workflows, the program or verification task is
changed as part of the reduction [17, 18]. This project instead studies
witness-to-witness transformations while the verification task stays fixed.

Related witness-transformation work also appears in earlier theses.

Ovezova studies witness modification after side-effect-removal program
transformations so that verification results from transformed programs can be
validated against the original program [19].

Kriegelsteiner develops a transformation from reach-safety YAML witnesses to
no-overflow YAML witnesses [20]. The evaluation validates reachability
correctness witnesses and transformed no-overflow correctness witnesses and
compares the resulting outcomes [20].

Auer studies semantically equivalent correctness witnesses from the perspective
of a validator [21].

These works are close because they study witness transformation or semantic
equivalence. The first two accompany program or property transformations
[19, 20]. The third concerns correctness witnesses [21].

This prior work means that witness transformation, witness reduction, semantic
over-approximation, semantic equivalence between witnesses, and evaluation of
validators on transformed witnesses are not new by themselves.

## Candidate Research Gap

The current candidate gap concerns the use of witness semantics as an explicit
test oracle for witness validators.

Existing work already transforms violation witnesses, defines sound semantic
relationships between original and transformed witnesses, and evaluates
validators on the transformed witnesses [14].

Fault Localization on Verification Witnesses defines several witness-reduction
variants. The reductions produce sound over-approximations, and the evaluation
measures how the transformations affect validator confirmation rates [14].

The Transformation Game also defines witness transformers as a general class of
verification component [16].

These results leave a narrower question.

This project asks whether SV-Witness semantics can support a set of
transformations with explicit semantic relationships between the original and
transformed witnesses.

The relationships may include preservation, broadening, or narrowing of the
executions represented by a witness.

The project then asks whether those relationships can be mapped to testable
constraints on validator outcomes.

This differs from only measuring whether a transformation increases or
decreases a validator's confirmation rate. The project tests whether the
semantic relationship can serve as part of a metamorphic oracle.

Sparrow applies a closely related idea to SMT formulas. It uses known
under-approximation and over-approximation relationships as metamorphic
relations when testing SMT solvers [9].

The current search has not found work that applies this relation-aware
metamorphic-oracle structure to SV-Witness violation-witness validators while
keeping the verification task fixed.

This is a candidate research gap, not a novelty claim.

## Claims Not Made

The project does not claim that it is the first work to:

- test witness validators;
- create crafted witness-validation tasks;
- compare witness validators;
- transform verification artifacts;
- transform one verification witness into another;
- backtransform witnesses after program transformations;
- study semantic equivalence between correctness witnesses;
- reduce violation witnesses;
- derive tests from verification witnesses;
- generate violation witnesses from other verification artifacts;
- define witness transformers;
- establish an over-approximation relationship between related witnesses;
- evaluate validator confirmation rates after witness transformation;
- use metamorphic or related-input testing;
- use semantics-preserving transformations for software testing;
- use inclusion or approximation relationships in metamorphic testing;
- test compilers, static analyzers, SMT solvers, or theorem provers through
  related inputs; or
- validate witnesses independently from the verifier that produced them.

## Remaining Evidence Gaps

The prior-art review is still incomplete in several areas:

- papers and artifacts about SV-Witness validator testing;
- the full history of SV-COMP validation benchmarks;
- validator-specific test suites;
- work on mutation or transformation of verification witnesses;
- metamorphic testing of formal-methods tools;
- testing of proof and certificate checkers;
- transformation and translation of proof certificates;
- additional theses and technical reports outside the sources reviewed here;
  and
- work published while this project is in progress.

Closer prior work would narrow the candidate research gap.

## References

1. D. Beyer and J. Strejček, "Case Study on Verification-Witness Validators:
   Where We Are and Where We Go," SAS 2022.
   DOI: 10.1007/978-3-031-22308-2_8.

2. P. Ayaziová, D. Beyer, M. Lingsch-Rosenfeld, M. Spiessl, and J. Strejček,
   "Software Verification Witnesses 2.0," SPIN 2024.
   DOI: 10.1007/978-3-031-66149-5_11.

3. D. Beyer and M. Spiessl, "MetaVal: Witness Validation via Verification,"
   CAV 2020.
   DOI: 10.1007/978-3-030-53291-8_10.

4. V. Le, M. Afshari, and Z. Su, "Compiler Validation via Equivalence Modulo
   Inputs," PLDI 2014.
   DOI: 10.1145/2594291.2594334.

5. H. Zhang, Y. Pei, J. Chen, and S. H. Tan, "Statfier: Automated Testing of
   Static Analyzers via Semantic-Preserving Program Transformations,"
   ESEC/FSE 2023.
   DOI: 10.1145/3611643.3616272.

6. SV-Witnesses project, user guide, format schemas, and WitnessLint.
   Accessed 2026-09-25.

7. SV-Witnesses project, release tags. Release 2.2, 2026-08-17.
   Accessed 2026-09-25.

8. SV-COMP 2026, witness rules, validation benchmarks, and witness-validation
   results.
   Accessed 2026-09-25.

9. P. Yao, H. Huang, W. Tang, Q. Shi, R. Wu, and C. Zhang,
   "Skeletal Approximation Enumeration for SMT Solver Testing,"
   ESEC/FSE 2021.
   DOI: 10.1145/3468264.3468540.

10. O. A. Tazl and F. Wotawa,
    "Metamorphic Testing of Logic Theorem Prover," ICTSS 2021.
    DOI: 10.1007/978-3-031-04673-5_10.

11. D. Beyer, M. Dangl, D. Dietsch, M. Heizmann, and A. Stahlbauer,
    "Witness Validation and Stepwise Testification across Software Verifiers,"
    ESEC/FSE 2015.
    DOI: 10.1145/2786805.2786867.

12. D. Beyer, M. Dangl, T. Lemberger, and M. Tautschnig,
    "Tests from Witnesses: Execution-Based Validation of Verification Results,"
    TAP 2018.
    DOI: 10.1007/978-3-319-92994-1_1.

13. D. Beyer and H. Wehrheim,
    "Verification Artifacts in Cooperative Verification: Survey and Unifying
    Component Framework," ISoLA 2020.
    DOI: 10.1007/978-3-030-61362-4_8.

14. D. Beyer, M. Kettl, and T. Lemberger,
    "Fault Localization on Verification Witnesses," SPIN 2024.
    DOI: 10.1007/978-3-031-66149-5_12.

15. D. Beyer, T. Lemberger, and H. Wachowitz,
    "Testing in Formal Verification via Witness Generation (Empirical
    Evaluation)," FASE 2026.
    DOI: 10.1007/978-3-032-22774-4_22.

16. D. Beyer and N.-Z. Lee,
    "The Transformation Game: Joining Forces for Verification,"
    Principles of Verification: Cycling the Probabilistic Landscape, 2025.
    DOI: 10.1007/978-3-031-75778-5_9.

17. D. Beyer, M. Jankola, M. Lingsch-Rosenfeld, T. Xia, and X. Zheng,
    "TransVer: A Modular Program-Transformation Framework for Reduction to
    Reachability," SPIN 2025.
    DOI: 10.1007/978-3-032-06847-7_1.
    TransVer tool repository, accessed 2026-09-26.

18. D. Beyer, M. Jankola, and M. Lingsch-Rosenfeld,
    "Transition Invariants Revisited: Termination Witnesses and Their
    Validation," CAV 2026.
    DOI: 10.1007/978-3-032-32537-2_2.

19. A. Ovezova,
    "Witness Modifications for Program Transformations: A Case Study on
    Side-Effect Removal,"
    Bachelor's Thesis, LMU Munich, Software Systems Lab, 2024.

20. T. Kriegelsteiner,
    "Transformation of Reach Safety YAML Witnesses to No Overflow YAML
    Witnesses,"
    Bachelor's Thesis, LMU Munich, Software Systems Lab, 2024.

21. M. Auer,
    "Finding Semantically Equivalent Correctness Witnesses,"
    Bachelor's Thesis, LMU Munich, Software Systems Lab, 2025.
