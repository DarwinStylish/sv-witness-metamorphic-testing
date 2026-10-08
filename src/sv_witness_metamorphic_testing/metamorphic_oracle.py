"""Relation-aware classification of normalized semantic claims."""

from enum import StrEnum

from .semantic_relation import BaseRelation


class OracleModelError(ValueError):
    """Raised when generic oracle inputs violate the runtime model."""


class SemanticClaim(StrEnum):
    """Semantic claim strength supplied by a justified normalizer."""

    NONEMPTY = "nonempty"
    EMPTY = "empty"
    NO_CLAIM = "no_claim"


class OracleClassification(StrEnum):
    """Consistency classification relative to an established semantic relation."""

    COMPATIBLE = "compatible"
    CONTRADICTION = "contradiction"
    INDETERMINATE = "indeterminate"


def _validate_inputs(
    relation: BaseRelation,
    source_claim: SemanticClaim,
    transformed_claim: SemanticClaim,
) -> None:
    if not isinstance(relation, BaseRelation):
        raise OracleModelError("relation must be a BaseRelation")

    if not isinstance(source_claim, SemanticClaim):
        raise OracleModelError("source_claim must be a SemanticClaim")

    if not isinstance(
        transformed_claim,
        SemanticClaim,
    ):
        raise OracleModelError("transformed_claim must be a SemanticClaim")


def classify_claim_pair(
    relation: BaseRelation,
    source_claim: SemanticClaim,
    transformed_claim: SemanticClaim,
) -> OracleClassification:
    """Classify two semantic claims under an established base relation.

    The caller is responsible for candidate admission, transformation-local
    evidence, and validator-specific normalization.

    COMPATIBLE means that the two claims can both be sound under the relation.
    It does not establish that either claim is true.

    CONTRADICTION means that the two claims cannot both be sound if the
    established relation and its premises are sound. It does not identify
    which component is wrong.

    INDETERMINATE means that the relation and current claim information are
    insufficient to classify the pair as compatible or contradictory. It is
    not an operational validator result.
    """
    _validate_inputs(
        relation,
        source_claim,
        transformed_claim,
    )

    if source_claim is SemanticClaim.NO_CLAIM or transformed_claim is SemanticClaim.NO_CLAIM:
        return OracleClassification.INDETERMINATE

    if relation is BaseRelation.EXACT:
        if source_claim is transformed_claim:
            return OracleClassification.COMPATIBLE

        return OracleClassification.CONTRADICTION

    if source_claim is SemanticClaim.NONEMPTY and transformed_claim is SemanticClaim.EMPTY:
        return OracleClassification.CONTRADICTION

    return OracleClassification.COMPATIBLE
