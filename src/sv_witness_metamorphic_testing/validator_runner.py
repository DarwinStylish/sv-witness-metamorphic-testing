"""Raw process execution for external witness validators."""

import math
import subprocess
from dataclasses import dataclass
from pathlib import Path


class RunnerModelError(ValueError):
    """Raised when a validator-runner value violates a local invariant."""


@dataclass(frozen=True, slots=True, kw_only=True)
class EnvironmentVariable:
    """One exact child-process environment entry."""

    name: str
    value: str

    def __post_init__(self) -> None:
        if type(self.name) is not str:
            raise RunnerModelError("environment-variable name must be a string")

        if not self.name:
            raise RunnerModelError("environment-variable name must not be empty")

        if "=" in self.name:
            raise RunnerModelError("environment-variable name must not contain '='")

        if "\0" in self.name:
            raise RunnerModelError("environment-variable name must not contain NUL")

        if type(self.value) is not str:
            raise RunnerModelError("environment-variable value must be a string")

        if "\0" in self.value:
            raise RunnerModelError("environment-variable value must not contain NUL")


def _validate_argv(
    argv: tuple[str, ...],
) -> None:
    if not isinstance(argv, tuple):
        raise RunnerModelError("argv must be a tuple")

    if not argv:
        raise RunnerModelError("argv must contain at least one argument")

    if any(type(argument) is not str for argument in argv):
        raise RunnerModelError("argv entries must all be strings")

    if any("\0" in argument for argument in argv):
        raise RunnerModelError("argv entries must not contain NUL")

    if not Path(argv[0]).is_absolute():
        raise RunnerModelError("argv[0] must be an absolute executable path")


def _validate_cwd(
    cwd: str,
) -> None:
    if type(cwd) is not str:
        raise RunnerModelError("cwd must be a string")

    if "\0" in cwd:
        raise RunnerModelError("cwd must not contain NUL")

    if not Path(cwd).is_absolute():
        raise RunnerModelError("cwd must be an absolute path")


def _validate_environment(
    environment: tuple[EnvironmentVariable, ...],
) -> None:
    if not isinstance(environment, tuple):
        raise RunnerModelError("environment must be a tuple")

    if any(not isinstance(variable, EnvironmentVariable) for variable in environment):
        raise RunnerModelError("environment entries must all be EnvironmentVariable objects")

    names = tuple(variable.name for variable in environment)

    if len(set(names)) != len(names):
        raise RunnerModelError("environment-variable names must be unique")


def _validate_timeout(
    timeout_seconds: float,
) -> None:
    if type(timeout_seconds) is not float:
        raise RunnerModelError("timeout_seconds must be a float")

    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0.0:
        raise RunnerModelError("timeout_seconds must be finite and positive")


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidatorInvocation:
    """Exact process configuration requested for one validator execution."""

    argv: tuple[str, ...]
    cwd: str
    environment: tuple[EnvironmentVariable, ...]
    timeout_seconds: float

    def __post_init__(self) -> None:
        _validate_argv(self.argv)
        _validate_cwd(self.cwd)
        _validate_environment(self.environment)
        _validate_timeout(self.timeout_seconds)


def _validate_bytes(
    value: bytes,
    *,
    name: str,
) -> None:
    if type(value) is not bytes:
        raise RunnerModelError(f"{name} must be bytes")


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessExit:
    """Raw observation of a process that returned."""

    returncode: int
    stdout: bytes
    stderr: bytes

    def __post_init__(self) -> None:
        if type(self.returncode) is not int:
            raise RunnerModelError("returncode must be an integer")

        _validate_bytes(
            self.stdout,
            name="stdout",
        )
        _validate_bytes(
            self.stderr,
            name="stderr",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessTimeout:
    """Raw observation of a process whose runner timeout expired."""

    stdout: bytes
    stderr: bytes

    def __post_init__(self) -> None:
        _validate_bytes(
            self.stdout,
            name="stdout",
        )
        _validate_bytes(
            self.stderr,
            name="stderr",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessSpawnFailure:
    """Structured observation of an OSError raised during process creation."""

    error_type: str
    errno: int | None
    filename: str | None

    def __post_init__(self) -> None:
        if type(self.error_type) is not str or not self.error_type:
            raise RunnerModelError("spawn-failure error_type must be a non-empty string")

        if self.errno is not None and type(self.errno) is not int:
            raise RunnerModelError("spawn-failure errno must be an integer when present")

        if self.filename is not None and type(self.filename) is not str:
            raise RunnerModelError("spawn-failure filename must be a string when present")


type ProcessObservation = ProcessExit | ProcessTimeout | ProcessSpawnFailure


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidatorRun:
    """One invocation together with its raw process observation."""

    invocation: ValidatorInvocation
    observation: ProcessObservation

    def __post_init__(self) -> None:
        if not isinstance(self.invocation, ValidatorInvocation):
            raise RunnerModelError("invocation must be a ValidatorInvocation")

        if not isinstance(
            self.observation,
            (
                ProcessExit,
                ProcessTimeout,
                ProcessSpawnFailure,
            ),
        ):
            raise RunnerModelError("observation must be a supported process observation")


def _timeout_stream(
    value: bytes | str | None,
    *,
    name: str,
) -> bytes:
    if value is None:
        return b""

    if type(value) is not bytes:
        raise RunnerModelError(f"captured timeout {name} must be bytes")

    return value


def _spawn_failure(
    error: OSError,
) -> ProcessSpawnFailure:
    reported_filename = error.filename

    filename = reported_filename if isinstance(reported_filename, str) else None

    return ProcessSpawnFailure(
        error_type=type(error).__name__,
        errno=error.errno,
        filename=filename,
    )


def run_validator(
    invocation: ValidatorInvocation,
) -> ValidatorRun:
    """Execute one validator process and retain only raw process observations."""

    if not isinstance(invocation, ValidatorInvocation):
        raise RunnerModelError("invocation must be a ValidatorInvocation")

    environment = {variable.name: variable.value for variable in invocation.environment}

    try:
        completed = subprocess.run(
            invocation.argv,
            cwd=invocation.cwd,
            env=environment,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=invocation.timeout_seconds,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as error:
        observation: ProcessObservation = ProcessTimeout(
            stdout=_timeout_stream(
                error.output,
                name="stdout",
            ),
            stderr=_timeout_stream(
                error.stderr,
                name="stderr",
            ),
        )
    except OSError as error:
        observation = _spawn_failure(error)
    else:
        observation = ProcessExit(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    return ValidatorRun(
        invocation=invocation,
        observation=observation,
    )
