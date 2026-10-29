from collections.abc import Callable
from dataclasses import FrozenInstanceError
from hashlib import sha256 as compute_sha256

import pytest

from sv_witness_metamorphic_testing.adversarial_corpus import (
    ADVERSARIAL_CORPUS,
    CorpusCase,
    materialize_case,
)
from sv_witness_metamorphic_testing.metamorphic_oracle import (
    OracleClassification,
    SemanticClaim,
)
from sv_witness_metamorphic_testing.multi_validator_evaluation import (
    CandidateAdmissionEvidence,
    NormalizedValidatorPair,
    NormalizedValidatorRun,
    evaluate_multi_validator_case,
)
from sv_witness_metamorphic_testing.semantic_relation import BaseRelation
from sv_witness_metamorphic_testing.task_model import Sha256Digest
from sv_witness_metamorphic_testing.validator_normalization import (
    BenchExecResultEvidence,
    NormalizationModelError,
    normalize_cpachecker_validation,
    normalize_theta_validation,
)
from sv_witness_metamorphic_testing.validator_runner import (
    ProcessExit,
    ProcessSpawnFailure,
    ProcessTimeout,
    ValidatorInvocation,
    ValidatorRun,
)

_REVISION = "2a1a063fea57af414f2b80c89009a958183498e6"
Normalizer = Callable[
    [ValidatorRun, BenchExecResultEvidence],
    NormalizedValidatorRun,
]


def _invocation() -> ValidatorInvocation:
    return ValidatorInvocation(
        argv=("/usr/bin/example-validator",),
        cwd="/tmp",
        environment=(),
        timeout_seconds=1.0,
    )


def _exit(returncode: int = 0) -> ValidatorRun:
    return ValidatorRun(
        invocation=_invocation(),
        observation=ProcessExit(
            returncode=returncode,
            stdout=b"fixture",
            stderr=b"",
        ),
    )


def _evidence(module: str, result: str) -> BenchExecResultEvidence:
    return BenchExecResultEvidence(
        tool_info_revision=_REVISION,
        tool_info_module=module,
        result=result,
    )


@pytest.mark.parametrize(
    ("normalizer", "module", "implementation"),
    [
        (
            normalize_cpachecker_validation,
            "benchexec.tools.cpachecker",
            "CPAchecker",
        ),
        (
            normalize_theta_validation,
            "benchexec.tools.theta",
            "Theta",
        ),
    ],
)
def test_confirmed_violation_is_nonempty(
    normalizer: Normalizer,
    module: str,
    implementation: str,
) -> None:
    run = _exit()
    value = normalizer(
        run,
        _evidence(module, "false(unreach-call)"),
    )

    assert value.run is run
    assert value.validator.implementation == implementation
    assert value.claim is SemanticClaim.NONEMPTY


@pytest.mark.parametrize(
    ("normalizer", "module", "result"),
    [
        (
            normalize_cpachecker_validation,
            "benchexec.tools.cpachecker",
            "true",
        ),
        (
            normalize_cpachecker_validation,
            "benchexec.tools.cpachecker",
            "ERROR (invalid witness file)",
        ),
        (
            normalize_theta_validation,
            "benchexec.tools.theta",
            "unknown",
        ),
        (
            normalize_theta_validation,
            "benchexec.tools.theta",
            "TIMEOUT",
        ),
    ],
)
def test_other_results_are_no_claim(
    normalizer: Normalizer,
    module: str,
    result: str,
) -> None:
    value = normalizer(
        _exit(),
        _evidence(module, result),
    )
    assert value.claim is SemanticClaim.NO_CLAIM


@pytest.mark.parametrize(
    "run",
    [
        ValidatorRun(
            invocation=_invocation(),
            observation=ProcessTimeout(
                stdout=b"",
                stderr=b"",
            ),
        ),
        ValidatorRun(
            invocation=_invocation(),
            observation=ProcessSpawnFailure(
                error_type="FileNotFoundError",
                errno=2,
                filename="/usr/bin/example-validator",
            ),
        ),
        _exit(returncode=1),
    ],
)
def test_confirming_status_requires_clean_exit(
    run: ValidatorRun,
) -> None:
    value = normalize_theta_validation(
        run,
        _evidence(
            "benchexec.tools.theta",
            "false(unreach-call)",
        ),
    )
    assert value.claim is SemanticClaim.NO_CLAIM


def test_contract_pins_are_enforced() -> None:
    wrong_revision = BenchExecResultEvidence(
        tool_info_revision="different",
        tool_info_module="benchexec.tools.cpachecker",
        result="false(unreach-call)",
    )
    wrong_module = _evidence(
        "benchexec.tools.cpachecker",
        "false(unreach-call)",
    )

    with pytest.raises(
        NormalizationModelError,
        match="pinned BenchExec",
    ):
        normalize_cpachecker_validation(
            _exit(),
            wrong_revision,
        )

    with pytest.raises(
        NormalizationModelError,
        match="validator-specific",
    ):
        normalize_theta_validation(
            _exit(),
            wrong_module,
        )


def test_evidence_is_immutable() -> None:
    evidence = _evidence(
        "benchexec.tools.theta",
        "unknown",
    )
    with pytest.raises(FrozenInstanceError):
        evidence.result = "true"  # type: ignore[misc]


def _exact_case() -> CorpusCase:
    return next(
        case for case in ADVERSARIAL_CORPUS if case.relation.base_relation is BaseRelation.EXACT
    )


def _admission(case: CorpusCase) -> CandidateAdmissionEvidence:
    source = next(
        artifact for artifact in materialize_case(case).artifacts if artifact.path == "source.yml"
    )
    return CandidateAdmissionEvidence(
        case_id=case.case_id,
        source_sha256=Sha256Digest(value=compute_sha256(source.content).hexdigest()),
        basis="independent-candidate-admission:test-fixture",
    )


def test_normalizers_compose_with_aggregate() -> None:
    case = _exact_case()

    def pair(
        normalizer: Normalizer,
        module: str,
    ) -> NormalizedValidatorPair:
        evidence = _evidence(
            module,
            "false(unreach-call)",
        )
        return NormalizedValidatorPair(
            source=normalizer(_exit(), evidence),
            transformed=normalizer(_exit(), evidence),
        )

    result = evaluate_multi_validator_case(
        case,
        _admission(case),
        (
            pair(
                normalize_cpachecker_validation,
                "benchexec.tools.cpachecker",
            ),
            pair(
                normalize_theta_validation,
                "benchexec.tools.theta",
            ),
        ),
    )

    assert tuple(item.validator.implementation for item in result.evaluations) == (
        "CPAchecker",
        "Theta",
    )
    assert all(
        item.source_claim is SemanticClaim.NONEMPTY
        and item.transformed_claim is SemanticClaim.NONEMPTY
        and item.classification is OracleClassification.COMPATIBLE
        for item in result.evaluations
    )
