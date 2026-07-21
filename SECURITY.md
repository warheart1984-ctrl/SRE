# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |
| < 1.0   | No        |

## Reporting a vulnerability

Please **do not** open public GitHub issues for security vulnerabilities.

Email the maintainers with:

- Description of the issue and potential impact
- Steps to reproduce
- Affected components (API, evidence registry, Dantomax/KMS hooks, etc.)

We aim to acknowledge reports within 5 business days.

## Scope notes

- **Dantomax / KMS:** Production deployments should use `SRE_KMS_MODE=remote` with a
  managed key service; the default local HMAC key is for development only.
- **API:** Bind to `127.0.0.1` by default. Do not expose the dev server to the public
  internet without authentication and TLS termination.
- **Mythar IP:** Security issues in proprietary Mythar creative assets should be reported
  through the same channel; licensing terms remain separate from the Apache-2.0 framework.
