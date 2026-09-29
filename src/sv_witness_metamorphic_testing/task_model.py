"""Internal model for fixed verification tasks."""

import re
from dataclasses import dataclass
from enum import StrEnum

_SHA256_PATTERN = re.compile(r"[0-9a-fA-F]{64}\Z")


class TaskModelError(ValueError):
    """Raised when an object violates a local verification-task invariant."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Sha256Digest:
    """SHA-256 digest represented as canonical lowercase hexadecimal text."""

    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str:
            raise TaskModelError("SHA-256 digest must be a string")

        if _SHA256_PATTERN.fullmatch(self.value) is None:
            raise TaskModelError("SHA-256 digest must contain exactly 64 hexadecimal characters")

        object.__setattr__(self, "value", self.value.lower())


@dataclass(frozen=True, slots=True, kw_only=True)
class ProgramInput:
    """One original verifier input together with its recorded content digest.

    The path is retained exactly as supplied by the task representation. This
    model performs no path normalization, filesystem lookup, or hash
    computation.
    """

    path: str
    sha256: Sha256Digest

    def __post_init__(self) -> None:
        if type(self.path) is not str:
            raise TaskModelError("program-input path must be a string")

        if not isinstance(self.sha256, Sha256Digest):
            raise TaskModelError("program-input sha256 must be a Sha256Digest")


@dataclass(frozen=True, slots=True, kw_only=True)
class Program:
    """Exact program identity used by the supported verification-task model.

    Input order and exact path spelling are preserved rather than normalized.
    """

    inputs: tuple[ProgramInput, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.inputs, tuple):
            raise TaskModelError("program inputs must be a tuple")

        if not self.inputs:
            raise TaskModelError("program must contain at least one original input")

        if any(not isinstance(program_input, ProgramInput) for program_input in self.inputs):
            raise TaskModelError("program inputs must all be ProgramInput objects")


@dataclass(frozen=True, slots=True, kw_only=True)
class Specification:
    """Opaque checked-specification text.

    Construction preserves the specification supplied by the verification
    task. It does not establish that the text denotes a supported
    `unreach-call` property or that two different texts are semantically
    equivalent. Membership in the supported research profile is a separate
    admission question.
    """

    text: str

    def __post_init__(self) -> None:
        if type(self.text) is not str:
            raise TaskModelError("specification text must be a string")


class Language(StrEnum):
    """Programming languages admitted by the current task profile."""

    C = "C"


class DataModel(StrEnum):
    """C data models admitted by SV-Witness task metadata."""

    ILP32 = "ILP32"
    LP64 = "LP64"


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionAssumption:
    """Opaque named machine or execution assumption.

    This project-side carrier permits a caller to retain assumptions that
    contribute to the semantic execution context but are not represented by
    the current SV-Witness `language` and `data_model` fields.

    The model assigns no semantic equivalence to different assumption objects.
    """

    name: str
    value: str

    def __post_init__(self) -> None:
        if type(self.name) is not str:
            raise TaskModelError("execution-assumption name must be a string")

        if type(self.value) is not str:
            raise TaskModelError("execution-assumption value must be a string")


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionContext:
    """Execution context M for a verification task.

    Additional assumptions are retained in caller-supplied order, including
    duplicate occurrences. This representation deliberately does not define
    normalization, deduplication, or semantic equivalence for them.
    """

    language: Language
    data_model: DataModel
    additional_assumptions: tuple[ExecutionAssumption, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.language, Language):
            raise TaskModelError("execution-context language must be a Language")

        if not isinstance(self.data_model, DataModel):
            raise TaskModelError("execution-context data_model must be a DataModel")

        if not isinstance(self.additional_assumptions, tuple):
            raise TaskModelError("additional execution assumptions must be a tuple")

        if any(
            not isinstance(assumption, ExecutionAssumption)
            for assumption in self.additional_assumptions
        ):
            raise TaskModelError(
                "additional execution assumptions must all be ExecutionAssumption objects"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class VerificationTask:
    """Fixed verification task tau = (P, phi, M).

    Witness provenance and witness-format metadata are deliberately not part of
    this model. Construction establishes the task value and local model
    invariants; it does not establish admission to the supported research
    profile.
    """

    program: Program
    specification: Specification
    execution_context: ExecutionContext

    def __post_init__(self) -> None:
        if not isinstance(self.program, Program):
            raise TaskModelError("verification-task program must be a Program")

        if not isinstance(self.specification, Specification):
            raise TaskModelError("verification-task specification must be a Specification")

        if not isinstance(self.execution_context, ExecutionContext):
            raise TaskModelError("verification-task execution_context must be an ExecutionContext")
