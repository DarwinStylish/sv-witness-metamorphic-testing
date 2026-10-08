"""Independent local evidence checks for concrete witness transformations."""

from dataclasses import dataclass, field

from .semantic_relation import BaseRelation
from .task_model import VerificationTask
from .witness_model import (
    AssumptionAction,
    AssumptionWaypoint,
    Segment,
    TargetWaypoint,
    ViolationSequence,
)


class EvidenceError(ValueError):
    """Raised when transformation-local evidence cannot be established."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ExplicitMainThreadApplication:
    """Application of explicit main-thread canonicalization."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ImplicitMainThreadApplication:
    """Application of implicit main-thread canonicalization."""


def _validate_application_index(
    index: int,
    *,
    name: str,
) -> None:
    if type(index) is not int:
        raise EvidenceError(f"{name} must be an integer")

    if index < 0:
        raise EvidenceError(f"{name} must be non-negative")


@dataclass(frozen=True, slots=True, kw_only=True)
class AvoidRemovalApplication:
    """Application of single selected avoid-assumption removal."""

    segment_index: int
    waypoint_index: int

    def __post_init__(self) -> None:
        _validate_application_index(
            self.segment_index,
            name="segment_index",
        )
        _validate_application_index(
            self.waypoint_index,
            name="waypoint_index",
        )


type TransformationApplication = (
    ExplicitMainThreadApplication | ImplicitMainThreadApplication | AvoidRemovalApplication
)


def _same_non_thread_payload(
    source: AssumptionWaypoint | TargetWaypoint,
    transformed: AssumptionWaypoint | TargetWaypoint,
) -> bool:
    if isinstance(source, AssumptionWaypoint):
        return (
            isinstance(transformed, AssumptionWaypoint)
            and source.action is transformed.action
            and source.constraint == transformed.constraint
            and source.location == transformed.location
        )

    return isinstance(transformed, TargetWaypoint) and source.location == transformed.location


def _check_main_thread_application(
    source: ViolationSequence,
    transformed: ViolationSequence,
    *,
    expected_thread_id: int | None,
) -> None:
    if len(source.segments) != len(transformed.segments):
        raise EvidenceError("main-thread transformation changed segment count")

    for source_segment, transformed_segment in zip(
        source.segments,
        transformed.segments,
        strict=True,
    ):
        if type(source_segment) is not type(transformed_segment):
            raise EvidenceError("main-thread transformation changed segment kind")

        if len(source_segment.waypoints) != len(transformed_segment.waypoints):
            raise EvidenceError("main-thread transformation changed waypoint count")

        for source_waypoint, transformed_waypoint in zip(
            source_segment.waypoints,
            transformed_segment.waypoints,
            strict=True,
        ):
            if not _same_non_thread_payload(
                source_waypoint,
                transformed_waypoint,
            ):
                raise EvidenceError("main-thread transformation changed non-thread payload")

            if transformed_waypoint.thread_id != expected_thread_id:
                raise EvidenceError("main-thread transformation has wrong thread representation")


def _source_avoid_waypoint(
    source: ViolationSequence,
    application: AvoidRemovalApplication,
) -> tuple[Segment, AssumptionWaypoint]:
    if application.segment_index >= len(source.segments):
        raise EvidenceError("segment_index outside source witness")

    source_segment = source.segments[application.segment_index]

    if application.waypoint_index >= len(source_segment.waypoints):
        raise EvidenceError("waypoint_index outside source segment")

    selected = source_segment.waypoints[application.waypoint_index]

    if (
        not isinstance(selected, AssumptionWaypoint)
        or selected.action is not AssumptionAction.AVOID
    ):
        raise EvidenceError("selected source waypoint must be an avoid assumption")

    return source_segment, selected


def _check_avoid_removal_application(
    source: ViolationSequence,
    transformed: ViolationSequence,
    application: AvoidRemovalApplication,
) -> None:
    source_segment, _ = _source_avoid_waypoint(
        source,
        application,
    )

    if len(source.segments) != len(transformed.segments):
        raise EvidenceError("avoid removal changed segment count")

    for index, (
        candidate_source_segment,
        candidate_transformed_segment,
    ) in enumerate(
        zip(
            source.segments,
            transformed.segments,
            strict=True,
        )
    ):
        if (
            index != application.segment_index
            and candidate_transformed_segment != candidate_source_segment
        ):
            raise EvidenceError("avoid removal changed an unselected segment")

    transformed_segment = transformed.segments[application.segment_index]

    if type(source_segment) is not type(transformed_segment):
        raise EvidenceError("avoid removal changed selected segment kind")

    if len(transformed_segment.waypoints) != (len(source_segment.waypoints) - 1):
        raise EvidenceError("avoid removal must remove exactly one waypoint")

    expected_waypoints = (
        *source_segment.waypoints[: application.waypoint_index],
        *source_segment.waypoints[application.waypoint_index + 1 :],
    )

    if transformed_segment.waypoints != expected_waypoints:
        raise EvidenceError("avoid removal result is not the selected one-position deletion")


@dataclass(frozen=True, slots=True, kw_only=True)
class TransformationLocalEvidence:
    """Local conformance evidence, conditional on independent source admission."""

    task: VerificationTask
    source: ViolationSequence
    transformed: ViolationSequence
    application: TransformationApplication
    base_relation: BaseRelation = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.task, VerificationTask):
            raise EvidenceError("task must be a VerificationTask")

        if not isinstance(self.source, ViolationSequence):
            raise EvidenceError("source must be a ViolationSequence")

        if not isinstance(self.transformed, ViolationSequence):
            raise EvidenceError("transformed must be a ViolationSequence")

        if isinstance(
            self.application,
            ExplicitMainThreadApplication,
        ):
            _check_main_thread_application(
                self.source,
                self.transformed,
                expected_thread_id=0,
            )
            relation = BaseRelation.EXACT

        elif isinstance(
            self.application,
            ImplicitMainThreadApplication,
        ):
            _check_main_thread_application(
                self.source,
                self.transformed,
                expected_thread_id=None,
            )
            relation = BaseRelation.EXACT

        elif isinstance(
            self.application,
            AvoidRemovalApplication,
        ):
            _check_avoid_removal_application(
                self.source,
                self.transformed,
                self.application,
            )
            relation = BaseRelation.BROADENING

        else:
            raise EvidenceError("application must be a supported transformation application")

        object.__setattr__(
            self,
            "base_relation",
            relation,
        )
