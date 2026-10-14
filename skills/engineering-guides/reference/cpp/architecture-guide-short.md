# C++ — Architecture & Framework Design Guide (Short)

Cheat sheet for system-level architecture, HLD/LLD, patterns, and operations in
modern (17/20) application-level C++. Full explanations and code samples:
[architecture-guide-detailed.md](./architecture-guide-detailed.md).
Language-agnostic version: [General Architecture Principles](../general/architecture-principles-short.md).

## 6 Principles at Architecture Scale

| Principle | C++ example |
|---|---|
| **Beautiful ✨** | A plugin registered via a factory map — adding a handler is one registration call. |
| **Explicit 🎯** | Composition root (`main.cc`) wires concrete implementations into constructors — the whole dependency graph is visible in one place. |
| **Readable 📖** | Domain-driven class names + typed structs, not `std::map<std::string, std::any>`. |
| **Simple 👌** | A small binary target; split into a library only once genuinely reused elsewhere. |
| **Scalable 🚀** | Slow work handed to a thread pool; the request-handling thread returns immediately. |
| **Consistent 🔄** | One CMake naming convention, one error-handling strategy, one logging shape everywhere. |

## Abstract vs. Implementation 🔌

Abstract base class with pure virtual functions (contract) vs. concrete
subclasses (implementations). Enables swapping providers, simplifies
orchestration, makes mocking with gMock trivial.

## Data Flow (User Registration example)

Client (plaintext, HTTPS) → edge/proxy (TLS terminates) → Validation layer
(typed struct, fail fast) → Service layer (Argon2id hash via libsodium, discard
plaintext) → Data access layer (prepared statement, persist hash only).

## Integration Patterns

- **DI** — pass dependencies as constructor parameters (`shared_ptr`/`unique_ptr`); never `new` a dependency inside a class.
- **Immutable events** — `const`-qualified struct fields for cross-boundary event payloads.
- **Facade** — one class hides a multi-service subsystem behind a simple method.
- **Adapter** — wrap third-party SDKs behind your own interface; only the adapter translation unit includes the vendor headers.

## Designing for Testability

DI + separation of concerns + adapters = testable by construction. New feature
loop: **RED** (failing test against the contract) → **GREEN** (implement + unit
test) → **BLUE** (refactor).

## HLD vs. LLD

Same as the [general guide](../general/architecture-principles-short.md#hld-vs-lld) —
nothing C++-specific about the documents themselves. LLD's static view uses
abstract base classes with pure virtual functions as the class-diagram contract.

## Design Patterns & Anti-Patterns

Language-agnostic — see the [general reference](../general/architecture-principles-short.md#design-patterns).

## Operational Standards

- **Centralized error handling** — an `AppError` exception hierarchy + one top-level `catch` at the request boundary; business logic stays exception-boilerplate-free.
- **Structured JSON logging** — `spdlog` with structured key-value fields; never PII/credentials.
- **Log levels:** `debug` (dev only) → `info` (routine) → `warn` (recoverable) → `error`/`critical` (alertable).

## Security Fundamentals 🔒

AuthN (session or JWT) vs. AuthZ (RBAC/ABAC), enforced at the boundary.
Prepared statements only, never string-concatenated SQL. **Memory safety is
part of your security surface** — RAII/smart pointers + `-fsanitize=address,undefined`
in CI aren't optional. OWASP Top 10 as a checklist; dependency scanning via
OWASP Dependency-Check/Trivy against your `vcpkg`/`conan` lockfile.

## CI/CD, Deployment & Observability

Pipeline: compiler at `-Wall -Wextra -Werror` + `clang-tidy` → unit tests →
build (CMake) → integration tests → staging → smoke/E2E → promote. Multi-stage
Docker (`gcc:13` builder → `debian-slim` runtime, non-root). Migrations via a
tool independent of the service (sqitch/Flyway), expand–contract for zero
downtime. Metrics via `prometheus-cpp` (RED method), tracing via OpenTelemetry
C++, liveness vs. readiness health checks.

## Background Work & Task Queues

In-process thread pool, or a message queue (RabbitMQ/ZeroMQ) cross-process. Pass
IDs not objects/pointers · idempotent by design · retries with backoff ·
structured per-job logging.

## Core Acronyms

KISS · DRY · YAGNI · SOLID · SLAP · LoD · CQS · CI/CD · TDD/BDD · CRUD · ACID ·
BASE · HLD · LLD — full definitions in the
[general reference](../general/architecture-principles-short.md#core-acronyms).
