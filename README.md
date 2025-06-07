# foss-build

`foss-build` is a small command line helper for building Free and Open Source
software. It automates the usual `autoconf`, `configure`, `make`, `make test`
and `make install` workflow while capturing logs for each step.

## Supported Python versions

The tool requires **Python 3.9 or newer**.

## Setup

Clone the repository and install the dependencies. You can either use a
virtual environment with `pip` or rely on `poetry` which is configured for the
project.

```bash
# using pip
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# or with poetry
poetry install
```

## Usage

```bash
foss-build [options] [commands]
```

Running without commands performs the full build sequence. Individual steps can
be specified to recover from failures. Useful options include `--large` for
installing under `/opt/stow` and `--no-sudo` to disable `sudo` during
installation.

Example:

```bash
foss-build                # run the standard build/test/install cycle
```

## Running tests

Install the development dependencies and execute the test suite with `pytest`.

```bash
# with pip
pip install pytest
pytest

# or with poetry
poetry install --with dev
poetry run pytest
```
