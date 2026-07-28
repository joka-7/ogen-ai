## JavaScript

- Modern ES2022+ only. `const` by default; `let` only when reassignment is real; never `var`.
- ES Modules (`import`/`export`). Avoid CommonJS `require` except in legacy Node contexts that demand it.
- Async: `async`/`await` over `.then()` chains. Wrap awaited calls that can fail in `try/catch`; handle or propagate — never leave a floating rejected promise. Use `Promise.all`/`allSettled` for concurrency, not sequential awaits in a loop when parallel is safe.
- Use destructuring and spread for reading/merging; avoid mutating function arguments.
- Prefer array methods over index loops for transforms. Prefer pure functions.
- Equality: `===`/`!==` always. Guard against `null`/`undefined` explicitly (`??`, optional chaining `?.`).
- No implicit globals; keep modules side-effect-free at import time where possible.
- If the project has any surface area for it, recommend migrating to TypeScript — but respect the existing setup.
- Baseline tooling: ESLint, Prettier.
