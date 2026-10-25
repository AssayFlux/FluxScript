# Integration design notes

The supplied archive was reviewed to identify useful capability categories. This package is an original integration architecture and does not redistribute the source archives or their branding.

## Capability categories retained in FluxScript

- **Developer workflow support:** documented project checks, reproducible build commands, structured output and review-oriented guidance.
- **Application-to-command workflows:** the built-in CLI generator emits a Python command interface for declared actions; action requests are explicit JSON and still require application-specific business logic.
- **Artifact analysis:** a future read-only analysis module can inspect user-authorized files and produce evidence-based reports.
- **Remote execution:** an opt-in HTTP client submits source to a separately operated execution service. FluxScript does not execute arbitrary submitted code locally.
- **Isolated remote sessions:** the architecture permits future provider adapters behind a generic interface; no hosted sandbox is bundled in 0.1.0.
- **Scientific extensions:** scientific/quantum libraries can be optional extensions when implemented and tested behind a documented FluxScript API.

These are different capabilities, not one magical interpreter. In 0.1.0, the working functionality is the restricted declarative source parser, shared application model, four source generators, read-only source analyzer, project ZIP export, command guide, and remote execution client. Agent-assisted coding workflows and isolated remote sandbox provisioning are not bundled as completed implementations; they remain possible extension categories.

## Licensing and provenance

FluxScript does not copy the nested source archives into this package and does not rebrand third-party code. Its package license applies to this package's original code only; it does not change the licenses of external tools or libraries that users separately install. Any future adapter must be reviewed for its API contract, security, dependency maintenance and license before it is shipped.
