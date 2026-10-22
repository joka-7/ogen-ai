# C++ — Coding Implementation Guide (Short)

Cheat sheet for line-by-line, function, and class-level modern C++ (17/20) code
quality. Full explanations and code samples: [coding-guide-detailed.md](./coding-guide-detailed.md).
Language-agnostic rationale: [General Coding Principles](../general/coding-principles-short.md).

## 6 Principles of Coding

| Principle | In one line |
|---|---|
| **Beautiful ✨** | RAII over manual `new`/`delete` — lifetime tied to scope, cleanup guaranteed. |
| **Readable 📖** | A named `struct`/`class` beats a `std::tuple` or loose parameter list. |
| **Explicit 🎯** | Dependencies are constructor parameters, not globals reached for. |
| **Simple 👌** | `<algorithm>`/`<ranges>` over hand-written loops. |
| **Scalable 🚀** | Offload slow work to a thread pool instead of blocking a hot path. |
| **Consistent 🔄** | `clang-format` + a documented style guide enforce it — not memory. |

## Guidelines

- **Indentation:** 2 or 4 spaces, `clang-format`-enforced.
- **Line length:** `clang-format`'s `ColumnLimit` — configure, don't hand-wrap.
- **Headers:** `#pragma once`; forward-declare where possible.
- **Includes:** own header → C headers → C++ stdlib → third-party → project headers, alphabetized per group.
- **`const`-correctness:** mark everything `const` unless it mutates.
- **Compiler flags:** `-Wall -Wextra -Werror` always; `-fsanitize=address,undefined` in debug/test builds; `clang-tidy` in CI.

## Naming Cheat Sheet

| Entity | Style | Example |
|---|---|---|
| Variables | `snake_case` | `user_name`, `is_active` |
| Functions/methods | `PascalCase` or `snake_case` (pick one) | `CalculateSum()` |
| Classes/Structs | `PascalCase` | `UserProfile` |
| Member variables | `snake_case_` (trailing underscore) | `connection_pool_` |
| Constants | `kPascalCase` or `UPPER_SNAKE_CASE` | `kMaxConnections` |
| Files | `snake_case.h` / `.cc` | `user_service.h` |

Name for **usage**, not internal detail.

**Avoid:** owning raw pointers (`T*` the caller must `delete` — use
`std::unique_ptr`/`std::shared_ptr`), macros where `constexpr`/templates would
do, redundant type-in-name suffixes, identifiers starting with `_` + capital
or containing `__` (reserved, undefined behavior).

## C++ Idioms

- **RAII + smart pointers:** `std::unique_ptr` (sole ownership) / `std::shared_ptr` (shared) — never manual `new`/`delete` in application code.
- **Rule of Zero:** if a class doesn't manage a resource directly, write none of the 5 special member functions — let the compiler generate them.
- **`const`-correctness:** pass by `const&`, mark non-mutating methods `const`.
- **`std::optional`:** over sentinel values (`-1`, `nullptr` as "not found").
- **`std::variant` + `std::visit`:** type-safe unions instead of a tagged struct + manual switch.
- **Structured bindings:** `for (const auto& [key, value] : map)`.
- **Move semantics:** `std::move` to transfer ownership without a deep copy.
- **Templates:** typed, reusable abstractions (`Cache<TKey, TValue>`) instead of `void*`/macros.
- **Immutable events:** `const` struct fields — compiler-enforced, not just convention.

## Concurrency Cheat Sheet

- C++ has **real** multi-threading (unlike Python's GIL or JS's single thread) — genuine parallelism, genuine data-race risk.
- `std::async` / `std::thread` for CPU-bound parallel work; `std::future::get()` to collect a result.
- **Protect shared state:** `std::lock_guard<std::mutex>` (RAII-unlocked) or `std::atomic<T>` for simple counters.
- **C++20 coroutines** (`co_await`/`co_return`) are the async/await equivalent, but need a task-type library on top of the raw language feature for an ergonomic feel.
- **Choose the model:** thread pool for CPU-bound/I/O-bound-at-scale; coroutines for ergonomic async I/O once your toolchain supports it well.
