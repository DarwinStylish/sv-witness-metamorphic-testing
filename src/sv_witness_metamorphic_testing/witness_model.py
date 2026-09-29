"""Internal model for the supported SV-Witness violation-witness profile."""

from dataclasses import dataclass
from enum import StrEnum
from typing import cast


class WitnessModelError(ValueError):
    """Raised when an object violates a local witness-model invariant."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Location:
    """Source location retained in the form relevant to the supported profile."""

    file_name: str
    line: int
    column: int | None = None
    function: str | None = None

    def __post_init__(self) -> None:
        if type(self.file_name) is not str:
            raise WitnessModelError("location file_name must be a string")

        if type(self.line) is not int or self.line < 1:
            raise WitnessModelError("location line must be a positive integer")

        if self.column is not None and (type(self.column) is not int or self.column < 1):
            raise WitnessModelError("location column must be a positive integer when present")

        if self.function is not None and type(self.function) is not str:
            raise WitnessModelError("location function must be a string when present")


@dataclass(frozen=True, slots=True, kw_only=True)
class CExpression:
    """Opaque `c_expression` text.

    Construction does not establish that the expression is semantically valid C.
    """

    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str:
            raise WitnessModelError("C expression value must be a string")


class AssumptionAction(StrEnum):
    """Actions supported for assumption waypoints in the project profile."""

    FOLLOW = "follow"
    AVOID = "avoid"


def _validate_thread_id(thread_id: int | None) -> None:
    if thread_id is None:
        return

    if type(thread_id) is not int or thread_id != 0:
        raise WitnessModelError("supported thread_id must be absent or the integer 0")


@dataclass(frozen=True, slots=True, kw_only=True)
class AssumptionWaypoint:
    """Supported sequential assumption waypoint."""

    action: AssumptionAction
    constraint: CExpression
    location: Location
    thread_id: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.action, AssumptionAction):
            raise WitnessModelError("assumption action must be an AssumptionAction")

        if not isinstance(self.constraint, CExpression):
            raise WitnessModelError("assumption constraint must be a CExpression")

        if not isinstance(self.location, Location):
            raise WitnessModelError("assumption location must be a Location")

        _validate_thread_id(self.thread_id)


@dataclass(frozen=True, slots=True, kw_only=True)
class TargetWaypoint:
    """Supported `unreach-call` target waypoint.

    Target waypoints have fixed type `target`, fixed action `follow`, and no
    constraint in the supported profile.
    """

    location: Location
    thread_id: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.location, Location):
            raise WitnessModelError("target location must be a Location")

        _validate_thread_id(self.thread_id)


@dataclass(frozen=True, slots=True, kw_only=True)
class NormalSegment:
    """Supported normal follow segment.

    A normal segment contains zero or more avoid assumptions followed by
    exactly one follow assumption.
    """

    waypoints: tuple[AssumptionWaypoint, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.waypoints, tuple):
            raise WitnessModelError("normal-segment waypoints must be a tuple")

        if not self.waypoints:
            raise WitnessModelError("normal segment must contain at least one waypoint")

        if any(not isinstance(waypoint, AssumptionWaypoint) for waypoint in self.waypoints):
            raise WitnessModelError("normal-segment waypoints must all be assumption waypoints")

        follow_positions = [
            index
            for index, waypoint in enumerate(self.waypoints)
            if waypoint.action is AssumptionAction.FOLLOW
        ]

        if len(follow_positions) != 1:
            raise WitnessModelError("normal segment must contain exactly one follow assumption")

        if follow_positions[0] != len(self.waypoints) - 1:
            raise WitnessModelError("normal segment follow assumption must be the last waypoint")


@dataclass(frozen=True, slots=True, kw_only=True)
class FinalSegment:
    """Supported final segment for an `unreach-call` violation sequence.

    A final segment contains zero or more avoid assumptions followed by exactly
    one target waypoint.
    """

    waypoints: tuple[AssumptionWaypoint | TargetWaypoint, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.waypoints, tuple):
            raise WitnessModelError("final-segment waypoints must be a tuple")

        if not self.waypoints:
            raise WitnessModelError("final segment must contain at least one waypoint")

        if not isinstance(self.waypoints[-1], TargetWaypoint):
            raise WitnessModelError("final segment must end with exactly one target waypoint")

        for waypoint in self.waypoints[:-1]:
            if not isinstance(waypoint, AssumptionWaypoint):
                raise WitnessModelError("target waypoint may appear only as the final waypoint")

            if waypoint.action is not AssumptionAction.AVOID:
                raise WitnessModelError("assumptions before the final target must use action avoid")


type Segment = NormalSegment | FinalSegment


@dataclass(frozen=True, slots=True, kw_only=True)
class ViolationSequence:
    """Profile-shaped violation sequence.

    Construction establishes only the local structure of the supported profile.
    It does not establish SV-Witness validity or represented-execution
    non-emptiness.
    """

    segments: tuple[Segment, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.segments, tuple):
            raise WitnessModelError("violation-sequence segments must be a tuple")

        if not self.segments:
            raise WitnessModelError("violation sequence must contain at least one segment")

        if not isinstance(self.segments[-1], FinalSegment):
            raise WitnessModelError("violation sequence must end with exactly one final segment")

        if any(not isinstance(segment, NormalSegment) for segment in self.segments[:-1]):
            raise WitnessModelError("only normal segments may precede the final segment")

    @property
    def normal_segments(self) -> tuple[NormalSegment, ...]:
        """Return normal segments in witness order."""

        return cast(tuple[NormalSegment, ...], self.segments[:-1])

    @property
    def final_segment(self) -> FinalSegment:
        """Return the unique final segment."""

        return cast(FinalSegment, self.segments[-1])
