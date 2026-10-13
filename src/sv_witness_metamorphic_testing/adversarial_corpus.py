"""Deterministic adversarial relation corpus and artifact materialization."""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import PurePosixPath
from uuid import UUID

from .exact_transformations import (
    explicit_main_thread,
    implicit_main_thread,
)
from .monotone_transformations import (
    remove_avoid_assumption,
)
from .task_model import (
    DataModel,
    ExecutionContext,
    Language,
    Program,
    ProgramInput,
    Sha256Digest,
    Specification,
    VerificationTask,
)
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
    CExpression,
    FinalSegment,
    Location,
    NormalSegment,
    TargetWaypoint,
    ViolationSequence,
)

_CASE_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")

_RESERVED_ARTIFACT_PATHS = frozenset(
    {
        "property.prp",
        "source.yml",
        "transformed.yml",
    }
)

_FORMAT_VERSION = "2.2"
_CREATION_TIME = "2026-10-13T00:00:00Z"
_PRODUCER_NAME = "sv-witness-metamorphic-testing"
_PRODUCER_VERSION = "0.1.0.dev0"

_SHARED_PROGRAM_PATH = "example.c"

_SHARED_PROGRAM_BYTES = b"""\
extern void __VERIFIER_error(void);

int main(void) {
    int x = 0;
    x = x + 1;
    if (x == 1) {
        x = x + 1;
    }
    if (x == 2) {
        __VERIFIER_error();
    }
    return 0;
}
"""

_SHARED_SPECIFICATION = "CHECK( init(main()), LTL(G ! call(__VERIFIER_error())) )"


class CorpusModelError(ValueError):
    """Raised when a corpus value violates its local contract."""


def _validate_relative_artifact_path(
    path: str,
    *,
    name: str,
) -> None:
    if type(path) is not str:
        raise CorpusModelError(f"{name} must be a string")

    if not path:
        raise CorpusModelError(f"{name} must not be empty")

    pure = PurePosixPath(path)

    if pure.is_absolute():
        raise CorpusModelError(f"{name} must be relative")

    if ".." in pure.parts:
        raise CorpusModelError(f"{name} must not contain parent components")

    if "\\" in path:
        raise CorpusModelError(f"{name} must use POSIX separators")


def _validate_slug(
    value: str,
    *,
    name: str,
) -> None:
    if type(value) is not str:
        raise CorpusModelError(f"{name} must be a string")

    if _CASE_ID_PATTERN.fullmatch(value) is None:
        raise CorpusModelError(f"{name} must be a lowercase ASCII slug")


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class WitnessArtifactMetadata:
    """Stable provenance metadata for one witness artifact."""

    format_version: str
    uuid: str
    creation_time: str
    producer_name: str
    producer_version: str

    def __post_init__(self) -> None:
        if self.format_version != _FORMAT_VERSION:
            raise CorpusModelError("witness format_version must be 2.2")

        if type(self.uuid) is not str:
            raise CorpusModelError("witness uuid must be a string")

        try:
            parsed_uuid = UUID(self.uuid)
        except (
            ValueError,
            AttributeError,
        ) as exc:
            raise CorpusModelError("witness uuid must be a valid UUID") from exc

        if str(parsed_uuid) != self.uuid:
            raise CorpusModelError("witness uuid must use canonical lowercase form")

        if type(self.creation_time) is not str:
            raise CorpusModelError("witness creation_time must be a string")

        try:
            parsed_time = datetime.strptime(
                self.creation_time,
                "%Y-%m-%dT%H:%M:%SZ",
            )
        except ValueError as exc:
            raise CorpusModelError(
                "witness creation_time must use UTC YYYY-MM-DDTHH:MM:SSZ form"
            ) from exc

        if parsed_time.strftime("%Y-%m-%dT%H:%M:%SZ") != self.creation_time:
            raise CorpusModelError("witness creation_time must use UTC YYYY-MM-DDTHH:MM:SSZ form")

        if type(self.producer_name) is not str or not self.producer_name:
            raise CorpusModelError("witness producer_name must be a non-empty string")

        if type(self.producer_version) is not str or not self.producer_version:
            raise CorpusModelError("witness producer_version must be a non-empty string")


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class CorpusProgramFile:
    """One program artifact bound to a task input."""

    path: str
    content: bytes

    def __post_init__(self) -> None:
        _validate_relative_artifact_path(
            self.path,
            name="program path",
        )

        if type(self.content) is not bytes:
            raise CorpusModelError("program content must be bytes")


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class CorpusCase:
    "One named relation-bearing corpus case."

    case_id: str
    description: str
    dimensions: tuple[str, ...]
    program_files: tuple[
        CorpusProgramFile,
        ...,
    ]
    source_metadata: WitnessArtifactMetadata
    transformed_metadata: WitnessArtifactMetadata
    relation: TransformationLocalEvidence

    def __post_init__(self) -> None:
        _validate_slug(
            self.case_id,
            name="case_id",
        )

        _validate_case_description(self.description)

        _validate_case_dimensions(self.dimensions)

        _validate_case_program_files(self.program_files)

        _validate_case_metadata_pair(
            self.source_metadata,
            self.transformed_metadata,
        )

        _validate_case_relation(self.relation)

        _validate_case_task_binding(
            self.program_files,
            self.relation,
        )

        _validate_case_locations(self.relation)


def _validate_case_description(
    description: str,
) -> None:
    if type(description) is not str or not description:
        raise CorpusModelError("description must be a non-empty string")


def _validate_case_dimensions(
    dimensions: tuple[str, ...],
) -> None:
    if (
        not isinstance(
            dimensions,
            tuple,
        )
        or not dimensions
    ):
        raise CorpusModelError("dimensions must be a non-empty tuple")

    for dimension in dimensions:
        _validate_slug(
            dimension,
            name="stress dimension",
        )

    if len(set(dimensions)) != len(dimensions):
        raise CorpusModelError("stress dimensions must be unique")


def _validate_case_program_files(
    program_files: tuple[
        CorpusProgramFile,
        ...,
    ],
) -> None:
    if (
        not isinstance(
            program_files,
            tuple,
        )
        or not program_files
    ):
        raise CorpusModelError("program_files must be a non-empty tuple")

    if any(
        not isinstance(
            program_file,
            CorpusProgramFile,
        )
        for program_file in program_files
    ):
        raise CorpusModelError("program_files must contain only CorpusProgramFile values")


def _validate_case_metadata_pair(
    source_metadata: WitnessArtifactMetadata,
    transformed_metadata: WitnessArtifactMetadata,
) -> None:
    if not isinstance(
        source_metadata,
        WitnessArtifactMetadata,
    ):
        raise CorpusModelError("source_metadata must be WitnessArtifactMetadata")

    if not isinstance(
        transformed_metadata,
        WitnessArtifactMetadata,
    ):
        raise CorpusModelError("transformed_metadata must be WitnessArtifactMetadata")

    if source_metadata.uuid == transformed_metadata.uuid:
        raise CorpusModelError("source and transformed witness UUIDs must differ")


def _validate_case_relation(
    relation: TransformationLocalEvidence,
) -> None:
    if not isinstance(
        relation,
        TransformationLocalEvidence,
    ):
        raise CorpusModelError("relation must be TransformationLocalEvidence")

    if relation.task.execution_context.additional_assumptions:
        raise CorpusModelError(
            "corpus materialization does not encode additional execution assumptions"
        )


def _validate_case_task_binding(
    program_files: tuple[
        CorpusProgramFile,
        ...,
    ],
    relation: TransformationLocalEvidence,
) -> None:
    program_paths = tuple(program_file.path for program_file in program_files)

    task_inputs = relation.task.program.inputs

    task_paths = tuple(program_input.path for program_input in task_inputs)

    if len(set(program_paths)) != len(program_paths):
        raise CorpusModelError("program artifact paths must be unique")

    if len(set(task_paths)) != len(task_paths):
        raise CorpusModelError("task program-input paths must be unique for corpus materialization")

    if program_paths != task_paths:
        raise CorpusModelError(
            "program artifact paths must exactly match task input paths in task order"
        )

    if any(path in _RESERVED_ARTIFACT_PATHS for path in program_paths):
        raise CorpusModelError("program artifact path collides with a reserved corpus artifact")

    for (
        program_file,
        program_input,
    ) in zip(
        program_files,
        task_inputs,
        strict=True,
    ):
        digest = sha256(program_file.content).hexdigest()

        if digest != program_input.sha256.value:
            raise CorpusModelError(
                f"program artifact hash does not match task input: {program_file.path}"
            )


def _validate_case_locations(
    relation: TransformationLocalEvidence,
) -> None:
    task_paths = {program_input.path for program_input in relation.task.program.inputs}

    for witness in (
        relation.source,
        relation.transformed,
    ):
        for segment in witness.segments:
            for waypoint in segment.waypoints:
                if waypoint.location.file_name not in task_paths:
                    raise CorpusModelError("witness location file_name must identify a task input")


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class MaterializedArtifact:
    """One relative artifact name and deterministic bytes."""

    path: str
    content: bytes

    def __post_init__(self) -> None:
        _validate_relative_artifact_path(
            self.path,
            name="artifact path",
        )

        if type(self.content) is not bytes:
            raise CorpusModelError("artifact content must be bytes")


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class MaterializedCorpusCase:
    """In-memory artifacts for one corpus case."""

    case_id: str
    artifacts: tuple[
        MaterializedArtifact,
        ...,
    ]

    def __post_init__(self) -> None:
        _validate_slug(
            self.case_id,
            name="case_id",
        )

        if (
            not isinstance(
                self.artifacts,
                tuple,
            )
            or not self.artifacts
        ):
            raise CorpusModelError("materialized artifacts must be a non-empty tuple")

        if any(
            not isinstance(
                artifact,
                MaterializedArtifact,
            )
            for artifact in self.artifacts
        ):
            raise CorpusModelError(
                "materialized artifacts must contain only MaterializedArtifact values"
            )

        paths = tuple(artifact.path for artifact in self.artifacts)

        if len(set(paths)) != len(paths):
            raise CorpusModelError("materialized artifact paths must be unique")


def _yaml_string(
    value: str,
) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
    )


def _emit_location(
    lines: list[str],
    *,
    location: Location,
    indent: str,
) -> None:
    lines.append(f"{indent}file_name: {_yaml_string(location.file_name)}")

    lines.append(f"{indent}line: {location.line}")

    if location.column is not None:
        lines.append(f"{indent}column: {location.column}")

    if location.function is not None:
        lines.append(f"{indent}function: {_yaml_string(location.function)}")


def _emit_waypoint(
    lines: list[str],
    waypoint: (AssumptionWaypoint | TargetWaypoint),
) -> None:
    if isinstance(
        waypoint,
        AssumptionWaypoint,
    ):
        lines.append('            type: "assumption"')
        lines.append(f'            action: "{waypoint.action.value}"')
        lines.append("            constraint:")
        lines.append(f"              value: {_yaml_string(waypoint.constraint.value)}")
        lines.append('              format: "c_expression"')
    else:
        lines.append('            type: "target"')
        lines.append('            action: "follow"')

    lines.append("            location:")

    _emit_location(
        lines,
        location=waypoint.location,
        indent="              ",
    )

    if waypoint.thread_id is not None:
        lines.append(f"            thread_id: {waypoint.thread_id}")


def _emit_witness(
    *,
    metadata: WitnessArtifactMetadata,
    task: VerificationTask,
    witness: ViolationSequence,
) -> bytes:
    lines = [
        '- entry_type: "violation_sequence"',
        "  metadata:",
        f"    format_version: {_yaml_string(metadata.format_version)}",
        f"    uuid: {_yaml_string(metadata.uuid)}",
        f"    creation_time: {_yaml_string(metadata.creation_time)}",
        "    producer:",
        f"      name: {_yaml_string(metadata.producer_name)}",
        f"      version: {_yaml_string(metadata.producer_version)}",
        "    task:",
        "      input_files:",
    ]

    lines.extend(
        f"        - {_yaml_string(program_input.path)}" for program_input in task.program.inputs
    )

    lines.append("      input_file_hashes:")

    lines.extend(
        (f"        {_yaml_string(program_input.path)}: {_yaml_string(program_input.sha256.value)}")
        for program_input in task.program.inputs
    )

    lines.extend(
        (
            f"      specification: {_yaml_string(task.specification.text)}",
            f'      data_model: "{task.execution_context.data_model.value}"',
            f'      language: "{task.execution_context.language.value}"',
            "  content:",
        )
    )

    for segment in witness.segments:
        lines.append("    - segment:")

        for waypoint in segment.waypoints:
            lines.append("        - waypoint:")

            _emit_waypoint(
                lines,
                waypoint,
            )

    return ("\n".join(lines) + "\n").encode("utf-8")


def materialize_case(
    case: CorpusCase,
) -> MaterializedCorpusCase:
    """Materialize a corpus case without I/O or process effects."""

    if not isinstance(
        case,
        CorpusCase,
    ):
        raise CorpusModelError("case must be a CorpusCase")

    program_artifacts = tuple(
        MaterializedArtifact(
            path=program_file.path,
            content=program_file.content,
        )
        for program_file in case.program_files
    )

    relation = case.relation

    artifacts = (
        *program_artifacts,
        MaterializedArtifact(
            path="property.prp",
            content=(relation.task.specification.text + "\n").encode("utf-8"),
        ),
        MaterializedArtifact(
            path="source.yml",
            content=_emit_witness(
                metadata=case.source_metadata,
                task=relation.task,
                witness=relation.source,
            ),
        ),
        MaterializedArtifact(
            path="transformed.yml",
            content=_emit_witness(
                metadata=case.transformed_metadata,
                task=relation.task,
                witness=relation.transformed,
            ),
        ),
    )

    return MaterializedCorpusCase(
        case_id=case.case_id,
        artifacts=artifacts,
    )


def _shared_task() -> VerificationTask:
    digest = sha256(_SHARED_PROGRAM_BYTES).hexdigest()

    return VerificationTask(
        program=Program(
            inputs=(
                ProgramInput(
                    path=_SHARED_PROGRAM_PATH,
                    sha256=Sha256Digest(
                        value=digest,
                    ),
                ),
            )
        ),
        specification=Specification(
            text=_SHARED_SPECIFICATION,
        ),
        execution_context=ExecutionContext(
            language=Language.C,
            data_model=DataModel.LP64,
        ),
    )


def _assumption(
    expression: str,
    *,
    line: int,
    action: AssumptionAction,
    thread_id: int | None,
) -> AssumptionWaypoint:
    return AssumptionWaypoint(
        action=action,
        constraint=CExpression(
            value=expression,
        ),
        location=Location(
            file_name=_SHARED_PROGRAM_PATH,
            line=line,
            column=5,
            function="main",
        ),
        thread_id=thread_id,
    )


def _target(
    *,
    thread_id: int | None,
) -> TargetWaypoint:
    return TargetWaypoint(
        location=Location(
            file_name=_SHARED_PROGRAM_PATH,
            line=10,
            column=9,
            function="main",
        ),
        thread_id=thread_id,
    )


def _source_witness(
    *,
    normal_avoids: tuple[
        tuple[str, int],
        ...,
    ] = (),
    final_avoids: tuple[
        tuple[str, int],
        ...,
    ] = (),
    thread_id: int | None,
) -> ViolationSequence:
    normal_waypoints = (
        *(
            _assumption(
                expression,
                line=line,
                action=AssumptionAction.AVOID,
                thread_id=thread_id,
            )
            for (
                expression,
                line,
            ) in normal_avoids
        ),
        _assumption(
            "x == 0",
            line=5,
            action=AssumptionAction.FOLLOW,
            thread_id=thread_id,
        ),
    )

    final_waypoints: tuple[
        AssumptionWaypoint | TargetWaypoint,
        ...,
    ] = (
        *(
            _assumption(
                expression,
                line=line,
                action=AssumptionAction.AVOID,
                thread_id=thread_id,
            )
            for (
                expression,
                line,
            ) in final_avoids
        ),
        _target(
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


def _transformed_for(
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


def _metadata(
    uuid: str,
) -> WitnessArtifactMetadata:
    return WitnessArtifactMetadata(
        format_version=_FORMAT_VERSION,
        uuid=uuid,
        creation_time=_CREATION_TIME,
        producer_name=_PRODUCER_NAME,
        producer_version=_PRODUCER_VERSION,
    )


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class _CaseMetadata:
    "Descriptive metadata used by the private corpus factory."

    case_id: str
    description: str
    dimensions: tuple[str, ...]


def _case(
    *,
    metadata: _CaseMetadata,
    source_uuid: str,
    transformed_uuid: str,
    source: ViolationSequence,
    application: TransformationApplication,
) -> CorpusCase:
    task = _shared_task()

    relation = TransformationLocalEvidence(
        task=task,
        source=source,
        transformed=_transformed_for(
            source,
            application,
        ),
        application=application,
    )

    return CorpusCase(
        case_id=metadata.case_id,
        description=metadata.description,
        dimensions=metadata.dimensions,
        program_files=(
            CorpusProgramFile(
                path=_SHARED_PROGRAM_PATH,
                content=_SHARED_PROGRAM_BYTES,
            ),
        ),
        source_metadata=_metadata(source_uuid),
        transformed_metadata=_metadata(transformed_uuid),
        relation=relation,
    )


def _validate_corpus(
    cases: tuple[
        CorpusCase,
        ...,
    ],
) -> tuple[
    CorpusCase,
    ...,
]:
    case_ids = tuple(case.case_id for case in cases)

    if len(set(case_ids)) != len(case_ids):
        raise CorpusModelError("corpus case IDs must be unique")

    if case_ids != tuple(sorted(case_ids)):
        raise CorpusModelError("corpus cases must be ordered by case_id")

    witness_uuids = tuple(
        uuid
        for case in cases
        for uuid in (
            case.source_metadata.uuid,
            case.transformed_metadata.uuid,
        )
    )

    if len(set(witness_uuids)) != len(witness_uuids):
        raise CorpusModelError("corpus witness UUIDs must be globally unique")

    return cases


ADVERSARIAL_CORPUS = _validate_corpus(
    (
        _case(
            metadata=_CaseMetadata(
                case_id="broadening-final-late-avoid",
                description="Remove the later of two final-segment avoid assumptions.",
                dimensions=(
                    "broadening-relation",
                    "final-segment-avoid-removal",
                    "distinguished-avoid-late",
                    "reducible-non-distinguished-avoids",
                ),
            ),
            source_uuid="00000000-0000-4000-8000-000000000001",
            transformed_uuid="00000000-0000-4000-8000-000000000002",
            source=_source_witness(final_avoids=(("x == 99", 9), ("x == 98", 9)), thread_id=None),
            application=AvoidRemovalApplication(segment_index=1, waypoint_index=1),
        ),
        _case(
            metadata=_CaseMetadata(
                case_id="broadening-normal-interior-avoid",
                description="Remove an interior avoid between neighboring normal-segment avoids.",
                dimensions=(
                    "broadening-relation",
                    "normal-segment-avoid-removal",
                    "adjacent-avoid-assumptions",
                    "distinguished-avoid-interior",
                    "reducible-non-distinguished-avoids",
                ),
            ),
            source_uuid="00000000-0000-4000-8000-000000000003",
            transformed_uuid="00000000-0000-4000-8000-000000000004",
            source=_source_witness(
                normal_avoids=(("x == 99", 5), ("x == 98", 5), ("x == 97", 5)), thread_id=None
            ),
            application=AvoidRemovalApplication(segment_index=0, waypoint_index=1),
        ),
        _case(
            metadata=_CaseMetadata(
                case_id="broadening-normal-single-avoid",
                description="Remove the only normal-segment avoid assumption.",
                dimensions=(
                    "broadening-relation",
                    "normal-segment-avoid-removal",
                    "distinguished-avoid-early",
                    "locally-irreducible",
                ),
            ),
            source_uuid="00000000-0000-4000-8000-000000000005",
            transformed_uuid="00000000-0000-4000-8000-000000000006",
            source=_source_witness(normal_avoids=(("x == 99", 5),), thread_id=None),
            application=AvoidRemovalApplication(segment_index=0, waypoint_index=0),
        ),
        _case(
            metadata=_CaseMetadata(
                case_id="exact-explicit-main-thread",
                description="Canonicalize absent main-thread identifiers to explicit zero.",
                dimensions=("exact-relation", "explicit-main-thread-canonicalization"),
            ),
            source_uuid="00000000-0000-4000-8000-000000000007",
            transformed_uuid="00000000-0000-4000-8000-000000000008",
            source=_source_witness(thread_id=None),
            application=ExplicitMainThreadApplication(),
        ),
        _case(
            metadata=_CaseMetadata(
                case_id="exact-implicit-main-thread",
                description="Canonicalize explicit-zero main-thread identifiers to absence.",
                dimensions=("exact-relation", "implicit-main-thread-canonicalization"),
            ),
            source_uuid="00000000-0000-4000-8000-000000000009",
            transformed_uuid="00000000-0000-4000-8000-000000000010",
            source=_source_witness(thread_id=0),
            application=ImplicitMainThreadApplication(),
        ),
        _case(
            metadata=_CaseMetadata(
                case_id="exact-irreducible-main-thread",
                description="Exact main-thread relation with no removable avoid assumption.",
                dimensions=(
                    "exact-relation",
                    "implicit-main-thread-canonicalization",
                    "locally-irreducible",
                ),
            ),
            source_uuid="00000000-0000-4000-8000-000000000011",
            transformed_uuid="00000000-0000-4000-8000-000000000012",
            source=_source_witness(thread_id=0),
            application=ImplicitMainThreadApplication(),
        ),
        _case(
            metadata=_CaseMetadata(
                case_id="exact-reducible-avoids",
                description="Exact main-thread relation containing distinct removable avoids.",
                dimensions=(
                    "exact-relation",
                    "explicit-main-thread-canonicalization",
                    "reducible-non-distinguished-avoids",
                ),
            ),
            source_uuid="00000000-0000-4000-8000-000000000013",
            transformed_uuid="00000000-0000-4000-8000-000000000014",
            source=_source_witness(normal_avoids=(("x == 99", 5), ("x == 98", 5)), thread_id=None),
            application=ExplicitMainThreadApplication(),
        ),
        _case(
            metadata=_CaseMetadata(
                case_id="exact-repeated-equal-avoids",
                description=(
                    "Exact relation with equal adjacent avoids producing duplicate reductions."
                ),
                dimensions=(
                    "exact-relation",
                    "explicit-main-thread-canonicalization",
                    "repeated-equal-avoid-assumptions",
                    "adjacent-avoid-assumptions",
                    "reducible-non-distinguished-avoids",
                ),
            ),
            source_uuid="00000000-0000-4000-8000-000000000015",
            transformed_uuid="00000000-0000-4000-8000-000000000016",
            source=_source_witness(normal_avoids=(("x == 99", 5), ("x == 99", 5)), thread_id=None),
            application=ExplicitMainThreadApplication(),
        ),
    )
)
