"""Deterministic model-level reduction of relation-bearing transformation cases."""

from collections.abc import Callable, Iterator

from .exact_transformations import (
    explicit_main_thread,
    implicit_main_thread,
)
from .monotone_transformations import remove_avoid_assumption
from .transformation_evidence import (
    AvoidRemovalApplication,
    ExplicitMainThreadApplication,
    ImplicitMainThreadApplication,
    TransformationApplication,
    TransformationLocalEvidence,
)
from .witness_model import (
    AssumptionAction,
    AssumptionWaypoint,
    ViolationSequence,
)


class CaseReductionError(ValueError):
    """Raised when a case-reduction input violates the runtime contract."""


type InterestingnessPredicate = Callable[
    [TransformationLocalEvidence],
    bool,
]


def _validate_case(
    case: TransformationLocalEvidence,
) -> None:
    if not isinstance(
        case,
        TransformationLocalEvidence,
    ):
        raise CaseReductionError("case must be a TransformationLocalEvidence")


def _waypoint_count(
    witness: ViolationSequence,
) -> int:
    return sum(len(segment.waypoints) for segment in witness.segments)


def case_size(
    case: TransformationLocalEvidence,
) -> int:
    """Return the source-witness waypoint count for one relation case."""

    _validate_case(case)

    return _waypoint_count(case.source)


def _evaluate_interestingness(
    predicate: InterestingnessPredicate,
    case: TransformationLocalEvidence,
) -> bool:
    result = predicate(case)

    if type(result) is not bool:
        raise CaseReductionError("interestingness predicate must return bool")

    return result


def _eligible_avoid_positions(
    case: TransformationLocalEvidence,
) -> Iterator[tuple[int, int]]:
    distinguished: tuple[int, int] | None = None

    if isinstance(
        case.application,
        AvoidRemovalApplication,
    ):
        distinguished = (
            case.application.segment_index,
            case.application.waypoint_index,
        )

    for segment_index, segment in enumerate(case.source.segments):
        for waypoint_index, waypoint in enumerate(segment.waypoints):
            position = (
                segment_index,
                waypoint_index,
            )

            if position == distinguished:
                continue

            if (
                isinstance(
                    waypoint,
                    AssumptionWaypoint,
                )
                and waypoint.action is AssumptionAction.AVOID
            ):
                yield position


def _reduce_source_once(
    case: TransformationLocalEvidence,
    *,
    segment_index: int,
    waypoint_index: int,
) -> ViolationSequence:
    reduced_source = remove_avoid_assumption(
        case.source,
        segment_index,
        waypoint_index,
    )

    _ = TransformationLocalEvidence(
        task=case.task,
        source=case.source,
        transformed=reduced_source,
        application=AvoidRemovalApplication(
            segment_index=segment_index,
            waypoint_index=waypoint_index,
        ),
    )

    return reduced_source


def _adjust_application(
    application: TransformationApplication,
    *,
    removed_segment_index: int,
    removed_waypoint_index: int,
) -> TransformationApplication:
    if not isinstance(
        application,
        AvoidRemovalApplication,
    ):
        return application

    if (
        removed_segment_index == application.segment_index
        and removed_waypoint_index < application.waypoint_index
    ):
        return AvoidRemovalApplication(
            segment_index=application.segment_index,
            waypoint_index=(application.waypoint_index - 1),
        )

    return application


def _apply_transformation(
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

    if isinstance(
        application,
        AvoidRemovalApplication,
    ):
        return remove_avoid_assumption(
            source,
            application.segment_index,
            application.waypoint_index,
        )

    raise CaseReductionError("unsupported transformation application")


def _reconstruct_case(
    current: TransformationLocalEvidence,
    source: ViolationSequence,
    application: TransformationApplication,
) -> TransformationLocalEvidence:
    transformed = _apply_transformation(
        source,
        application,
    )

    reconstructed = TransformationLocalEvidence(
        task=current.task,
        source=source,
        transformed=transformed,
        application=application,
    )

    if type(reconstructed.application) is not type(current.application):
        raise CaseReductionError("reconstructed case changed application family")

    if reconstructed.base_relation != current.base_relation:
        raise CaseReductionError("reconstructed case changed base relation")

    return reconstructed


def single_step_reductions(
    case: TransformationLocalEvidence,
) -> tuple[TransformationLocalEvidence, ...]:
    """Return deterministic distinct one-avoid reductions of a relation case."""

    _validate_case(case)

    candidates: list[TransformationLocalEvidence] = []

    for (
        segment_index,
        waypoint_index,
    ) in _eligible_avoid_positions(case):
        reduced_source = _reduce_source_once(
            case,
            segment_index=segment_index,
            waypoint_index=waypoint_index,
        )

        application = _adjust_application(
            case.application,
            removed_segment_index=segment_index,
            removed_waypoint_index=waypoint_index,
        )

        candidate = _reconstruct_case(
            case,
            reduced_source,
            application,
        )

        if case_size(candidate) != (case_size(case) - 1):
            raise CaseReductionError("single-step reduction did not decrease source size by one")

        if candidate not in candidates:
            candidates.append(candidate)

    return tuple(candidates)


def reduce_case(
    case: TransformationLocalEvidence,
    interestingness: InterestingnessPredicate,
) -> TransformationLocalEvidence:
    """Greedily reduce one relation case under a caller-supplied predicate.

    The predicate is an operational selection mechanism only. It does not
    establish candidate admission, transformation-local evidence, or semantic
    relation correctness.

    The result is locally irreducible under the single-avoid reduction
    neighborhood and predicate. It is not claimed to be globally minimal.
    """

    _validate_case(case)

    if not callable(interestingness):
        raise CaseReductionError("interestingness must be callable")

    if not _evaluate_interestingness(
        interestingness,
        case,
    ):
        raise CaseReductionError("initial case must satisfy interestingness predicate")

    current = case

    while True:
        accepted: TransformationLocalEvidence | None = None

        for candidate in single_step_reductions(current):
            if _evaluate_interestingness(
                interestingness,
                candidate,
            ):
                accepted = candidate
                break

        if accepted is None:
            return current

        if case_size(accepted) >= case_size(current):
            raise CaseReductionError("accepted reduction did not strictly decrease case size")

        current = accepted
