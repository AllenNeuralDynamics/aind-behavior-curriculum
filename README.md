# aind-behavior-curriculum

[![License](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)
![CI](https://github.com/AllenNeuralDynamics/aind-behavior-curriculum/actions/workflows/test_and_lint.yml/badge.svg)
[![PyPI - Version](https://img.shields.io/pypi/v/aind-behavior-curriculum)](https://pypi.org/project/aind-behavior-curriculum/)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
![Interrogate](https://img.shields.io/badge/interrogate-100.0%25-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen?logo=codecov)
![Python](https://img.shields.io/badge/python->=3.11-blue?logo=python)

A core problem in mice training is accurately keeping track of each mouse's training stage and accurately setting the corresponding rig parameters. As the number of behavior studies, research assistants, and mice increase, manual tracking and parameter input is prone to human error. This library provides a flexible framework for defining mice curriculum enabling mouse training to be automated.

> [!WARNING]
> This library is still in development. Expect breaking changes in future releases.

## Installation
```bash
pip install aind-behavior-curriculum
```

## Documentation

The full documentation is available at [https://aind-behavior-curriculum.readthedocs.io/en/latest/](https://aind-behavior-curriculum.readthedocs.io/en/latest/)

## Contributing

### Issues and Bugs

If you find any issues or bugs, please open an issue on [GitHub](https://github.com/AllenNeuralDynamics/aind-behavior-curriculum/issues)

### Suggesting changes and Pull Requests

If you would like to suggest changes or contribute to the project, please open a pull request on [GitHub](https://github.com/AllenNeuralDynamics/aind-behavior-curriculum/pulls).
Attempt to open a pull request that is scoped to a single issue or feature to make the review process easier.

#### Dependencies and lockfile

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency management and lockfile generation.

You can create a new environment with:

```bash
uv venv
```

or run standalone commands with:

```bash
uv run <command>
```

#### Linting

This project uses:

`ruff` for linting. To lint the project, run the following commands:

```bash
ruff format .
ruff check .
```

`interrogate` for documentation analysis:

```bash
interrogate --verbose .
```

and `codespell` for spell checking:

```bash
codespell .
```

#### Testing

The project uses `unittest` for testing and `coverage` for coverage analysis.

```bash
coverage run -m unittest
coverage report
```
