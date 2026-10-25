# FluxScript 0.1.0 — Verification report

Tested from the source tree in a Linux/Python 3.13 environment on 2026-10-25.

## Passed

- ZIP archive integrity and duplicate-path check.
- `python -m compileall -q fluxscript tests`.
- `python -m unittest discover -s tests -v`: 14 tests passed.
- `python -m pytest -q`: 14 tests passed (pytest was already available in the test environment).
- Built a wheel with `python -m pip wheel . --no-deps --no-build-isolation`.
- Built an sdist with `setuptools.build_meta.build_sdist`.
- Installed the wheel into an isolated target directory and ran `python -m fluxscript --version`, `developer`, and `targets`.
- Created a starter project and validated its `app.py`.
- Generated and structurally validated web, Android, iOS and CLI starter projects using `--no-install-deps`.
- Generated web JavaScript passed `node --check`; generated TypeScript passed `tsc --noEmit -p tsconfig.json`.
- Verified notebook JSON and parsed every notebook code cell for Python syntax.
- Verified automatic dependency manager behavior using mocked pip calls in unit tests.

## Not completed in this environment

- `twine check`: Twine was not installed and network/DNS was unavailable, so the tool could not be installed here.
- Publishing to PyPI or pushing to GitHub: not attempted; requires the owner's accounts, credentials and explicit confirmation.
- Native Android compilation: Android SDK/JDK toolchain build not run.
- iOS compilation/signing: requires macOS and Xcode and was not run.
- Live dependency downloads/upgrades: not run as an online integration test; unit tests mock pip invocations.

## Release note

This is an alpha release (`0.1.0`). The generated Android/iOS outputs are source projects, not guaranteed installable APK/IPA files. Review the package and run the release notebook in an internet-connected environment before publishing.
