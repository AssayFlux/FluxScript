# Security policy

FluxScript 0.1.0 is an alpha developer tool. Do not treat generated projects or remote execution as production-secure by default.

## Reporting

Do not publish exploit details for an issue that could affect users of a deployed service. Contact the package maintainer through the verified contact listed in the project's release metadata or repository security page. No private security-response SLA is implied by this file.

## Security boundaries

- The source parser never imports or executes the source program. It accepts only a restricted AST subset and enforces input-size and model validation limits.
- Generated code is not automatically safe for every downstream environment. Review and test it before deployment.
- The remote execution adapter is a network client, not an execution sandbox. A service operator must enforce authentication, per-user quotas, time/memory/process limits, isolation, patching, network/filesystem restrictions, logging and retention policy.
- Remote execution may disclose submitted source and stdin to the configured service. Do not send secrets or confidential code unless approved by the service owner.
- Avoid committing tokens. Use environment variables or a secret manager.
