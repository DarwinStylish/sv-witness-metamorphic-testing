from sv_witness_metamorphic_testing.semantic_relation import (
    BaseRelation,
)


def test_base_relation_surface_is_closed() -> None:
    assert tuple(BaseRelation) == (
        BaseRelation.EXACT,
        BaseRelation.BROADENING,
    )


def test_base_relation_values_are_stable() -> None:
    assert BaseRelation.EXACT.value == "exact"
    assert BaseRelation.BROADENING.value == "broadening"
