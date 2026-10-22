# TypeScript — Coding Implementation Guide (Detailed)

This is the detailed reference for writing clean, readable, and maintainable
TypeScript code at the line-by-line, function, and class level. Framework-agnostic —
applies whether the code runs in Node, a browser, or an edge runtime. For the
condensed version, see [coding-guide-short.md](./coding-guide-short.md).

> **This guide assumes the [General Coding Principles](../general/coding-principles-detailed.md)** —
> it shows how those language-agnostic principles look in idiomatic TypeScript.
> Read that first; the "why" behind each principle below lives there.

> Related TypeScript guides: [Architecture Guide](./architecture-guide-detailed.md) ·
> [Testing Guide](./testing-guide-detailed.md)

## Table of Contents

1. [Principles of Coding](#principles-of-coding)
2. [Guidelines](#guidelines)
3. [Naming Conventions](#naming-conventions)
4. [Names to Avoid 🚫](#names-to-avoid-)
5. [TypeScript-Idiomatic Code](#typescript-idiomatic-code)
6. [Async I/O](#async-io)

---

## Principles of Coding

How the [six general principles](../general/coding-principles-detailed.md#the-6-principles-of-coding)
look in idiomatic TypeScript.

### Beautiful ✨

Prefer types and language features that let you declare *what* the shape of your
data is, and let the compiler catch violations for you.

```typescript
// Less beautiful — a loosely-typed object; nothing stops a caller from passing garbage.
function createOrder(data: any) {
  return { id: data.id, total: data.total, status: "PENDING" };
}

// More beautiful — the type is the contract; invalid shapes fail to compile.
interface OrderInput {
  id: string;
  total: number;
}

interface Order extends OrderInput {
  status: "PENDING" | "PROCESSED" | "CANCELLED";
}

function createOrder(data: OrderInput): Order {
  return { ...data, status: "PENDING" };
}
```

### Readable 📖

A discriminated union beats an object with a pile of optional fields — the
compiler forces you to handle every case, and invalid combinations become
unrepresentable.

```typescript
// Less readable — which fields are actually set depends on `status`, but nothing enforces it.
interface ApiResponse {
  status: string;
  data?: unknown;
  error?: string;
}

// More readable — a discriminated union makes invalid states unrepresentable.
type ApiResponse<T> =
  | { status: "success"; data: T }
  | { status: "error"; error: string };

function handleResponse<T>(response: ApiResponse<T>): void {
  if (response.status === "success") {
    console.log(response.data);   // TS knows `data` exists here
  } else {
    console.error(response.error); // TS knows `error` exists here
  }
}
```

### Explicit 🎯

Dependencies are constructor parameters, not module-level singletons reached for
implicitly.

```typescript
// Less explicit — a hidden, module-level dependency; hard to test, hard to swap out.
import { defaultLogger } from "./logger";

class OrderService {
  placeOrder(orderId: string): void {
    defaultLogger.info(`Placing order ${orderId}`);
  }
}

// More explicit — the dependency is a declared, injected parameter.
interface Logger {
  info(message: string): void;
}

class OrderService {
  constructor(private readonly logger: Logger) {}

  placeOrder(orderId: string): void {
    this.logger.info(`Placing order ${orderId}`);
  }
}
```

### Simple 👌

Prefer the standard library's array methods over manually reimplementing them
with loops.

```typescript
// More complex — manual accumulation, easy to get an off-by-one or mutation bug wrong.
function activeUserNames(users: { name: string; active: boolean }[]): string[] {
  const names: string[] = [];
  for (let i = 0; i < users.length; i++) {
    if (users[i].active) {
      names.push(users[i].name);
    }
  }
  return names;
}

// Simpler — declarative, no manual index/mutation bookkeeping.
function activeUserNames(users: { name: string; active: boolean }[]): string[] {
  return users.filter((u) => u.active).map((u) => u.name);
}
```

### Scalability 🚀

Offload slow, synchronous-feeling work instead of blocking the caller — in
JavaScript's single-threaded event loop, this means never doing CPU-heavy work
synchronously on the main thread.

```typescript
// Less scalable — a CPU-heavy synchronous loop blocks the entire event loop.
function processLargeReport(rows: string[]): void {
  for (const row of rows) {
    heavyComputation(row); // blocks everything else on this thread
  }
}

// More scalable — offload to a worker thread (or a background job queue) instead.
import { Worker } from "node:worker_threads";

function processLargeReportAsync(rows: string[]): Promise<void> {
  return new Promise((resolve, reject) => {
    const worker = new Worker("./report-worker.js", { workerData: rows });
    worker.on("message", resolve);
    worker.on("error", reject);
  });
}
```

### Consistent 🔄

Same naming, formatting, and API-shape conventions everywhere in the codebase —
enforced by ESLint + Prettier, not memory.

---

## Guidelines

Community-standard conventions (largely the
[TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html) and
common ESLint/Prettier defaults) that make code predictable to any TypeScript
developer.

### Code Layout

| Aspect | Rule |
|---|---|
| **Indentation** | 2 spaces per level (near-universal convention; enforced by Prettier). |
| **Line length** | Enforced by Prettier's `printWidth` (80 is the default; many teams use 100). Not a hand-applied rule — configure the formatter and stop discussing it. |
| **Semicolons** | Pick one project-wide convention (with or without ASI-reliant style) and let Prettier enforce it — never mix. |
| **Imports** | Order: (1) Node/runtime built-ins, (2) third-party packages, (3) local/project imports — alphabetized within each group. Most teams enforce this with `eslint-plugin-import`. |
| **Strings** | Pick single or double quotes and let Prettier enforce it; template literals for interpolation, never string concatenation. |
| **Comments** | `//` for implementation notes near the code; JSDoc (`/** ... */`) on exported functions/types so editors surface docs on hover. |
| **Type annotations** | Explicit return types on exported/public functions; let inference handle the rest (locals, simple expressions). |

```typescript
// Imports — correct order
import { readFile } from "node:fs/promises";

import { z } from "zod";

import { UserService } from "./user-service";
import { logger } from "../shared/logger";
```

```typescript
/**
 * Calculates the area of a circle.
 *
 * @param radius - The radius of the circle (must be positive).
 * @returns The area of the circle.
 * @throws {RangeError} If the radius is not positive.
 */
function calculateArea(radius: number): number {
  if (radius <= 0) {
    throw new RangeError("Radius must be positive.");
  }
  return Math.PI * radius * radius;
}
```

### `tsconfig.json` Essentials

- **`"strict": true`** — non-negotiable; turns on strict null checks, no implicit `any`, and the rest of the strict family. Enable it on day one — retrofitting a large codebase to strict mode later is far more painful.
- **`"noUncheckedIndexedAccess": true`** — array/object index access returns `T | undefined` instead of silently assuming the key exists.
- **`"esModuleInterop": true`** — sane interop with CommonJS packages.

---

## Naming Conventions

Name things for **usage**, not internal detail, so the implementation can change
without breaking callers:

```typescript
class UserRepository {
  // Better — describes usage, hides how data is actually fetched (DB, cache, API).
  getUserDetails(userId: string): Promise<UserDetails> {
    return this.db.users.findOne({ id: userId });
  }
}
```

### Naming Styles

| Entity | Style | Example |
|---|---|---|
| Variables | `camelCase` | `userName`, `isActive` |
| Functions/methods | `camelCase` | `calculateSum()`, `getUserProfile()` |
| Constants (module-level, immutable) | `UPPER_SNAKE_CASE` or `camelCase` | `MAX_CONNECTIONS`, `defaultTimeout` — many modern style guides prefer `camelCase` even for constants; pick one and apply it consistently |
| Classes | `PascalCase` | `UserProfile`, `HttpRequestError` |
| Interfaces & Types | `PascalCase`, **no `I` prefix** | `UserRepository`, not `IUserRepository` (the `I`-prefix convention is a C# holdover the TS team explicitly recommends against) |
| Enum members | `PascalCase` | `Color.Red` |
| Generic type parameters | Short `PascalCase` | `T`, `K`, `V`, or descriptive (`TInput`, `TOutput`) for complex generics |
| Files | `kebab-case.ts` (common) or `camelCase.ts` — pick one per project | `user-service.ts`, `http-client.ts` |
| Private class fields | `camelCase`, optionally prefixed `#` (true private) or `_` (convention-only) | `#connectionPool`, `private readonly logger` |

---

## Names to Avoid 🚫

Same [general rules](../general/coding-principles-detailed.md#names-to-avoid-),
TypeScript-flavored:

| Issue | Why | Fix |
|---|---|---|
| `any` as an escape hatch | Silently disables type checking for everything that flows through it | `unknown` + a type guard, or a proper generic |
| Ambiguous letters `l`, `O`, `I` | Confused with `1`/`0` | `length`, `offsetValue`, `identityMatrix` |
| Redundant type-in-name suffixes | `userList: string[]` adds no signal the type doesn't already carry | `users: string[]` |
| Non-null assertion (`!`) as a default habit | Silences a real compiler warning instead of addressing it | Narrow with an `if` check, or a proper type guard |
| Shadowing global/builtin names | Breaks `Array`, `Object`, `Promise`, etc. | `myArray`, `userObject`, `pendingPromise` |

---

## TypeScript-Idiomatic Code

Idioms that make code feel natural to experienced TypeScript developers.

### `interface` vs. `type`

Both declare shapes; the practical difference is extensibility.

```typescript
// interface: prefer for object shapes that might be extended or implemented.
interface User {
  id: string;
  name: string;
}
interface AdminUser extends User {
  permissions: string[];
}

// type: required for unions, intersections, tuples, and mapped/utility-type compositions.
type Status = "pending" | "active" | "disabled";
type UserWithStatus = User & { status: Status };
```

### Discriminated Unions Over Optional-Field Soup

```typescript
type LoadingState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "success"; data: string[] }
  | { kind: "error"; message: string };

function render(state: LoadingState): string {
  switch (state.kind) {
    case "idle":
      return "Waiting to start...";
    case "loading":
      return "Loading...";
    case "success":
      return `Loaded ${state.data.length} items`;
    case "error":
      return `Error: ${state.message}`;
  }
}
```

### Readonly & Immutability

```typescript
interface Point {
  readonly x: number;
  readonly y: number;
}

function translate(p: Point, dx: number, dy: number): Point {
  return { x: p.x + dx, y: p.y + dy };   // returns a new object; never mutates p
}

const ids: readonly string[] = ["a", "b", "c"];   // compiler rejects ids.push(...)
```

### Optional Chaining & Nullish Coalescing

```typescript
const city = user?.address?.city ?? "Unknown";   // safe traversal + a real default

// Nullish coalescing (??) only falls back on null/undefined — unlike ||,
// it doesn't treat 0, "", or false as "missing".
const pageSize = requestedPageSize ?? 20;
```

### Type Guards & Narrowing

```typescript
interface EmailNotifier {
  kind: "email";
  send(to: string, body: string): Promise<void>;
}
interface SmsNotifier {
  kind: "sms";
  send(to: string, body: string): Promise<void>;
}
type Notifier = EmailNotifier | SmsNotifier;

function isEmailNotifier(notifier: Notifier): notifier is EmailNotifier {
  return notifier.kind === "email";
}

function describe(notifier: Notifier): string {
  if (isEmailNotifier(notifier)) {
    return "Sends email"; // narrowed to EmailNotifier here
  }
  return "Sends SMS";
}
```

### Generics for Reusable, Typed Abstractions

```typescript
class Cache<TKey, TValue> {
  private readonly store = new Map<TKey, TValue>();

  get(key: TKey): TValue | undefined {
    return this.store.get(key);
  }

  set(key: TKey, value: TValue): void {
    this.store.set(key, value);
  }
}

const userCache = new Cache<string, User>();  // fully typed, no casts needed
```

### Utility Types

```typescript
interface CreateUserRequest {
  name: string;
  email: string;
  password: string;
}

type UpdateUserRequest = Partial<Omit<CreateUserRequest, "password">>;
// { name?: string; email?: string } — derived, not hand-duplicated

type UserSummary = Pick<CreateUserRequest, "name" | "email">;
```

### Enums vs. Literal Unions

```typescript
// TS enums have real runtime footprint and some well-known quirks (reverse
// mappings for numeric enums, non-tree-shakeable output). Many modern style
// guides prefer a literal union or an `as const` object instead:
type Role = "admin" | "editor" | "viewer";

const Role = {
  Admin: "admin",
  Editor: "editor",
  Viewer: "viewer",
} as const;
type RoleValue = (typeof Role)[keyof typeof Role];   // "admin" | "editor" | "viewer"
```

### Immutable Data: `readonly` Interfaces for Events

Mirrors the general principle of treating anything that "already happened" as
immutable:

```typescript
interface OrderPlacedEvent {
  readonly orderId: string;
  readonly userId: string;
  readonly totalAmount: number;
}

function handleAnalytics(event: OrderPlacedEvent): void {
  // event.totalAmount = 0;  // ❌ compile error — readonly enforced statically
  console.log(`Analytics updated for order ${event.orderId}`);
}
```

Unlike Python's `@dataclass(frozen=True)` (a **runtime** guarantee — mutation
raises an exception), TypeScript's `readonly` is a **compile-time-only** check —
it disappears at runtime, so code that bypasses the type system (e.g. via `any`
or `Object.assign`) can still mutate the object. For a runtime guarantee too, use
`Object.freeze()` in addition to `readonly`.

---

## Async I/O

`async`/`await` sits on top of the same single-threaded event loop as the rest of
JavaScript — it's syntax for working with `Promise`s, not a separate concurrency
model.

### The Basics

```typescript
async function fetchUser(userId: string): Promise<{ id: string; name: string }> {
  await new Promise((resolve) => setTimeout(resolve, 100)); // simulates I/O
  return { id: userId, name: "Alice" };
}

async function main(): Promise<void> {
  const user = await fetchUser("1");
  console.log(user);
}

main();
```

### Running Things Concurrently

```typescript
// Sequential — each await blocks the next from starting.
async function fetchAllSequential(ids: string[]) {
  const results = [];
  for (const id of ids) {
    results.push(await fetchUser(id));
  }
  return results;
}

// Concurrent — all requests start immediately, resolve as a batch.
async function fetchAllConcurrent(ids: string[]) {
  return Promise.all(ids.map((id) => fetchUser(id)));
}
```

`Promise.all` rejects as soon as any promise rejects. `Promise.allSettled` waits
for every promise to settle (fulfilled or rejected) and gives you the outcome of
each — the right choice when partial failure is acceptable.

### The Cardinal Sin: Blocking the Event Loop

Unlike Python's GIL-bound threads, JavaScript has exactly one thread running your
code — a long synchronous computation blocks *everything*, including I/O
callbacks that are otherwise ready to run.

```typescript
// ❌ A synchronous, CPU-heavy loop blocks the entire process — no other
// request can be handled until this returns, no matter how many are queued.
function computeExpensiveSync(data: number[]): number {
  return data.reduce((sum, n) => sum + heavyMath(n), 0);
}

// ✅ Offload CPU-bound work to a worker thread so the event loop stays free.
import { Worker } from "node:worker_threads";

function computeExpensiveAsync(data: number[]): Promise<number> {
  return new Promise((resolve, reject) => {
    const worker = new Worker("./compute-worker.js", { workerData: data });
    worker.once("message", resolve);
    worker.once("error", reject);
  });
}
```

`await`ing a genuinely I/O-bound call (a network request, a file read, a DB
query) does **not** block the event loop — it yields control back so other work
can run while that I/O completes. The trap is CPU-bound work pretending to be
async by wrapping it in a `Promise` without actually leaving the main thread.

### Choosing the Right Concurrency Model

| Workload | Use |
|---|---|
| I/O-bound (network calls, DB queries, file I/O) | `async`/`await` — this is the native model, no extra tooling needed |
| CPU-bound (image processing, heavy computation) | `worker_threads` (Node) or Web Workers (browser) — genuine parallelism, off the main thread |
| CPU-bound, needs process isolation | `child_process` (Node), or offload to a background job queue |

### Testing Async Code

Unlike Python (which needs `pytest-asyncio`), Jest and Vitest support `async`
test functions natively — see the [Testing Guide](./testing-guide-detailed.md#testing-async-code)
for a worked example.
