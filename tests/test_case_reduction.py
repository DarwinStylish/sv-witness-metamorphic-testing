from typing import cast

import pytest

from sv_witness_metamorphic_testing.case_reduction import (
    CaseReductionError,
    InterestingnessPredicate,
    case_size,
    reduce_case,
    single_step_reductions,
)
from sv_witness_metamorphic_testing.exact_transformations import (
    explicit_main_thread,
    implicit_main_thread,
)
from sv_witness_metamorphic_testing.monotone_transformations import (
    remove_avoid_assumption,
)
from sv_witness_metamorphic_testing.semantic_relation import (
    BaseRelation,
)
from sv_witness_metamorphic_testing.task_model import (
    DataModel,
    ExecutionContext,
    Language,
    Program,
    ProgramInput,
    Sha256Digest,
    Specification,
    VerificationTask,
)
from sv_witness_metamorphic_testing.transformation_evidence import (
    AvoidRemovalApplication,
    ExplicitMainThreadApplication,
    ImplicitMainThreadApplication,
    TransformationApplication,
    TransformationLocalEvidence,
)
from sv_witness_metamorphic_testing.witness_model import (
    AssumptionAction,
    AssumptionWaypoint,
    CExpression,
    FinalSegment,
    Location,
    NormalSegment,
    TargetWaypoint,
    ViolationSequence,
)


def task() -> VerificationTask:
    return VerificationTask(
        program=Program(
            inputs=(
                ProgramInput(
                    path="example.c",
                    sha256=Sha256Digest(value="a" * 64),
                ),
            )
        ),
        specification=Specification(
            text=("CHECK( init(main()), LTL(G ! call(__VERIFIER_error())) )")
        ),
        execution_context=ExecutionContext(
            language=Language.C,
            data_model=DataModel.LP64,
        ),
    )


def assumption(
    action: AssumptionAction,
    *,
    expression: str,
    line: int,
    thread_id: int | None = None,
) -> AssumptionWaypoint:
    return AssumptionWaypoint(
        action=action,
        constraint=CExpression(
            value=expression,
        ),
        location=Location(
            file_name="example.c",
            line=line,
            column=3,
            function="main",
        ),
        thread_id=thread_id,
    )


def target(
    *,
    line: int,
    thread_id: int | None = None,
) -> TargetWaypoint:
    return TargetWaypoint(
        location=Location(
            file_name="example.c",
            line=line,
            column=5,
            function="main",
        ),
        thread_id=thread_id,
    )


def witness(
    *,
    normal_avoids: tuple[str, ...] = (
        "a",
        "b",
    ),
    final_avoids: tuple[str, ...] = ("c",),
    thread_id: int | None = None,
) -> ViolationSequence:
    normal_waypoints = (
        *(
            assumption(
                AssumptionAction.AVOID,
                expression=label,
                line=10 + index,
                thread_id=thread_id,
            )
            for index, label in enumerate(normal_avoids)
        ),
        assumption(
            AssumptionAction.FOLLOW,
            expression="follow",
            line=40,
            thread_id=thread_id,
        ),
    )

    final_waypoints: tuple[AssumptionWaypoint | TargetWaypoint, ...] = (
        *(
            assumption(
                AssumptionAction.AVOID,
                expression=label,
                line=50 + index,
                thread_id=thread_id,
            )
            for index, label in enumerate(final_avoids)
        ),
        target(
            line=90,
            thread_id=thread_id,
        ),
    )

    return ViolationSequence(
        segments=(
            NormalSegment(
                waypoints=normal_waypoints,
            ),
            FinalSegment(
                waypoints=final_waypoints,
            ),
        )
    )


def transformed_for(
    source: ViolationSequence,
    application: TransformationApplication,
) -> ViolationSequence:
    if isinstance(
        application,
        ExplicitMainThreadApplication,
    ):
        return explicit_main_thread(source)

    if isinstance(
        application,
        ImplicitMainThreadApplication,
    ):
        return implicit_main_thread(source)

    return remove_avoid_assumption(
        source,
        application.segment_index,
        application.waypoint_index,
    )


def relation_case(
    source: ViolationSequence,
    application: TransformationApplication,
) -> TransformationLocalEvidence:
    return TransformationLocalEvidence(
        task=task(),
        source=source,
        transformed=transformed_for(
            source,
            application,
        ),
        application=application,
    )


def avoid_labels(
    source: ViolationSequence,
) -> tuple[str, ...]:
    return tuple(
        waypoint.constraint.value
        for segment in source.segments
        for waypoint in segment.waypoints
        if (
            isinstance(
                waypoint,
                AssumptionWaypoint,
            )
            and waypoint.action is AssumptionAction.AVOID
        )
    )


def test_case_size_counts_source_waypoints() -> None:
    case = relation_case(
        witness(),
        ExplicitMainThreadApplication(),
    )
    expected_size = 5

    assert case_size(case) == expected_size


def test_case_size_rejects_wrong_runtime_type() -> None:
    with pytest.raises(
        CaseReductionError,
        match=("case must be a TransformationLocalEvidence"),
    ):
        case_size(
            cast(
                TransformationLocalEvidence,
                object(),
            )
        )


def test_explicit_candidates_follow_source_order() -> None:
    case = relation_case(
        witness(),
        ExplicitMainThreadApplication(),
    )

    candidates = single_step_reductions(case)

    assert tuple(avoid_labels(candidate.source) for candidate in candidates) == (
        ("b", "c"),
        ("a", "c"),
        ("a", "b"),
    )


def test_explicit_candidates_rebuild_transformed_side() -> None:
    case = relation_case(
        witness(),
        ExplicitMainThreadApplication(),
    )

    for candidate in single_step_reductions(case):
        assert candidate.transformed == explicit_main_thread(candidate.source)
        assert isinstance(
            candidate.application,
            ExplicitMainThreadApplication,
        )
        assert candidate.base_relation is BaseRelation.EXACT
        assert candidate.task is case.task


def test_implicit_candidates_rebuild_transformed_side() -> None:
    case = relation_case(
        witness(thread_id=0),
        ImplicitMainThreadApplication(),
    )

    for candidate in single_step_reductions(case):
        assert candidate.transformed == implicit_main_thread(candidate.source)
        assert isinstance(
            candidate.application,
            ImplicitMainThreadApplication,
        )
        assert candidate.base_relation is BaseRelation.EXACT


def test_avoid_case_skips_distinguished_waypoint() -> None:
    case = relation_case(
        witness(),
        AvoidRemovalApplication(
            segment_index=0,
            waypoint_index=1,
        ),
    )

    candidates = single_step_reductions(case)

    assert tuple(avoid_labels(candidate.source) for candidate in candidates) == (
        ("b", "c"),
        ("a", "b"),
    )

    assert all("b" in avoid_labels(candidate.source) for candidate in candidates)


def test_earlier_same_segment_removal_adjusts_distinguished_index() -> None:
    case = relation_case(
        witness(
            normal_avoids=(
                "a",
                "b",
                "c",
            ),
            final_avoids=(),
        ),
        AvoidRemovalApplication(
            segment_index=0,
            waypoint_index=1,
        ),
    )

    candidates = single_step_reductions(case)

    first = candidates[0]

    assert avoid_labels(first.source) == (
        "b",
        "c",
    )
    assert first.application == (
        AvoidRemovalApplication(
            segment_index=0,
            waypoint_index=0,
        )
    )
    assert avoid_labels(first.transformed) == ("c",)


def test_later_same_segment_removal_keeps_distinguished_index() -> None:
    case = relation_case(
        witness(
            normal_avoids=(
                "a",
                "b",
                "c",
            ),
            final_avoids=(),
        ),
        AvoidRemovalApplication(
            segment_index=0,
            waypoint_index=1,
        ),
    )

    candidates = single_step_reductions(case)

    later = candidates[1]

    assert avoid_labels(later.source) == (
        "a",
        "b",
    )
    assert later.application == (
        AvoidRemovalApplication(
            segment_index=0,
            waypoint_index=1,
        )
    )
    assert avoid_labels(later.transformed) == ("a",)


def test_other_segment_removal_keeps_distinguished_index() -> None:
    case = relation_case(
        witness(),
        AvoidRemovalApplication(
            segment_index=0,
            waypoint_index=1,
        ),
    )

    candidates = single_step_reductions(case)
    other_segment = candidates[1]

    assert avoid_labels(other_segment.source) == (
        "a",
        "b",
    )
    assert other_segment.application == (
        AvoidRemovalApplication(
            segment_index=0,
            waypoint_index=1,
        )
    )


def test_final_segment_distinguished_index_adjusts() -> None:
    case = relation_case(
        witness(
            normal_avoids=(),
            final_avoids=(
                "c",
                "d",
            ),
        ),
        AvoidRemovalApplication(
            segment_index=1,
            waypoint_index=1,
        ),
    )

    candidates = single_step_reductions(case)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert avoid_labels(candidate.source) == ("d",)
    assert candidate.application == (
        AvoidRemovalApplication(
            segment_index=1,
            waypoint_index=0,
        )
    )
    assert avoid_labels(candidate.transformed) == ()


def test_avoid_candidates_preserve_broadening_relation() -> None:
    case = relation_case(
        witness(),
        AvoidRemovalApplication(
            segment_index=0,
            waypoint_index=1,
        ),
    )

    for candidate in single_step_reductions(case):
        assert candidate.base_relation is BaseRelation.BROADENING


def test_duplicate_reconstructed_cases_are_suppressed() -> None:
    duplicate = assumption(
        AssumptionAction.AVOID,
        expression="same",
        line=10,
    )

    source = ViolationSequence(
        segments=(
            NormalSegment(
                waypoints=(
                    duplicate,
                    duplicate,
                    assumption(
                        AssumptionAction.FOLLOW,
                        expression="follow",
                        line=40,
                    ),
                )
            ),
            FinalSegment(waypoints=(target(line=90),)),
        )
    )

    case = relation_case(
        source,
        ExplicitMainThreadApplication(),
    )

    candidates = single_step_reductions(case)

    assert len(candidates) == 1
    assert avoid_labels(candidates[0].source) == ("same",)


def test_case_without_eligible_avoids_has_no_candidates() -> None:
    case = relation_case(
        witness(
            normal_avoids=(),
            final_avoids=(),
        ),
        ExplicitMainThreadApplication(),
    )

    assert single_step_reductions(case) == ()


def test_candidate_generation_does_not_mutate_case() -> None:
    case = relation_case(
        witness(),
        ExplicitMainThreadApplication(),
    )

    source_before = case.source
    transformed_before = case.transformed

    _ = single_step_reductions(case)

    assert case.source == source_before
    assert case.transformed == transformed_before


def test_every_candidate_is_exactly_one_waypoint_smaller() -> None:
    case = relation_case(
        witness(),
        ExplicitMainThreadApplication(),
    )

    for candidate in single_step_reductions(case):
        assert case_size(candidate) == (case_size(case) - 1)


def test_single_step_reductions_reject_wrong_runtime_type() -> None:
    with pytest.raises(
        CaseReductionError,
        match=("case must be a TransformationLocalEvidence"),
    ):
        single_step_reductions(
            cast(
                TransformationLocalEvidence,
                object(),
            )
        )


def test_reduce_case_accept_all_removes_all_eligible_avoids() -> None:
    case = relation_case(
        witness(),
        ExplicitMainThreadApplication(),
    )

    reduced = reduce_case(
        case,
        lambda candidate: True,
    )

    expected_size = 2

    assert avoid_labels(reduced.source) == ()
    assert case_size(reduced) == expected_size
    assert reduced.transformed == explicit_main_thread(reduced.source)
    assert reduced.base_relation is BaseRelation.EXACT


def test_reduce_avoid_case_retains_distinguished_waypoint() -> None:
    case = relation_case(
        witness(),
        AvoidRemovalApplication(
            segment_index=0,
            waypoint_index=1,
        ),
    )

    reduced = reduce_case(
        case,
        lambda candidate: True,
    )

    assert avoid_labels(reduced.source) == ("b",)

    assert reduced.application == (
        AvoidRemovalApplication(
            segment_index=0,
            waypoint_index=0,
        )
    )

    assert avoid_labels(reduced.transformed) == ()

    assert reduced.base_relation is BaseRelation.BROADENING


def test_repeated_earlier_removals_rebase_distinguished_index() -> None:
    case = relation_case(
        witness(
            normal_avoids=(
                "a",
                "b",
                "c",
            ),
            final_avoids=(),
        ),
        AvoidRemovalApplication(
            segment_index=0,
            waypoint_index=2,
        ),
    )

    reduced = reduce_case(
        case,
        lambda candidate: True,
    )

    assert avoid_labels(reduced.source) == ("c",)

    assert reduced.application == (
        AvoidRemovalApplication(
            segment_index=0,
            waypoint_index=0,
        )
    )

    assert avoid_labels(reduced.transformed) == ()


def test_reduce_case_uses_first_accept_and_restarts() -> None:
    case = relation_case(
        witness(),
        ExplicitMainThreadApplication(),
    )

    observed: list[tuple[str, ...]] = []

    def interesting(
        candidate: TransformationLocalEvidence,
    ) -> bool:
        labels = avoid_labels(candidate.source)

        observed.append(labels)

        return "a" in labels

    reduced = reduce_case(
        case,
        interesting,
    )

    assert avoid_labels(reduced.source) == ("a",)

    assert observed == [
        ("a", "b", "c"),
        ("b", "c"),
        ("a", "c"),
        ("c",),
        ("a",),
        (),
    ]


def test_reduce_case_returns_original_when_no_candidate_is_accepted() -> None:
    case = relation_case(
        witness(),
        ExplicitMainThreadApplication(),
    )

    initial_size = case_size(case)

    def interesting(
        candidate: TransformationLocalEvidence,
    ) -> bool:
        return case_size(candidate) == initial_size

    reduced = reduce_case(
        case,
        interesting,
    )

    assert reduced is case


def test_reduce_case_without_candidates_returns_original() -> None:
    case = relation_case(
        witness(
            normal_avoids=(),
            final_avoids=(),
        ),
        ExplicitMainThreadApplication(),
    )

    reduced = reduce_case(
        case,
        lambda candidate: True,
    )

    assert reduced is case


def test_reduce_case_requires_initial_interestingness() -> None:
    case = relation_case(
        witness(),
        ExplicitMainThreadApplication(),
    )

    with pytest.raises(
        CaseReductionError,
        match=("initial case must satisfy interestingness predicate"),
    ):
        reduce_case(
            case,
            lambda candidate: False,
        )


def test_reduce_case_rejects_non_callable_predicate() -> None:
    case = relation_case(
        witness(),
        ExplicitMainThreadApplication(),
    )

    with pytest.raises(
        CaseReductionError,
        match="interestingness must be callable",
    ):
        reduce_case(
            case,
            cast(
                InterestingnessPredicate,
                object(),
            ),
        )


def test_reduce_case_requires_boolean_predicate_result() -> None:
    case = relation_case(
        witness(),
        ExplicitMainThreadApplication(),
    )

    def non_boolean(
        candidate: TransformationLocalEvidence,
    ) -> bool:
        return cast(bool, 1)

    with pytest.raises(
        CaseReductionError,
        match=("interestingness predicate must return bool"),
    ):
        reduce_case(
            case,
            non_boolean,
        )


def test_predicate_exception_is_not_swallowed() -> None:
    case = relation_case(
        witness(),
        ExplicitMainThreadApplication(),
    )

    def failing(
        candidate: TransformationLocalEvidence,
    ) -> bool:
        raise RuntimeError("predicate failure")

    with pytest.raises(
        RuntimeError,
        match="predicate failure",
    ):
        reduce_case(
            case,
            failing,
        )


@pytest.mark.parametrize(
    "application, expected_relation",
    [
        (
            ExplicitMainThreadApplication(),
            BaseRelation.EXACT,
        ),
        (
            ImplicitMainThreadApplication(),
            BaseRelation.EXACT,
        ),
        (
            AvoidRemovalApplication(
                segment_index=0,
                waypoint_index=1,
            ),
            BaseRelation.BROADENING,
        ),
    ],
)
def test_reduction_preserves_application_family_and_relation(
    application: TransformationApplication,
    expected_relation: BaseRelation,
) -> None:
    source = witness(
        thread_id=(
            0
            if isinstance(
                application,
                ImplicitMainThreadApplication,
            )
            else None
        )
    )

    case = relation_case(
        source,
        application,
    )

    reduced = reduce_case(
        case,
        lambda candidate: True,
    )

    assert type(reduced.application) is type(case.application)
    assert reduced.base_relation is expected_relation
    assert reduced.task is case.task


def test_interestingness_type_alias_accepts_callable() -> None:
    def predicate(
        _candidate: TransformationLocalEvidence,
    ) -> bool:
        return True

    typed_predicate: InterestingnessPredicate = predicate

    assert callable(typed_predicate)
