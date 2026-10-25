# FluxScript 0.1.0

FluxScript is a Python-first project generator and developer command-line toolkit. It provides a restricted declarative Python source format, shared application model, web source generation, native-platform source starters, project export, and an optional remote execution-service client.

> **Release status:** 0.1.0 is an alpha. It is suitable for experimentation and generated-source workflows, not a claim that arbitrary Python compiles to every platform. Inspect generated source and validate native projects with their real toolchains before production use.

## Install

After the package is published under the PyPI project name `FluxScript`, install it with `python -m pip install FluxScript`. Package names are case-insensitive on PyPI. Until publication, install from the source checkout using the command below.


From the extracted source directory:

```bash
python -m pip install .
fluxscript --version
fluxscript guide
```

After FluxScript has been published to PyPI, users can install or update it with `python -m pip install --upgrade FluxScript`. It has **not** been published from this archive. FluxScript's core has no mandatory third-party runtime dependencies. When a builder is invoked, it automatically upgrades the Python helper packages required for that target's validation. Use `--no-install-deps` to disable this network/install step when the helper is already installed. This does not install operating-system toolchains.

## First project

```bash
fluxscript new my_app
cd my_app
fluxscript check app.py
fluxscript website app.py
```

Preview the generated site:

```bash
cd build/web
python -m http.server 8000
```

Open `http://127.0.0.1:8000` in a browser.

## Generate a project ZIP into storage

```bash
fluxscript generateproject --source app.py --target web
fluxscript generateproject --source app.py --target android
fluxscript generateproject --source app.py --target ios
fluxscript generateproject --source app.py --target all
```

This creates **both a project directory and a ZIP archive**. By default, FluxScript uses `/storage/emulated/0/FluxScriptProjects` when that shared Android storage location exists and is writable; otherwise it uses `~/FluxScriptProjects`. Specify `--storage /path/to/folder` to choose a different location.

## Builders

```bash
fluxscript website app.py --out build/web
fluxscript android app.py --out build/android
fluxscript ios app.py --out build/ios
fluxscript cli app.py --out build/cli
fluxscript build app.py --target all --out build/all
```

- **Website:** HTML, responsive CSS, JavaScript, TypeScript, and structural HTML validation. Buttons emit action events; real business logic, APIs, authentication and persistence must be connected by the developer.
- **Android:** Kotlin/Gradle source project with a manifest validated by a safe XML parser. Building an APK requires a JDK, Android SDK, and compatible Gradle/Android Gradle Plugin toolchain.
- **iOS:** SwiftUI source starter. Building/signing an app requires macOS and Xcode. The builder does not produce an IPA.
- **CLI:** standalone Python `argparse` command interface for declared button actions; generated commands emit JSON action requests for application-specific handlers to consume.

The web and Android builder commands automatically upgrade their respective Python validation helper package to the latest available release. The iOS source generator has no Python helper dependency to install. Native build tools are not pip packages and are not silently downloaded.

## Remote execution service

Configure an execution API that implements the documented runtime-listing and code-execution request shape. FluxScript never starts a remote service implicitly.

```bash
fluxscript service status
export FLUXSCRIPT_SERVICE_URL='http://127.0.0.1:2000/api/v2'
export FLUXSCRIPT_SERVICE_TOKEN='your-token-if-required'
fluxscript service runtimes
fluxscript service run python 3.12 main.py
fluxscript service run javascript 20.11.1 app.js --stdin-file input.txt
```

Remote non-local endpoints must use HTTPS. Never send secrets or untrusted code to an execution service unless you trust its operator and isolation controls. Client-side limits do not make a server secure.

## Commands

Run `fluxscript guide` for the complete built-in command reference. Other useful commands:

```bash
fluxscript --help
fluxscript new [directory]
fluxscript check [app.py]
fluxscript targets
fluxscript doctor
fluxscript integrations
fluxscript analyze ./source --out report.json
fluxscript review ./source
```

## Source format and security boundary

The `app.py` source is parsed using Python's AST and is **not executed**. Version 0.1.0 accepts only an explicit subset of declarative constructors, assignments, and page-registration calls. It is not a general Python interpreter or arbitrary Python-to-native compiler. Unsupported statements are rejected.

## Development and release checks

```bash
python -m compileall -q fluxscript tests
python -m unittest discover -s tests -v
python -m pip install build twine
python -m build
python -m twine check dist/*
```

See `docs/ARCHITECTURE.md`, `docs/COMMANDS.md`, `docs/INTEGRATION_NOTES.md`, `docs/ROADMAP.md`, and `docs/PYPI_RELEASE.md`.

## Clean command names

The CLI accepts easy-to-type commands without hyphens or underscores: `fluxscript website app.py`, `fluxscript android app.py`, `fluxscript ios app.py`, `fluxscript cli app.py`, `fluxscript generateproject --source app.py --target all`, and `fluxscript device`. Existing hyphenated commands remain supported for compatibility.

## Author

**Md Safarujjaman** is the author listed in the package metadata. Run `fluxscript developer` to display the project author and version.
