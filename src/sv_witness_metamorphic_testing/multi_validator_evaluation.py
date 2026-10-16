"""Validator-neutral multi-validator evaluation records."""

from dataclasses import dataclass
from hashlib import sha256 as compute_sha256

from .adversarial_corpus import CorpusCase, materialize_case
from .metamorphic_oracle import (
    OracleClassification,
    SemanticClaim,
    classify_claim_pair,
)
from .semantic_relation import BaseRelation
from .task_model import Sha256Digest
from .validator_runner import ValidatorRun

_MINIMUM_IMPLEMENTATIONS = 2
_REQUIRED_ARTIFACT_PATHS = frozenset({"property.prp", "source.yml", "transformed.yml"})


class EvaluationModelError(ValueError):
    """Raised when an evaluation value violates its local contract."""


def _text(value: str, *, name: str) -> None:
    if type(value) is not str or not value:
        raise EvaluationModelError(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidatorIdentity:
    """Validator implementation and version recorded by an experiment."""

    implementation: str
    version: str

    def __post_init__(self) -> None:
        _text(self.implementation, name="validator implementation")
        _text(self.version, name="validator version")


@dataclass(frozen=True, slots=True, kw_only=True)
class AdapterIdentity:
    """Identity and justification reference for one normalization adapter."""

    name: str
    version: str
    normalization_contract: str

    def __post_init__(self) -> None:
        _text(self.name, name="adapter name")
        _text(self.version, name="adapter version")
        _text(self.normalization_contract, name="normalization contract")


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactDigest:
    """SHA-256 identity of one materialized corpus artifact."""

    path: str
    sha256: Sha256Digest

    def __post_init__(self) -> None:
        _text(self.path, name="artifact path")
        if not isinstance(self.sha256, Sha256Digest):
            raise EvaluationModelError("artifact sha256 must be a Sha256Digest")


@dataclass(frozen=True, slots=True, kw_only=True)
class CandidateAdmissionEvidence:
    """Recorded external basis for source candidate-domain admission."""

    case_id: str
    source_sha256: Sha256Digest
    basis: str

    def __post_init__(self) -> None:
        _text(self.case_id, name="admission case_id")
        _text(self.basis, name="admission basis")
        if not isinstance(self.source_sha256, Sha256Digest):
            raise EvaluationModelError("admission source_sha256 must be a Sha256Digest")


@dataclass(frozen=True, slots=True, kw_only=True)
class NormalizedValidatorRun:
    """Raw validator run paired with one justified semantic claim."""

    validator: ValidatorIdentity
    adapter: AdapterIdentity
    run: ValidatorRun
    claim: SemanticClaim

    def __post_init__(self) -> None:
        if not isinstance(self.validator, ValidatorIdentity):
            raise EvaluationModelError("validator must be a ValidatorIdentity")
        if not isinstance(self.adapter, AdapterIdentity):
            raise EvaluationModelError("adapter must be an AdapterIdentity")
        if not isinstance(self.run, ValidatorRun):
            raise EvaluationModelError("run must be a ValidatorRun")
        if not isinstance(self.claim, SemanticClaim):
            raise EvaluationModelError("claim must be a SemanticClaim")


@dataclass(frozen=True, slots=True, kw_only=True)
class NormalizedValidatorPair:
    """Source and transformed observations from one validator and adapter."""

    source: NormalizedValidatorRun
    transformed: NormalizedValidatorRun

    def __post_init__(self) -> None:
        if not isinstance(self.source, NormalizedValidatorRun):
            raise EvaluationModelError("source must be a NormalizedValidatorRun")
        if not isinstance(self.transformed, NormalizedValidatorRun):
            raise EvaluationModelError("transformed must be a NormalizedValidatorRun")
        if self.source.validator != self.transformed.validator:
            raise EvaluationModelError(
                "source and transformed runs must use the same validator identity"
            )
        if self.source.adapter != self.transformed.adapter:
            raise EvaluationModelError(
                "source and transformed runs must use the same adapter identity"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidatorPairEvaluation:
    """Stored result for one validator under one established relation."""

    validator: ValidatorIdentity
    adapter: AdapterIdentity
    relation: BaseRelation
    source_run: ValidatorRun
    transformed_run: ValidatorRun
    source_claim: SemanticClaim
    transformed_claim: SemanticClaim
    classification: OracleClassification

    def __post_init__(self) -> None:
        if not isinstance(self.validator, ValidatorIdentity):
            raise EvaluationModelError("validator must be a ValidatorIdentity")
        if not isinstance(self.adapter, AdapterIdentity):
            raise EvaluationModelError("adapter must be an AdapterIdentity")
        if not isinstance(self.relation, BaseRelation):
            raise EvaluationModelError("relation must be a BaseRelation")
        if not isinstance(self.source_run, ValidatorRun) or not isinstance(
            self.transformed_run, ValidatorRun
        ):
            raise EvaluationModelError("pair runs must be ValidatorRun values")
        if not isinstance(self.source_claim, SemanticClaim) or not isinstance(
            self.transformed_claim, SemanticClaim
        ):
            raise EvaluationModelError("pair claims must be SemanticClaim values")
        if not isinstance(self.classification, OracleClassification):
            raise EvaluationModelError("classification must be an OracleClassification")


@dataclass(frozen=True, slots=True, kw_only=True)
class MultiValidatorEvaluation:
    """Complete relation-aware record for one case across validators."""

    case_id: str
    relation: BaseRelation
    artifact_digests: tuple[ArtifactDigest, ...]
    admission_evidence: CandidateAdmissionEvidence
    evaluations: tuple[ValidatorPairEvaluation, ...]

    def __post_init__(self) -> None:
        _text(self.case_id, name="case_id")
        if not isinstance(self.relation, BaseRelation):
            raise EvaluationModelError("relation must be a BaseRelation")
        _validate_artifact_digests(self.artifact_digests)
        _validate_admission_binding(
            case_id=self.case_id,
            admission=self.admission_evidence,
            artifact_digests=self.artifact_digests,
        )
        _validate_evaluations(self.evaluations, relation=self.relation)


def _validate_artifact_digests(artifact_digests: tuple[ArtifactDigest, ...]) -> None:
    if not isinstance(artifact_digests, tuple) or not artifact_digests:
        raise EvaluationModelError("artifact_digests must be a non-empty tuple")
    if any(not isinstance(digest, ArtifactDigest) for digest in artifact_digests):
        raise EvaluationModelError("artifact_digests must contain only ArtifactDigest values")

    paths = tuple(digest.path for digest in artifact_digests)
    if len(set(paths)) != len(paths):
        raise EvaluationModelError("artifact digest paths must be unique")
    if _REQUIRED_ARTIFACT_PATHS.difference(paths):
        raise EvaluationModelError("artifact digests are missing required corpus artifacts")


def _source_digest(artifact_digests: tuple[ArtifactDigest, ...]) -> Sha256Digest:
    return next(digest.sha256 for digest in artifact_digests if digest.path == "source.yml")


def _validate_admission_binding(
    *,
    case_id: str,
    admission: CandidateAdmissionEvidence,
    artifact_digests: tuple[ArtifactDigest, ...],
) -> None:
    if not isinstance(admission, CandidateAdmissionEvidence):
        raise EvaluationModelError("admission_evidence must be CandidateAdmissionEvidence")
    if admission.case_id != case_id:
        raise EvaluationModelError("admission evidence must identify the evaluated case")
    if admission.source_sha256 != _source_digest(artifact_digests):
        raise EvaluationModelError(
            "admission evidence must identify the materialized source witness"
        )


def _implementation_names(
    evaluations: tuple[ValidatorPairEvaluation, ...],
) -> tuple[str, ...]:
    return tuple(evaluation.validator.implementation for evaluation in evaluations)


def _validate_evaluations(
    evaluations: tuple[ValidatorPairEvaluation, ...],
    *,
    relation: BaseRelation,
) -> None:
    if not isinstance(evaluations, tuple):
        raise EvaluationModelError("evaluations must be a tuple")
    if len(evaluations) < _MINIMUM_IMPLEMENTATIONS:
        raise EvaluationModelError(
            "multi-validator evaluation requires at least two validator implementations"
        )
    if any(not isinstance(item, ValidatorPairEvaluation) for item in evaluations):
        raise EvaluationModelError("evaluations must contain only ValidatorPairEvaluation values")

    implementations = _implementation_names(evaluations)
    if len(set(implementations)) != len(implementations):
        raise EvaluationModelError("validator implementations must be distinct")

    for evaluation in evaluations:
        if evaluation.relation is not relation:
            raise EvaluationModelError("every validator evaluation must use the aggregate relation")
        expected = classify_claim_pair(
            relation,
            evaluation.source_claim,
            evaluation.transformed_claim,
        )
        if evaluation.classification is not expected:
            raise EvaluationModelError("classification must equal the generic oracle result")


def _artifact_digests(case: CorpusCase) -> tuple[ArtifactDigest, ...]:
    return tuple(
        ArtifactDigest(
            path=artifact.path,
            sha256=Sha256Digest(value=compute_sha256(artifact.content).hexdigest()),
        )
        for artifact in materialize_case(case).artifacts
    )


def _validate_pairs(pairs: tuple[NormalizedValidatorPair, ...]) -> None:
    if not isinstance(pairs, tuple):
        raise EvaluationModelError("pairs must be a tuple")
    if len(pairs) < _MINIMUM_IMPLEMENTATIONS:
        raise EvaluationModelError(
            "multi-validator evaluation requires at least two validator implementations"
        )
    if any(not isinstance(pair, NormalizedValidatorPair) for pair in pairs):
        raise EvaluationModelError("pairs must contain only NormalizedValidatorPair values")

    implementations = tuple(pair.source.validator.implementation for pair in pairs)
    if len(set(implementations)) != len(implementations):
        raise EvaluationModelError("validator implementations must be distinct")


def _evaluate_pair(
    relation: BaseRelation,
    pair: NormalizedValidatorPair,
) -> ValidatorPairEvaluation:
    source = pair.source
    transformed = pair.transformed
    return ValidatorPairEvaluation(
        validator=source.validator,
        adapter=source.adapter,
        relation=relation,
        source_run=source.run,
        transformed_run=transformed.run,
        source_claim=source.claim,
        transformed_claim=transformed.claim,
        classification=classify_claim_pair(
            relation,
            source.claim,
            transformed.claim,
        ),
    )


def evaluate_multi_validator_case(
    case: CorpusCase,
    admission_evidence: CandidateAdmissionEvidence,
    pairs: tuple[NormalizedValidatorPair, ...],
) -> MultiValidatorEvaluation:
    """Evaluate normalized pairs after checking source-admission binding."""

    if not isinstance(case, CorpusCase):
        raise EvaluationModelError("case must be a CorpusCase")

    artifact_digests = _artifact_digests(case)
    _validate_admission_binding(
        case_id=case.case_id,
        admission=admission_evidence,
        artifact_digests=artifact_digests,
    )
    _validate_pairs(pairs)

    evaluations = tuple(_evaluate_pair(case.relation.base_relation, pair) for pair in pairs)

    return MultiValidatorEvaluation(
        case_id=case.case_id,
        relation=case.relation.base_relation,
        artifact_digests=artifact_digests,
        admission_evidence=admission_evidence,
        evaluations=evaluations,
    )
