## Security

- Secrets come from env/secret managers, never source, never logs, never error messages returned to clients.
- Validate and sanitize all external input at the boundary. Parameterize queries — never string-build SQL. Escape/encode output per context (HTML, shell, etc.).
- Least privilege for tokens, DB users, and service accounts. Scope and expire credentials.
- Don't roll your own crypto or auth. Use vetted libraries; use the platform's password hashing (argon2/bcrypt), not fast hashes.
- Fail closed: on an auth/permission check error, deny.
- Keep dependencies patched; flag known-vulnerable versions rather than pinning to them.
