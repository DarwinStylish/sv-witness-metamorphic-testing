# Validator Execution Protocol

## Purpose

This document defines the initial operational protocol for executing an
SV-Witness validator and recording how the operating-system process behaved.

The runner provides raw process observations for later experimental analysis.

It does not define validator-result semantics, validator correctness, or
metamorphic-oracle rules.

The distinction is intentional.

The formal transformation algebra states that semantic relations between
witnesses do not directly classify validator runs. A separate operational
outcome model is required before such runs can be interpreted.

## Operational Boundary

The initial runner performs one operation:

\[
\text{ValidatorInvocation}
\longrightarrow
\text{ValidatorRun}.
\]

A `ValidatorInvocation` specifies the process configuration requested by the
caller.

A `ValidatorRun` records the resulting process observation.

The runner does not decide whether a validator:

- confirmed a violation;
- rejected a witness;
- returned an unknown verification result;
- encountered an unsupported witness feature;
- encountered an internal analysis failure; or
- behaved consistently with a metamorphic relation.

Those interpretations require validator-specific normalization and an
operational outcome model outside this protocol.

## Invocation Model

A validator invocation contains:

1. an argument vector;
2. an explicit working directory;
3. an explicit complete process environment; and
4. an explicit timeout.

The invocation model is immutable.

### Argument Vector

The argument vector is represented as

\[
a = (a_0, a_1, \ldots, a_n).
\]

It must:

- be a tuple;
- contain at least one element;
- contain only strings;
- contain no NUL characters; and
- use an absolute executable path in \(a_0\).

Arguments after \(a_0\) are retained exactly as supplied.

Empty strings after \(a_0\) are permitted because an empty argument is a valid
process argument on supported operating systems.

The runner does not:

- parse a shell command;
- perform shell quoting;
- invoke a command through a shell;
- rewrite arguments; or
- normalize path arguments.

The executable path itself must be absolute so executable lookup does not
silently depend on the caller's ambient `PATH`.

The operating system may still reject the executable path. Such a failure is
recorded as a process-spawn observation.

## Working Directory

Every invocation supplies a working-directory string.

The working directory must be an absolute path according to the host operating
system.

The runner does not silently use the Python process's current working
directory.

The supplied path is retained without resolving symlinks or normalizing its
spelling.

The constructor does not require that the directory already exist.

Failure by the operating system to start the process with the supplied working
directory is recorded as a spawn failure.

This distinction keeps invocation construction separate from actual process
execution.

## Environment

Every invocation supplies the complete child-process environment.

The runner must not silently inherit the caller's environment.

Environment entries contain an exact string name and string value.

Environment names must:

- be non-empty;
- contain no `=` character; and
- contain no NUL character.

Environment values must contain no NUL character.

Duplicate environment names are rejected by the invocation model.

The initial model retains environment entries in caller-supplied order, but
does not assign semantic significance to that order.

Before process creation, the entries are converted into the environment mapping
passed to the operating-system process interface.

A caller that needs variables such as `PATH`, `HOME`, `LANG`, `LC_ALL`, or
tool-specific configuration must provide them explicitly.

## Standard Input

The initial runner provides no interactive standard input.

The child process receives the platform subprocess `DEVNULL` source as standard
input.

This prevents validator behavior from depending on terminal interaction or
unrecorded caller input.

Supplying explicit input bytes is outside the initial runner.

## Standard Output and Standard Error

Standard output and standard error are captured separately.

Both are retained as byte strings.

The runner performs no:

- character decoding;
- newline conversion;
- whitespace normalization;
- ANSI-sequence removal;
- message parsing; or
- validator-specific interpretation.

Byte preservation is required because validator-output encoding is not part of
the current model.

Text decoding belongs to a later normalization layer when a validator adapter
requires it.

## Timeout

Every invocation supplies a finite positive timeout in seconds.

The timeout is part of the invocation rather than an ambient runner default.

The runner distinguishes timeout from normal process termination.

A timeout is not represented using an invented return code.

If the subprocess interface provides stdout or stderr captured before timeout,
those partial byte streams are retained.

If no partial stream was captured, the corresponding stream is represented by
an empty byte string.

The timeout observation does not by itself mean that the validator produced a
particular semantic result.

## Process Observations

The initial observation model contains three mutually exclusive forms:

1. process exit;
2. process timeout; and
3. process-spawn failure.

These are process-level observations.

They are not validator-result classes.

### Process Exit

A process-exit observation records:

- the raw integer subprocess return code;
- captured stdout bytes; and
- captured stderr bytes.

The runner does not require return code zero.

It also does not assign semantic meaning to any particular return code.

On POSIX systems, a negative return code may indicate signal termination.

The initial runner retains that integer without translating it into a signal
name or validator-result category.

### Process Timeout

A process-timeout observation records:

- partial stdout bytes, if any; and
- partial stderr bytes, if any.

It contains no ordinary process return code.

The timeout value that governed the run remains available through the retained
invocation.

### Process-Spawn Failure

A process-spawn failure occurs when the operating system cannot create the
requested child process.

The initial model records available structured information from the resulting
`OSError`, including:

- the exception class name;
- `errno`, when present; and
- the filename reported by the exception, when present.

A spawn failure is returned as a run observation.

It is not converted into a validator-result category.

Programming errors and violations of invocation-model invariants remain Python
exceptions rather than process observations.

## Run Record

A `ValidatorRun` retains:

- the exact immutable `ValidatorInvocation`; and
- one process observation.

Conceptually,

\[
R = (I, O),
\]

where:

- \(I\) is the requested invocation; and
- \(O\) is the raw process observation.

Retaining the invocation allows an observation to be interpreted only in the
process context under which it was produced.

## Proposed Runtime Types

The initial runtime surface may contain:

    RunnerModelError(ValueError)

    EnvironmentVariable
        name: str
        value: str

    ValidatorInvocation
        argv: tuple[str, ...]
        cwd: str
        environment: tuple[EnvironmentVariable, ...]
        timeout_seconds: float

    ProcessExit
        returncode: int
        stdout: bytes
        stderr: bytes

    ProcessTimeout
        stdout: bytes
        stderr: bytes

    ProcessSpawnFailure
        error_type: str
        errno: int | None
        filename: str | None

    ProcessObservation =
        ProcessExit
        | ProcessTimeout
        | ProcessSpawnFailure

    ValidatorRun
        invocation: ValidatorInvocation
        observation: ProcessObservation

    run_validator(
        invocation: ValidatorInvocation,
    ) -> ValidatorRun

All record types are immutable.

The runner function is the only component in this protocol that performs
process execution.

## Execution Procedure

For a valid `ValidatorInvocation`, the initial runner performs the equivalent
of:

1. pass the exact argument vector to the subprocess API;
2. use the supplied absolute working directory;
3. construct the complete child environment only from the supplied environment
   entries;
4. connect standard input to `DEVNULL`;
5. capture stdout and stderr separately as bytes;
6. use the supplied timeout;
7. disable shell execution;
8. disable automatic exception raising for non-zero return codes;
9. return a process-exit observation when the process returns;
10. return a process-timeout observation when timeout occurs; or
11. return a process-spawn-failure observation when process creation raises
    `OSError`.

The runner must not invoke `shell=True`.

## Executable Resolution

The initial invocation requires `argv[0]` to be an absolute executable path.

The runner therefore does not perform its own `PATH` search and does not
silently replace the executable argument with another path.

This requirement removes one source of hidden ambient state.

It does not prove that the executable contents remain unchanged between two
runs.

## Reproducibility Boundary

This runner records enough process configuration to replay the requested local
process invocation without silently inheriting the caller's current directory
or environment.

That is narrower than complete experimental reproducibility.

The initial runner does not establish:

- the content digest of the validator executable;
- the validator version;
- shared-library identities;
- container or operating-system identity;
- kernel version;
- CPU architecture details;
- filesystem snapshots;
- resource-limit identity beyond the runner timeout;
- scheduler behavior; or
- external service state.

Those facts may be required by a later reproducibility package.

The runner therefore must not describe a `ValidatorRun` as proof that two
executions occurred in identical environments.

## No Duration or Wall-Clock Time

The initial run record does not include:

- wall-clock start time;
- wall-clock end time; or
- measured elapsed duration.

These values are useful for performance analysis but are not required to
distinguish the process observations needed by the current stage.

Adding them would also introduce nondeterministic metadata into the first run
model.

They can be added later if an experiment requires them.

## No Additional Resource Limits

The initial runner models only wall-clock timeout.

It does not configure:

- CPU-time limits;
- address-space limits;
- process-count limits;
- file-size limits;
- container limits; or
- cgroup limits.

Such controls may later be added as explicit invocation configuration.

They must not be assumed merely because the runner uses a timeout.

## Separation from Transformation Evidence

Transformation evidence and validator execution have different roles.

Transformation evidence establishes local conformance of a transformed witness
to an already-defined transformation contract, conditional on independent
source admission.

The validator runner records what an external validator process did.

The runner does not use validator execution to justify transformation evidence.

The runner also does not require a `TransformationLocalEvidence` object merely
to execute a process.

Later orchestration may associate transformation evidence with multiple
validator runs without merging the two models.

## Separation from the Outcome Model

The raw runner stops before validator-result normalization.

For example, raw observations may include:

    returncode = 0
    stdout = b"..."
    stderr = b""

or:

    returncode = 1
    stdout = b""
    stderr = b"..."

or a timeout with partial stdout, or a spawn failure with `errno = 2`.

A validator-specific adapter may later interpret a supported validator's
documented output contract.

That adapter is separate from the raw process runner.

This prevents process mechanics from embedding assumptions such as:

- exit code zero means witness confirmation;
- a particular output string means rejection;
- timeout means an unknown verification result; or
- every non-zero return code has the same meaning.

## Separation from the Metamorphic Oracle

The runner observes one process invocation at a time.

It does not compare source-witness and transformed-witness runs.

It therefore does not:

- constrain pairs of validator results;
- classify related run pairs;
- identify metamorphic violations;
- infer validator incompleteness;
- infer validator correctness; or
- identify software defects.

Those operations require the later operational outcome model and metamorphic
oracle.

## Initial Platform Interpretation

The model retains subprocess return codes in the representation exposed by
Python on the host operating system.

Platform-specific interpretation is deliberately deferred.

For example, a negative POSIX return code is preserved as a negative integer
rather than being converted into a cross-platform termination category.

The raw observation therefore remains close to the subprocess interface.

## Failure Semantics

Failure to launch the requested process is an observed execution failure, not a
validator semantic result.

Timeout is an observed execution condition, not a validator semantic result.

Non-zero return is an observed process termination, not a validator semantic
result.

Captured diagnostic text is raw process output, not a semantic result.

This distinction must remain intact until the operational outcome layer defines
validator-specific interpretation rules.

## Exclusions

The initial runner does not provide:

- validator-specific result parsers;
- confirmation/rejection/unknown classes;
- exit-code-to-result mappings;
- diagnostic-text-to-result mappings;
- validator-version discovery;
- executable hashing;
- automatic `PATH` resolution;
- ambient environment inheritance;
- ambient working-directory inheritance;
- shell command execution;
- interactive input;
- output decoding;
- output normalization;
- source/transformed run comparison;
- transformation-relation checking;
- metamorphic outcome constraints;
- defect classification;
- validator completeness assumptions; or
- a general experiment scheduler.

Those concerns belong to later operational or reproducibility layers.
