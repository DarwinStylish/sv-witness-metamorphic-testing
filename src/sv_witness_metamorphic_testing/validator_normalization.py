"""Concrete normalization contracts for selected violation-witness validators."""

from dataclasses import dataclass

from .metamorphic_oracle import SemanticClaim
from .multi_validator_evaluation import (
    AdapterIdentity,
    NormalizedValidatorRun,
    ValidatorIdentity,
)
from .validator_runner import ProcessExit, ValidatorRun

_BENCHEXEC_TOOL_INFO_REVISION = "2a1a063fea57af414f2b80c89009a958183498e6"
_CPACHECKER_VERSION = "4.2.2-3728-g5c33b8d955"
_THETA_VERSION = "git-f30b2fb88f9345df07878b0363c2bf1f8e76c604"
_CPACHECKER_TOOL_INFO = "benchexec.tools.cpachecker"
_THETA_TOOL_INFO = "benchexec.tools.theta"
_CONFIRMED_UNREACH_CALL = "false(unreach-call)"
_ADAPTER_VERSION = "1"


class NormalizationModelError(ValueError):
    """Raised when normalization evidence violates a pinned contract."""


def _text(value: str, *, name: str) -> None:
    if type(value) is not str or not value:
        raise NormalizationModelError(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True, kw_only=True)
class BenchExecResultEvidence:
    """Standardized BenchExec result with explicit tool-info provenance."""

    tool_info_revision: str
    tool_info_module: str
    result: str

    def __post_init__(self) -> None:
        _text(self.tool_info_revision, name="tool_info_revision")
        _text(self.tool_info_module, name="tool_info_module")
        _text(self.result, name="result")


def _claim_for_result(run: ValidatorRun, result: str) -> SemanticClaim:
    observation = run.observation

    if (
        result == _CONFIRMED_UNREACH_CALL
        and isinstance(observation, ProcessExit)
        and observation.returncode == 0
    ):
        return SemanticClaim.NONEMPTY

    return SemanticClaim.NO_CLAIM


def _normalize(
    *,
    run: ValidatorRun,
    evidence: BenchExecResultEvidence,
    validator: ValidatorIdentity,
    adapter: AdapterIdentity,
    tool_info_module: str,
) -> NormalizedValidatorRun:
    if not isinstance(run, ValidatorRun):
        raise NormalizationModelError("run must be a ValidatorRun")

    if not isinstance(evidence, BenchExecResultEvidence):
        raise NormalizationModelError("evidence must be BenchExecResultEvidence")

    if evidence.tool_info_revision != _BENCHEXEC_TOOL_INFO_REVISION:
        raise NormalizationModelError("evidence must use the pinned BenchExec tool-info revision")

    if evidence.tool_info_module != tool_info_module:
        raise NormalizationModelError(
            "evidence must use the validator-specific BenchExec tool-info module"
        )

    return NormalizedValidatorRun(
        validator=validator,
        adapter=adapter,
        run=run,
        claim=_claim_for_result(run, evidence.result),
    )


def normalize_cpachecker_validation(
    run: ValidatorRun,
    evidence: BenchExecResultEvidence,
) -> NormalizedValidatorRun:
    """Normalize pinned CPAchecker violation-witness validation evidence."""

    return _normalize(
        run=run,
        evidence=evidence,
        validator=ValidatorIdentity(
            implementation="CPAchecker",
            version=_CPACHECKER_VERSION,
        ),
        adapter=AdapterIdentity(
            name="cpachecker-benchexec-status",
            version=_ADAPTER_VERSION,
            normalization_contract=(
                "cpachecker-4.2.2-3728-g5c33b8d955/benchexec-2a1a063/violation-unreach-call-v1"
            ),
        ),
        tool_info_module=_CPACHECKER_TOOL_INFO,
    )


def normalize_theta_validation(
    run: ValidatorRun,
    evidence: BenchExecResultEvidence,
) -> NormalizedValidatorRun:
    """Normalize pinned Theta violation-witness validation evidence."""

    return _normalize(
        run=run,
        evidence=evidence,
        validator=ValidatorIdentity(
            implementation="Theta",
            version=_THETA_VERSION,
        ),
        adapter=AdapterIdentity(
            name="theta-benchexec-status",
            version=_ADAPTER_VERSION,
            normalization_contract=(
                "theta-f30b2fb88f9345df07878b0363c2bf1f8e76c604/"
                "benchexec-2a1a063/violation-unreach-call-v1"
            ),
        ),
        tool_info_module=_THETA_TOOL_INFO,
    )
