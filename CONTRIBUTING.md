# Contributing

Contributions are welcome through pull requests.

## Development setup

Create a virtual environment and install the development dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

## Verification

Before opening a pull request, run:

```bash
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/pytest
.venv/bin/python -m build
.venv/bin/reuse lint
```

## Branches and pull requests

Use a short-lived branch for each change.

Keep pull requests focused on one coherent change and include the tests or
documentation needed to review it.

## Commits

Use Conventional Commits for commit messages.

Examples:

```text
feat(parser): parse witness segments
fix(transform): preserve avoid waypoint semantics
test(parser): cover malformed witness input
docs: update development setup
```

## Dependencies

New dependencies should have a clear purpose and should be included in the same
pull request as the change that needs them.
