# TypeScript — Coding Implementation Guide (Short)

Cheat sheet for line-by-line, function, and class-level TypeScript code quality.
Full explanations and code samples: [coding-guide-detailed.md](./coding-guide-detailed.md).
Language-agnostic rationale: [General Coding Principles](../general/coding-principles-short.md).

## 6 Principles of Coding

| Principle | In one line |
|---|---|
| **Beautiful ✨** | Let types declare the shape of data; the compiler catches violations. |
| **Readable 📖** | Discriminated unions over optional-field soup — invalid states become unrepresentable. |
| **Explicit 🎯** | Dependencies are constructor parameters, not module-level singletons. |
| **Simple 👌** | Array methods (`map`/`filter`/`reduce`) over manual loops. |
| **Scalable 🚀** | CPU-bound work goes to a worker thread; never block the single-threaded event loop. |
| **Consistent 🔄** | ESLint + Prettier enforce naming/formatting — not code review nitpicks. |

## Guidelines

- **Indentation:** 2 spaces (Prettier default).
- **Line length:** Prettier's `printWidth` (80 default, 100 common) — configure, don't discuss.
- **Imports:** built-ins → third-party → local, alphabetized within each group.
- **Comments:** `//` inline, JSDoc (`/** */`) on exported functions/types.
- **`tsconfig.json`:** `"strict": true` from day one; also `noUncheckedIndexedAccess` and `esModuleInterop`.

## Naming Cheat Sheet

| Entity | Style | Example |
|---|---|---|
| Variables / functions | `camelCase` | `userName`, `getUserProfile()` |
| Classes / Interfaces / Types | `PascalCase`, no `I` prefix | `UserProfile`, `UserRepository` |
| Constants | `UPPER_SNAKE_CASE` or `camelCase` | `MAX_CONNECTIONS` — pick one, apply everywhere |
| Generics | Short `PascalCase` | `T`, `K`, `V`, or `TInput`/`TOutput` |
| Files | `kebab-case.ts` (common) | `user-service.ts` |

Name for **usage**, not internal detail.

**Avoid:** `any` as an escape hatch, non-null assertion (`!`) as a default habit,
redundant type-in-name suffixes, shadowing globals (`Array`, `Object`, `Promise`).

## TypeScript Idioms

- **`interface` vs `type`:** `interface` for extensible object shapes; `type` for unions/intersections/mapped types.
- **Discriminated unions:** a `kind`/`status` tag + `switch` — the compiler enforces exhaustiveness.
- **Immutability:** `readonly` properties/arrays (compile-time only — pair with `Object.freeze()` for a runtime guarantee too).
- **`?.` / `??`:** safe traversal + a real default (`??` only falls back on `null`/`undefined`, unlike `||`).
- **Type guards:** `x is Foo` predicate functions for safe narrowing across a union.
- **Generics:** typed, reusable abstractions (`Cache<TKey, TValue>`) instead of `any`.
- **Utility types:** `Partial`, `Pick`, `Omit`, `Record` — derive types instead of hand-duplicating them.
- **Enums:** prefer a literal union or an `as const` object over `enum` (avoids runtime footprint and numeric-enum quirks).

## Async I/O Cheat Sheet

- `async`/`await` = sugar over `Promise`, on the same single-threaded event loop — not a separate concurrency model.
- `Promise.all` — fails fast on first rejection. `Promise.allSettled` — waits for every promise, gives you each outcome (use when partial failure is OK).
- **Never block the event loop** — a synchronous CPU-heavy loop blocks everything, including ready-to-run I/O callbacks. Offload to `worker_threads` (Node) / Web Workers (browser).
- Jest/Vitest support `async` test functions natively — no extra plugin needed (unlike Python's `pytest-asyncio`).
