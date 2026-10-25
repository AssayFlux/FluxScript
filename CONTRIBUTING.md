# Contributing

1. Keep core runtime dependencies at zero unless a dependency is essential and justified.
2. Do not execute source being compiled. Extend the parser through explicit AST node allowlists and tests.
3. Keep the semantic model backend-neutral. Validate model constraints before any backend writes files.
4. Add regression tests for parser rejection cases, escaping, multi-page generation, CLI behavior and service error handling.
5. Run before submitting changes:

   ```bash
   python -m compileall -q fluxscript tests
   python -m unittest discover -s tests -v
   python -m pip wheel . --no-deps --no-build-isolation -w /tmp/fluxscript-wheel
   ```

6. If Node.js and TypeScript are available, generate a sample project and run `node --check app.js` and `tsc --noEmit`. Validate Kotlin/Gradle on a configured Android SDK/JDK and SwiftUI on macOS/Xcode; do not claim those targets build if they were not actually tested.
7. Never include service tokens, user source files, generated credentials or proprietary third-party code in commits.
8. Version changes require updating `fluxscript/version.py`, `pyproject.toml`, tests and release notes together.
