[[]# certpath

`certpath` finds matching certificate and private key files using SADE file naming conventions.

## Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/DroneResponse/certpath@main
```

Or, if you have access to the internal package index:

```bash
pip install certpath
```

## Development Setup

Create and activate a virtual environment, then install the project in editable mode with development dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

Or if you use `direnv` you can run:
```bash
direnv allow .
pip install -e ".[dev]"
```

## Running Tests

```bash
# from the project root
pytest
```

## Package and Release/Publish

```bash
bump-my-version bump '<patch | minor | major>'

devpi use '<package index URL>'
devpi login

devpi upload
```