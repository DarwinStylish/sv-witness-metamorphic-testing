# SV-Witness Metamorphic Testing

Research software for studying semantics-guided metamorphic testing of
SV-Witness validators.

## Status

This project is under active development. Its supported witness subset,
transformation model, and evaluation methods are still being defined.

## Development

Python 3.12 or later is required.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

Run the local checks with:

```bash
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/pytest
.venv/bin/python -m build
.venv/bin/reuse lint
```

## Documentation

Project documentation is under [`docs/`](docs/README.md).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Security

See [`SECURITY.md`](SECURITY.md).

## License

Project-owned source code and documentation are licensed under the Apache
License 2.0 unless stated otherwise. Licensing metadata follows the REUSE
Specification.
