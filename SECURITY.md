# Security Policy

## Supported version

Security fixes are applied to the latest version on the `main` branch.

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub Security Advisories.
Do not publish credentials, tokens, personal data, or exploit details in a public issue.

## Deployment notes

- Set a unique `SECRET_KEY` through environment variables.
- Replace all example passwords before seeding or deployment.
- Keep `.env`, runtime JSON files, databases, and build artifacts out of Git.
- Use HTTPS and a managed PostgreSQL service in production.
