# TypeScript — Architecture & Framework Design Guide (Short)

Cheat sheet for system-level architecture, HLD/LLD, patterns, and operations in
framework-agnostic TypeScript. Full explanations and code samples:
[architecture-guide-detailed.md](./architecture-guide-detailed.md).
Language-agnostic version: [General Architecture Principles](../general/architecture-principles-short.md).

## 6 Principles at Architecture Scale

| Principle | TypeScript example |
|---|---|
| **Beautiful ✨** | Declarative route table → handler modules; adding a route touches one entry. |
| **Explicit 🎯** | Composition root (`main.ts`) wires concrete implementations via constructors — no decorator auto-wiring to trace. |
| **Readable 📖** | Domain-driven service names + typed request/response interfaces, not `Record<string, unknown>`. |
| **Simple 👌** | One `server.ts` with a few routes; split into modules only once it's actually unwieldy. |
| **Scalable 🚀** | Slow work handed to a background job queue (BullMQ); the handler returns immediately. |
| **Consistent 🔄** | Standard API paths, one JSON envelope, one error shape across every route. |

## Abstract vs. Implementation 🔌

`interface` (contract) vs. concrete class. Enables swapping providers, simplifies
orchestration, makes mocking in tests trivial.

## Data Flow (User Registration example)

Client (plaintext, HTTPS) → edge/proxy (TLS terminates) → Validation layer (Zod
schema, fail fast) → Service layer (Argon2id hash, discard plaintext) → Data
access layer (persist hash only).

## Integration Patterns

- **DI** — pass dependencies into constructors; never `new` a dependency inside a class.
- **Immutable events** — `readonly` interfaces for cross-boundary event payloads.
- **Facade** — one class hides a multi-service subsystem behind a simple method.
- **Adapter** — wrap third-party SDKs (Stripe, AWS SDK) behind your own interface; only the adapter imports the vendor library.

## Designing for Testability

DI + separation of concerns + adapters = testable by construction. New feature
loop: **RED** (failing test against the contract) → **GREEN** (implement + unit
test) → **BLUE** (refactor).

## HLD vs. LLD

Same as the [general guide](../general/architecture-principles-short.md#hld-vs-lld) —
nothing TypeScript-specific about the documents themselves. LLD's static view
uses `interface`s as the class-diagram contract.

## Design Patterns & Anti-Patterns

Language-agnostic — see the [general reference](../general/architecture-principles-short.md#design-patterns).

## Operational Standards

- **Centralized error handling** — an `AppError` class hierarchy + one error-handling hook at the framework boundary; handlers stay try/catch-free.
- **Structured JSON logging** — `pino` + `AsyncLocalStorage` for request-scoped context (request ID, user ID); never PII/credentials.
- **Log levels:** `debug` (dev only) → `info` (routine) → `warn` (recoverable) → `error` (alertable).

## Security Fundamentals 🔒

AuthN (session or JWT) vs. AuthZ (RBAC/ABAC), enforced at the boundary.
Parameterized queries only. OWASP Top 10 as a checklist. TLS everywhere;
rate-limit public/auth endpoints. Dependency scanning via `npm audit`/Snyk in CI.

## CI/CD, Deployment & Observability

Pipeline: `eslint` + `tsc --noEmit` → unit tests → build (`npm run build`) →
integration tests → staging → smoke/E2E → promote. Non-root, multi-stage
`node:20-slim` containers. Prisma/Knex/TypeORM migrations, expand–contract for
zero downtime. Metrics via `prom-client` (RED method), tracing via OpenTelemetry
JS, liveness vs. readiness health checks.

## Background Work & Task Queues

BullMQ (Redis-backed) is the common choice. Pass IDs not objects · idempotent by
design · retries with backoff · structured per-job logging.

## Core Acronyms

KISS · DRY · YAGNI · SOLID · SLAP · LoD · CQS · CI/CD · TDD/BDD · CRUD · ACID ·
BASE · HLD · LLD — full definitions in the
[general reference](../general/architecture-principles-short.md#core-acronyms).
