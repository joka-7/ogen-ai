# C++ — Coding Implementation Guide (Detailed)

This is the detailed reference for writing clean, readable, and maintainable
modern C++ (C++17/20) at the line-by-line, function, and class level —
application/service-level C++, not embedded/systems programming. For the
condensed version, see [coding-guide-short.md](./coding-guide-short.md).

> **This guide assumes the [General Coding Principles](../general/coding-principles-detailed.md)** —
> it shows how those language-agnostic principles look in idiomatic C++. Read
> that first; the "why" behind each principle below lives there.

> Related C++ guides: [Architecture Guide](./architecture-guide-detailed.md) ·
> [Testing Guide](./testing-guide-detailed.md)

## Table of Contents

1. [Principles of Coding](#principles-of-coding)
2. [Guidelines](#guidelines)
3. [Naming Conventions](#naming-conventions)
4. [Names to Avoid 🚫](#names-to-avoid-)
5. [C++-Idiomatic Code](#c-idiomatic-code)
6. [Concurrency](#concurrency)

---

## Principles of Coding

How the [six general principles](../general/coding-principles-detailed.md#the-6-principles-of-coding)
look in idiomatic modern C++.

### Beautiful ✨

Let RAII and the type system express intent — a resource's lifetime tied to a
scope, rather than manually paired `new`/`delete` calls the reader has to verify
by hand.

```cpp
// Less beautiful — manual lifetime management; a thrown exception before
// delete leaks the buffer, and every return path must remember to clean up.
void ProcessFile(const std::string& path) {
    FILE* file = fopen(path.c_str(), "r");
    if (file == nullptr) {
        return;
    }
    // ... read file ...
    fclose(file);
}

// More beautiful — RAII: the destructor guarantees cleanup on every path,
// including exceptions.
void ProcessFile(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        return;
    }
    // ... read file ...
}   // file closes automatically here, no matter how the function exits
```

### Readable 📖

A `struct`/`class` with named, typed fields beats a `std::tuple` or a bag of
loose parameters — the shape is documented by the type, not by argument order.

```cpp
// Less readable — what does this tuple mean without checking the signature?
std::tuple<std::string, int, bool> GetUserSummary(int user_id);

// More readable — self-documenting; a caller doesn't need to memorize field order.
struct UserSummary {
    std::string name;
    int age;
    bool is_active;
};

UserSummary GetUserSummary(int user_id);
```

### Explicit 🎯

Dependencies are constructor parameters, not globals reached for inside a class.

```cpp
// Less explicit — a hidden global dependency; hard to test, hard to swap out.
Logger& GlobalLogger();

class OrderService {
public:
    void PlaceOrder(int order_id) {
        GlobalLogger().Info("Placing order " + std::to_string(order_id));
    }
};

// More explicit — the dependency is a declared, injected constructor parameter.
class OrderService {
public:
    explicit OrderService(std::shared_ptr<Logger> logger) : logger_(std::move(logger)) {}

    void PlaceOrder(int order_id) {
        logger_->Info("Placing order " + std::to_string(order_id));
    }

private:
    std::shared_ptr<Logger> logger_;
};
```

### Simple 👌

Prefer `<algorithm>`/`<ranges>` over hand-written loops for standard operations —
fewer places to get an off-by-one or iterator-invalidation bug wrong.

```cpp
// More complex — manual loop, easy to get the bounds or mutation wrong.
std::vector<std::string> ActiveUserNames(const std::vector<User>& users) {
    std::vector<std::string> names;
    for (size_t i = 0; i < users.size(); ++i) {
        if (users[i].active) {
            names.push_back(users[i].name);
        }
    }
    return names;
}

// Simpler — declarative; the standard algorithm owns the iteration details.
std::vector<std::string> ActiveUserNames(const std::vector<User>& users) {
    std::vector<std::string> names;
    for (const auto& user : users | std::views::filter(&User::active)) {
        names.push_back(user.name);
    }
    return names;
}
```

### Scalability 🚀

Offload slow, blocking work to a thread pool or background worker instead of
doing it on a hot path.

```cpp
// Less scalable — a synchronous, blocking call on the request-handling path.
void HandleUploadRequest(const Upload& upload) {
    GenerateThumbnail(upload);   // slow, blocks this thread the whole time
    RespondOk();
}

// More scalable — hand the slow work to a thread pool; respond immediately.
void HandleUploadRequest(const Upload& upload, ThreadPool& pool) {
    pool.Submit([upload] { GenerateThumbnail(upload); });
    RespondAccepted();
}
```

### Consistent 🔄

Same naming, formatting, and API-shape conventions everywhere in the codebase —
enforced by `clang-format` and a documented style guide, not memory.

---

## Guidelines

Community-standard conventions (this guide follows the shape of the
[C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)
and the Google C++ Style Guide's naming scheme, two of the most widely adopted
references) that make code predictable to any C++ developer.

### Code Layout

| Aspect | Rule |
|---|---|
| **Indentation** | 2 or 4 spaces (pick one, enforce with `clang-format`); never tabs. |
| **Line length** | Enforced by `clang-format`'s `ColumnLimit` (80 or 100 are both common) — configure it, don't hand-wrap. |
| **Braces** | One brace style per project (`clang-format` enforces it); never mix. |
| **Headers** | `#pragma once` (or include guards) in every header; forward-declare instead of `#include` where possible to cut compile-time coupling. |
| **Includes** | Order: (1) the header's own matching `.h` first, (2) C system headers, (3) C++ standard library, (4) third-party libraries, (5) project headers — alphabetized within each group (Google style; `clang-format`'s `IncludeCategories` enforces it). |
| **Comments** | `//` for implementation notes; Doxygen-style (`/** ... */`) on public declarations in headers. |
| **`const`-correctness** | Mark every parameter, method, and variable `const` unless it's mutated — the compiler then catches accidental mutation for you. |

```cpp
// my_class.cc — include order
#include "my_class.h"      // 1. matching header first

#include <cstdint>          // 2. C system headers
#include <algorithm>        // 3. C++ standard library
#include <vector>

#include <fmt/format.h>     // 4. third-party libraries

#include "shared/logger.h"  // 5. project headers
```

```cpp
/**
 * Calculates the area of a circle.
 *
 * @param radius The radius of the circle (must be positive).
 * @return The area of the circle.
 * @throws std::invalid_argument if radius is not positive.
 */
double CalculateArea(double radius) {
    if (radius <= 0) {
        throw std::invalid_argument("Radius must be positive.");
    }
    return M_PI * radius * radius;
}
```

### Compiler Flags Worth Enabling from Day One

- **`-Wall -Wextra -Werror`** — treat warnings as errors; a warning today is a bug tomorrow.
- **`-fsanitize=address,undefined`** in debug/test builds — catches memory errors and undefined behavior that silently "work" until they don't.
- **`clang-tidy`** in CI — static analysis for common bug patterns (Core Guidelines checks, modernize-* checks) beyond what the compiler itself flags.

---

## Naming Conventions

Name things for **usage**, not internal detail:

```cpp
class UserRepository {
public:
    // Better — describes usage; hides how data is actually fetched (DB, cache, API).
    UserDetails GetUserDetails(int user_id) const;
};
```

### Naming Styles

| Entity | Style | Example |
|---|---|---|
| Variables | `snake_case` | `user_name`, `is_active` |
| Functions/methods | `PascalCase` (Google style) or `snake_case` (standard-library style) — pick one per project | `CalculateSum()`, `calculate_sum()` |
| Classes/Structs | `PascalCase` | `UserProfile`, `HttpRequest` |
| Member variables | `snake_case` with a trailing underscore | `connection_pool_`, `is_ready_` |
| Constants | `kPascalCase` (Google style) or `UPPER_SNAKE_CASE` | `kMaxConnections`, `MAX_CONNECTIONS` |
| Namespaces | short, `snake_case` | `myapp::services` |
| Template parameters | short `PascalCase` | `T`, `K`, `V`, or descriptive (`TInput`) for complex templates |
| Files | `snake_case.h` / `snake_case.cc` | `user_service.h`, `user_service.cc` |

---

## Names to Avoid 🚫

Same [general rules](../general/coding-principles-detailed.md#names-to-avoid-),
C++-flavored:

| Issue | Why | Fix |
|---|---|---|
| Ambiguous letters `l`, `O`, `I` | Confused with `1`/`0` | `length`, `offset_value`, `identity_matrix` |
| Owning raw pointers (`T*` that the caller must `delete`) | No signal about ownership; a silent leak or double-free waiting to happen | `std::unique_ptr<T>` (or `std::shared_ptr<T>` for shared ownership) |
| Redundant type-in-name suffixes | `user_vector`, `name_string` add no signal a type already carries | `users`, `name` |
| Macros for anything a `constexpr`/`inline function`/template could do | No type safety, no scoping, invisible to the debugger | `constexpr` values, `inline` functions, templates |
| Shadowing standard-library or reserved names | Confuses readers and, for reserved identifiers (leading underscore + capital, double underscore), is undefined behavior | Never start an identifier with `_` followed by a capital letter, or contain `__` |

---

## C++-Idiomatic Code

Idioms that make code feel natural to experienced modern C++ developers.

### RAII & Smart Pointers

Tie every resource's lifetime to an object's scope — never manage raw
`new`/`delete` by hand in application code.

```cpp
class ConnectionPool {
public:
    // unique_ptr: sole ownership, moved not copied.
    std::unique_ptr<Connection> Acquire() {
        return std::make_unique<Connection>();
    }
};

class SharedCache {
public:
    // shared_ptr: shared ownership, reference-counted.
    std::shared_ptr<CacheEntry> Get(const std::string& key) {
        return entries_[key];
    }

private:
    std::unordered_map<std::string, std::shared_ptr<CacheEntry>> entries_;
};
```

### The Rule of Zero (Prefer It Over the Rule of Three/Five)

If a class doesn't manage a resource directly, don't write a destructor, copy
constructor, copy assignment, move constructor, or move assignment at all — let
the compiler generate them from your (already RAII-safe) members.

```cpp
// Rule of Zero: every member is already RAII-safe (string, vector, unique_ptr),
// so the compiler-generated special member functions are all correct as-is.
class UserSession {
private:
    std::string user_id_;
    std::vector<std::string> permissions_;
    std::unique_ptr<Connection> connection_;
    // No custom destructor/copy/move needed — the defaults are correct.
};
```

### `const`-Correctness & References

```cpp
// Pass by const reference to avoid a copy when you don't need ownership.
void PrintUser(const User& user);

// Return by value for small/movable types — modern compilers elide the copy (RVO/NRVO).
User BuildUser(const std::string& name);

// Mark methods const when they don't mutate observable state.
class Circle {
public:
    double Area() const { return M_PI * radius_ * radius_; }
private:
    double radius_;
};
```

### `std::optional` Over Sentinel Values

```cpp
// Less safe — -1 as "not found" is a convention the caller must remember and check.
int FindUserId(const std::string& email);   // returns -1 if not found

// Safer — the type itself says "might not have a value"; the compiler forces a check.
std::optional<int> FindUserId(const std::string& email);

std::optional<int> id = FindUserId("alice@example.com");
if (id.has_value()) {
    std::cout << "Found: " << *id << "\n";
}
```

### `std::variant` for Type-Safe Unions

```cpp
struct EmailNotification { std::string address; };
struct SmsNotification { std::string phone_number; };

using Notification = std::variant<EmailNotification, SmsNotification>;

void Send(const Notification& notification) {
    std::visit([](const auto& n) {
        using T = std::decay_t<decltype(n)>;
        if constexpr (std::is_same_v<T, EmailNotification>) {
            std::cout << "Emailing " << n.address << "\n";
        } else if constexpr (std::is_same_v<T, SmsNotification>) {
            std::cout << "Texting " << n.phone_number << "\n";
        }
    }, notification);
}
```

### Structured Bindings

```cpp
std::map<std::string, int> scores{{"alice", 90}, {"bob", 85}};

for (const auto& [name, score] : scores) {   // no more .first/.second noise
    std::cout << name << ": " << score << "\n";
}
```

### Move Semantics

```cpp
class Buffer {
public:
    explicit Buffer(std::vector<uint8_t> data) : data_(std::move(data)) {}
    // The caller's vector is left empty (moved-from), avoiding a deep copy.

private:
    std::vector<uint8_t> data_;
};

std::vector<uint8_t> large_data = LoadFile("data.bin");
Buffer buffer(std::move(large_data));   // transfers ownership, no copy
```

### Templates for Reusable, Typed Abstractions

```cpp
template <typename TKey, typename TValue>
class Cache {
public:
    std::optional<TValue> Get(const TKey& key) const {
        auto it = store_.find(key);
        return it != store_.end() ? std::optional<TValue>(it->second) : std::nullopt;
    }

    void Set(const TKey& key, TValue value) {
        store_[key] = std::move(value);
    }

private:
    std::unordered_map<TKey, TValue> store_;
};

Cache<std::string, User> user_cache;   // fully typed, no casts needed
```

### Immutable Data: `const` Structs for Events

Mirrors the general principle of treating anything that "already happened" as
immutable — mark every field `const` so the compiler rejects mutation:

```cpp
struct OrderPlacedEvent {
    const std::string order_id;
    const std::string user_id;
    const double total_amount;
};

void HandleAnalytics(const OrderPlacedEvent& event) {
    // event.total_amount = 0;  // ❌ compile error — const member, cannot assign
    std::cout << "Analytics updated for order " << event.order_id << "\n";
}
```

---

## Concurrency

C++ has genuine multi-threading (unlike Python's GIL-bound threads or
JavaScript's single-threaded event loop) — real parallelism, and real data-race
risk if shared state isn't synchronized.

### The Basics: `std::thread` and `std::async`

```cpp
#include <future>
#include <thread>

int FetchUserCount() {
    // Simulate I/O or computation.
    return 42;
}

int main() {
    // std::async runs the task (possibly on another thread) and returns a
    // future you can wait on — the simplest way to get a result back.
    std::future<int> count_future = std::async(std::launch::async, FetchUserCount);
    int count = count_future.get();   // blocks until the result is ready
    return 0;
}
```

### Protecting Shared State

```cpp
#include <mutex>

class Counter {
public:
    void Increment() {
        std::lock_guard<std::mutex> lock(mutex_);   // RAII: unlocked automatically, even on exception
        ++count_;
    }

    int Value() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return count_;
    }

private:
    mutable std::mutex mutex_;
    int count_ = 0;
};
```

For simple counters, `std::atomic<int>` avoids the mutex entirely and is
typically faster — reach for a mutex when you need to protect more than one
related value atomically.

### C++20 Coroutines (Brief)

C++20 introduces native `co_await`/`co_return` coroutines — the same conceptual
shape as `async`/`await` in Python/TypeScript, but the standard library ships
only the building blocks; a coroutine *task* type (like `cppcoro::task<T>` or a
library-provided equivalent) is needed to get an ergonomic async/await feel.
Most application-level C++ services get further with a thread pool for I/O
concurrency until coroutine library support matures further in the project's
toolchain.

### Choosing the Right Concurrency Model

| Workload | Use |
|---|---|
| CPU-bound, parallelizable | `std::thread` / `std::async` / a thread pool — genuine parallelism across cores |
| I/O-bound, high concurrency | A thread pool sized for I/O wait, or C++20 coroutines with an async I/O library |
| Producer/consumer, background work | A thread-safe queue + a worker thread pool — see the [Architecture guide's Background Work section](./architecture-guide-detailed.md#background-work--task-queues) |

### Testing Concurrent Code

Multi-threaded code is inherently harder to test deterministically — see the
[Testing Guide](./testing-guide-detailed.md#testing-concurrent-code) for
strategies (synchronization points, avoiding sleep-based timing assumptions).
