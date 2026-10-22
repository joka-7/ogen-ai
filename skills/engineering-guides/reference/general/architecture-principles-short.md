# General Architecture Principles (Short)

Cheat sheet for language-agnostic system architecture. Full explanations:
[architecture-principles-detailed.md](./architecture-principles-detailed.md).

> Concrete code per language: [Python](../python/architecture-guide-short.md) ·
> [TypeScript](../typescript/architecture-guide-short.md) · [C++](../cpp/architecture-guide-short.md)

## Core Questions

- **What does it do?** — Responsibility / boundaries (SRP).
- **Why do we need it?** — Purpose / value vs. alternatives.
- **How does it happen?** — End-to-end flow.

## 6 Principles at Architecture Scale

| Principle | Architectural example |
|---|---|
| **Beautiful ✨** | Pluggable plugin architecture — new service = one declarative route definition. |
| **Explicit 🎯** | DI container at startup wires concrete implementations; no auto-discovery magic. |
| **Readable 📖** | Domain-driven service names + typed schemas instead of nested untyped maps. |
| **Simple 👌** | Start with a "majestic monolith"; modularize only as needed (YAGNI). |
| **Scalable 🚀** | Decouple slow work via a background queue or message bus. |
| **Consistent 🔄** | Standard API paths, noun conventions, uniform response envelopes system-wide. |

## Integration Patterns

- **DI** — pass dependencies into constructors; never hardcode instantiation.
- **Immutable events** — frozen event payloads for cross-boundary communication.
- **Facade** — one simple method hides a multi-service subsystem.
- **Adapter** — wrap third-party SDKs behind your own interface; only the adapter imports the vendor library.

## Data Flow (User Registration example)

Client (plaintext, HTTPS) → API Gateway (TLS terminates) → Validation layer
(schema, fail fast) → Service layer (Argon2id hash, discard plaintext) →
Data access layer (persist hash via ORM/query builder only).

## Designing for Testability

DI + separation of concerns + adapters = testable by construction. New feature loop:
**RED** (failing test against the contract) → **GREEN** (implement + unit test) → **BLUE** (refactor).

## HLD vs. LLD

| | HLD | LLD |
|---|---|---|
| Scope | Whole system | Single module/component |
| Audience | Architects, PMs, leads | Developers, reviewers |
| Output | Block/sequence diagrams, DFDs | Class diagrams, pseudocode, test plans |
| Testing | Integration & E2E strategy | Unit test plan (AAA + mocking) |

**HLD checklist:** Requirements (FRs/NFRs) → Static view (block diagrams **and a real
directory map**) → Dynamic view (sequence diagrams) → Data storage (primary store, cache,
blob storage, backup/DR) → Config management (secrets > env > local config > defaults)
→ Data validation/I/O → Integration test strategy.

> The block diagram says how the system is **shaped**; the directory map says which file to
> **open**. They are not substitutes — see
> [documentation principles](./documentation-principles-short.md).

**LLD checklist:** Class/interface diagrams → Pseudocode/flowcharts → I/O schemas →
Config keys → DI wiring → Error contract → Logging plan → Unit test plan.

## Design Patterns

- **Creational:** Factory Method, Singleton, Builder.
- **Structural:** Adapter, Decorator, Facade.
- **Behavioral:** Observer, Strategy, Template Method.

## Anti-Patterns 🚫

God Object · Spaghetti Code · Lava Flow · Boat Anchor.

## Operational Standards

- **Centralized error handling** — custom exception hierarchy + framework-level handlers; business logic stays try/catch-free.
- **Structured JSON logging** — 3 pillars: *what* (level + context, never PII), *where* (stdout → centralized aggregator), *how* (structured format).
- **Log levels:** `DEBUG` (dev only) → `INFO` (routine) → `WARNING` (recoverable) → `ERROR` (alertable failure).

## Security Fundamentals 🔒

AuthN (who are you — session or JWT) vs. AuthZ (what can you do — RBAC/ABAC),
enforced at the boundary. Parameterized queries only. OWASP Top 10 as a checklist,
not an afterthought. TLS everywhere; rate-limit public/auth endpoints.

## CI/CD, Deployment & Observability

Pipeline: lint/type-check → unit tests → build → integration tests → staging →
smoke/E2E → promote. Non-root containers, pinned base images. Expand–contract
pattern for zero-downtime migrations. Metrics (RED method), tracing, and
liveness-vs-readiness health checks — logging alone isn't observability.

## Background Work & Task Queues

Pass IDs not objects · idempotent by design · retries with backoff + dead-letter
queue · structured per-task logging.

## Core Acronyms

KISS · DRY · YAGNI · SOLID · SLAP · LoD · CQS · CI/CD · TDD/BDD · CRUD · ACID ·
BASE · HLD · LLD — full definitions in the
[detailed guide](./architecture-principles-detailed.md#core-engineering-acronyms-reference-).
