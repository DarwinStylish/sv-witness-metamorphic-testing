import pytest

from sv_witness_metamorphic_testing.monotone_transformations import (
    TransformationDomainError,
    remove_avoid_assumption,
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


def assumption(
    action: AssumptionAction,
    *,
    line: int,
    expression: str,
) -> AssumptionWaypoint:
    return AssumptionWaypoint(
        action=action,
        constraint=CExpression(value=expression),
        location=Location(
            file_name="example.c",
            line=line,
            column=3,
            function="main",
        ),
    )


def target(
    *,
    line: int,
) -> TargetWaypoint:
    return TargetWaypoint(
        location=Location(
            file_name="example.c",
            line=line,
            column=5,
            function="main",
        )
    )


def witness_with_avoids() -> ViolationSequence:
    first = NormalSegment(
        waypoints=(
            assumption(
                AssumptionAction.AVOID,
                line=3,
                expression="x != 0",
            ),
            assumption(
                AssumptionAction.AVOID,
                line=4,
                expression="y != 0",
            ),
            assumption(
                AssumptionAction.FOLLOW,
                line=7,
                expression="ready == 1",
            ),
        )
    )

    second = NormalSegment(
        waypoints=(
            assumption(
                AssumptionAction.AVOID,
                line=9,
                expression="retry != 1",
            ),
            assumption(
                AssumptionAction.FOLLOW,
                line=10,
                expression="phase == 2",
            ),
        )
    )

    final = FinalSegment(
        waypoints=(
            assumption(
                AssumptionAction.AVOID,
                line=11,
                expression="failed != 1",
            ),
            target(
                line=14,
            ),
        )
    )

    return ViolationSequence(
        segments=(
            first,
            second,
            final,
        )
    )


def test_remove_first_avoid_from_normal_segment() -> None:
    witness = witness_with_avoids()
    source_segment = witness.normal_segments[0]

    transformed = remove_avoid_assumption(
        witness,
        0,
        0,
    )

    assert transformed.normal_segments[0].waypoints == (
        source_segment.waypoints[1],
        source_segment.waypoints[2],
    )


def test_remove_later_avoid_from_normal_segment() -> None:
    witness = witness_with_avoids()
    source_segment = witness.normal_segments[0]

    transformed = remove_avoid_assumption(
        witness,
        0,
        1,
    )

    assert transformed.normal_segments[0].waypoints == (
        source_segment.waypoints[0],
        source_segment.waypoints[2],
    )


def test_remove_avoid_from_final_segment() -> None:
    witness = witness_with_avoids()
    source_target = witness.final_segment.waypoints[-1]

    transformed = remove_avoid_assumption(
        witness,
        2,
        0,
    )

    assert transformed.final_segment.waypoints == (source_target,)


def test_removal_preserves_other_segment_objects() -> None:
    witness = witness_with_avoids()

    transformed = remove_avoid_assumption(
        witness,
        1,
        0,
    )

    assert transformed.segments[0] is witness.segments[0]
    assert transformed.segments[2] is witness.segments[2]


def test_removal_preserves_remaining_waypoint_objects_and_order() -> None:
    witness = witness_with_avoids()
    source_segment = witness.normal_segments[0]

    transformed = remove_avoid_assumption(
        witness,
        0,
        0,
    )

    transformed_segment = transformed.normal_segments[0]

    assert transformed_segment.waypoints[0] is source_segment.waypoints[1]
    assert transformed_segment.waypoints[1] is source_segment.waypoints[2]


def test_removal_preserves_required_follow_waypoint() -> None:
    witness = witness_with_avoids()
    source_follow = witness.normal_segments[0].waypoints[-1]

    transformed = remove_avoid_assumption(
        witness,
        0,
        1,
    )

    assert transformed.normal_segments[0].waypoints[-1] is source_follow
    assert transformed.normal_segments[0].waypoints[-1].action is AssumptionAction.FOLLOW


def test_removal_preserves_final_target() -> None:
    witness = witness_with_avoids()
    source_target = witness.final_segment.waypoints[-1]

    transformed = remove_avoid_assumption(
        witness,
        2,
        0,
    )

    assert transformed.final_segment.waypoints[-1] is source_target
    assert isinstance(
        transformed.final_segment.waypoints[-1],
        TargetWaypoint,
    )


def test_removal_does_not_mutate_input_witness() -> None:
    witness = witness_with_avoids()
    original_segments = witness.segments
    original_first_waypoints = witness.normal_segments[0].waypoints

    remove_avoid_assumption(
        witness,
        0,
        0,
    )

    assert witness.segments is original_segments
    assert witness.normal_segments[0].waypoints is original_first_waypoints


@pytest.mark.parametrize(
    ("segment_index", "waypoint_index", "message"),
    [
        (-1, 0, "segment_index out of range"),
        (3, 0, "segment_index out of range"),
        (0, -1, "waypoint_index out of range"),
        (0, 3, "waypoint_index out of range"),
    ],
)
def test_removal_rejects_out_of_range_positions(
    segment_index: int,
    waypoint_index: int,
    message: str,
) -> None:
    witness = witness_with_avoids()

    with pytest.raises(
        TransformationDomainError,
        match=message,
    ):
        remove_avoid_assumption(
            witness,
            segment_index,
            waypoint_index,
        )


def test_removal_rejects_boolean_segment_index() -> None:
    witness = witness_with_avoids()

    with pytest.raises(
        TransformationDomainError,
        match="segment_index must be an integer",
    ):
        remove_avoid_assumption(
            witness,
            True,
            0,
        )


def test_removal_rejects_boolean_waypoint_index() -> None:
    witness = witness_with_avoids()

    with pytest.raises(
        TransformationDomainError,
        match="waypoint_index must be an integer",
    ):
        remove_avoid_assumption(
            witness,
            0,
            False,
        )


def test_removal_rejects_follow_assumption() -> None:
    witness = witness_with_avoids()

    with pytest.raises(
        TransformationDomainError,
        match="selected waypoint must be an avoid assumption",
    ):
        remove_avoid_assumption(
            witness,
            0,
            2,
        )


def test_removal_rejects_target_waypoint() -> None:
    witness = witness_with_avoids()

    with pytest.raises(
        TransformationDomainError,
        match="selected waypoint must be an avoid assumption",
    ):
        remove_avoid_assumption(
            witness,
            2,
            1,
        )
