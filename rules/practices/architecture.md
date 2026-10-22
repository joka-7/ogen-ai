## Architecture (HLD/LLD)

- Before building anything non-trivial, the repo should answer — in a design doc/ADR, or
  legibly in the code's own structure — what it does (responsibility/boundaries), why it's
  needed versus the alternatives, and how it flows end-to-end.
- **HLD checklist:** requirements (functional + non-functional) → static view (components,
  module boundaries, **and a real directory map** — the block diagram says how the system is
  shaped, the directory map says which file to open) → dynamic view (sequence/data flow) → data storage (primary store, cache,
  blob storage, backup/DR) → config/secrets precedence (secrets manager > env > local config >
  defaults; fail fast on missing values at startup, don't default a secret) → data validation
  at the edge → integration-test strategy across component boundaries.
- **LLD checklist:** class/interface contracts → pseudocode for non-obvious logic → exact I/O
  schemas → config keys → DI wiring (constructor injection from one composition root, never a
  hardcoded `new`/instantiation buried in business logic) → one consistent error contract (an
  exception hierarchy or a typed `Result`/discriminated union — not a mix of both, not neither)
  → a deliberate logging plan → the unit test plan (AAA + mocking targets).
- Separate the contract (interface/ABC/trait — what) from the concrete implementation (how).
  Business logic depends on the contract, never a concrete class directly — this is what makes
  swapping implementations and testing with fakes trivial.
- Centralize error handling at the framework/transport boundary; business logic itself stays
  try/catch-free.
- Structured logging only: level + context (request/user IDs — never PII), machine-readable,
  shipped to a central aggregator — not ad-hoc `print`/`console.log`.
- Offload slow or non-request-critical work to a background queue; the handler returns
  immediately. Background tasks: pass IDs not objects, idempotent by design, retries with
  backoff and a dead-letter path.
- Apply the six principles at system scale: *Beautiful* (declarative registration — a new handler is one entry), *Explicit* (one composition root; no auto-wiring magic to trace), *Readable* (domain-driven names and typed schemas, not untyped maps), *Simple* (start as a monolith, split only on real need — YAGNI), *Scalable* (slow work leaves the request path), *Consistent* (one path style, one response envelope, one error shape everywhere).
- Integration patterns: **Adapter** wraps every third-party SDK behind your own interface — only the adapter imports the vendor library. **Facade** hides a multi-service subsystem behind one method. **Immutable events** (`frozen`/`readonly`/`const`) cross boundaries.
- Anti-patterns to refuse: God Object, Spaghetti Code, Lava Flow (dead code nobody dares remove), Boat Anchor (code kept "in case").
- Log levels: `DEBUG` (dev only) → `INFO` (routine) → `WARNING` (recoverable) → `ERROR` (alertable failure). Logs go to stdout and an aggregator. Logging alone isn't observability: add RED-method metrics (rate, errors, duration), tracing (OpenTelemetry), and separate liveness and readiness health checks.
- CI/CD order: lint/type-check → unit tests → build → integration tests → staging → smoke/E2E → promote. Containers run non-root from pinned base images. Schema changes use expand–contract for zero-downtime deploys.
- Design for testability up front: DI + separation of concerns + adapters make code testable by construction. Data crossing the edge is validated by schema before the service layer sees it.
- Full explanations, per-language detail (Python, TypeScript, C++) and worked code: the `engineering-guides` skill.
