from dataclasses import FrozenInstanceError, fields, replace
from hashlib import sha256 as compute_sha256
from typing import cast

import pytest

import sv_witness_metamorphic_testing.multi_validator_evaluation as evaluation_module
from sv_witness_metamorphic_testing.adversarial_corpus import (
    ADVERSARIAL_CORPUS,
    materialize_case,
)
from sv_witness_metamorphic_testing.metamorphic_oracle import (
    OracleClassification,
    SemanticClaim,
)
from sv_witness_metamorphic_testing.multi_validator_evaluation import (
    AdapterIdentity,
    ArtifactDigest,
    CandidateAdmissionEvidence,
    EvaluationModelError,
    MultiValidatorEvaluation,
    NormalizedValidatorPair,
    NormalizedValidatorRun,
    ValidatorIdentity,
    evaluate_multi_validator_case,
)
from sv_witness_metamorphic_testing.task_model import Sha256Digest
from sv_witness_metamorphic_testing.validator_runner import (
    ProcessExit,
    ProcessSpawnFailure,
    ProcessTimeout,
    ValidatorInvocation,
    ValidatorRun,
)

_EXPECTED_ARTIFACT_COUNT = 4


def _run(marker: bytes) -> ValidatorRun:
    return ValidatorRun(
        invocation=ValidatorInvocation(
            argv=("/usr/bin/example-validator",),
            cwd="/tmp",
            environment=(),
            timeout_seconds=1.0,
        ),
        observation=ProcessExit(returncode=0, stdout=marker, stderr=b""),
    )


def _identity(name: str, version: str = "1.0") -> ValidatorIdentity:
    return ValidatorIdentity(implementation=name, version=version)


def _adapter(name: str) -> AdapterIdentity:
    return AdapterIdentity(
        name=f"{name}-adapter",
        version="1.0",
        normalization_contract=f"contract:{name}:1.0",
    )


def _normalized(
    name: str,
    claim: SemanticClaim,
    marker: bytes,
    *,
    version: str = "1.0",
    run: ValidatorRun | None = None,
) -> NormalizedValidatorRun:
    return NormalizedValidatorRun(
        validator=_identity(name, version),
        adapter=_adapter(name),
        run=_run(marker) if run is None else run,
        claim=claim,
    )


def _pair(
    name: str,
    source_claim: SemanticClaim,
    transformed_claim: SemanticClaim,
    *,
    version: str = "1.0",
) -> NormalizedValidatorPair:
    marker = name.encode("ascii")
    return NormalizedValidatorPair(
        source=_normalized(
            name,
            source_claim,
            b"source-" + marker,
            version=version,
        ),
        transformed=_normalized(
            name,
            transformed_claim,
            b"transformed-" + marker,
            version=version,
        ),
    )


def _admission() -> CandidateAdmissionEvidence:
    case = ADVERSARIAL_CORPUS[0]
    source = next(
        artifact for artifact in materialize_case(case).artifacts if artifact.path == "source.yml"
    )
    return CandidateAdmissionEvidence(
        case_id=case.case_id,
        source_sha256=Sha256Digest(value=compute_sha256(source.content).hexdigest()),
        basis="independent-candidate-admission:test-fixture",
    )


def _pairs() -> tuple[NormalizedValidatorPair, ...]:
    return (
        _pair(
            "validator-a",
            SemanticClaim.NONEMPTY,
            SemanticClaim.EMPTY,
        ),
        _pair(
            "validator-b",
            SemanticClaim.NO_CLAIM,
            SemanticClaim.NO_CLAIM,
        ),
    )


@pytest.mark.parametrize(
    ("implementation", "version"),
    [("", "1.0"), ("validator-a", "")],
)
def test_validator_identity_rejects_empty_fields(
    implementation: str,
    version: str,
) -> None:
    with pytest.raises(EvaluationModelError, match="validator"):
        ValidatorIdentity(
            implementation=implementation,
            version=version,
        )


@pytest.mark.parametrize(
    ("name", "version", "contract"),
    [("", "1.0", "contract"), ("adapter", "", "contract"), ("adapter", "1.0", "")],
)
def test_adapter_identity_rejects_empty_fields(
    name: str,
    version: str,
    contract: str,
) -> None:
    with pytest.raises(EvaluationModelError):
        AdapterIdentity(
            name=name,
            version=version,
            normalization_contract=contract,
        )


def test_admission_requires_typed_source_digest() -> None:
    with pytest.raises(EvaluationModelError, match="source_sha256"):
        CandidateAdmissionEvidence(
            case_id="case-a",
            source_sha256=cast(Sha256Digest, "0" * 64),
            basis="external-admission",
        )


def test_normalized_run_preserves_raw_record() -> None:
    run = _run(b"raw")
    normalized = _normalized(
        "validator-a",
        SemanticClaim.NO_CLAIM,
        b"unused",
        run=run,
    )
    assert normalized.run is run
    assert normalized.claim is SemanticClaim.NO_CLAIM


def test_pair_requires_same_validator_identity() -> None:
    with pytest.raises(EvaluationModelError, match="same validator identity"):
        NormalizedValidatorPair(
            source=_normalized(
                "validator-a",
                SemanticClaim.NO_CLAIM,
                b"a",
            ),
            transformed=_normalized(
                "validator-b",
                SemanticClaim.NO_CLAIM,
                b"b",
            ),
        )


def test_pair_requires_same_adapter_identity() -> None:
    source = _normalized(
        "validator-a",
        SemanticClaim.NO_CLAIM,
        b"a",
    )
    transformed = replace(
        source,
        adapter=AdapterIdentity(
            name="other-adapter",
            version="1.0",
            normalization_contract="other-contract",
        ),
        run=_run(b"b"),
    )
    with pytest.raises(EvaluationModelError, match="same adapter identity"):
        NormalizedValidatorPair(source=source, transformed=transformed)


def test_admission_binding_is_checked_before_oracle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_classifier(*args: object) -> object:
        raise AssertionError("oracle called before admission binding")

    monkeypatch.setattr(
        evaluation_module,
        "classify_claim_pair",
        fail_classifier,
    )

    with pytest.raises(EvaluationModelError, match="materialized source witness"):
        evaluate_multi_validator_case(
            ADVERSARIAL_CORPUS[0],
            replace(
                _admission(),
                source_sha256=Sha256Digest(value="0" * 64),
            ),
            _pairs(),
        )


def test_evaluation_rejects_wrong_admission_case() -> None:
    with pytest.raises(EvaluationModelError, match="evaluated case"):
        evaluate_multi_validator_case(
            ADVERSARIAL_CORPUS[0],
            replace(_admission(), case_id="different-case"),
            _pairs(),
        )


def test_evaluation_rejects_wrong_source_digest() -> None:
    with pytest.raises(EvaluationModelError, match="materialized source witness"):
        evaluate_multi_validator_case(
            ADVERSARIAL_CORPUS[0],
            replace(
                _admission(),
                source_sha256=Sha256Digest(value="0" * 64),
            ),
            _pairs(),
        )


def test_evaluation_requires_two_implementations() -> None:
    with pytest.raises(EvaluationModelError, match="at least two"):
        evaluate_multi_validator_case(
            ADVERSARIAL_CORPUS[0],
            _admission(),
            (_pairs()[0],),
        )


def test_two_versions_of_one_implementation_do_not_count_as_multi_validator() -> None:
    with pytest.raises(EvaluationModelError, match="implementations must be distinct"):
        evaluate_multi_validator_case(
            ADVERSARIAL_CORPUS[0],
            _admission(),
            (
                _pair(
                    "validator-a",
                    SemanticClaim.NO_CLAIM,
                    SemanticClaim.NO_CLAIM,
                    version="1.0",
                ),
                _pair(
                    "validator-a",
                    SemanticClaim.NO_CLAIM,
                    SemanticClaim.NO_CLAIM,
                    version="2.0",
                ),
            ),
        )


def test_evaluation_preserves_independent_oracle_results() -> None:
    result = evaluate_multi_validator_case(
        ADVERSARIAL_CORPUS[0],
        _admission(),
        _pairs(),
    )
    assert result.evaluations[0].classification is OracleClassification.CONTRADICTION
    assert result.evaluations[1].classification is OracleClassification.INDETERMINATE


def test_artifact_digests_match_materialized_bytes() -> None:
    case = ADVERSARIAL_CORPUS[0]
    result = evaluate_multi_validator_case(case, _admission(), _pairs())
    materialized = materialize_case(case)

    assert len(result.artifact_digests) == _EXPECTED_ARTIFACT_COUNT
    assert tuple(item.path for item in result.artifact_digests) == tuple(
        artifact.path for artifact in materialized.artifacts
    )
    assert tuple(item.sha256.value for item in result.artifact_digests) == tuple(
        compute_sha256(artifact.content).hexdigest() for artifact in materialized.artifacts
    )


def test_timeout_and_spawn_failure_remain_raw_no_claim_observations() -> None:
    invocation = ValidatorInvocation(
        argv=("/usr/bin/example-validator",),
        cwd="/tmp",
        environment=(),
        timeout_seconds=1.0,
    )
    timeout = ValidatorRun(
        invocation=invocation,
        observation=ProcessTimeout(stdout=b"partial", stderr=b""),
    )
    spawn_failure = ValidatorRun(
        invocation=invocation,
        observation=ProcessSpawnFailure(
            error_type="FileNotFoundError",
            errno=2,
            filename="/usr/bin/example-validator",
        ),
    )
    first = NormalizedValidatorPair(
        source=_normalized(
            "validator-a",
            SemanticClaim.NO_CLAIM,
            b"",
            run=timeout,
        ),
        transformed=_normalized(
            "validator-a",
            SemanticClaim.NO_CLAIM,
            b"",
            run=spawn_failure,
        ),
    )
    result = evaluate_multi_validator_case(
        ADVERSARIAL_CORPUS[0],
        _admission(),
        (
            first,
            _pair(
                "validator-b",
                SemanticClaim.NO_CLAIM,
                SemanticClaim.NO_CLAIM,
            ),
        ),
    )

    assert result.evaluations[0].source_run is timeout
    assert result.evaluations[0].transformed_run is spawn_failure
    assert result.evaluations[0].classification is OracleClassification.INDETERMINATE


def test_aggregate_rejects_manual_classification_mismatch() -> None:
    result = evaluate_multi_validator_case(
        ADVERSARIAL_CORPUS[0],
        _admission(),
        _pairs(),
    )
    inconsistent = replace(
        result.evaluations[0],
        classification=OracleClassification.COMPATIBLE,
    )

    with pytest.raises(EvaluationModelError, match="generic oracle result"):
        replace(
            result,
            evaluations=(
                inconsistent,
                result.evaluations[1],
            ),
        )


def test_aggregate_has_no_consensus_or_majority_field() -> None:
    names = {field.name for field in fields(MultiValidatorEvaluation)}
    assert names.isdisjoint({"majority", "consensus", "truth", "preferred_validator"})


def test_evaluation_models_are_immutable() -> None:
    value = _identity("validator-a")
    with pytest.raises(FrozenInstanceError):
        value.version = "2.0"  # type: ignore[misc]


def test_artifact_digest_requires_sha256_digest() -> None:
    with pytest.raises(EvaluationModelError, match="Sha256Digest"):
        ArtifactDigest(
            path="source.yml",
            sha256=cast(Sha256Digest, "0" * 64),
        )
