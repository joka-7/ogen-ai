# Python — Architecture & Framework Design Guide (Short)

Cheat sheet for system-level architecture, HLD/LLD, patterns, and operations in a
Python stack. Full explanations and code samples: [architecture-guide-detailed.md](./architecture-guide-detailed.md).
Language-agnostic version: [General Architecture Principles](../general/architecture-principles-short.md).

## 6 Principles at Architecture Scale

| Principle | Architectural example |
|---|---|
| **Beautiful ✨** | Pluggable plugin architecture — new service = one declarative YAML route. |
| **Explicit 🎯** | DI container at startup wires concrete implementations; no auto-discovery magic. |
| **Readable 📖** | Domain-driven service names + typed schemas instead of nested untyped dicts. |
| **Simple 👌** | Start with a "majestic monolith" / micro-framework; modularize only as needed (YAGNI). |
| **Scalable 🚀** | Decouple slow work via background queues or a message bus (Celery, Kafka, RabbitMQ). |
| **Consistent 🔄** | Standard API paths, noun conventions, uniform JSON envelopes system-wide. |

## Abstract vs. Implementation 🔌

Contract (interface/ABC) vs. concrete class. Enables swapping providers, simplifies
orchestration, enforces consistent signatures, and makes mocking in tests trivial.

## Data Flow (User Registration example)

Browser (plaintext, HTTPS) → API Gateway (TLS terminates) → Validation layer
(Pydantic schema, fail fast) → Service layer (Argon2id hash, discard plaintext) →
Data access layer (persist `password_hash` via ORM only).

## Integration Patterns

- **DI** — pass dependencies into constructors; never hardcode instantiation.
- **Immutable events** — `@dataclass(frozen=True)` for cross-boundary event payloads.
- **Facade** — one simple method hides a multi-service subsystem.
- **Adapter** — wrap third-party SDKs (Stripe, boto3) behind your own interface; only the adapter imports the vendor library.

## Designing for Testability

DI + separation of concerns + adapters = testable by construction. New feature loop:
**RED** (write a failing integration test against the contract) → **GREEN** (implement + unit test) → **BLUE** (refactor).

## HLD vs. LLD

| | HLD | LLD |
|---|---|---|
| Scope | Whole system | Single module/component |
| Audience | Architects, PMs, leads | Developers, reviewers |
| Output | Block/sequence diagrams, DFDs | Class diagrams, pseudocode, test plans |
| Testing | Integration & E2E strategy | Unit test plan (AAA + mocking) |

### HLD checklist

1. **Requirements** — Functional (FRs) + Non-Functional (NFRs); NFRs drive architecture.
2. **Static view** — block diagrams, components/modules list.
3. **Dynamic view** — DFDs, sequence diagrams, state/activity diagrams.
4. **Data storage** — Primary store (SQL + ORM, ACID), Cache (Redis, cache-aside), Blob storage (S3, DB stores only a reference), Backup/DR (automated backups, PITR, read replicas).
5. **Config management** — priority: Secrets Manager > env vars > `.env` > static config > defaults; `APP_ENV`-driven; fail-fast validated startup (Pydantic `BaseSettings`).
6. **Data validation / I/O** — schema at the edge, JSON + snake_case + ISO-8601 UTC, hashing/masking, pagination.
7. **Integration test strategy** — verify cross-component contracts.

### LLD checklist

1. Class diagrams & method signatures.
2. Pseudocode / flowcharts / state diagrams.
3. I/O data schemas (exact JSON request/response).
4. Component configuration keys.
5. Concrete DI wiring.
6. Error contract (custom exception hierarchy).
7. Structured logging plan (specific log events/levels).
8. Unit test plan (AAA pattern, mocking targets).

## Design Patterns

- **Creational:** Factory Method, Singleton, Builder.
- **Structural:** Adapter, Decorator, Facade.
- **Behavioral:** Observer, Strategy, Template Method.

## Anti-Patterns 🚫

God Object · Spaghetti Code · Lava Flow · Boat Anchor.

## Operational Standards

- **Centralized error handling** — custom `AppError` hierarchy + framework-level exception handlers (e.g. FastAPI `@app.exception_handler`); views stay try/except-free.
- **Structured JSON logging** — 3 pillars: *what* (level + context bindings like `request_id`/`user_id`, never PII), *where* (stdout → centralized aggregator), *how* (machine-readable JSON).
- **Log levels:** `DEBUG` (dev only) → `INFO` (routine) → `WARNING` (recoverable) → `ERROR` (alertable failure).
- **Background tasks (Celery):** one task module per concern; pass IDs not objects; idempotent; configure retries (`max_retries`).

## Core Acronyms

KISS · DRY · YAGNI · SOLID · SLAP · LoD · CQS · CI/CD · TDD/BDD · CRUD · ACID · BASE · HLD · LLD
— see [architecture-guide-detailed.md](./architecture-guide-detailed.md#core-engineering-acronyms-reference-) for full definitions.
