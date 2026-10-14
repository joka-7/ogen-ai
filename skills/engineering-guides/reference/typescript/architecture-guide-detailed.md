# TypeScript — Architecture & Framework Design Guide (Detailed)

Higher-level system architecture, boundaries, HLD/LLD design documents, design
patterns, and operational standards — in framework-agnostic TypeScript. The
patterns below apply whether you're building on Express, NestJS, Fastify, or a
custom HTTP layer; nothing here is tied to a specific framework. For the
condensed version, see [architecture-guide-short.md](./architecture-guide-short.md).

> **This guide assumes the [General Architecture Principles](../general/architecture-principles-detailed.md)** —
> it shows how those language-agnostic concepts look in TypeScript. Read that
> first for the "why"; this guide is the "how, in TypeScript."

> Related TypeScript guides: [Coding Guide](./coding-guide-detailed.md) ·
> [Testing Guide](./testing-guide-detailed.md)

## Table of Contents

1. [Design Principles at the System Level](#design-principles-at-the-system-level)
2. [Abstract vs. Implementation 🔌](#abstract-vs-implementation-)
3. [Data Flow Strategy 🗺️](#data-flow-strategy-)
4. [Integration Patterns: DI, Events & Facade 🔌🚪](#integration-patterns-di-events--facade-)
5. [Designing for Testability](#designing-for-testability)
6. [Design Documents: HLD & LLD 🗺️📜](#design-documents-hld--lld-)
7. [Design Patterns & Anti-Patterns 💡](#design-patterns--anti-patterns-)
8. [Operational Logging & Centralized Error Strategy ☁️](#operational-logging--centralized-error-strategy-)
9. [Security Fundamentals 🔒](#security-fundamentals-)
10. [CI/CD, Deployment & Observability 🚀📈](#cicd-deployment--observability-)
11. [Background Work & Task Queues](#background-work--task-queues)
12. [Software Engineering Rules](#software-engineering-rules)
13. [What Is a "Component" in TypeScript?](#what-is-a-component-in-typescript)
14. [Core Engineering Acronyms Reference 📜](#core-engineering-acronyms-reference-)

---

## Design Principles at the System Level

The [general architecture principles](../general/architecture-principles-detailed.md#design-principles-at-the-system-level)
as they typically show up in a TypeScript stack:

| Principle | In a TypeScript stack |
|---|---|
| **Beautiful ✨** | A router that maps a declarative route table to handler modules — adding a route is one entry, no framework internals touched. |
| **Explicit 🎯** | A composition root (`main.ts`/`bootstrap.ts`) constructs concrete repositories and injects them into services via their constructors — no decorator-driven auto-wiring magic to trace through. |
| **Readable 📖** | Domain-driven service names (`UserService`, `PaymentGatewayService`) with typed request/response interfaces instead of `Record<string, unknown>`. |
| **Simple 👌** | A single `server.ts` with a handful of routes, split into modules only once a folder actually gets unwieldy. |
| **Scalable 🚀** | Slow work (PDF generation, email) handed off to a background job queue so the HTTP handler returns immediately. |
| **Consistent 🔄** | Standardized paths (`GET /api/v1/products`), consistent JSON envelopes, and one error-response shape across every route. |

---

## Abstract vs. Implementation 🔌

TypeScript's shape for the [general abstract-vs-implementation principle](../general/coding-principles-detailed.md#abstract-vs-implementation-):
an `interface` as the contract, concrete classes as the implementations.

```typescript
// 1. The Abstract Part (interfaces.ts)
export interface Notifier {
  send(recipient: string, message: string): Promise<boolean>;
}

// 2. The Implementation Part (providers.ts)
export class EmailNotifier implements Notifier {
  async send(recipient: string, message: string): Promise<boolean> {
    console.log(`Sending SMTP email to ${recipient}: ${message}`);
    return true;
  }
}

export class SmsNotifier implements Notifier {
  async send(recipient: string, message: string): Promise<boolean> {
    console.log(`Sending Twilio SMS to ${recipient}: ${message}`);
    return true;
  }
}

export class LogNotifier implements Notifier {
  async send(recipient: string, message: string): Promise<boolean> {
    console.log(`LOG ONLY -> ${recipient}: ${message}`);
    return true;
  }
}

// 3. Business Logic depending on Abstraction (register-user.ts)
export async function registerNewUser(
  userData: { email: string },
  notifier: Notifier,
): Promise<void> {
  console.log(`Creating user ${userData.email}...`);
  await notifier.send(userData.email, "Welcome!");
}

// 4. Application Assembly Entry Point (main.ts)
const notifier: Notifier =
  process.env.NODE_ENV === "development" ? new LogNotifier() : new EmailNotifier();

registerNewUser({ email: "alice@example.com" }, notifier);
```

---

## Data Flow Strategy 🗺️

The [general data flow strategy](../general/architecture-principles-detailed.md#data-flow-strategy-)
worked through a TypeScript stack (framework-agnostic — `HttpRequest`/`HttpResponse`
stand in for whatever router you use):

### User Registration Data Flow (step by step)

1. **Origin (client):** password in plaintext memory, sent over HTTPS.
2. **Edge / reverse proxy:** TLS terminates; raw JSON forwarded to the app.
3. **Validation layer:** parsed and validated against a schema (e.g. Zod); fails fast if invalid.
4. **Service layer:** password undergoes irreversible one-way hashing (Argon2id, via `argon2`); plaintext discarded.
5. **Data access layer:** email and password hash persisted — plaintext password never touches storage.

```typescript
// schemas.ts — Step 3: Validation Layer
import { z } from "zod";

export const UserRegistrationSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});
export type UserRegistrationInput = z.infer<typeof UserRegistrationSchema>;

// user-repository.ts — Step 5: Data Access Layer
export interface User {
  id: string;
  email: string;
  passwordHash: string;
  createdAt: Date;
}

export interface UserRepository {
  create(email: string, passwordHash: string): Promise<User>;
}

export class PostgresUserRepository implements UserRepository {
  async create(email: string, passwordHash: string): Promise<User> {
    // Direct database interaction is isolated here (e.g. via a query builder/ORM).
    return { id: crypto.randomUUID(), email, passwordHash, createdAt: new Date() };
  }
}

// user-service.ts — Step 4: Business Logic Layer
import * as argon2 from "argon2";

export class UserService {
  constructor(private readonly repo: UserRepository) {}

  async registerUser(input: UserRegistrationInput): Promise<User> {
    const passwordHash = await argon2.hash(input.password); // Argon2id by default
    return this.repo.create(input.email, passwordHash);
  }
}
```

---

## Integration Patterns: DI, Events & Facade 🔌🚪

### Pattern 1: Dependency Injection (DI)

Inject dependencies via constructors rather than instantiating them inside a class.

```typescript
export class RegistrationService {
  constructor(
    private readonly notifier: Notifier,
    private readonly workspaceSvc: WorkspaceService,
  ) {}

  async registerUser(email: string): Promise<void> {
    const userId = "123";
    await this.notifier.send(email, "Welcome!");
    await this.workspaceSvc.createDefaultWorkspace(userId);
  }
}
```

### Pattern 2: Immutable Event-Driven Decoupling

`readonly` event interfaces for cross-boundary communication.

```typescript
export interface OrderPlacedEvent {
  readonly orderId: string;
  readonly userId: string;
  readonly totalAmount: number;
}

function handleAnalytics(event: OrderPlacedEvent): void {
  // event.totalAmount = 0;  // ❌ compile error — readonly enforced statically
  console.log(`Analytics updated for order ${event.orderId}`);
}
```

### Pattern 3: Facade Pattern

A single, simplified gateway over a complex, multi-service subsystem.

```typescript
export class NotificationFacade {
  constructor(
    private readonly templateMgr: TemplateManager,
    private readonly emailGw: EmailGateway,
    private readonly userSvc: UserProfileService,
  ) {}

  async sendWelcome(email: string): Promise<void> {
    const name = await this.userSvc.getUserName(email);
    const template = await this.templateMgr.getTemplate("welcome");
    const body = template.replace("{{name}}", name);
    await this.emailGw.send(email, "Welcome!", body);
  }
}
```

### Isolating Third-Party Libraries (Adapter)

Wrap a third-party SDK behind your own interface — only the adapter module ever
imports the vendor library.

```typescript
// payment-gateway.ts — your application's generic contract
export interface PaymentGateway {
  charge(amountCents: number, token: string): Promise<string>; // returns transaction ID
}

export class PaymentDeclinedError extends Error {}

// adapters/stripe-gateway.ts — the only file that imports the Stripe SDK
import Stripe from "stripe";
import { PaymentGateway, PaymentDeclinedError } from "../payment-gateway";

export class StripeGateway implements PaymentGateway {
  private readonly stripe: Stripe;

  constructor(apiKey: string) {
    this.stripe = new Stripe(apiKey);
  }

  async charge(amountCents: number, token: string): Promise<string> {
    try {
      // PaymentIntents API — Stripe's current recommended flow (the legacy
      // Charges API is deprecated and doesn't support SCA/3-D Secure).
      const intent = await this.stripe.paymentIntents.create({
        amount: amountCents,
        currency: "usd",
        payment_method: token,
        confirm: true,
      });
      return intent.id;
    } catch (err) {
      throw new PaymentDeclinedError(`Card declined by Stripe: ${err}`);
    }
  }
}
```

---

## Designing for Testability

The DI, separation of concerns, and adapter isolation above are what make
TypeScript components testable with Jest/Vitest in the first place — see
[Designing for Testability](../general/architecture-principles-detailed.md#designing-for-testability)
for the RED/GREEN/BLUE workflow and the [Testing Guide](./testing-guide-detailed.md#hard-to-write-unit-tests--code-design-flaws)
for the "hard to test = design flaw" diagnosis table.

---

## Design Documents: HLD & LLD 🗺️📜

The [general HLD/LLD guide](../general/architecture-principles-detailed.md#design-documents-hld--lld-)
covers the concepts in detail. Two TypeScript-specific concretizations:

1. **Static View — Interfaces & Method Signatures.** TypeScript `interface`s as
   contracts, a service class depending only on those interfaces:

   ```typescript
   // interfaces.ts
   export interface UserRepository {
     findByEmail(email: string): Promise<User | null>;
     save(user: User): Promise<User>;
   }

   export interface PasswordHasher {
     hash(password: string): Promise<string>;
     verify(password: string, hashed: string): Promise<boolean>;
   }

   // user-service.ts
   export class UserService {
     constructor(
       private readonly repo: UserRepository,
       private readonly hasher: PasswordHasher,
     ) {}

     async registerUser(email: string, plaintextPassword: string): Promise<User> {
       // Registers a new user after validating input and business rules.
       throw new Error("not implemented");
     }
   }
   ```

2. **Integration & Concrete DI Wiring** — how the interfaces above get concrete
   implementations at the application's composition root:

   ```typescript
   const userRepository = new PostgresUserRepository(config.databaseUrl);
   const passwordHasher = new Argon2PasswordHasher();
   const userService = new UserService(userRepository, passwordHasher);
   ```

The remaining parts of the LLD checklist (dynamic view/pseudocode, I/O schemas,
config keys, error contracts, logging plan, unit test plan) follow the same shape
shown in the [general guide's worked example](../general/architecture-principles-detailed.md#design-documents-hld--lld-).

---

## Design Patterns & Anti-Patterns 💡

The [general design patterns & anti-patterns reference](../general/architecture-principles-detailed.md#design-patterns--anti-patterns-)
applies as-is — none of it is TypeScript-specific. TypeScript examples of several
already appear above: [Facade](#pattern-3-facade-pattern), [Adapter](#isolating-third-party-libraries-adapter).

---

## Operational Logging & Centralized Error Strategy ☁️

### Centralized Error Handling 🛡️

A base `AppError` hierarchy plus one error-handling layer at the boundary — the
exact framework hook varies (Express error middleware, a NestJS exception filter,
a Fastify error handler), but the shape is identical:

```typescript
// errors.ts
export abstract class AppError extends Error {
  abstract readonly statusCode: number;
}

export class ResourceNotFoundError extends AppError {
  readonly statusCode = 404;
  constructor(resourceName: string, resourceId: string) {
    super(`${resourceName} with ID '${resourceId}' was not found.`);
  }
}

export class PermissionDeniedError extends AppError {
  readonly statusCode = 403;
  constructor() {
    super("Action not permitted.");
  }
}

// error-handler.ts — framework-agnostic shape; wire this into whatever
// error-handling hook your HTTP layer provides.
export function toErrorResponse(err: unknown): { statusCode: number; body: object } {
  if (err instanceof AppError) {
    return { statusCode: err.statusCode, body: { error: err.name, detail: err.message } };
  }
  return { statusCode: 500, body: { error: "InternalServerError" } };
}

// handlers/get-user.ts — clean handler, no try/catch boilerplate
export async function getUserHandler(userId: string): Promise<User> {
  const user = await userService.getUserById(userId); // throws ResourceNotFoundError
  return user;
}
```

Create **custom, semantic error classes** (`InsufficientStockError`, not a bare
`Error`) so the centralized handler knows exactly how to respond.

### Structured Contextual Logging (JSON) ⚙️

The [3 pillars of structured logging](../general/architecture-principles-detailed.md#operational-logging--centralized-error-strategy-)
via `pino` (a fast, structured-JSON-native Node logger) with request-scoped context:

```typescript
import pino from "pino";
import { randomUUID } from "node:crypto";
import { AsyncLocalStorage } from "node:async_hooks";

const logger = pino();
const requestContext = new AsyncLocalStorage<{ requestId: string }>();

// middleware.ts — framework-agnostic shape: wrap each request in a context scope.
export function withRequestContext<T>(fn: () => T): T {
  return requestContext.run({ requestId: randomUUID() }, fn);
}

export class OrderService {
  placeOrder(userId: string, itemCount: number): void {
    const ctx = requestContext.getStore();
    logger.info({ userId, itemCount, requestId: ctx?.requestId }, "Order placement initiated");
  }
}
```

```json
{
  "level": "info",
  "time": "2026-08-17T00:35:00.000Z",
  "userId": "42",
  "itemCount": 3,
  "requestId": "req-987a-654b",
  "msg": "Order placement initiated"
}
```

**Log levels:** `debug` (dev only) → `info` (routine) → `warn` (recoverable) →
`error` (alertable failure) — the same 4-level shape as the
[general logging guidance](../general/architecture-principles-detailed.md#operational-logging--centralized-error-strategy-).

---

## Security Fundamentals 🔒

The [general security fundamentals](../general/architecture-principles-detailed.md#security-fundamentals-)
(AuthN vs. AuthZ, the OWASP Top 10 checklist, transport/rate-limiting) apply as-is.
One TypeScript-specific concretization:

### Enforce Authorization at the Boundary, Not in Business Logic

```typescript
// A framework-agnostic authorization guard — adapt to your router's middleware shape.
export function requireRole(requiredRole: string) {
  return (currentUser: { roles: string[] }): void => {
    if (!currentUser.roles.includes(requiredRole)) {
      throw new PermissionDeniedError();
    }
  };
}

// Usage in a handler:
export async function deleteUserHandler(userId: string, currentUser: AuthUser): Promise<void> {
  requireRole("admin")(currentUser);
  await userService.deleteUser(userId);
}
```

### Injection Prevention

```typescript
// ❌ Classic SQL injection — untrusted input concatenated straight into the query.
const rows = await db.query(`SELECT * FROM users WHERE email = '${email}'`);

// ✅ Parameterized queries (or an ORM/query builder, which does this automatically).
const rows = await db.query("SELECT * FROM users WHERE email = $1", [email]);
```

The CI-stage dependency scanning the OWASP checklist references is `npm audit`
(or Snyk/Dependabot) for this ecosystem.

---

## CI/CD, Deployment & Observability 🚀📈

The [general pipeline stages](../general/architecture-principles-detailed.md#cicd-deployment--observability-)
apply unchanged — in TypeScript, stage 1 is `eslint` + `tsc --noEmit`, and stages
2/4/6 are covered in the [Testing Guide](./testing-guide-detailed.md).

### Containerization Basics

```dockerfile
# Dockerfile — multi-stage build: no dev dependencies or TS source shipped to prod.
FROM node:20-slim AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build   # tsc emits to dist/

FROM node:20-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY --from=builder /app/dist ./dist
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser
CMD ["node", "dist/main.js"]
```

Follows the [general containerization rules](../general/architecture-principles-detailed.md#cicd-deployment--observability-)
(pinned base image, non-root user, multi-stage build).

### Database Migrations

Managed by a dedicated tool (Prisma Migrate, Knex, or TypeORM migrations), run as
an explicit pipeline step — never applied by hand against production. Follow the
[expand–contract pattern](../general/architecture-principles-detailed.md#cicd-deployment--observability-)
for zero-downtime schema changes.

### Observability Beyond Logging

The [general observability guidance](../general/architecture-principles-detailed.md#cicd-deployment--observability-)
via `prom-client` and the OpenTelemetry JS SDK:

**Metrics** (RED method):

```typescript
import { Counter, Histogram } from "prom-client";

const requestCount = new Counter({
  name: "http_requests_total",
  help: "Total HTTP requests",
  labelNames: ["method", "path", "status"],
});
const requestLatency = new Histogram({
  name: "http_request_duration_seconds",
  help: "Request latency",
  labelNames: ["path"],
});

// Wrap this around your router's request handling, however that's wired in your framework.
export async function withMetrics(
  method: string,
  path: string,
  handler: () => Promise<{ status: number }>,
): Promise<{ status: number }> {
  const stopTimer = requestLatency.startTimer({ path });
  const response = await handler();
  stopTimer();
  requestCount.inc({ method, path, status: response.status });
  return response;
}
```

**Health checks** (liveness vs. readiness):

```typescript
export async function livenessCheck(): Promise<{ status: string }> {
  return { status: "ok" }; // no dependency checks — just "am I running"
}

export async function readinessCheck(db: { ping(): Promise<void> }): Promise<{ status: string }> {
  try {
    await db.ping();
    return { status: "ready" };
  } catch {
    throw new Error("Database unavailable");
  }
}
```

---

## Background Work & Task Queues

Offload slow, resource-intensive operations (thumbnail generation, CSV import) so
the request/response cycle isn't blocked — commonly with **BullMQ** (Redis-backed)
in the Node ecosystem:

```typescript
// queues/image-queue.ts
import { Queue, Worker } from "bullmq";

interface ImageJobData {
  imageId: string;
  width: number;
  height: number;
}

export const imageQueue = new Queue<ImageJobData>("image-processing");

export const imageWorker = new Worker<ImageJobData>(
  "image-processing",
  async (job) => {
    const { imageId, width, height } = job.data; // pass IDs, not objects
    const imageRecord = await getImageFromDb(imageId);
    await resizeImage(imageRecord.path, width, height);
    await markImageAsProcessed(imageId);
  },
  { attempts: 3, backoff: { type: "exponential", delay: 60_000 } },
);
```

Same principles as any queue system: **pass IDs, not objects**; design tasks to
be **idempotent**; configure **retries with backoff**; **structured logging**
(bind a job ID to every log line for that job's lifecycle).

---

## Software Engineering Rules

Language-agnostic — see the [general 10 rules](../general/architecture-principles-detailed.md#software-engineering-rules).

---

## What Is a "Component" in TypeScript?

The [general "component" concept](../general/architecture-principles-detailed.md#what-is-a-component)
in TypeScript, concretely:

- **A single class** — for narrow responsibilities, its public methods are the interface.
- **A module with a barrel file (very common)** — a directory of related files with an `index.ts` that re-exports only what's meant to be public; everything else is an internal implementation detail.
- **A main class within a module** — a primary entry-point/facade class relying on sibling helper files; the *module* is still the component, not any single class.

---

## Core Engineering Acronyms Reference 📜

Language-agnostic — see the [general acronyms reference](../general/architecture-principles-detailed.md#core-engineering-acronyms-reference-).
