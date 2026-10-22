## TypeScript

- `strict: true` is non-negotiable, plus `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes`. Treat compiler errors as build failures.
- No `any`. Use `unknown` for genuinely dynamic values and narrow with type guards before use. No non-null assertions (`!`) except where provably safe with a comment explaining why.
- `interface` for object shapes and public contracts; `type` for unions, intersections, and mapped/conditional types.
- Model impossible states out of existence: discriminated unions over boolean flags; `readonly` on data that shouldn't mutate.
- No enums for simple cases — prefer `as const` union types. Reserve `enum` for interop needs.
- Errors: custom classes extending `Error` so `instanceof` works; never throw strings. For expected failures, prefer a typed `Result`/discriminated-union return over throwing.
- Prefer immutable transformations (`map`/`filter`/`reduce`, spread) over in-place mutation.
- Keep types close to where they're used; export shared contracts from a dedicated module. Don't over-abstract with deep generics unless it removes real duplication.
- Logging: a structured logger (`pino` or `winston`) behind a thin project interface — never `console.log` in service/library code. Log objects, not interpolated strings (`log.info({ orderId }, "msg")`), pass errors as `err` so the stack serializes, child loggers for request context, redact secrets via the logger's redaction config. Never log secrets or PII.
- Baseline tooling: `tsc --noEmit`, ESLint (typescript-eslint strict), Prettier.
- Idioms: type guards (`x is Foo`) and `switch` on a `kind`/`status` tag with an exhaustiveness check; `?.` and `??` (not `||`, which also swallows `0` and `""`); utility types (`Partial`, `Pick`, `Omit`, `Record`) over hand-duplicated shapes; generics over `any`. `readonly` is compile-time only — pair with `Object.freeze()` where a runtime guarantee matters.
- Naming: `camelCase` variables/functions, `PascalCase` types/classes/interfaces with no `I` prefix, `kebab-case.ts` files; pick one constants style and apply it everywhere. Imports built-ins → third-party → local.
- Async: `async`/`await` is sugar over `Promise` on one event loop. `Promise.all` fails fast; `Promise.allSettled` when partial failure is acceptable. CPU-heavy work goes to `worker_threads`/Web Workers — a synchronous loop blocks all I/O callbacks. Background jobs via a queue (BullMQ), not in the request handler.
- Validate external input at the edge with a schema (Zod) before it becomes a typed value.
