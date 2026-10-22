## C++

- Target C++17/20. Build with `-Wall -Wextra -Werror`; debug/test builds add `-fsanitize=address,undefined`; run `clang-tidy` in CI. `clang-format` is the only formatting authority.
- RAII for every resource; no manual `new`/`delete` in application code. `std::unique_ptr` for sole ownership, `std::shared_ptr` only for genuinely shared ownership. No owning raw pointers.
- Rule of Zero: if a class doesn't manage a resource directly, declare none of the five special member functions. If it does, define or delete all five.
- `const`-correctness everywhere: pass by `const&`, mark non-mutating methods `const`, make event/DTO fields `const`.
- `std::optional` over sentinel values; `std::variant` + `std::visit` over a tagged struct and manual switch; structured bindings for map iteration; `<algorithm>`/`<ranges>` over hand-written loops; `constexpr`/templates over macros and `void*`.
- Headers: `#pragma once`, forward-declare where possible; include order is own header → C headers → C++ stdlib → third-party → project, alphabetized per group. Never start identifiers with `_` + capital or contain `__` (reserved).
- Contracts are abstract base classes with pure virtual functions; dependencies are constructor parameters wired in one composition root (`main.cc`), never `new`ed inside a class.
- Errors: one `AppError`-rooted exception hierarchy (or a typed result) used consistently, caught once at the request/process boundary. No empty `catch`, no `catch (...)` that swallows.
- Concurrency has real data races: protect shared state with `std::lock_guard<std::mutex>` or `std::atomic<T>`; CPU-bound work goes to a thread pool, never a hot path. Coroutines need a task-type library to be ergonomic.
- Logging: `spdlog` (or the project's single logger) with structured key-value fields — never `std::cout`/`printf` in library or service code. Levels: `debug` (dev only) → `info` → `warn` (recoverable) → `error`/`critical` (alertable). Never log secrets or PII.
- Naming: `PascalCase` types, `snake_case` variables, `snake_case_` members, `kPascalCase` constants, `snake_case.h`/`.cc` files; pick one function-name style per codebase and keep it. Tests: GoogleTest/gMock, one `*_test.cc` per source file.
