from sv_witness_metamorphic_testing.exact_transformations import (
    explicit_main_thread,
    implicit_main_thread,
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

type Waypoint = AssumptionWaypoint | TargetWaypoint


def assumption(
    action: AssumptionAction,
    *,
    line: int,
    expression: str,
    thread_id: int | None,
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
        thread_id=thread_id,
    )


def target(
    *,
    line: int,
    thread_id: int | None,
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


def mixed_witness() -> ViolationSequence:
    first = NormalSegment(
        waypoints=(
            assumption(
                AssumptionAction.AVOID,
                line=3,
                expression="guard != 0",
                thread_id=None,
            ),
            assumption(
                AssumptionAction.FOLLOW,
                line=4,
                expression="x == 1",
                thread_id=0,
            ),
        )
    )
    second = NormalSegment(
        waypoints=(
            assumption(
                AssumptionAction.AVOID,
                line=6,
                expression="retry == 0",
                thread_id=0,
            ),
            assumption(
                AssumptionAction.FOLLOW,
                line=7,
                expression="y == 2",
                thread_id=None,
            ),
        )
    )
    final = FinalSegment(
        waypoints=(
            assumption(
                AssumptionAction.AVOID,
                line=9,
                expression="failed != 1",
                thread_id=None,
            ),
            target(
                line=12,
                thread_id=0,
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


def all_waypoints(
    witness: ViolationSequence,
) -> tuple[Waypoint, ...]:
    return tuple(waypoint for segment in witness.segments for waypoint in segment.waypoints)


def thread_ids(
    witness: ViolationSequence,
) -> tuple[int | None, ...]:
    return tuple(waypoint.thread_id for waypoint in all_waypoints(witness))


def assert_non_thread_payload_preserved(
    before: ViolationSequence,
    after: ViolationSequence,
) -> None:
    before_waypoints = all_waypoints(before)
    after_waypoints = all_waypoints(after)

    assert tuple(type(segment) for segment in after.segments) == tuple(
        type(segment) for segment in before.segments
    )
    assert tuple(type(waypoint) for waypoint in after_waypoints) == tuple(
        type(waypoint) for waypoint in before_waypoints
    )
    assert tuple(waypoint.location.line for waypoint in after_waypoints) == tuple(
        waypoint.location.line for waypoint in before_waypoints
    )

    for source, transformed in zip(
        before_waypoints,
        after_waypoints,
        strict=True,
    ):
        assert transformed.location is source.location

        if isinstance(source, AssumptionWaypoint):
            assert isinstance(transformed, AssumptionWaypoint)
            assert transformed.action is source.action
            assert transformed.constraint is source.constraint
        else:
            assert isinstance(source, TargetWaypoint)
            assert isinstance(transformed, TargetWaypoint)


def test_explicit_main_thread_sets_every_waypoint_to_zero() -> None:
    witness = mixed_witness()

    transformed = explicit_main_thread(witness)

    assert thread_ids(transformed) == (
        0,
        0,
        0,
        0,
        0,
        0,
    )


def test_implicit_main_thread_removes_every_thread_id() -> None:
    witness = mixed_witness()

    transformed = implicit_main_thread(witness)

    assert thread_ids(transformed) == (
        None,
        None,
        None,
        None,
        None,
        None,
    )


def test_explicit_main_thread_preserves_non_thread_payload() -> None:
    witness = mixed_witness()

    transformed = explicit_main_thread(witness)

    assert_non_thread_payload_preserved(
        witness,
        transformed,
    )


def test_implicit_main_thread_preserves_non_thread_payload() -> None:
    witness = mixed_witness()

    transformed = implicit_main_thread(witness)

    assert_non_thread_payload_preserved(
        witness,
        transformed,
    )


def test_transformations_do_not_mutate_source_witness() -> None:
    witness = mixed_witness()
    original_thread_ids = thread_ids(witness)

    explicit_main_thread(witness)
    implicit_main_thread(witness)

    assert thread_ids(witness) == original_thread_ids


def test_explicit_main_thread_is_idempotent() -> None:
    witness = mixed_witness()

    once = explicit_main_thread(witness)
    twice = explicit_main_thread(once)

    assert twice == once


def test_implicit_main_thread_is_idempotent() -> None:
    witness = mixed_witness()

    once = implicit_main_thread(witness)
    twice = implicit_main_thread(once)

    assert twice == once


def test_explicit_main_thread_preserves_canonical_witness() -> None:
    witness = explicit_main_thread(mixed_witness())

    assert explicit_main_thread(witness) == witness


def test_implicit_main_thread_preserves_canonical_witness() -> None:
    witness = implicit_main_thread(mixed_witness())

    assert implicit_main_thread(witness) == witness


def test_explicit_after_implicit_chooses_explicit_form() -> None:
    witness = mixed_witness()

    composed = explicit_main_thread(implicit_main_thread(witness))

    assert composed == explicit_main_thread(witness)


def test_implicit_after_explicit_chooses_implicit_form() -> None:
    witness = mixed_witness()

    composed = implicit_main_thread(explicit_main_thread(witness))

    assert composed == implicit_main_thread(witness)


def test_transformations_preserve_segment_and_waypoint_order() -> None:
    witness = mixed_witness()

    for transformed in (
        explicit_main_thread(witness),
        implicit_main_thread(witness),
    ):
        assert tuple(type(segment) for segment in transformed.segments) == tuple(
            type(segment) for segment in witness.segments
        )
        assert tuple(waypoint.location.line for waypoint in all_waypoints(transformed)) == tuple(
            waypoint.location.line for waypoint in all_waypoints(witness)
        )
