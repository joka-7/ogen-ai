## Security

- Secrets come from env/secret managers, never source, never logs, never error messages returned to clients.
- Validate and sanitize all external input at the boundary. Parameterize queries — never string-build SQL. Escape/encode output per context (HTML, shell, etc.).
- Least privilege for tokens, DB users, and service accounts. Scope and expire credentials.
- Don't roll your own crypto or auth. Use vetted libraries; use the platform's password hashing (argon2/bcrypt), not fast hashes.
- Fail closed: on an auth/permission check error, deny.
- Keep dependencies patched; flag known-vulnerable versions rather than pinning to them.
- Authentication (who are you: session or JWT) and authorization (what may you do: RBAC/ABAC) are separate checks, both enforced at the boundary — never trusted from the client. TLS everywhere; rate-limit public and auth endpoints.
- Treat the OWASP Top 10 as a design checklist, not a post-hoc audit. Scan dependencies in CI (`npm audit`, `pip-audit`, Trivy, or the ecosystem equivalent).
- In memory-unsafe languages, memory safety is part of the security surface: RAII/smart pointers and sanitizers in CI are not optional.
- Plaintext secrets (passwords) are hashed in the service layer and the plaintext discarded; only the hash is persisted.
