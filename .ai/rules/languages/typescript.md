## TypeScript

- `strict: true` is non-negotiable, plus `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes`. Treat compiler errors as build failures.
- No `any`. Use `unknown` for genuinely dynamic values and narrow with type guards before use. No non-null assertions (`!`) except where provably safe with a comment explaining why.
- `interface` for object shapes and public contracts; `type` for unions, intersections, and mapped/conditional types.
- Model impossible states out of existence: discriminated unions over boolean flags; `readonly` on data that shouldn't mutate.
- No enums for simple cases — prefer `as const` union types. Reserve `enum` for interop needs.
- Errors: custom classes extending `Error` so `instanceof` works; never throw strings. For expected failures, prefer a typed `Result`/discriminated-union return over throwing.
- Prefer immutable transformations (`map`/`filter`/`reduce`, spread) over in-place mutation.
- Keep types close to where they're used; export shared contracts from a dedicated module. Don't over-abstract with deep generics unless it removes real duplication.
- Baseline tooling: `tsc --noEmit`, ESLint (typescript-eslint strict), Prettier.
