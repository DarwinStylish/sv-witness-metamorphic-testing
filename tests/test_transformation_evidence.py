from dataclasses import FrozenInstanceError, replace
from typing import cast

import pytest

from sv_witness_metamorphic_testing.exact_transformations import (
    explicit_main_thread,
    implicit_main_thread,
)
from sv_witness_metamorphic_testing.monotone_transformations import (
    remove_avoid_assumption,
)
from sv_witness_metamorphic_testing.semantic_relation import BaseRelation
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
    EvidenceError,
    ExplicitMainThreadApplication,
    ImplicitMainThreadApplication,
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
                    sha256=Sha256Digest(
                        value="a" * 64,
                    ),
                ),
            )
        ),
        specification=Specification(
            text=("CHECK(init(main()), LTL(G ! call(__VERIFIER_error())))")
        ),
        execution_context=ExecutionContext(
            language=Language.C,
            data_model=DataModel.LP64,
        ),
    )


def assumption(
    action: AssumptionAction,
    *,
    line: int,
    expression: str,
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


def source_witness() -> ViolationSequence:
    return ViolationSequence(
        segments=(
            NormalSegment(
                waypoints=(
                    assumption(
                        AssumptionAction.AVOID,
                        line=3,
                        expression="x != 0",
                        thread_id=None,
                    ),
                    assumption(
                        AssumptionAction.AVOID,
                        line=4,
                        expression="y != 0",
                        thread_id=0,
                    ),
                    assumption(
                        AssumptionAction.FOLLOW,
                        line=7,
                        expression="ready == 1",
                        thread_id=None,
                    ),
                )
            ),
            FinalSegment(
                waypoints=(
                    assumption(
                        AssumptionAction.AVOID,
                        line=10,
                        expression="failed != 1",
                        thread_id=0,
                    ),
                    target(
                        line=14,
                        thread_id=None,
                    ),
                )
            ),
        )
    )


@pytest.mark.parametrize(
    ("segment_index", "waypoint_index", "message"),
    [
        (-1, 0, "segment_index must be non-negative"),
        (0, -1, "waypoint_index must be non-negative"),
    ],
)
def test_avoid_application_rejects_negative_indices(
    segment_index: int,
    waypoint_index: int,
    message: str,
) -> None:
    with pytest.raises(
        EvidenceError,
        match=message,
    ):
        AvoidRemovalApplication(
            segment_index=segment_index,
            waypoint_index=waypoint_index,
        )


def test_avoid_application_rejects_boolean_segment_index() -> None:
    with pytest.raises(
        EvidenceError,
        match="segment_index must be an integer",
    ):
        AvoidRemovalApplication(
            segment_index=True,
            waypoint_index=0,
        )


def test_avoid_application_rejects_boolean_waypoint_index() -> None:
    with pytest.raises(
        EvidenceError,
        match="waypoint_index must be an integer",
    ):
        AvoidRemovalApplication(
            segment_index=0,
            waypoint_index=False,
        )


def test_explicit_main_thread_evidence_is_exact() -> None:
    source = source_witness()
    transformed = explicit_main_thread(source)

    evidence = TransformationLocalEvidence(
        task=task(),
        source=source,
        transformed=transformed,
        application=ExplicitMainThreadApplication(),
    )

    assert evidence.base_relation is BaseRelation.EXACT
    assert evidence.source == source
    assert evidence.transformed == transformed


def test_implicit_main_thread_evidence_is_exact() -> None:
    source = source_witness()
    transformed = implicit_main_thread(source)

    evidence = TransformationLocalEvidence(
        task=task(),
        source=source,
        transformed=transformed,
        application=ImplicitMainThreadApplication(),
    )

    assert evidence.base_relation is BaseRelation.EXACT


def test_explicit_evidence_rejects_wrong_thread_representation() -> None:
    source = source_witness()
    transformed = implicit_main_thread(source)

    with pytest.raises(
        EvidenceError,
        match="wrong thread representation",
    ):
        TransformationLocalEvidence(
            task=task(),
            source=source,
            transformed=transformed,
            application=ExplicitMainThreadApplication(),
        )


def test_implicit_evidence_rejects_wrong_thread_representation() -> None:
    source = source_witness()
    transformed = explicit_main_thread(source)

    with pytest.raises(
        EvidenceError,
        match="wrong thread representation",
    ):
        TransformationLocalEvidence(
            task=task(),
            source=source,
            transformed=transformed,
            application=ImplicitMainThreadApplication(),
        )


def test_main_thread_evidence_rejects_non_thread_payload_change() -> None:
    source = source_witness()
    transformed = explicit_main_thread(source)

    first_segment = transformed.normal_segments[0]
    first_waypoint = first_segment.waypoints[0]

    changed_waypoint = replace(
        first_waypoint,
        constraint=CExpression(
            value="changed != 0",
        ),
    )

    changed_segment = replace(
        first_segment,
        waypoints=(
            changed_waypoint,
            *first_segment.waypoints[1:],
        ),
    )

    changed = replace(
        transformed,
        segments=(
            changed_segment,
            *transformed.segments[1:],
        ),
    )

    with pytest.raises(
        EvidenceError,
        match="changed non-thread payload",
    ):
        TransformationLocalEvidence(
            task=task(),
            source=source,
            transformed=changed,
            application=ExplicitMainThreadApplication(),
        )


def test_main_thread_evidence_rejects_waypoint_count_change() -> None:
    source = source_witness()
    transformed = explicit_main_thread(source)

    first_segment = transformed.normal_segments[0]

    extra_avoid = assumption(
        AssumptionAction.AVOID,
        line=6,
        expression="extra != 0",
        thread_id=0,
    )

    changed_segment = replace(
        first_segment,
        waypoints=(
            *first_segment.waypoints[:-1],
            extra_avoid,
            first_segment.waypoints[-1],
        ),
    )

    changed = replace(
        transformed,
        segments=(
            changed_segment,
            *transformed.segments[1:],
        ),
    )

    with pytest.raises(
        EvidenceError,
        match="changed waypoint count",
    ):
        TransformationLocalEvidence(
            task=task(),
            source=source,
            transformed=changed,
            application=ExplicitMainThreadApplication(),
        )


def test_normal_avoid_removal_evidence_is_broadening() -> None:
    source = source_witness()
    transformed = remove_avoid_assumption(
        source,
        0,
        1,
    )

    evidence = TransformationLocalEvidence(
        task=task(),
        source=source,
        transformed=transformed,
        application=AvoidRemovalApplication(
            segment_index=0,
            waypoint_index=1,
        ),
    )

    assert evidence.base_relation is BaseRelation.BROADENING


def test_final_avoid_removal_evidence_is_broadening() -> None:
    source = source_witness()
    transformed = remove_avoid_assumption(
        source,
        1,
        0,
    )

    evidence = TransformationLocalEvidence(
        task=task(),
        source=source,
        transformed=transformed,
        application=AvoidRemovalApplication(
            segment_index=1,
            waypoint_index=0,
        ),
    )

    assert evidence.base_relation is BaseRelation.BROADENING


def test_avoid_evidence_rejects_segment_outside_source() -> None:
    source = source_witness()

    with pytest.raises(
        EvidenceError,
        match="segment_index outside source witness",
    ):
        TransformationLocalEvidence(
            task=task(),
            source=source,
            transformed=source,
            application=AvoidRemovalApplication(
                segment_index=2,
                waypoint_index=0,
            ),
        )


def test_avoid_evidence_rejects_waypoint_outside_source_segment() -> None:
    source = source_witness()

    with pytest.raises(
        EvidenceError,
        match="waypoint_index outside source segment",
    ):
        TransformationLocalEvidence(
            task=task(),
            source=source,
            transformed=source,
            application=AvoidRemovalApplication(
                segment_index=0,
                waypoint_index=3,
            ),
        )


def test_avoid_evidence_rejects_follow_selection() -> None:
    source = source_witness()

    with pytest.raises(
        EvidenceError,
        match="selected source waypoint must be an avoid assumption",
    ):
        TransformationLocalEvidence(
            task=task(),
            source=source,
            transformed=source,
            application=AvoidRemovalApplication(
                segment_index=0,
                waypoint_index=2,
            ),
        )


def test_avoid_evidence_rejects_target_selection() -> None:
    source = source_witness()

    with pytest.raises(
        EvidenceError,
        match="selected source waypoint must be an avoid assumption",
    ):
        TransformationLocalEvidence(
            task=task(),
            source=source,
            transformed=source,
            application=AvoidRemovalApplication(
                segment_index=1,
                waypoint_index=1,
            ),
        )


def test_avoid_evidence_rejects_change_to_unselected_segment() -> None:
    source = source_witness()
    transformed = remove_avoid_assumption(
        source,
        0,
        0,
    )

    changed_final = replace(
        transformed.final_segment,
        waypoints=(
            target(
                line=15,
                thread_id=None,
            ),
        ),
    )

    changed = replace(
        transformed,
        segments=(
            transformed.normal_segments[0],
            changed_final,
        ),
    )

    with pytest.raises(
        EvidenceError,
        match="changed an unselected segment",
    ):
        TransformationLocalEvidence(
            task=task(),
            source=source,
            transformed=changed,
            application=AvoidRemovalApplication(
                segment_index=0,
                waypoint_index=0,
            ),
        )


def test_avoid_evidence_rejects_wrong_selected_deletion() -> None:
    source = source_witness()

    incorrectly_transformed = remove_avoid_assumption(
        source,
        0,
        0,
    )

    with pytest.raises(
        EvidenceError,
        match="selected one-position deletion",
    ):
        TransformationLocalEvidence(
            task=task(),
            source=source,
            transformed=incorrectly_transformed,
            application=AvoidRemovalApplication(
                segment_index=0,
                waypoint_index=1,
            ),
        )


def test_evidence_retains_equal_immutable_task_value() -> None:
    first_task = task()
    equal_task = task()

    source = source_witness()
    transformed = explicit_main_thread(source)

    evidence = TransformationLocalEvidence(
        task=equal_task,
        source=source,
        transformed=transformed,
        application=ExplicitMainThreadApplication(),
    )

    assert first_task == equal_task
    assert first_task is not equal_task
    assert evidence.task == first_task


def test_evidence_is_frozen() -> None:
    source = source_witness()

    evidence = TransformationLocalEvidence(
        task=task(),
        source=source,
        transformed=explicit_main_thread(source),
        application=ExplicitMainThreadApplication(),
    )

    relation_attribute = "base_relation"

    with pytest.raises(FrozenInstanceError):
        setattr(
            evidence,
            relation_attribute,
            BaseRelation.BROADENING,
        )


def test_evidence_has_no_source_admission_claim() -> None:
    source = source_witness()

    evidence = TransformationLocalEvidence(
        task=task(),
        source=source,
        transformed=explicit_main_thread(source),
        application=ExplicitMainThreadApplication(),
    )

    assert not hasattr(evidence, "source_admitted")
    assert not hasattr(evidence, "witness_valid")
    assert not hasattr(evidence, "task_bound")


def test_evidence_rejects_invalid_task_runtime_type() -> None:
    source = source_witness()

    with pytest.raises(
        EvidenceError,
        match="task must be a VerificationTask",
    ):
        TransformationLocalEvidence(
            task=cast(VerificationTask, object()),
            source=source,
            transformed=explicit_main_thread(source),
            application=ExplicitMainThreadApplication(),
        )


def test_evidence_rejects_invalid_source_runtime_type() -> None:
    source = source_witness()

    with pytest.raises(
        EvidenceError,
        match="source must be a ViolationSequence",
    ):
        TransformationLocalEvidence(
            task=task(),
            source=cast(ViolationSequence, object()),
            transformed=explicit_main_thread(source),
            application=ExplicitMainThreadApplication(),
        )


def test_evidence_rejects_invalid_transformed_runtime_type() -> None:
    source = source_witness()

    with pytest.raises(
        EvidenceError,
        match="transformed must be a ViolationSequence",
    ):
        TransformationLocalEvidence(
            task=task(),
            source=source,
            transformed=cast(ViolationSequence, object()),
            application=ExplicitMainThreadApplication(),
        )
