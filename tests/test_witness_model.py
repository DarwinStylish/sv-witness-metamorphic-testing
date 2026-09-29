from dataclasses import FrozenInstanceError

import pytest

from sv_witness_metamorphic_testing.witness_model import (
    AssumptionAction,
    AssumptionWaypoint,
    CExpression,
    FinalSegment,
    Location,
    NormalSegment,
    TargetWaypoint,
    ViolationSequence,
    WitnessModelError,
)


def location() -> Location:
    return Location(file_name="example.c", line=7)


def assumption(
    action: AssumptionAction,
    *,
    thread_id: int | None = None,
) -> AssumptionWaypoint:
    return AssumptionWaypoint(
        action=action,
        constraint=CExpression(value="x == 1"),
        location=location(),
        thread_id=thread_id,
    )


def target(*, thread_id: int | None = None) -> TargetWaypoint:
    return TargetWaypoint(
        location=Location(
            file_name="example.c",
            line=12,
            column=5,
            function="main",
        ),
        thread_id=thread_id,
    )


def test_location_preserves_optional_field_absence() -> None:
    value = location()

    assert value.column is None
    assert value.function is None


@pytest.mark.parametrize("line", [0, -1])
def test_location_rejects_non_positive_line(line: int) -> None:
    with pytest.raises(WitnessModelError, match="line"):
        Location(file_name="example.c", line=line)


@pytest.mark.parametrize("column", [0, -1])
def test_location_rejects_non_positive_column(column: int) -> None:
    with pytest.raises(WitnessModelError, match="column"):
        Location(file_name="example.c", line=1, column=column)


def test_c_expression_is_retained_as_opaque_text() -> None:
    expression = CExpression(value="((x + 1) == y)")

    assert expression.value == "((x + 1) == y)"


def test_thread_id_preserves_absent_and_explicit_zero() -> None:
    absent = assumption(AssumptionAction.FOLLOW)
    explicit_zero = assumption(AssumptionAction.FOLLOW, thread_id=0)

    assert absent.thread_id is None
    assert explicit_zero.thread_id == 0


@pytest.mark.parametrize("thread_id", [-1, 1, 2])
def test_thread_id_rejects_values_outside_profile(thread_id: int) -> None:
    with pytest.raises(WitnessModelError, match="thread_id"):
        assumption(AssumptionAction.FOLLOW, thread_id=thread_id)


def test_normal_segment_accepts_avoids_followed_by_one_follow() -> None:
    avoid = assumption(AssumptionAction.AVOID)
    follow = assumption(AssumptionAction.FOLLOW)

    segment = NormalSegment(waypoints=(avoid, follow))

    assert segment.waypoints == (avoid, follow)


def test_normal_segment_rejects_missing_follow() -> None:
    avoid = assumption(AssumptionAction.AVOID)

    with pytest.raises(WitnessModelError, match="exactly one follow"):
        NormalSegment(waypoints=(avoid,))


def test_normal_segment_rejects_multiple_follow_waypoints() -> None:
    first = assumption(AssumptionAction.FOLLOW)
    second = assumption(AssumptionAction.FOLLOW)

    with pytest.raises(WitnessModelError, match="exactly one follow"):
        NormalSegment(waypoints=(first, second))


def test_normal_segment_requires_follow_to_be_last() -> None:
    follow = assumption(AssumptionAction.FOLLOW)
    avoid = assumption(AssumptionAction.AVOID)

    with pytest.raises(WitnessModelError, match="last waypoint"):
        NormalSegment(waypoints=(follow, avoid))


def test_final_segment_accepts_avoids_followed_by_target() -> None:
    avoid = assumption(AssumptionAction.AVOID)
    final_target = target()

    segment = FinalSegment(waypoints=(avoid, final_target))

    assert segment.waypoints == (avoid, final_target)


def test_final_segment_rejects_follow_assumption_before_target() -> None:
    follow = assumption(AssumptionAction.FOLLOW)

    with pytest.raises(WitnessModelError, match="action avoid"):
        FinalSegment(waypoints=(follow, target()))


def test_final_segment_rejects_target_before_final_position() -> None:
    with pytest.raises(WitnessModelError, match="only as the final"):
        FinalSegment(waypoints=(target(), target()))


def test_violation_sequence_preserves_segment_order() -> None:
    first = NormalSegment(waypoints=(assumption(AssumptionAction.FOLLOW),))
    second = NormalSegment(
        waypoints=(
            assumption(AssumptionAction.AVOID),
            assumption(AssumptionAction.FOLLOW),
        )
    )
    final = FinalSegment(waypoints=(target(),))

    sequence = ViolationSequence(segments=(first, second, final))

    assert sequence.normal_segments == (first, second)
    assert sequence.final_segment is final
    assert sequence.segments == (first, second, final)


def test_violation_sequence_rejects_empty_sequence() -> None:
    with pytest.raises(WitnessModelError, match="at least one"):
        ViolationSequence(segments=())


def test_violation_sequence_requires_final_segment_last() -> None:
    normal = NormalSegment(waypoints=(assumption(AssumptionAction.FOLLOW),))
    final = FinalSegment(waypoints=(target(),))

    with pytest.raises(WitnessModelError, match="end with exactly one final"):
        ViolationSequence(segments=(normal,))

    with pytest.raises(WitnessModelError, match="only normal segments"):
        ViolationSequence(segments=(final, normal, final))


def test_model_objects_are_immutable() -> None:
    value = location()

    with pytest.raises(FrozenInstanceError):
        value.line = 8  # type: ignore[misc]


def test_location_rejects_non_string_file_name() -> None:
    with pytest.raises(WitnessModelError, match="file_name"):
        Location(file_name=7, line=1)  # type: ignore[arg-type]


def test_location_rejects_non_string_function() -> None:
    with pytest.raises(WitnessModelError, match="function"):
        Location(
            file_name="example.c",
            line=1,
            function=7,  # type: ignore[arg-type]
        )


def test_location_rejects_boolean_line() -> None:
    with pytest.raises(WitnessModelError, match="line"):
        Location(file_name="example.c", line=True)


def test_c_expression_rejects_non_string_value() -> None:
    with pytest.raises(WitnessModelError, match="C expression"):
        CExpression(value=7)  # type: ignore[arg-type]


def test_assumption_rejects_raw_string_action() -> None:
    with pytest.raises(WitnessModelError, match="action"):
        AssumptionWaypoint(
            action="follow",  # type: ignore[arg-type]
            constraint=CExpression(value="x == 1"),
            location=location(),
        )


def test_assumption_rejects_non_expression_constraint() -> None:
    with pytest.raises(WitnessModelError, match="constraint"):
        AssumptionWaypoint(
            action=AssumptionAction.FOLLOW,
            constraint="x == 1",  # type: ignore[arg-type]
            location=location(),
        )


def test_assumption_rejects_non_location() -> None:
    with pytest.raises(WitnessModelError, match="location"):
        AssumptionWaypoint(
            action=AssumptionAction.FOLLOW,
            constraint=CExpression(value="x == 1"),
            location="example.c:7",  # type: ignore[arg-type]
        )


def test_target_rejects_non_location() -> None:
    with pytest.raises(WitnessModelError, match="location"):
        TargetWaypoint(
            location="example.c:12",  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("thread_id", [-1, 1, 2, True])
def test_target_rejects_thread_ids_outside_profile(
    thread_id: int,
) -> None:
    with pytest.raises(WitnessModelError, match="thread_id"):
        target(thread_id=thread_id)


def test_normal_segment_rejects_target_waypoint_consistently() -> None:
    with pytest.raises(
        WitnessModelError,
        match="assumption waypoints",
    ):
        NormalSegment(
            waypoints=(target(),),  # type: ignore[arg-type]
        )


def test_normal_segment_rejects_arbitrary_element_consistently() -> None:
    with pytest.raises(
        WitnessModelError,
        match="assumption waypoints",
    ):
        NormalSegment(
            waypoints=("not-a-waypoint",),  # type: ignore[arg-type]
        )
