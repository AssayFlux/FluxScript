# FluxScript roadmap

## 0.1.0 — alpha foundation

- [x] Restricted declarative Python source parser (no source execution).
- [x] Shared app/page/element model and validation.
- [x] Web, Android, iOS and standalone CLI source generation.
- [x] Read-only source/project analysis with structured JSON reports.
- [x] Target-specific helper dependency installation on builder invocation.
- [x] Generated-output checks and timestamped directory + ZIP export.
- [x] Full `guide` command and service-call commands.
- [x] Unit tests and package build workflow.

## Next engineering milestones

1. Stabilize the shared intermediate representation and versioned backend contract.
2. Add real action handlers, state, navigation, forms, and API wiring to generated web applications.
3. Compile generated Android projects in a reproducible CI environment and add UI/state/action handling.
4. Add a real Xcode project generator and validate on macOS CI.
5. Add end-to-end golden tests and cross-target behavior parity tests.
6. Implement a genuine FluxScript language front end only after syntax, type rules and runtime semantics are specified.
7. Add external capability adapters only after their licenses, security model, dependencies and tests are reviewed.
8. Run TestPyPI install and release checks before publishing to PyPI.

## Explicit non-goals for 0.1.0

- Compiling arbitrary Python into every target.
- Claiming generated mobile source is a tested APK or IPA.
- Executing untrusted source code on the user's local machine.
- Bundling external tools or claiming provider integration without a working adapter.
