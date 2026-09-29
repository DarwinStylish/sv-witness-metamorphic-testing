from dataclasses import FrozenInstanceError

import pytest

from sv_witness_metamorphic_testing.task_model import (
    DataModel,
    ExecutionAssumption,
    ExecutionContext,
    Language,
    Program,
    ProgramInput,
    Sha256Digest,
    Specification,
    TaskModelError,
    VerificationTask,
)

DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def program_input(
    path: str = "./example.c",
    digest: str = DIGEST_A,
) -> ProgramInput:
    return ProgramInput(
        path=path,
        sha256=Sha256Digest(value=digest),
    )


def program() -> Program:
    return Program(inputs=(program_input(),))


def specification() -> Specification:
    return Specification(text="G ! call(reach_error())")


def execution_context() -> ExecutionContext:
    return ExecutionContext(
        language=Language.C,
        data_model=DataModel.ILP32,
    )


def task() -> VerificationTask:
    return VerificationTask(
        program=program(),
        specification=specification(),
        execution_context=execution_context(),
    )


def test_sha256_digest_preserves_digest_identity_canonically() -> None:
    digest = Sha256Digest(value="A" * 64)

    assert digest.value == "a" * 64


@pytest.mark.parametrize(
    "value",
    [
        "",
        "a" * 63,
        "a" * 65,
        "g" * 64,
        "not-a-digest",
    ],
)
def test_sha256_digest_rejects_invalid_text(value: str) -> None:
    with pytest.raises(TaskModelError, match="64 hexadecimal"):
        Sha256Digest(value=value)


def test_sha256_digest_rejects_non_string() -> None:
    with pytest.raises(TaskModelError, match="string"):
        Sha256Digest(value=7)  # type: ignore[arg-type]


def test_program_input_preserves_exact_path_spelling() -> None:
    value = program_input(path="./src/../src/example.c")

    assert value.path == "./src/../src/example.c"


def test_program_input_rejects_non_string_path() -> None:
    with pytest.raises(TaskModelError, match="path"):
        ProgramInput(
            path=7,  # type: ignore[arg-type]
            sha256=Sha256Digest(value=DIGEST_A),
        )


def test_program_input_rejects_raw_digest_string() -> None:
    with pytest.raises(TaskModelError, match="Sha256Digest"):
        ProgramInput(
            path="./example.c",
            sha256=DIGEST_A,  # type: ignore[arg-type]
        )


def test_program_preserves_input_order() -> None:
    first = program_input("./first.c", DIGEST_A)
    second = program_input("./second.c", DIGEST_B)

    value = Program(inputs=(first, second))

    assert value.inputs == (first, second)


def test_reordered_program_inputs_remain_distinguishable() -> None:
    first = program_input("./first.c", DIGEST_A)
    second = program_input("./second.c", DIGEST_B)

    left = Program(inputs=(first, second))
    right = Program(inputs=(second, first))

    assert left != right


def test_program_rejects_empty_input_sequence() -> None:
    with pytest.raises(TaskModelError, match="at least one"):
        Program(inputs=())


def test_program_rejects_non_tuple_inputs() -> None:
    with pytest.raises(TaskModelError, match="tuple"):
        Program(inputs=[program_input()])  # type: ignore[arg-type]


def test_program_rejects_non_program_input_element() -> None:
    with pytest.raises(TaskModelError, match="ProgramInput"):
        Program(
            inputs=("./example.c",),  # type: ignore[arg-type]
        )


def test_specification_retains_opaque_text() -> None:
    text = "CHECK( init(main()), LTL(G ! call(reach_error())) )"

    value = Specification(text=text)

    assert value.text == text


@pytest.mark.parametrize(
    "text",
    [
        "G ! call(reach_error())",
        "G ! overflow",
        "G ! data-race",
        "",
    ],
)
def test_specification_construction_does_not_perform_profile_admission(
    text: str,
) -> None:
    value = Specification(text=text)

    assert value.text == text


def test_specification_rejects_non_string() -> None:
    with pytest.raises(TaskModelError, match="string"):
        Specification(text=7)  # type: ignore[arg-type]


def test_language_profile_is_c() -> None:
    assert tuple(Language) == (Language.C,)
    assert Language.C.value == "C"


def test_data_models_match_task_schema() -> None:
    assert tuple(DataModel) == (
        DataModel.ILP32,
        DataModel.LP64,
    )


def test_execution_assumption_retains_opaque_pair() -> None:
    assumption = ExecutionAssumption(
        name="compiler-mode",
        value="example-mode",
    )

    assert assumption.name == "compiler-mode"
    assert assumption.value == "example-mode"


def test_execution_assumption_rejects_non_string_name() -> None:
    with pytest.raises(TaskModelError, match="name"):
        ExecutionAssumption(
            name=7,  # type: ignore[arg-type]
            value="example",
        )


def test_execution_assumption_rejects_non_string_value() -> None:
    with pytest.raises(TaskModelError, match="value"):
        ExecutionAssumption(
            name="example",
            value=7,  # type: ignore[arg-type]
        )


def test_execution_context_retains_additional_assumptions() -> None:
    assumption = ExecutionAssumption(
        name="example-assumption",
        value="example-value",
    )

    context = ExecutionContext(
        language=Language.C,
        data_model=DataModel.LP64,
        additional_assumptions=(assumption,),
    )

    assert context.additional_assumptions == (assumption,)


def test_execution_context_preserves_assumption_order() -> None:
    first = ExecutionAssumption(name="first", value="1")
    second = ExecutionAssumption(name="second", value="2")

    forward = ExecutionContext(
        language=Language.C,
        data_model=DataModel.ILP32,
        additional_assumptions=(first, second),
    )
    reversed_context = ExecutionContext(
        language=Language.C,
        data_model=DataModel.ILP32,
        additional_assumptions=(second, first),
    )

    assert forward.additional_assumptions == (first, second)
    assert reversed_context.additional_assumptions == (second, first)
    assert forward != reversed_context


def test_execution_context_preserves_duplicate_assumptions() -> None:
    assumption = ExecutionAssumption(name="mode", value="example")

    context = ExecutionContext(
        language=Language.C,
        data_model=DataModel.ILP32,
        additional_assumptions=(assumption, assumption),
    )

    assert context.additional_assumptions == (
        assumption,
        assumption,
    )


def test_execution_context_rejects_raw_language_string() -> None:
    with pytest.raises(TaskModelError, match="language"):
        ExecutionContext(
            language="C",  # type: ignore[arg-type]
            data_model=DataModel.ILP32,
        )


def test_execution_context_rejects_raw_data_model_string() -> None:
    with pytest.raises(TaskModelError, match="data_model"):
        ExecutionContext(
            language=Language.C,
            data_model="ILP32",  # type: ignore[arg-type]
        )


def test_execution_context_rejects_non_tuple_assumptions() -> None:
    with pytest.raises(TaskModelError, match="tuple"):
        ExecutionContext(
            language=Language.C,
            data_model=DataModel.ILP32,
            additional_assumptions=[],  # type: ignore[arg-type]
        )


def test_execution_context_rejects_invalid_assumption_element() -> None:
    with pytest.raises(TaskModelError, match="ExecutionAssumption"):
        ExecutionContext(
            language=Language.C,
            data_model=DataModel.ILP32,
            additional_assumptions=(
                "example",  # type: ignore[arg-type]
            ),
        )


def test_verification_task_preserves_tau_components() -> None:
    p = program()
    phi = specification()
    m = execution_context()

    value = VerificationTask(
        program=p,
        specification=phi,
        execution_context=m,
    )

    assert value.program is p
    assert value.specification is phi
    assert value.execution_context is m


def test_verification_task_rejects_raw_program() -> None:
    with pytest.raises(TaskModelError, match="program"):
        VerificationTask(
            program="./example.c",  # type: ignore[arg-type]
            specification=specification(),
            execution_context=execution_context(),
        )


def test_verification_task_rejects_raw_specification() -> None:
    with pytest.raises(TaskModelError, match="specification"):
        VerificationTask(
            program=program(),
            specification="G ! call(reach_error())",  # type: ignore[arg-type]
            execution_context=execution_context(),
        )


def test_verification_task_rejects_raw_execution_context() -> None:
    with pytest.raises(TaskModelError, match="execution_context"):
        VerificationTask(
            program=program(),
            specification=specification(),
            execution_context="ILP32 C",  # type: ignore[arg-type]
        )


def test_task_identity_excludes_witness_provenance() -> None:
    value = task()

    assert not hasattr(value, "uuid")
    assert not hasattr(value, "creation_time")
    assert not hasattr(value, "producer")
    assert not hasattr(value, "format_version")


def test_task_model_objects_are_immutable() -> None:
    value = task()

    with pytest.raises(FrozenInstanceError):
        value.program = program()  # type: ignore[misc]
