import errno
import os
import signal
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import cast

import pytest

from sv_witness_metamorphic_testing.validator_runner import (
    EnvironmentVariable,
    ProcessExit,
    ProcessSpawnFailure,
    ProcessTimeout,
    RunnerModelError,
    ValidatorInvocation,
    run_validator,
)

EXIT_CODE = 7


def executable() -> str:
    return str(Path(sys.executable).resolve())


def make_invocation(
    cwd: Path,
    script: str,
    *,
    arguments: tuple[str, ...] = (),
    environment: tuple[EnvironmentVariable, ...] = (),
    timeout_seconds: float = 2.0,
) -> ValidatorInvocation:
    return ValidatorInvocation(
        argv=(
            executable(),
            "-c",
            script,
            *arguments,
        ),
        cwd=str(cwd),
        environment=environment,
        timeout_seconds=timeout_seconds,
    )


def test_environment_variable_preserves_exact_value() -> None:
    variable = EnvironmentVariable(
        name="VALIDATOR_MODE",
        value="a value with spaces",
    )

    assert variable.name == "VALIDATOR_MODE"
    assert variable.value == "a value with spaces"


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        (
            "",
            "value",
            "environment-variable name must not be empty",
        ),
        (
            "A=B",
            "value",
            "environment-variable name must not contain '='",
        ),
        (
            "A\0B",
            "value",
            "environment-variable name must not contain NUL",
        ),
        (
            "NAME",
            "a\0b",
            "environment-variable value must not contain NUL",
        ),
    ],
)
def test_environment_variable_rejects_invalid_text(
    name: str,
    value: str,
    message: str,
) -> None:
    with pytest.raises(
        RunnerModelError,
        match=message,
    ):
        EnvironmentVariable(
            name=name,
            value=value,
        )


def test_invocation_rejects_non_tuple_argv(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        RunnerModelError,
        match="argv must be a tuple",
    ):
        ValidatorInvocation(
            argv=cast(
                tuple[str, ...],
                [executable()],
            ),
            cwd=str(tmp_path),
            environment=(),
            timeout_seconds=1.0,
        )


def test_invocation_rejects_empty_argv(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        RunnerModelError,
        match="argv must contain at least one argument",
    ):
        ValidatorInvocation(
            argv=(),
            cwd=str(tmp_path),
            environment=(),
            timeout_seconds=1.0,
        )


def test_invocation_rejects_relative_executable(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        RunnerModelError,
        match=r"argv\[0\] must be an absolute executable path",
    ):
        ValidatorInvocation(
            argv=("validator",),
            cwd=str(tmp_path),
            environment=(),
            timeout_seconds=1.0,
        )


def test_invocation_rejects_nul_argument(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        RunnerModelError,
        match="argv entries must not contain NUL",
    ):
        ValidatorInvocation(
            argv=(
                executable(),
                "bad\0argument",
            ),
            cwd=str(tmp_path),
            environment=(),
            timeout_seconds=1.0,
        )


def test_invocation_rejects_relative_cwd() -> None:
    with pytest.raises(
        RunnerModelError,
        match="cwd must be an absolute path",
    ):
        ValidatorInvocation(
            argv=(executable(),),
            cwd="relative-directory",
            environment=(),
            timeout_seconds=1.0,
        )


def test_invocation_rejects_nul_cwd() -> None:
    with pytest.raises(
        RunnerModelError,
        match="cwd must not contain NUL",
    ):
        ValidatorInvocation(
            argv=(executable(),),
            cwd="/tmp/bad\0directory",
            environment=(),
            timeout_seconds=1.0,
        )


def test_invocation_rejects_duplicate_environment_names(
    tmp_path: Path,
) -> None:
    duplicate_environment = (
        EnvironmentVariable(
            name="MODE",
            value="one",
        ),
        EnvironmentVariable(
            name="MODE",
            value="two",
        ),
    )

    with pytest.raises(
        RunnerModelError,
        match="environment-variable names must be unique",
    ):
        ValidatorInvocation(
            argv=(executable(),),
            cwd=str(tmp_path),
            environment=duplicate_environment,
            timeout_seconds=1.0,
        )


@pytest.mark.parametrize(
    "timeout_seconds",
    [
        0.0,
        -1.0,
        float("inf"),
        float("-inf"),
        float("nan"),
    ],
)
def test_invocation_rejects_non_positive_or_non_finite_timeout(
    tmp_path: Path,
    timeout_seconds: float,
) -> None:
    with pytest.raises(
        RunnerModelError,
        match="timeout_seconds must be finite and positive",
    ):
        ValidatorInvocation(
            argv=(executable(),),
            cwd=str(tmp_path),
            environment=(),
            timeout_seconds=timeout_seconds,
        )


def test_invocation_rejects_non_float_timeout(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        RunnerModelError,
        match="timeout_seconds must be a float",
    ):
        ValidatorInvocation(
            argv=(executable(),),
            cwd=str(tmp_path),
            environment=(),
            timeout_seconds=1,
        )


def test_normal_exit_preserves_returncode_and_raw_bytes(
    tmp_path: Path,
) -> None:
    invocation = make_invocation(
        tmp_path,
        (
            "import sys;"
            "sys.stdout.buffer.write(b'raw-out\\xff');"
            "sys.stderr.buffer.write(b'raw-err\\xfe');"
            f"raise SystemExit({EXIT_CODE})"
        ),
    )

    run = run_validator(invocation)

    assert run.invocation == invocation
    assert isinstance(run.observation, ProcessExit)
    assert run.observation.returncode == EXIT_CODE
    assert run.observation.stdout == b"raw-out\xff"
    assert run.observation.stderr == b"raw-err\xfe"


def test_argument_boundaries_are_preserved_without_shell(
    tmp_path: Path,
) -> None:
    arguments = (
        "a b",
        "",
        "$(echo not-a-shell)",
    )

    invocation = make_invocation(
        tmp_path,
        (
            "import sys;"
            "sys.stdout.buffer.write("
            "b'\\x1f'.join("
            "item.encode('utf-8') "
            "for item in sys.argv[1:]"
            ")"
            ")"
        ),
        arguments=arguments,
    )

    run = run_validator(invocation)

    assert isinstance(run.observation, ProcessExit)
    assert run.observation.returncode == 0
    assert run.observation.stdout == (b"a b\x1f\x1f$(echo not-a-shell)")


def test_explicit_environment_does_not_inherit_parent_variable(
    tmp_path: Path,
) -> None:
    ambient_name = "SV_WITNESS_RUNNER_AMBIENT_TEST"
    previous = os.environ.get(ambient_name)

    os.environ[ambient_name] = "ambient"

    try:
        invocation = make_invocation(
            tmp_path,
            (
                "import os,sys;"
                "text = "
                "os.environ.get('RUNNER_ONLY', '<missing>') "
                "+ '|' + "
                "os.environ.get("
                "'SV_WITNESS_RUNNER_AMBIENT_TEST', '<missing>'"
                ");"
                "sys.stdout.buffer.write(text.encode('utf-8'))"
            ),
            environment=(
                EnvironmentVariable(
                    name="RUNNER_ONLY",
                    value="explicit",
                ),
            ),
        )

        run = run_validator(invocation)
    finally:
        if previous is None:
            del os.environ[ambient_name]
        else:
            os.environ[ambient_name] = previous

    assert isinstance(run.observation, ProcessExit)
    assert run.observation.returncode == 0
    assert run.observation.stdout == b"explicit|<missing>"


def test_environment_order_is_retained_in_invocation(
    tmp_path: Path,
) -> None:
    environment = (
        EnvironmentVariable(
            name="SECOND",
            value="2",
        ),
        EnvironmentVariable(
            name="FIRST",
            value="1",
        ),
    )

    invocation = ValidatorInvocation(
        argv=(executable(),),
        cwd=str(tmp_path),
        environment=environment,
        timeout_seconds=1.0,
    )

    assert invocation.environment == environment


def test_standard_input_is_devnull(
    tmp_path: Path,
) -> None:
    invocation = make_invocation(
        tmp_path,
        (
            "import sys;"
            "data = sys.stdin.buffer.read();"
            "sys.stdout.buffer.write(str(len(data)).encode('ascii'))"
        ),
    )

    run = run_validator(invocation)

    assert isinstance(run.observation, ProcessExit)
    assert run.observation.returncode == 0
    assert run.observation.stdout == b"0"


def test_timeout_preserves_partial_raw_streams(
    tmp_path: Path,
) -> None:
    invocation = make_invocation(
        tmp_path,
        (
            "import sys,time;"
            "sys.stdout.buffer.write(b'before-out\\n');"
            "sys.stdout.flush();"
            "sys.stderr.buffer.write(b'before-err\\n');"
            "sys.stderr.flush();"
            "time.sleep(30)"
        ),
        timeout_seconds=1.0,
    )

    run = run_validator(invocation)

    assert isinstance(run.observation, ProcessTimeout)
    assert run.observation.stdout == b"before-out\n"
    assert run.observation.stderr == b"before-err\n"


def test_missing_executable_is_spawn_failure(
    tmp_path: Path,
) -> None:
    missing = str(tmp_path / "definitely-missing-validator")

    invocation = ValidatorInvocation(
        argv=(missing,),
        cwd=str(tmp_path),
        environment=(),
        timeout_seconds=1.0,
    )

    run = run_validator(invocation)

    assert isinstance(
        run.observation,
        ProcessSpawnFailure,
    )
    assert run.observation.error_type == "FileNotFoundError"
    assert run.observation.errno == errno.ENOENT
    assert run.observation.filename == missing


def test_missing_working_directory_is_spawn_failure(
    tmp_path: Path,
) -> None:
    missing_cwd = str(tmp_path / "missing-working-directory")

    invocation = ValidatorInvocation(
        argv=(
            executable(),
            "-c",
            "raise SystemExit(0)",
        ),
        cwd=missing_cwd,
        environment=(),
        timeout_seconds=1.0,
    )

    run = run_validator(invocation)

    assert isinstance(
        run.observation,
        ProcessSpawnFailure,
    )
    assert run.observation.error_type == "FileNotFoundError"
    assert run.observation.errno == errno.ENOENT


@pytest.mark.skipif(
    os.name != "posix",
    reason="negative subprocess signal return codes are POSIX-specific",
)
def test_signal_returncode_remains_raw_integer(
    tmp_path: Path,
) -> None:
    invocation = make_invocation(
        tmp_path,
        ("import os,signal;os.kill(os.getpid(), signal.SIGTERM)"),
    )

    run = run_validator(invocation)

    assert isinstance(run.observation, ProcessExit)
    assert run.observation.returncode == -signal.SIGTERM


def test_run_record_is_frozen(
    tmp_path: Path,
) -> None:
    invocation = make_invocation(
        tmp_path,
        "raise SystemExit(0)",
    )

    run = run_validator(invocation)
    attribute = "observation"

    with pytest.raises(FrozenInstanceError):
        setattr(
            run,
            attribute,
            ProcessTimeout(
                stdout=b"",
                stderr=b"",
            ),
        )


def test_run_validator_rejects_wrong_runtime_type() -> None:
    with pytest.raises(
        RunnerModelError,
        match="invocation must be a ValidatorInvocation",
    ):
        run_validator(
            cast(
                ValidatorInvocation,
                object(),
            )
        )


def test_runner_records_no_validator_result_classification(
    tmp_path: Path,
) -> None:
    invocation = make_invocation(
        tmp_path,
        "raise SystemExit(0)",
    )

    run = run_validator(invocation)

    assert not hasattr(run, "confirmed")
    assert not hasattr(run, "rejected")
    assert not hasattr(run, "unknown")
    assert not hasattr(run, "verdict")
    assert not hasattr(run, "outcome")
