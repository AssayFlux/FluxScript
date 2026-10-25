# FluxScript command reference

## Installation and project setup

```bash
python -m pip install --upgrade FluxScript
fluxscript --version
fluxscript new my_app
cd my_app
fluxscript check app.py
```

## Builders

```bash
fluxscript website app.py [--out build/web] [--no-install-deps]
fluxscript website builder app.py             # equivalent spelling
fluxscript android app.py [--out build/android] [--no-install-deps]
fluxscript android builder app.py              # equivalent spelling
fluxscript ios app.py [--out build/ios] [--no-install-deps]
fluxscript cli app.py [--out build/cli] [--no-install-deps]
fluxscript build app.py --target web|android|ios|cli|all --out build [--no-install-deps]
```

The web builder installs/upgrades the latest `beautifulsoup4` helper to validate generated HTML. The Android builder installs/upgrades the latest `defusedxml` helper to safely parse its generated manifest. iOS source generation has no extra Python helper. Use `--no-install-deps` to require already-installed helpers and avoid pip/network activity. JDK, Android SDK, Gradle, macOS and Xcode are not Python packages.

## Export a generated project to storage

```bash
fluxscript generateproject --source app.py --target web
fluxscript Generate Project --source app.py --target web  # equivalent spelling
fluxscript generateproject --source app.py --target android --storage ~/FluxScriptProjects
fluxscript generateproject --source app.py --target cli
fluxscript generateproject --source app.py --target all
```

The command generates source files into a new project directory and packages the result as a ZIP in the same storage folder. Default storage is `/storage/emulated/0/FluxScriptProjects` when it is writable, otherwise `~/FluxScriptProjects`. The archive includes a manifest listing generated targets and files. Existing output is not overwritten; each export gets a timestamped name.

## Utility commands

- `fluxscript guide` or `fluxscript Guide` — print all commands and usage.
- `fluxscript targets` — list target generators and platform requirements.
- `fluxscript doctor` — detect Python, Node/npm, Java, Gradle, Xcode and Android SDK environment hints.
- `fluxscript integrations` — list FluxScript capabilities and detected local toolchains.
- `fluxscript analyze PATH [--out report.json]` — read-only file inventory, Python AST summary, syntax errors, hashes, and review flags for dynamic execution/process/deserialization calls.
- `fluxscript review PATH` — alias for `analyze`. Analysis does not import or execute the inspected source.
- `fluxscript --help` — CLI syntax.

## Remote execution service

```bash
fluxscript service status
export FLUXSCRIPT_SERVICE_URL='http://127.0.0.1:2000/api/v2'
export FLUXSCRIPT_SERVICE_TOKEN='optional-secret'
fluxscript service runtimes
fluxscript service run python 3.12 main.py
fluxscript service run python 3.12 main.py --stdin-file input.txt
```

The endpoint is an operator-managed service. `status` does not make a network request; `runtimes` and `run` do. HTTP is allowed only for loopback endpoints; remote endpoints must use HTTPS. Keep tokens out of source control.


## Clean aliases and device detection

The CLI accepts clean command names without hyphens or underscores: `website`, `web`, `android`, `ios`, `cli`, `generateproject`, `device`, and `developer`. Legacy names such as `website-builder` and `generate-project` remain supported. Use `fluxscript device` to print best-effort runtime device and operating-system information, or `fluxscript developer` to show the package author. `--noinstalldeps` is an alias for `--no-install-deps`.
