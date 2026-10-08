from enum import StrEnum
from typing import cast

import pytest

from sv_witness_metamorphic_testing.metamorphic_oracle import (
    OracleClassification,
    OracleModelError,
    SemanticClaim,
    classify_claim_pair,
)
from sv_witness_metamorphic_testing.semantic_relation import (
    BaseRelation,
)


def test_semantic_claim_surface_is_closed() -> None:
    assert tuple(SemanticClaim) == (
        SemanticClaim.NONEMPTY,
        SemanticClaim.EMPTY,
        SemanticClaim.NO_CLAIM,
    )


def test_semantic_claim_values_are_stable() -> None:
    assert SemanticClaim.NONEMPTY.value == "nonempty"
    assert SemanticClaim.EMPTY.value == "empty"
    assert SemanticClaim.NO_CLAIM.value == "no_claim"


def test_oracle_classification_surface_is_closed() -> None:
    assert tuple(OracleClassification) == (
        OracleClassification.COMPATIBLE,
        OracleClassification.CONTRADICTION,
        OracleClassification.INDETERMINATE,
    )


def test_oracle_classification_values_are_stable() -> None:
    assert OracleClassification.COMPATIBLE.value == "compatible"
    assert OracleClassification.CONTRADICTION.value == "contradiction"
    assert OracleClassification.INDETERMINATE.value == "indeterminate"


@pytest.mark.parametrize(
    (
        "source_claim",
        "transformed_claim",
        "expected",
    ),
    [
        (
            SemanticClaim.NONEMPTY,
            SemanticClaim.NONEMPTY,
            OracleClassification.COMPATIBLE,
        ),
        (
            SemanticClaim.NONEMPTY,
            SemanticClaim.EMPTY,
            OracleClassification.CONTRADICTION,
        ),
        (
            SemanticClaim.NONEMPTY,
            SemanticClaim.NO_CLAIM,
            OracleClassification.INDETERMINATE,
        ),
        (
            SemanticClaim.EMPTY,
            SemanticClaim.NONEMPTY,
            OracleClassification.CONTRADICTION,
        ),
        (
            SemanticClaim.EMPTY,
            SemanticClaim.EMPTY,
            OracleClassification.COMPATIBLE,
        ),
        (
            SemanticClaim.EMPTY,
            SemanticClaim.NO_CLAIM,
            OracleClassification.INDETERMINATE,
        ),
        (
            SemanticClaim.NO_CLAIM,
            SemanticClaim.NONEMPTY,
            OracleClassification.INDETERMINATE,
        ),
        (
            SemanticClaim.NO_CLAIM,
            SemanticClaim.EMPTY,
            OracleClassification.INDETERMINATE,
        ),
        (
            SemanticClaim.NO_CLAIM,
            SemanticClaim.NO_CLAIM,
            OracleClassification.INDETERMINATE,
        ),
    ],
)
def test_exact_claim_pair_classification(
    source_claim: SemanticClaim,
    transformed_claim: SemanticClaim,
    expected: OracleClassification,
) -> None:
    assert (
        classify_claim_pair(
            BaseRelation.EXACT,
            source_claim,
            transformed_claim,
        )
        is expected
    )


@pytest.mark.parametrize(
    (
        "source_claim",
        "transformed_claim",
        "expected",
    ),
    [
        (
            SemanticClaim.NONEMPTY,
            SemanticClaim.NONEMPTY,
            OracleClassification.COMPATIBLE,
        ),
        (
            SemanticClaim.NONEMPTY,
            SemanticClaim.EMPTY,
            OracleClassification.CONTRADICTION,
        ),
        (
            SemanticClaim.NONEMPTY,
            SemanticClaim.NO_CLAIM,
            OracleClassification.INDETERMINATE,
        ),
        (
            SemanticClaim.EMPTY,
            SemanticClaim.NONEMPTY,
            OracleClassification.COMPATIBLE,
        ),
        (
            SemanticClaim.EMPTY,
            SemanticClaim.EMPTY,
            OracleClassification.COMPATIBLE,
        ),
        (
            SemanticClaim.EMPTY,
            SemanticClaim.NO_CLAIM,
            OracleClassification.INDETERMINATE,
        ),
        (
            SemanticClaim.NO_CLAIM,
            SemanticClaim.NONEMPTY,
            OracleClassification.INDETERMINATE,
        ),
        (
            SemanticClaim.NO_CLAIM,
            SemanticClaim.EMPTY,
            OracleClassification.INDETERMINATE,
        ),
        (
            SemanticClaim.NO_CLAIM,
            SemanticClaim.NO_CLAIM,
            OracleClassification.INDETERMINATE,
        ),
    ],
)
def test_broadening_claim_pair_classification(
    source_claim: SemanticClaim,
    transformed_claim: SemanticClaim,
    expected: OracleClassification,
) -> None:
    assert (
        classify_claim_pair(
            BaseRelation.BROADENING,
            source_claim,
            transformed_claim,
        )
        is expected
    )


class UnrelatedRelation(StrEnum):
    EXACT = "exact"


class UnrelatedClaim(StrEnum):
    NONEMPTY = "nonempty"


@pytest.mark.parametrize(
    "relation",
    [
        cast(BaseRelation, "exact"),
        cast(
            BaseRelation,
            UnrelatedRelation.EXACT,
        ),
        cast(BaseRelation, None),
    ],
)
def test_classifier_rejects_invalid_relation_runtime_type(
    relation: BaseRelation,
) -> None:
    with pytest.raises(
        OracleModelError,
        match="relation must be a BaseRelation",
    ):
        classify_claim_pair(
            relation,
            SemanticClaim.NONEMPTY,
            SemanticClaim.NONEMPTY,
        )


@pytest.mark.parametrize(
    "source_claim",
    [
        cast(SemanticClaim, "nonempty"),
        cast(
            SemanticClaim,
            UnrelatedClaim.NONEMPTY,
        ),
        cast(SemanticClaim, None),
    ],
)
def test_classifier_rejects_invalid_source_claim_runtime_type(
    source_claim: SemanticClaim,
) -> None:
    with pytest.raises(
        OracleModelError,
        match="source_claim must be a SemanticClaim",
    ):
        classify_claim_pair(
            BaseRelation.EXACT,
            source_claim,
            SemanticClaim.NONEMPTY,
        )


@pytest.mark.parametrize(
    "transformed_claim",
    [
        cast(SemanticClaim, "empty"),
        cast(
            SemanticClaim,
            UnrelatedClaim.NONEMPTY,
        ),
        cast(SemanticClaim, None),
    ],
)
def test_classifier_rejects_invalid_transformed_claim_runtime_type(
    transformed_claim: SemanticClaim,
) -> None:
    with pytest.raises(
        OracleModelError,
        match="transformed_claim must be a SemanticClaim",
    ):
        classify_claim_pair(
            BaseRelation.EXACT,
            SemanticClaim.NONEMPTY,
            transformed_claim,
        )
