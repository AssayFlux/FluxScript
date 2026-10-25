# PyPI release checklist

The distribution name is `FluxScript` (PyPI canonicalizes names to lowercase), version `0.1.0`. This archive has not been published to PyPI. Verify the name is available and appropriate on PyPI before attempting publication. The import package is `fluxscript`; CLI commands are `fluxscript` and `flux`.

## Build and validate locally

```bash
python -m pip install --upgrade build twine
python -m compileall -q fluxscript
python -m unittest discover -s tests -v
python -m build
python -m twine check dist/*
```

Then test in a fresh virtual environment:

```bash
python -m venv /tmp/fluxscript-venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source /tmp/fluxscript-venv/bin/activate
python -m pip install dist/fluxscript-0.1.0-py3-none-any.whl
fluxscript --version
fluxscript new smoke-project
cd smoke-project
fluxscript check app.py
fluxscript build app.py --target web --out build/web
```

## Publish securely

1. Check PyPI name availability and metadata, README rendering, license, author/maintainer contact and version.
2. Create a PyPI project and configure Trusted Publishing from GitHub Actions where possible; avoid long-lived API tokens in source or committed workflow files.
3. Publish to TestPyPI first and test installation in a clean environment.
4. Pin GitHub Actions to trusted versions/SHAs according to your release policy, grant minimal permissions, and publish only from a protected release workflow.
5. After review, publish the exact tested artifacts to PyPI. Do not rebuild different artifacts between validation and publication.
6. Tag the source and publish hashes/SBOM/release notes.

## Example GitHub Actions direction

Use a protected GitHub release trigger, build wheel and sdist, run tests and `twine check`, then use PyPI Trusted Publishing. Do not add a PyPI publishing workflow until the package owner, repository URL, PyPI project name and release permissions are confirmed.
