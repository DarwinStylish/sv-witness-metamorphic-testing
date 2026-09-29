"""Exact transformations over supported main-thread witness syntax."""

from dataclasses import replace

from .witness_model import (
    AssumptionWaypoint,
    NormalSegment,
    Segment,
    TargetWaypoint,
    ViolationSequence,
)


def _assumption_with_thread_id(
    waypoint: AssumptionWaypoint,
    thread_id: int | None,
) -> AssumptionWaypoint:
    if waypoint.thread_id == thread_id:
        return waypoint

    return replace(waypoint, thread_id=thread_id)


def _target_with_thread_id(
    waypoint: TargetWaypoint,
    thread_id: int | None,
) -> TargetWaypoint:
    if waypoint.thread_id == thread_id:
        return waypoint

    return replace(waypoint, thread_id=thread_id)


def _final_waypoint_with_thread_id(
    waypoint: AssumptionWaypoint | TargetWaypoint,
    thread_id: int | None,
) -> AssumptionWaypoint | TargetWaypoint:
    if isinstance(waypoint, AssumptionWaypoint):
        return _assumption_with_thread_id(waypoint, thread_id)

    return _target_with_thread_id(waypoint, thread_id)


def _segment_with_thread_id(
    segment: Segment,
    thread_id: int | None,
) -> Segment:
    if isinstance(segment, NormalSegment):
        normal_waypoints = tuple(
            _assumption_with_thread_id(waypoint, thread_id) for waypoint in segment.waypoints
        )

        if normal_waypoints == segment.waypoints:
            return segment

        return replace(segment, waypoints=normal_waypoints)

    final_waypoints = tuple(
        _final_waypoint_with_thread_id(waypoint, thread_id) for waypoint in segment.waypoints
    )

    if final_waypoints == segment.waypoints:
        return segment

    return replace(segment, waypoints=final_waypoints)


def _main_thread_form(
    witness: ViolationSequence,
    thread_id: int | None,
) -> ViolationSequence:
    segments = tuple(_segment_with_thread_id(segment, thread_id) for segment in witness.segments)

    if segments == witness.segments:
        return witness

    return replace(witness, segments=segments)


def explicit_main_thread(
    witness: ViolationSequence,
) -> ViolationSequence:
    """Represent every supported waypoint with explicit main-thread id zero."""

    return _main_thread_form(witness, 0)


def implicit_main_thread(
    witness: ViolationSequence,
) -> ViolationSequence:
    """Represent every supported waypoint with an absent main-thread id."""

    return _main_thread_form(witness, None)
