# General Architecture Principles (Detailed)

Language-agnostic system architecture: boundaries, HLD/LLD design documents,
design patterns, and operational standards. Every principle here applies
regardless of implementation language. For the condensed version, see
[architecture-principles-short.md](./architecture-principles-short.md).

> **Language-specific implementations** live in each language's own
> architecture guide: [Python](../python/architecture-guide-detailed.md) ·
> [TypeScript](../typescript/architecture-guide-detailed.md) ·
> [C++](../cpp/architecture-guide-detailed.md)

> Related general guides: [Coding Principles](./coding-principles-detailed.md) ·
> [Testing Principles](./testing-principles-detailed.md)

## Table of Contents

1. [Core Questions of Design](#core-questions-of-design)
2. [Design Principles at the System Level](#design-principles-at-the-system-level)
3. [Integration Patterns](#integration-patterns)
4. [Data Flow Strategy 🗺️](#data-flow-strategy-)
5. [Designing for Testability](#designing-for-testability)
6. [Design Documents: HLD & LLD 🗺️📜](#design-documents-hld--lld-)
7. [Design Patterns & Anti-Patterns 💡](#design-patterns--anti-patterns-)
8. [Operational Logging & Centralized Error Strategy ☁️](#operational-logging--centralized-error-strategy-)
9. [Security Fundamentals 🔒](#security-fundamentals-)
10. [CI/CD, Deployment & Observability 🚀📈](#cicd-deployment--observability-)
11. [Background Work & Task Queues](#background-work--task-queues)
12. [Software Engineering Rules](#software-engineering-rules)
13. [What Is a "Component"?](#what-is-a-component)
14. [Core Engineering Acronyms Reference 📜](#core-engineering-acronyms-reference-)

---

## Core Questions of Design

- **What does it do? (Responsibility):** Define the core function and boundaries — aligns with SRP.
- **Why do we need it? (Purpose):** Articulate the value proposition and trade-offs vs. alternatives.
- **How does it happen? (Flow):** Describe the primary end-to-end processing lifecycle.

## Design Principles at the System Level

The [six coding principles](./coding-principles-detailed.md#the-6-principles-of-coding)
take on architectural meaning when scaled up from a function to a system:

### 1. Beautiful Design ✨ (Conceptual Elegance)

Clarity of purpose, intuitive component interactions, and a "pit of success" that
guides developers toward the right choice.

> **Example:** An API Gateway with a **pluggable plugin architecture** — adding a
> new service is a small declarative route definition (`/users -> http://user-service`),
> no gateway re-compilation required.

### 2. Explicit Design 🎯 (No Magic)

Dependencies, configuration, and data flows are stated and traceable, not hidden
behind auto-magical conventions.

> **Example:** An explicit **Dependency Injection (DI) container** at startup
> constructs repositories and injects them into service constructors — instead of
> relying on global auto-discovery.

### 3. Readable Design 📖 (Clear Boundaries & Contracts)

Structure is instantly recognizable via standard naming, typed schemas, and explicit
component boundaries.

> **Example:** Domain-driven service names (`UserService`, `PaymentGatewayService`,
> `ShippingService`) paired with typed request/response models instead of nested
> untyped maps (`userData["profile"]["info"]["card"]`).

### 4. Simple Design 👌 (Gentle Complexity Curve)

Minimize moving parts; offer high-value primitives without forcing overhead on
standard tasks.

> **Example:** Starting with a well-structured, single-deployable "majestic
> monolith" — organized internally like separate services (clear module
> boundaries) but deployed as one unit until scale actually demands splitting it.

### 5. Scalable Design 🚀 (Decoupled & Asynchronous)

Capabilities scale horizontally by decoupling long-running work from the
synchronous request/response loop.

> **Example:** Offloading slow operations (PDF generation, email) to a background
> worker/task queue so API endpoints return instantly (e.g. HTTP `202 Accepted`)
> instead of blocking the caller. See [Background Work & Task Queues](#background-work--task-queues) below.

### 6. Consistent Design 🔄 (Uniform Conventions)

API conventions, response envelopes, error structures, and domain models follow
predictable standards system-wide.

> **Example:** Standardized paths (`GET /api/v1/products/`), noun conventions, and
> uniform JSON error wrappers across all services.

---

## Integration Patterns

These build directly on [Abstract vs. Implementation](./coding-principles-detailed.md#abstract-vs-implementation-)
— applied to how whole components are wired together, not just individual classes.

### Pattern 1: Dependency Injection (DI)

Inject dependencies via constructors/parameters rather than hardcoding
instantiation inside a class. The class declares what it needs; the application's
entry point decides what concrete implementation to hand it.

### Pattern 2: Immutable Event-Driven Decoupling

Use frozen, read-only data structures for event communication across service
boundaries. An event represents a fact that already happened — it should never be
mutable, so nothing downstream can corrupt what an upstream component already
observed. Pair this with a message broker/event bus and independent consumers to
fully decouple producers from consumers (if the email consumer is down, order
placement still succeeds).

### Pattern 3: Facade Pattern

A single, simplified gateway over a complex, multi-service subsystem — client code
calls one method; the facade internally coordinates however many collaborators
that requires.

### Pattern 4: Isolating Third-Party Libraries (Adapter)

Never let core business logic depend directly on a third-party library or SDK —
wrap it behind an adapter implementing your own interface. This isolates change
(swapping one payment provider for another touches one file), keeps tests fast
(fake your interface, not the vendor SDK), and prevents the vendor's API quirks
from leaking into business logic.

> Concrete code for all four patterns: [Python](../python/architecture-guide-detailed.md#integration-patterns-di-events--facade-) ·
> [TypeScript](../typescript/architecture-guide-detailed.md) ·
> [C++](../cpp/architecture-guide-detailed.md)

---

## Data Flow Strategy 🗺️

Charting the journey of information — from origin, through processing, to its
final destination — is critical for:

- **Clarity & debugging** — trace invalid states backward to find the exact corruption point.
- **Security boundaries 🔒** — identify where sensitive data (passwords, PII) crosses trust boundaries and needs sanitization/hashing.
- **Validation** — enforce schemas at system edges to protect core business logic from malformed payloads.

### User Registration Data Flow (step by step)

A worked example that shows the pattern — every non-trivial flow through a system
should be traceable this concretely:

1. **Origin (client):** password in plaintext memory, sent over HTTPS (encrypted in transit).
2. **API Gateway / edge:** TLS terminates; the raw payload is forwarded to the app server.
3. **Validation layer:** deserialized and validated against a schema; fails fast if invalid.
4. **Service layer:** password undergoes irreversible one-way hashing (Argon2id is the current top recommendation; bcrypt is an acceptable alternative); plaintext discarded.
5. **Data access layer:** email and password hash persisted — plaintext password never touches storage.

> Concrete code: [Python](../python/architecture-guide-detailed.md#data-flow-strategy-) ·
> [TypeScript](../typescript/architecture-guide-detailed.md) ·
> [C++](../cpp/architecture-guide-detailed.md)

---

## Designing for Testability

Design the architecture to be testable from the start — dependency injection,
separation of concerns, and abstracting external services (all covered above) are
what make fast, isolated unit tests possible in the first place. If a component is
hard to test, that's a design signal, not a testing problem — see the
[Testing Principles guide](./testing-principles-detailed.md#hard-to-write-unit-tests--code-design-flaws)
for the diagnosis table.

### A Practical Workflow for a New Feature 🔴🟢🔵 (TDD-Style)

1. **Design the API contract.** Decide the endpoint/interface, its inputs, and its success response *before* writing any implementation.
2. **Write a failing integration test (RED).** Target the contract directly — it fails because the implementation doesn't exist yet.
3. **Write implementation code & unit tests (GREEN).** Build the components. Write fast **unit tests** for the internal logic. Once every piece is in place, the integration test passes too.
4. **Refactor (BLUE).** Clean up the implementation with the safety net of passing tests.

This loop keeps the design decision (the contract) separate from implementation
detail, and forces every new feature to be verifiably testable before it's
considered done.

---

## Design Documents: HLD & LLD 🗺️📜

Designing before implementing prevents structural flaws, reduces technical debt,
and aligns teams — and neither document is tied to any particular language.

### Mental Model: Building a House 🏠

- **High-Level Design (HLD):** the **architect's blueprint** — the whole building,
  room layout, how major utilities connect, how it fits the site. Audience:
  architects, team leads, PMs, clients.
- **Low-Level Design (LLD):** the **construction plan for a single room** — exact
  wall studs, wiring, screw types, paint codes. Audience: the developers
  implementing that module.

### High-Level Design (HLD)

#### 1. Requirements

- **Functional (FRs):** capabilities the system must perform (e.g. "must allow users to upload profile photos").
- **Non-Functional (NFRs):** system qualities/constraints (e.g. "must process 1,000 uploads/sec"; "p99 latency < 200ms"). HLD choices are driven by NFRs.

#### 2. Static View (system at rest)

- **Block diagrams:** major services (API Gateway, User Service, Notification Service, Database) and connection lines.
- **Components & modules:** structured listing of each service, its responsibility, and exposed interfaces.
- **Directory map:** the annotated repository tree — every file and what is inside it. The block diagram says how the system is *shaped*; the directory map says which file to *open*, and a newcomer needs both. "Auth Service" does not tell anyone whether the token logic is in `auth/tokens.py` or `middleware/session.py`.
  > Generate this map and fail CI on drift, or don't ship one — a stale directory map costs a reader far more than a missing one, and destroys their trust in every other document. Full reasoning, and the generated-vs-written split, in [documentation principles](./documentation-principles-detailed.md#2-why-the-directory-map-is-separate-).

#### 3. Dynamic View (system in motion)

- **Data Flow Diagrams / flowcharts:** end-to-end trace of key use cases.
- **Sequence diagrams:** inter-service call chains and payload movement, chronologically.
- **UML state / activity diagrams:** state transitions for complex domain entities.

#### 4. Data Storage Strategy

- **A. Primary Data Store** — declare the *type* of database and reasoning. For structured, transactional data, a relational (SQL) database gives ACID guarantees when run on a transactional engine at an appropriate isolation level. Access is through an ORM/query builder to keep raw queries out of business logic.
  > **Caveat:** "SQL" doesn't automatically mean ACID — it depends on the engine and isolation level. Confirm both; don't assume from the word "relational" alone.
- **B. Caching Layer** — an in-memory store (Redis or equivalent) to cut latency and DB load. Cache *categories* of data (sessions, rarely-changing settings, expensive query results), not specific keys, using a **cache-aside** strategy.
- **C. Blob Storage (unstructured data)** — large binary files (images, videos, docs) go to object storage (S3/GCS or equivalent), never the relational DB. The primary DB stores only a reference key/URL.
- **D. Backup & Disaster Recovery** — automated backups, **Point-in-Time Recovery** (e.g. 7-day retention), and **read replicas** in a separate availability zone for rapid failover.

#### 5. Configuration Management Strategy

**Source priority (highest → lowest):**

1. **Secrets Manager** (AWS Secrets Manager, Vault) — production runtime secrets.
2. **Environment variables** — set by the container/orchestrator (12-Factor App); overrides local config files.
3. **Local `.env` / config file** — developer convenience, strictly git-ignored.
4. **Static config files** (checked into version control) — non-sensitive static settings.
5. **Default values** — hardcoded fallbacks (lowest priority).

**Key principles:**

- Active environment set via a single variable (`development`/`staging`/`production`) so one build artifact promotes across environments unchanged.
- Zero credentials in version control; production secrets fetched via IAM/runtime roles.
- Fail-fast validation at startup using a strongly-typed schema — the process should refuse to start with invalid or missing configuration, not fail confusingly later at first use.

**Configuration Flow:** App startup triggers a central Settings object that pulls
from sources in priority order → validation gatekeeper aborts startup on failure →
an immutable, validated config instance is available globally once running.

#### 6. Data Validation & I/O Strategy

- **System boundary protection:** rigorous schema verification at the edge, before payloads touch business domains.
- **Standardized formats:** a consistent serialization format (JSON is the default choice for most APIs), a consistent field-naming convention, and strict UTC ISO-8601 timestamps.
- **Critical transformations:** inbound password hashing (Argon2id preferred; bcrypt an acceptable alternative), data masking/anonymization before storage or logging.
- **Payload management:** pagination (cursor vs. limit/offset) to cap memory usage and network transfer.

#### 7. Integration Test Strategy

High-level verification plans validating inter-component contracts (e.g. confirming
`OrderService` correctly calls `PaymentGateway.charge()`).

### Low-Level Design (LLD)

Zooms into a **single component**, giving developers actionable implementation
details without further architectural decisions.

1. **Static View — Class/Interface Diagrams & Method Signatures.** Public interfaces, attributes, method signatures, access modifiers.

   ```text
   interface UserRepository:
       findByEmail(email: string) -> User | null
       save(user: User) -> User

   interface PasswordHasher:
       hash(password: string) -> string
       verify(password: string, hashed: string) -> bool

   class UserService:
       constructor(repo: UserRepository, hasher: PasswordHasher)
       registerUser(email: string, plaintextPassword: string) -> User
           # Registers a new user after validating input and business rules.
   ```

2. **Dynamic View — Pseudocode, Flowcharts & State Diagrams.** Solves algorithmic complexity and edge cases before coding.

   **`UserService.registerUser` logic:**
   1. Input `(email, password)`.
   2. Password strong enough? No → raise `InvalidPasswordError`, end.
   3. `UserRepository.findByEmail(email)`.
   4. User exists? Yes → raise `UserAlreadyExistsError`, end.
   5. `PasswordHasher.hash(password)` → `hashedPassword`.
   6. Construct `User` entity.
   7. `UserRepository.save(user)` → `savedUser`.
   8. Return `savedUser`.

   **`User` entity state diagram:**
   `[Unverified] --(verification link)--> [Verified] --(admin locks)--> [Disabled] --(admin unlocks)--> [Verified]`

3. **I/O Data Schemas** — unambiguous request/response contracts.

   ```jsonc
   // POST /users (request)
   { "email": "user@example.com", "password": "SecurePassword123!" }

   // GET /users/{id} (response)
   { "id": 101, "email": "user@example.com", "createdAt": "2026-08-17T00:35:00Z" }
   ```

4. **Component Configuration Keys** — e.g. for a Postgres-backed `UserRepository`: `DATABASE_URL` (required), `DB_POOL_SIZE` (default 5), `DB_CONNECT_TIMEOUT` (default 10s).

5. **Integration & Concrete DI Wiring** — how constructor dependencies are instantiated and passed at the application's entry point.

6. **Error Contracts & Custom Exception Hierarchy** — e.g. `UserAlreadyExistsError`, `InvalidPasswordError`.

7. **Structured Observability (Logs Plan):**
   - `INFO`: "Attempting to register new user with email: {email}" — at method start.
   - `INFO`: "Successfully registered new user with id: {newUserId}" — at completion.
   - `WARNING`: "Registration attempt for existing email: {email}" — on duplicate.

8. **Unit Test Plan (AAA & Mocking)** — e.g. `test_registerUser_success`, `test_registerUser_raisesError_whenEmailExists`, `test_registerUser_hashesPassword_beforeSaving`. See the [Testing Principles guide](./testing-principles-detailed.md).

> Concrete code for all 8 parts: [Python](../python/architecture-guide-detailed.md#design-documents-hld--lld-) ·
> [TypeScript](../typescript/architecture-guide-detailed.md) ·
> [C++](../cpp/architecture-guide-detailed.md)

### Relationship Summary: HLD vs. LLD

| Aspect | High-Level Design (HLD) | Low-Level Design (LLD) |
|---|---|---|
| **Scope** | Entire system/application architecture | A single module or component |
| **Audience** | Architects, team leads, PMs, clients | Developers, code reviewers |
| **Focus** | System structure, service interaction, NFRs | Internal logic, classes, methods, data schemas |
| **Primary output** | Block diagrams, sequence diagrams, DFDs | Class diagrams, pseudocode, unit test plans |
| **Testing plan** | Integration & E2E test strategy | Unit test plan (AAA & mocking) |
| **Goal** | Architectural soundness & scalability | Correct, clean, maintainable code |

---

## Design Patterns & Anti-Patterns 💡

### Creational

- **Factory Method** — defines an interface for object creation, letting subclasses decide which class to instantiate.
- **Singleton** — ensures a class has only one instance and a global access point.
- **Builder** — constructs complex objects step by step, separating construction from representation.

### Structural

- **Adapter** — translates an incompatible interface into what the client expects.
- **Decorator** — dynamically adds behavior without altering structure.
- **Facade** — simplified interface over a complex subsystem.

### Behavioral

- **Observer** — one-to-many subscription; notifies dependents on state change.
- **Strategy** — encapsulates interchangeable algorithms.
- **Template Method** — defines an algorithm's skeleton in a base class, deferring steps to subclasses.

### Anti-Patterns 🚫

| Anti-pattern | Description |
|---|---|
| **God Object / God Class** | A class that knows or does too much — violates SRP. |
| **Spaghetti Code** | Tangled control flow, deep nesting, unstructured jumps. |
| **Lava Flow** | Dead/obsolete code kept out of fear of breaking unknown dependents. |
| **Boat Anchor** | Useless legacy components kept for political/financial reasons. |

---

## Operational Logging & Centralized Error Strategy ☁️

### Centralized Error Handling 🛡️

Handle errors globally at application boundaries via middleware — keep the
business logic on the happy path, with no `try`/`catch` boilerplate scattered
through every handler.

Create **custom, semantic exceptions** (`InsufficientStockError`, not a bare
generic error type) so the centralized handler knows exactly how to respond, and
callers stay free of defensive error-handling blocks.

> Concrete code: [Python](../python/architecture-guide-detailed.md#operational-logging--centralized-error-strategy-) ·
> [TypeScript](../typescript/architecture-guide-detailed.md) ·
> [C++](../cpp/architecture-guide-detailed.md)

### Structured Contextual Logging (JSON) ⚙️

**The 3 pillars:**

1. **What to log (context):** levels (`DEBUG`/`INFO`/`WARNING`/`ERROR`) plus key-value
   bindings (a request ID, a user ID, an entity ID). Never log PII or credentials.
2. **Where to log (centralization):** stream to stdout in production, aggregate
   centrally (Datadog, ELK, CloudWatch) — never write to ephemeral local files.
3. **How to log (structure):** machine-readable JSON (or an equivalent structured
   format) for instant filtering/querying.

**Log levels:**

| Level | Meaning |
|---|---|
| `DEBUG` | Highly detailed development info — disabled in production. |
| `INFO` | Routine events/milestones — app behaving as expected. |
| `WARNING` | Unexpected but recoverable, non-critical event. |
| `ERROR` | Critical failure that prevented an operation — should trigger alerts. |

---

## Security Fundamentals 🔒

Security is a cross-cutting concern enforced at boundaries — the same theme as
centralized error handling and I/O validation above, applied to authentication,
authorization, and injection prevention.

### Authentication vs. Authorization

- **Authentication (AuthN)** — *who are you?* Verifies identity. Two common shapes:
  - **Session-based** — server-side session store, opaque cookie on the client. Easy to revoke; requires server state.
  - **Token-based (JWT)** — stateless, self-contained token. Scales easily, but revocation is hard (the token is valid until it expires) — mitigate with **short-lived access tokens** (minutes) plus a **refresh token** flow.
- **Authorization (AuthZ)** — *what are you allowed to do?* Checked *after* authentication, typically **role-based (RBAC)** or **policy/attribute-based (ABAC)**.

### Enforce Authorization at the Boundary, Not in Business Logic

Same principle as centralized error handling: authorization checks belong in
middleware/interceptors, not scattered through service methods.

### Injection Prevention

Never build queries (or shell commands, or file paths) by string-formatting
untrusted input:

```text
# ❌ Classic injection — untrusted input concatenated straight into a query/command.
query = "SELECT * FROM users WHERE email = '" + email + "'"

# ✅ Parameterized queries (or an ORM/query builder, which does this for you automatically).
query("SELECT * FROM users WHERE email = ?", [email])
```

> Concrete code: [Python](../python/architecture-guide-detailed.md#security-fundamentals-) ·
> [TypeScript](../typescript/architecture-guide-detailed.md) ·
> [C++](../cpp/architecture-guide-detailed.md)

### A Working Checklist (OWASP Top 10, Condensed)

| Category | Guard against it by… |
|---|---|
| Broken Access Control | Centralized authZ checks at the boundary (above); never trust client-supplied role/permission claims alone. |
| Injection | Parameterized queries/ORM; schema validation at the edge. |
| Cryptographic Failures | TLS everywhere; Argon2id/bcrypt for passwords; never hand-roll crypto. |
| Security Misconfiguration | Fail-closed defaults; no debug mode in production; secrets never in version control. |
| Vulnerable & Outdated Components | Automated dependency scanning in CI. |
| Identification & AuthN Failures | Rate-limit login/auth endpoints; short-lived tokens; MFA where the product supports it. |

### Transport & Rate Limiting

- **HTTPS/TLS everywhere** — including internal service-to-service calls where feasible; enable HSTS on public endpoints.
- **Rate limit** public and authentication endpoints to blunt brute-force and credential-stuffing attempts — enforce this at the API Gateway/edge so every route is covered by default, not opt-in per endpoint.

---

## CI/CD, Deployment & Observability 🚀📈

### Pipeline Stages

A typical pipeline, each stage gating the next:

1. **Lint & type-check** — fail fast on style/type errors before anything else runs.
2. **Unit tests** — fast, isolated, run on every commit/PR.
3. **Build** — build the deployable artifact/image, tag it with the commit SHA (not `latest`).
4. **Integration tests** — run against the built artifact plus real service dependencies (test DB, etc.).
5. **Deploy to staging** — automatic on merge to the main branch.
6. **Smoke / E2E tests** — a small, critical-path suite against staging.
7. **Promote to production** — manual approval or an automated canary/blue-green rollout, with automatic rollback on an error-rate or health-check regression.

### Containerization Basics

Key rules, regardless of language: pin the base image version, run as a
**non-root user**, keep the build toolchain out of the final image (multi-stage
build), and ignore secrets/local caches from the build context so they never end
up baked into the image.

### Database Migrations

Managed by a dedicated migration tool, run as an explicit pipeline step — never
applied by hand against production.

> **Expand–contract pattern for zero-downtime schema changes:** add the new
> column/table (*expand*) → deploy code that writes to both old and new → backfill
> existing rows → deploy code that reads only from the new shape → drop the old
> column in a later migration (*contract*). Never remove a column in the same
> deploy that stops using it — old and new code may run side-by-side briefly
> during a rolling deploy.

### Observability Beyond Logging

Structured logging (above) is one of three pillars — the other two:

- **Metrics** — aggregate, queryable numbers. The **RED method** (Rate, Errors,
  Duration) is a solid default for a service.
- **Tracing** — follows one request across service boundaries, correlated by a
  trace/span ID (the distributed-systems extension of the request ID already used
  in structured logging).
- **Health checks** — liveness and readiness are different questions; conflating
  them causes orchestrators to kill healthy instances that are merely waiting on a
  slow dependency. A **liveness** check answers "is the process alive?" with no
  dependency checks; a **readiness** check answers "am I ready for traffic?" by
  checking the dependencies the service actually needs.

> Concrete code (Dockerfile, metrics, tracing, health checks): [Python](../python/architecture-guide-detailed.md#cicd-deployment--observability-) ·
> [TypeScript](../typescript/architecture-guide-detailed.md) ·
> [C++](../cpp/architecture-guide-detailed.md)

---

## Background Work & Task Queues

The concrete extension of [Scalable Design](#5-scalable-design--decoupled--asynchronous)
above: offload slow, resource-intensive operations (thumbnail generation, CSV
import, PDF generation) so the main request/response cycle isn't blocked. The
principles that transfer across every queue technology (Celery, BullMQ, a
thread-pool-backed job runner, or anything else):

- **Pass identifiers, not objects.** Queues typically serialize messages (often as JSON); complex objects don't serialize well, and the underlying record may have changed by the time a worker picks the job up. Pass an ID and let the worker re-fetch current state.
- **Idempotency.** A task must be safe to run more than once — at-least-once delivery is the norm for most queue systems, so a task that isn't idempotent will eventually double-apply.
- **Resilience & retries.** Configure automatic retries with backoff for transient failures (a downstream service being briefly unavailable), and route non-retryable failures to a dead-letter queue for inspection instead of retrying forever.
- **Structured logging per task**, following the same 3 pillars as request logging — bind a job ID to every log line for a task so its whole lifecycle is traceable.

> Concrete code: [Python](../python/architecture-guide-detailed.md#background-tasks-celery) ·
> [TypeScript](../typescript/architecture-guide-detailed.md) ·
> [C++](../cpp/architecture-guide-detailed.md)

---

## Software Engineering Rules

1. Write clean, understandable code.
2. Use version control (Git); commit frequently with clear messages.
3. Write tests — unit, integration, end-to-end.
4. Practice code review to catch bugs, improve quality, share knowledge.
5. Document code, APIs, and system architecture.
6. Apply rigor and formality — a systematic, disciplined approach.
7. Separate concerns — divide systems into distinct, modular parts.
8. Anticipate change — design for flexibility and extensibility.
9. Emphasize design — invest in HLD/LLD before writing code; architectural flaws are far costlier to fix than code bugs.
10. Act in the public interest — uphold ethics, security, and privacy.

---

## What Is a "Component"?

Conceptually, a component is a modular, often independently deployable/replaceable
part of a system that encapsulates its internals and exposes a well-defined
interface with a clear responsibility. How this maps onto code varies by language,
but the shape is universal:

- **A single class** — for narrow responsibilities, its public methods are the interface.
- **A module/package/namespace (very common)** — for non-trivial complexity, a group of related internal files behind one public entry point. Internal files are "private" implementation details; the public interface is whatever the entry point explicitly re-exports.
- **A main class within a module** — a primary entry-point/facade class relying on sibling helper files; the *module* is still the component, not any single class inside it.

> How each language expresses this: [Python](../python/architecture-guide-detailed.md#what-is-a-component-in-python) —
> a package with `__init__.py` · [TypeScript](../typescript/architecture-guide-detailed.md) —
> a module with a barrel `index.ts` · [C++](../cpp/architecture-guide-detailed.md) —
> a namespace or a library target.

---

## Core Engineering Acronyms Reference 📜

| Acronym | Full Form | Core Focus |
|---|---|---|
| **KISS** | Keep It Simple, Stupid | Avoid unnecessary design complexity. |
| **DRY** | Don't Repeat Yourself | Abstract duplicate logic into reusable modules. |
| **YAGNI** | You Ain't Gonna Need It | Don't build unrequested future capabilities. |
| **SOLID** | OO Design Principles | Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion. |
| **SLAP** | Single Level of Abstraction Principle | Keep statements in a method at the same detail level. |
| **LoD** | Law of Demeter | Avoid chaining calls across distant objects ("don't talk to strangers"). |
| **CQS** | Command-Query Separation | Separate state mutation (command) from data querying (query). |
| **CI/CD** | Continuous Integration / Deployment | Automate build, test, and release pipelines. |
| **TDD/BDD** | Test/Behavior Driven Development | Write tests or behavior specs before execution code. |
| **CRUD** | Create, Read, Update, Delete | Basic persistence lifecycle operations. |
| **ACID** | Atomicity, Consistency, Isolation, Durability | Relational DB transaction integrity guarantees. |
| **BASE** | Basically Available, Soft state, Eventually consistent | Distributed-systems alternative to ACID (often NoSQL); favors availability over immediate consistency. |
| **HLD** | High-Level Design | Overall architecture and inter-component design. |
| **LLD** | Low-Level Design | Detailed internal class, method, and schema design. |
