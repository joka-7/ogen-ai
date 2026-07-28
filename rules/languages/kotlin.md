## Kotlin

- Null safety: never use `!!`. Use safe calls `?.`, the Elvis operator `?:`, `requireNotNull`/`checkNotNull` with a message, or restructure so the value can't be null.
- `val` over `var`; immutable read-only collections (`List`, `Map`) unless mutation is genuinely required.
- Model state with `sealed class`/`sealed interface` and use exhaustive `when` (no `else` branch on sealed hierarchies, so new cases surface as compile errors).
- Prefer data classes for value types; use `copy()` for derived instances rather than mutation.
- Coroutines for async — structured concurrency only. Launch inside a scope (`viewModelScope`/`lifecycleScope` on Android, or an explicitly managed `CoroutineScope`); never `GlobalScope`. Respect cancellation; make suspend functions main-safe by dispatching blocking work off the main thread.
- Use extension functions to keep call sites readable, but don't hide surprising behavior in them.
- Prefer expression bodies and the standard scope functions (`let`, `run`, `apply`, `also`, `with`) idiomatically — not stacked so deep they obscure flow.
- Errors: prefer sealed result types or `Result<T>` for expected failures over exceptions in business logic.
- Baseline tooling: `ktlint`/`detekt`, compiler warnings treated as errors where practical.
