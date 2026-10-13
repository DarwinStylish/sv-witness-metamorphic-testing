from dataclasses import (
    FrozenInstanceError,
    replace,
)
from hashlib import sha256
from typing import cast

import pytest

from sv_witness_metamorphic_testing.adversarial_corpus import (
    ADVERSARIAL_CORPUS,
    CorpusCase,
    CorpusModelError,
    CorpusProgramFile,
    MaterializedArtifact,
    MaterializedCorpusCase,
    materialize_case,
)
from sv_witness_metamorphic_testing.case_reduction import (
    single_step_reductions,
)
from sv_witness_metamorphic_testing.exact_transformations import (
    explicit_main_thread,
    implicit_main_thread,
)
from sv_witness_metamorphic_testing.monotone_transformations import (
    remove_avoid_assumption,
)
from sv_witness_metamorphic_testing.semantic_relation import (
    BaseRelation,
)
from sv_witness_metamorphic_testing.task_model import (
    ExecutionAssumption,
    ExecutionContext,
    Program,
    ProgramInput,
    VerificationTask,
)
from sv_witness_metamorphic_testing.transformation_evidence import (
    AvoidRemovalApplication,
    ExplicitMainThreadApplication,
    ImplicitMainThreadApplication,
    TransformationLocalEvidence,
)
from sv_witness_metamorphic_testing.witness_model import (
    AssumptionWaypoint,
    NormalSegment,
    ViolationSequence,
)

_INITIAL_CORPUS_SIZE = 8
_MAIN_THREAD_WAYPOINT_COUNT = 2
_REDUCTION_CANDIDATE_COUNT = 2


def case_by_id(
    case_id: str,
) -> CorpusCase:
    return next(case for case in ADVERSARIAL_CORPUS if case.case_id == case_id)


def artifacts_by_path(
    case: CorpusCase,
) -> dict[str, bytes]:
    materialized = materialize_case(case)

    return {artifact.path: artifact.content for artifact in materialized.artifacts}


def test_initial_corpus_contains_eight_cases() -> None:
    assert len(ADVERSARIAL_CORPUS) == _INITIAL_CORPUS_SIZE


def test_corpus_ids_are_unique_and_sorted() -> None:
    case_ids = tuple(case.case_id for case in ADVERSARIAL_CORPUS)

    assert len(set(case_ids)) == len(case_ids)
    assert case_ids == tuple(sorted(case_ids))


def test_corpus_witness_uuids_are_globally_unique() -> None:
    values = tuple(
        uuid
        for case in ADVERSARIAL_CORPUS
        for uuid in (
            case.source_metadata.uuid,
            case.transformed_metadata.uuid,
        )
    )

    assert len(set(values)) == len(values)


def test_corpus_covers_exact_and_broadening_relations() -> None:
    assert {case.relation.base_relation for case in ADVERSARIAL_CORPUS} == {
        BaseRelation.EXACT,
        BaseRelation.BROADENING,
    }


def test_frozen_stress_dimension_vocabulary_is_covered() -> None:
    dimensions = {dimension for case in ADVERSARIAL_CORPUS for dimension in case.dimensions}

    assert {
        "explicit-main-thread-canonicalization",
        "implicit-main-thread-canonicalization",
        "exact-relation",
        "broadening-relation",
        "normal-segment-avoid-removal",
        "final-segment-avoid-removal",
        "adjacent-avoid-assumptions",
        "repeated-equal-avoid-assumptions",
        "distinguished-avoid-early",
        "distinguished-avoid-interior",
        "distinguished-avoid-late",
        "reducible-non-distinguished-avoids",
        "locally-irreducible",
    } <= dimensions


def test_every_transformed_witness_is_reconstructed_by_its_operator() -> None:
    for case in ADVERSARIAL_CORPUS:
        application = case.relation.application
        source = case.relation.source

        if isinstance(
            application,
            ExplicitMainThreadApplication,
        ):
            expected = explicit_main_thread(source)
        elif isinstance(
            application,
            ImplicitMainThreadApplication,
        ):
            expected = implicit_main_thread(source)
        else:
            expected = remove_avoid_assumption(
                source,
                application.segment_index,
                application.waypoint_index,
            )

        assert case.relation.transformed == expected


def test_program_artifacts_match_task_paths_and_hashes() -> None:
    for case in ADVERSARIAL_CORPUS:
        assert tuple(program_file.path for program_file in case.program_files) == tuple(
            program_input.path for program_input in case.relation.task.program.inputs
        )

        for (
            program_file,
            program_input,
        ) in zip(
            case.program_files,
            case.relation.task.program.inputs,
            strict=True,
        ):
            assert sha256(program_file.content).hexdigest() == program_input.sha256.value


def test_shared_program_has_frozen_digest() -> None:
    expected = "0671d84e1fe87c46c6c79b7d10e8a3fa4547f93b02b34e7b1ad59c2cb74805ed"

    for case in ADVERSARIAL_CORPUS:
        assert case.relation.task.program.inputs[0].sha256.value == expected


def test_all_locations_identify_task_inputs() -> None:
    for case in ADVERSARIAL_CORPUS:
        task_paths = {program_input.path for program_input in case.relation.task.program.inputs}

        for witness in (
            case.relation.source,
            case.relation.transformed,
        ):
            for segment in witness.segments:
                for waypoint in segment.waypoints:
                    assert waypoint.location.file_name in task_paths


def test_location_columns_point_to_non_whitespace_program_text() -> None:
    for case in ADVERSARIAL_CORPUS:
        lines = case.program_files[0].content.decode("utf-8").splitlines()

        for witness in (
            case.relation.source,
            case.relation.transformed,
        ):
            for segment in witness.segments:
                for waypoint in segment.waypoints:
                    location = waypoint.location

                    assert location.column is not None

                    line = lines[location.line - 1]

                    character = line[location.column - 1]

                    assert not character.isspace()


def test_materialization_is_byte_deterministic() -> None:
    for case in ADVERSARIAL_CORPUS:
        assert materialize_case(case) == materialize_case(case)


def test_materialized_artifact_order_is_fixed() -> None:
    for case in ADVERSARIAL_CORPUS:
        materialized = materialize_case(case)

        assert tuple(artifact.path for artifact in materialized.artifacts) == (
            "example.c",
            "property.prp",
            "source.yml",
            "transformed.yml",
        )


def test_property_artifact_is_task_specification_plus_newline() -> None:
    for case in ADVERSARIAL_CORPUS:
        artifacts = artifacts_by_path(case)

        assert artifacts["property.prp"] == (case.relation.task.specification.text + "\n").encode(
            "utf-8"
        )


def test_witness_artifacts_have_one_trailing_newline() -> None:
    for case in ADVERSARIAL_CORPUS:
        artifacts = artifacts_by_path(case)

        for path in (
            "source.yml",
            "transformed.yml",
        ):
            content = artifacts[path]

            assert content.endswith(b"\n")

            assert not content.endswith(b"\n\n")


def test_witness_artifacts_have_supported_top_level_shape() -> None:
    for case in ADVERSARIAL_CORPUS:
        artifacts = artifacts_by_path(case)

        for path in (
            "source.yml",
            "transformed.yml",
        ):
            text = artifacts[path].decode("utf-8")

            assert text.startswith('- entry_type: "violation_sequence"\n')

            assert text.count('- entry_type: "violation_sequence"') == 1

            assert '    format_version: "2.2"' in text

            assert "  metadata:\n" in text

            assert "    task:\n" in text

            assert "  content:\n" in text


def test_witness_artifacts_bind_exact_task_metadata() -> None:
    for case in ADVERSARIAL_CORPUS:
        artifacts = artifacts_by_path(case)

        source_text = artifacts["source.yml"].decode("utf-8")

        task = case.relation.task

        for program_input in task.program.inputs:
            assert f'"{program_input.path}"' in source_text

            assert program_input.sha256.value in source_text

        assert task.specification.text in source_text

        assert f'"{task.execution_context.data_model.value}"' in source_text

        assert f'"{task.execution_context.language.value}"' in source_text


def test_assumption_emission_has_c_expression_format() -> None:
    case = case_by_id("broadening-normal-interior-avoid")

    text = artifacts_by_path(case)["source.yml"].decode("utf-8")

    assert '            type: "assumption"' in text

    assert '              format: "c_expression"' in text


def test_target_emission_has_no_constraint() -> None:
    case = case_by_id("exact-explicit-main-thread")

    text = artifacts_by_path(case)["source.yml"].decode("utf-8")

    target_tail = text.split(
        '            type: "target"',
        maxsplit=1,
    )[1]

    assert target_tail.startswith('\n            action: "follow"')

    assert "constraint:" not in target_tail


def test_explicit_main_thread_materialization_preserves_absence_then_zero() -> None:
    case = case_by_id("exact-explicit-main-thread")

    artifacts = artifacts_by_path(case)

    source = artifacts["source.yml"].decode("utf-8")

    transformed = artifacts["transformed.yml"].decode("utf-8")

    assert "thread_id:" not in source

    assert transformed.count("thread_id: 0") == _MAIN_THREAD_WAYPOINT_COUNT


def test_implicit_main_thread_materialization_preserves_zero_then_absence() -> None:
    case = case_by_id("exact-implicit-main-thread")

    artifacts = artifacts_by_path(case)

    source = artifacts["source.yml"].decode("utf-8")

    transformed = artifacts["transformed.yml"].decode("utf-8")

    assert source.count("thread_id: 0") == _MAIN_THREAD_WAYPOINT_COUNT

    assert "thread_id:" not in transformed


def test_source_and_transformed_artifacts_are_distinct() -> None:
    for case in ADVERSARIAL_CORPUS:
        artifacts = artifacts_by_path(case)

        assert artifacts["source.yml"] != artifacts["transformed.yml"]


def test_source_and_transformed_metadata_uuids_are_distinct_in_bytes() -> None:
    for case in ADVERSARIAL_CORPUS:
        artifacts = artifacts_by_path(case)

        source = artifacts["source.yml"].decode("utf-8")

        transformed = artifacts["transformed.yml"].decode("utf-8")

        assert case.source_metadata.uuid in source

        assert case.transformed_metadata.uuid in transformed

        assert case.transformed_metadata.uuid not in source

        assert case.source_metadata.uuid not in transformed


def test_repeated_equal_avoids_suppress_duplicate_reductions() -> None:
    case = case_by_id("exact-repeated-equal-avoids")

    candidates = single_step_reductions(case.relation)

    assert len(candidates) == 1


def test_exact_reducible_case_has_two_reduction_candidates() -> None:
    case = case_by_id("exact-reducible-avoids")

    assert len(single_step_reductions(case.relation)) == _REDUCTION_CANDIDATE_COUNT


@pytest.mark.parametrize(
    "case_id",
    [
        "broadening-normal-single-avoid",
        "exact-irreducible-main-thread",
    ],
)
def test_locally_irreducible_cases_have_no_reduction_candidates(
    case_id: str,
) -> None:
    case = case_by_id(case_id)

    assert single_step_reductions(case.relation) == ()


def test_broadening_interior_case_retains_two_non_distinguished_candidates() -> None:
    case = case_by_id("broadening-normal-interior-avoid")

    assert len(single_step_reductions(case.relation)) == _REDUCTION_CANDIDATE_COUNT


def test_broadening_final_late_case_retains_earlier_candidate() -> None:
    case = case_by_id("broadening-final-late-avoid")

    candidates = single_step_reductions(case.relation)

    assert len(candidates) == 1

    application = candidates[0].application

    assert isinstance(
        application,
        AvoidRemovalApplication,
    )

    assert application.segment_index == 1
    assert application.waypoint_index == 0


def test_case_id_rejects_non_slug() -> None:
    base = ADVERSARIAL_CORPUS[0]

    with pytest.raises(
        CorpusModelError,
        match="lowercase ASCII slug",
    ):
        replace(
            base,
            case_id="Not Valid",
        )


def test_case_rejects_empty_description() -> None:
    base = ADVERSARIAL_CORPUS[0]

    with pytest.raises(
        CorpusModelError,
        match="description",
    ):
        replace(
            base,
            description="",
        )


def test_case_rejects_non_tuple_dimensions() -> None:
    base = ADVERSARIAL_CORPUS[0]

    with pytest.raises(
        CorpusModelError,
        match="dimensions",
    ):
        replace(
            base,
            dimensions=cast(
                tuple[str, ...],
                ["exact-relation"],
            ),
        )


def test_case_rejects_duplicate_dimensions() -> None:
    base = ADVERSARIAL_CORPUS[0]

    with pytest.raises(
        CorpusModelError,
        match="unique",
    ):
        replace(
            base,
            dimensions=(
                "exact-relation",
                "exact-relation",
            ),
        )


def test_case_rejects_program_hash_mismatch() -> None:
    base = ADVERSARIAL_CORPUS[0]

    wrong = replace(
        base.program_files[0],
        content=b"different\n",
    )

    with pytest.raises(
        CorpusModelError,
        match="hash",
    ):
        replace(
            base,
            program_files=(wrong,),
        )


def test_case_rejects_program_path_mismatch() -> None:
    base = ADVERSARIAL_CORPUS[0]

    wrong = CorpusProgramFile(
        path="other.c",
        content=base.program_files[0].content,
    )

    with pytest.raises(
        CorpusModelError,
        match="exactly match",
    ):
        replace(
            base,
            program_files=(wrong,),
        )


def test_case_rejects_equal_witness_uuids() -> None:
    base = ADVERSARIAL_CORPUS[0]

    with pytest.raises(
        CorpusModelError,
        match="UUIDs must differ",
    ):
        replace(
            base,
            transformed_metadata=(base.source_metadata),
        )


def test_case_rejects_unmaterialized_execution_assumptions() -> None:
    base = case_by_id("exact-explicit-main-thread")

    old_task = base.relation.task

    context = ExecutionContext(
        language=(old_task.execution_context.language),
        data_model=(old_task.execution_context.data_model),
        additional_assumptions=(
            ExecutionAssumption(
                name="example",
                value="retained-only-in-task-model",
            ),
        ),
    )

    task = VerificationTask(
        program=old_task.program,
        specification=old_task.specification,
        execution_context=context,
    )

    relation = TransformationLocalEvidence(
        task=task,
        source=base.relation.source,
        transformed=(base.relation.transformed),
        application=(base.relation.application),
    )

    with pytest.raises(
        CorpusModelError,
        match="additional execution assumptions",
    ):
        replace(
            base,
            relation=relation,
        )


def test_case_rejects_location_outside_task_input_set() -> None:
    base = case_by_id("exact-explicit-main-thread")

    source = base.relation.source
    normal = source.normal_segments[0]
    follow = normal.waypoints[-1]

    bad_follow = replace(
        follow,
        location=replace(
            follow.location,
            file_name="other.c",
        ),
    )

    bad_normal = NormalSegment(
        waypoints=(
            *normal.waypoints[:-1],
            bad_follow,
        )
    )

    bad_source = ViolationSequence(
        segments=(
            bad_normal,
            source.final_segment,
        )
    )

    bad_relation = TransformationLocalEvidence(
        task=base.relation.task,
        source=bad_source,
        transformed=(explicit_main_thread(bad_source)),
        application=(ExplicitMainThreadApplication()),
    )

    with pytest.raises(
        CorpusModelError,
        match="task input",
    ):
        replace(
            base,
            relation=bad_relation,
        )


def test_metadata_rejects_wrong_format_version() -> None:
    base = ADVERSARIAL_CORPUS[0].source_metadata

    with pytest.raises(
        CorpusModelError,
        match="format_version",
    ):
        replace(
            base,
            format_version="2.1",
        )


def test_metadata_rejects_invalid_uuid() -> None:
    base = ADVERSARIAL_CORPUS[0].source_metadata

    with pytest.raises(
        CorpusModelError,
        match="valid UUID",
    ):
        replace(
            base,
            uuid="not-a-uuid",
        )


def test_metadata_rejects_noncanonical_uuid() -> None:
    base = ADVERSARIAL_CORPUS[0].source_metadata

    with pytest.raises(
        CorpusModelError,
        match="canonical lowercase",
    ):
        replace(
            base,
            uuid="AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA",
        )


def test_metadata_rejects_non_utc_second_creation_time() -> None:
    base = ADVERSARIAL_CORPUS[0].source_metadata

    with pytest.raises(
        CorpusModelError,
        match="UTC",
    ):
        replace(
            base,
            creation_time=("2026-10-13T00:00:00+00:00"),
        )


@pytest.mark.parametrize(
    "path",
    [
        "/absolute.c",
        "../escape.c",
        "nested/../escape.c",
        r"windows\path.c",
    ],
)
def test_program_file_rejects_unsafe_relative_paths(
    path: str,
) -> None:
    with pytest.raises(
        CorpusModelError,
        match=r"relative|parent|POSIX",
    ):
        CorpusProgramFile(
            path=path,
            content=b"",
        )


def test_program_file_rejects_non_bytes() -> None:
    with pytest.raises(
        CorpusModelError,
        match="bytes",
    ):
        CorpusProgramFile(
            path="example.c",
            content=cast(
                bytes,
                "not-bytes",
            ),
        )


def test_materialize_case_rejects_wrong_runtime_type() -> None:
    with pytest.raises(
        CorpusModelError,
        match="CorpusCase",
    ):
        materialize_case(
            cast(
                CorpusCase,
                object(),
            )
        )


def test_materialized_values_are_immutable() -> None:
    materialized = materialize_case(ADVERSARIAL_CORPUS[0])

    with pytest.raises(
        FrozenInstanceError,
    ):
        materialized.case_id = "changed"  # type: ignore[misc]


def test_materialized_case_rejects_duplicate_paths() -> None:
    artifact = MaterializedArtifact(
        path="a",
        content=b"a",
    )

    with pytest.raises(
        CorpusModelError,
        match="unique",
    ):
        MaterializedCorpusCase(
            case_id="duplicate-paths",
            artifacts=(
                artifact,
                artifact,
            ),
        )


def test_materialized_witnesses_quote_metadata_and_expressions() -> None:
    case = case_by_id("exact-repeated-equal-avoids")

    source = artifacts_by_path(case)["source.yml"].decode("utf-8")

    assert 'value: "x == 99"' in source

    assert 'producer:\n      name: "sv-witness-metamorphic-testing"' in source


def test_relation_case_remains_directly_reducer_compatible() -> None:
    for case in ADVERSARIAL_CORPUS:
        candidates = single_step_reductions(case.relation)

        assert isinstance(
            candidates,
            tuple,
        )


def test_corpus_model_objects_are_immutable() -> None:
    case = ADVERSARIAL_CORPUS[0]

    with pytest.raises(
        FrozenInstanceError,
    ):
        case.case_id = "changed"  # type: ignore[misc]


def test_program_task_objects_are_not_redefined_by_corpus() -> None:
    for case in ADVERSARIAL_CORPUS:
        assert isinstance(
            case.relation.task.program,
            Program,
        )

        assert all(
            isinstance(
                program_input,
                ProgramInput,
            )
            for program_input in case.relation.task.program.inputs
        )


def test_relation_source_contains_only_supported_waypoint_models() -> None:
    for case in ADVERSARIAL_CORPUS:
        for segment in case.relation.source.segments:
            for waypoint in segment.waypoints:
                assert hasattr(
                    waypoint,
                    "location",
                )

                if isinstance(
                    waypoint,
                    AssumptionWaypoint,
                ):
                    assert waypoint.constraint.value
