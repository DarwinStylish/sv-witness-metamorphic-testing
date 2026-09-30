"""Implementations of monotone witness transformations."""

from dataclasses import replace

from .witness_model import (
    AssumptionAction,
    AssumptionWaypoint,
    FinalSegment,
    NormalSegment,
    Segment,
    ViolationSequence,
)


class TransformationDomainError(ValueError):
    """Raised when a requested transformation application is outside its domain."""


def _validate_index(
    index: int,
    *,
    name: str,
    length: int,
) -> None:
    if type(index) is not int:
        raise TransformationDomainError(f"{name} must be an integer")

    if index < 0 or index >= length:
        raise TransformationDomainError(f"{name} out of range")


def _remove_from_normal_segment(
    segment: NormalSegment,
    waypoint_index: int,
) -> NormalSegment:
    selected = segment.waypoints[waypoint_index]

    if selected.action is not AssumptionAction.AVOID:
        raise TransformationDomainError("selected waypoint must be an avoid assumption")

    waypoints = segment.waypoints[:waypoint_index] + segment.waypoints[waypoint_index + 1 :]

    return replace(
        segment,
        waypoints=waypoints,
    )


def _remove_from_final_segment(
    segment: FinalSegment,
    waypoint_index: int,
) -> FinalSegment:
    selected = segment.waypoints[waypoint_index]

    if (
        not isinstance(selected, AssumptionWaypoint)
        or selected.action is not AssumptionAction.AVOID
    ):
        raise TransformationDomainError("selected waypoint must be an avoid assumption")

    waypoints = segment.waypoints[:waypoint_index] + segment.waypoints[waypoint_index + 1 :]

    return replace(
        segment,
        waypoints=waypoints,
    )


def _remove_from_segment(
    segment: Segment,
    waypoint_index: int,
) -> Segment:
    _validate_index(
        waypoint_index,
        name="waypoint_index",
        length=len(segment.waypoints),
    )

    if isinstance(segment, NormalSegment):
        return _remove_from_normal_segment(
            segment,
            waypoint_index,
        )

    return _remove_from_final_segment(
        segment,
        waypoint_index,
    )


def remove_avoid_assumption(
    witness: ViolationSequence,
    segment_index: int,
    waypoint_index: int,
) -> ViolationSequence:
    """Remove one selected avoid assumption using zero-based positions."""

    _validate_index(
        segment_index,
        name="segment_index",
        length=len(witness.segments),
    )

    segment = witness.segments[segment_index]
    transformed_segment = _remove_from_segment(
        segment,
        waypoint_index,
    )

    segments = (
        *witness.segments[:segment_index],
        transformed_segment,
        *witness.segments[segment_index + 1 :],
    )

    return replace(
        witness,
        segments=segments,
    )
