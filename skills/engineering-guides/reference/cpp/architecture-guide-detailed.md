# C++ — Architecture & Framework Design Guide (Detailed)

Higher-level system architecture, boundaries, HLD/LLD design documents, design
patterns, and operational standards — in modern, application/service-level C++
(17/20). For the condensed version, see
[architecture-guide-short.md](./architecture-guide-short.md).

> **This guide assumes the [General Architecture Principles](../general/architecture-principles-detailed.md)** —
> it shows how those language-agnostic concepts look in C++. Read that first for
> the "why"; this guide is the "how, in C++."

> Related C++ guides: [Coding Guide](./coding-guide-detailed.md) ·
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
13. [What Is a "Component" in C++?](#what-is-a-component-in-c)
14. [Core Engineering Acronyms Reference 📜](#core-engineering-acronyms-reference-)

---

## Design Principles at the System Level

The [general architecture principles](../general/architecture-principles-detailed.md#design-principles-at-the-system-level)
as they typically show up in a C++ service:

| Principle | In a C++ stack |
|---|---|
| **Beautiful ✨** | A plugin registered via a factory map — adding a handler is one registration call, no dispatcher internals touched. |
| **Explicit 🎯** | A composition root (`main.cc`) constructs concrete repositories and injects them into services via constructors — the entire dependency graph is visible in one place. |
| **Readable 📖** | Domain-driven class names (`UserService`, `PaymentGatewayService`) with strongly-typed structs instead of `std::map<std::string, std::any>`. |
| **Simple 👌** | A small binary target with a handful of translation units; split into a library only once a module is genuinely reused elsewhere. |
| **Scalable 🚀** | Slow work (report generation, image processing) handed to a thread pool or background worker so the request-handling thread returns immediately. |
| **Consistent 🔄** | One CMake target-naming convention, one error-handling strategy (exceptions vs. `std::expected`), and one logging shape across every service. |

---

## Abstract vs. Implementation 🔌

C++'s shape for the [general abstract-vs-implementation principle](../general/coding-principles-detailed.md#abstract-vs-implementation-):
an abstract base class with pure virtual functions as the contract, concrete
subclasses as the implementations.

```cpp
// notifier.h — 1. The Abstract Part
class Notifier {
public:
    virtual ~Notifier() = default;
    virtual bool Send(const std::string& recipient, const std::string& message) = 0;
};

// providers.h — 2. The Implementation Part
class EmailNotifier : public Notifier {
public:
    bool Send(const std::string& recipient, const std::string& message) override {
        std::cout << "Sending SMTP email to " << recipient << ": " << message << "\n";
        return true;
    }
};

class SmsNotifier : public Notifier {
public:
    bool Send(const std::string& recipient, const std::string& message) override {
        std::cout << "Sending Twilio SMS to " << recipient << ": " << message << "\n";
        return true;
    }
};

class LogNotifier : public Notifier {
public:
    bool Send(const std::string& recipient, const std::string& message) override {
        std::cout << "LOG ONLY -> " << recipient << ": " << message << "\n";
        return true;
    }
};

// register_user.h — 3. Business Logic depending on Abstraction
void RegisterNewUser(const std::string& email, Notifier& notifier) {
    std::cout << "Creating user " << email << "...\n";
    notifier.Send(email, "Welcome!");
}

// main.cc — 4. Application Assembly Entry Point
int main() {
    std::unique_ptr<Notifier> notifier =
        IsDevelopmentEnv() ? std::make_unique<LogNotifier>()
                            : std::make_unique<EmailNotifier>();
    RegisterNewUser("alice@example.com", *notifier);
    return 0;
}
```

---

## Data Flow Strategy 🗺️

The [general data flow strategy](../general/architecture-principles-detailed.md#data-flow-strategy-)
worked through a C++ stack:

### User Registration Data Flow (step by step)

1. **Origin (client):** password in plaintext memory, sent over HTTPS.
2. **Edge / reverse proxy:** TLS terminates; the raw payload reaches the service.
3. **Validation layer:** parsed into a typed struct and validated; rejects malformed input immediately.
4. **Service layer:** password undergoes irreversible one-way hashing (Argon2id, via `libsodium`); plaintext discarded.
5. **Data access layer:** email and password hash persisted via prepared statements — plaintext password never touches storage.

```cpp
// user.h — the persisted shape
struct User {
    std::string id;
    std::string email;
    std::string password_hash;
};

// user_repository.h — Step 5: Data Access Layer
class UserRepository {
public:
    virtual ~UserRepository() = default;
    virtual User Create(const std::string& email, const std::string& password_hash) = 0;
};

class PostgresUserRepository : public UserRepository {
public:
    explicit PostgresUserRepository(std::shared_ptr<pqxx::connection> conn)
        : conn_(std::move(conn)) {}

    User Create(const std::string& email, const std::string& password_hash) override {
        pqxx::work txn(*conn_);
        // Prepared statement — never string-concatenate untrusted input into SQL.
        auto row = txn.exec_params1(
            "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id",
            email, password_hash);
        txn.commit();
        return User{.id = row[0].as<std::string>(), .email = email, .password_hash = password_hash};
    }

private:
    std::shared_ptr<pqxx::connection> conn_;
};

// user_service.h — Step 4: Business Logic Layer
class UserService {
public:
    explicit UserService(std::shared_ptr<UserRepository> repo) : repo_(std::move(repo)) {}

    User RegisterUser(const std::string& email, const std::string& plaintext_password) {
        std::string hashed = HashPasswordArgon2id(plaintext_password);  // via libsodium
        return repo_->Create(email, hashed);
    }

private:
    std::shared_ptr<UserRepository> repo_;
};
```

---

## Integration Patterns: DI, Events & Facade 🔌🚪

### Pattern 1: Dependency Injection (DI)

Inject dependencies via constructors rather than instantiating them inside a class.

```cpp
class RegistrationService {
public:
    RegistrationService(std::shared_ptr<Notifier> notifier,
                         std::shared_ptr<WorkspaceService> workspace_svc)
        : notifier_(std::move(notifier)), workspace_svc_(std::move(workspace_svc)) {}

    void RegisterUser(const std::string& email) {
        const std::string user_id = "123";
        notifier_->Send(email, "Welcome!");
        workspace_svc_->CreateDefaultWorkspace(user_id);
    }

private:
    std::shared_ptr<Notifier> notifier_;
    std::shared_ptr<WorkspaceService> workspace_svc_;
};
```

### Pattern 2: Immutable Event-Driven Decoupling

`const`-qualified struct fields for event communication across service boundaries.

```cpp
struct OrderPlacedEvent {
    const std::string order_id;
    const std::string user_id;
    const double total_amount;
};

void HandleAnalytics(const OrderPlacedEvent& event) {
    // event.total_amount = 0;  // ❌ compile error — const member
    std::cout << "Analytics updated for order " << event.order_id << "\n";
}
```

### Pattern 3: Facade Pattern

A single, simplified gateway over a complex, multi-service subsystem.

```cpp
class NotificationFacade {
public:
    NotificationFacade(std::shared_ptr<TemplateManager> template_mgr,
                        std::shared_ptr<EmailGateway> email_gw,
                        std::shared_ptr<UserProfileService> user_svc)
        : template_mgr_(std::move(template_mgr)),
          email_gw_(std::move(email_gw)),
          user_svc_(std::move(user_svc)) {}

    void SendWelcome(const std::string& email) {
        std::string name = user_svc_->GetUserName(email);
        std::string body = template_mgr_->GetTemplate("welcome").Render(name);
        email_gw_->Send(email, "Welcome!", body);
    }

private:
    std::shared_ptr<TemplateManager> template_mgr_;
    std::shared_ptr<EmailGateway> email_gw_;
    std::shared_ptr<UserProfileService> user_svc_;
};
```

### Isolating Third-Party Libraries (Adapter)

Wrap a third-party SDK behind your own interface — only the adapter translation
unit ever includes the vendor library's headers.

```cpp
// payment_gateway.h — your application's generic contract
class PaymentGateway {
public:
    virtual ~PaymentGateway() = default;
    virtual std::string Charge(int amount_cents, const std::string& token) = 0;  // returns transaction ID
};

class PaymentDeclinedError : public std::runtime_error {
public:
    explicit PaymentDeclinedError(const std::string& msg) : std::runtime_error(msg) {}
};

// adapters/stripe_gateway.h — the only file that includes the Stripe SDK headers
class StripeGateway : public PaymentGateway {
public:
    explicit StripeGateway(std::string api_key) : api_key_(std::move(api_key)) {}

    std::string Charge(int amount_cents, const std::string& token) override {
        try {
            // PaymentIntents API — Stripe's current recommended flow (the legacy
            // Charges API is deprecated and doesn't support SCA/3-D Secure).
            auto intent = stripe::PaymentIntent::Create(amount_cents, "usd", token, api_key_);
            return intent.id();
        } catch (const stripe::CardError& e) {
            throw PaymentDeclinedError(std::string("Card declined by Stripe: ") + e.what());
        }
    }

private:
    std::string api_key_;
};
```

---

## Designing for Testability

The DI, separation of concerns, and adapter isolation above are what make C++
components testable with Google Test/gMock in the first place — see
[Designing for Testability](../general/architecture-principles-detailed.md#designing-for-testability)
for the RED/GREEN/BLUE workflow and the [Testing Guide](./testing-guide-detailed.md#hard-to-write-unit-tests--code-design-flaws)
for the "hard to test = design flaw" diagnosis table.

---

## Design Documents: HLD & LLD 🗺️📜

The [general HLD/LLD guide](../general/architecture-principles-detailed.md#design-documents-hld--lld-)
covers the concepts in detail. Two C++-specific concretizations:

1. **Static View — Abstract Base Classes & Method Signatures.** Pure virtual
   functions as interfaces, a service class depending only on those interfaces:

   ```cpp
   // interfaces.h
   class UserRepository {
   public:
       virtual ~UserRepository() = default;
       virtual std::optional<User> FindByEmail(const std::string& email) = 0;
       virtual User Save(const User& user) = 0;
   };

   class PasswordHasher {
   public:
       virtual ~PasswordHasher() = default;
       virtual std::string Hash(const std::string& password) = 0;
       virtual bool Verify(const std::string& password, const std::string& hashed) = 0;
   };

   // user_service.h
   class UserService {
   public:
       UserService(std::shared_ptr<UserRepository> repo, std::shared_ptr<PasswordHasher> hasher)
           : repo_(std::move(repo)), hasher_(std::move(hasher)) {}

       // Registers a new user after validating input and business rules.
       User RegisterUser(const std::string& email, const std::string& plaintext_password);

   private:
       std::shared_ptr<UserRepository> repo_;
       std::shared_ptr<PasswordHasher> hasher_;
   };
   ```

2. **Integration & Concrete DI Wiring** — how the interfaces above get concrete
   implementations at the application's composition root:

   ```cpp
   auto user_repository = std::make_shared<PostgresUserRepository>(db_connection);
   auto password_hasher = std::make_shared<Argon2PasswordHasher>();
   auto user_service = std::make_shared<UserService>(user_repository, password_hasher);
   ```

The remaining parts of the LLD checklist (dynamic view/pseudocode, I/O schemas,
config keys, error contracts, logging plan, unit test plan) follow the same
shape shown in the [general guide's worked example](../general/architecture-principles-detailed.md#design-documents-hld--lld-).

---

## Design Patterns & Anti-Patterns 💡

The [general design patterns & anti-patterns reference](../general/architecture-principles-detailed.md#design-patterns--anti-patterns-)
applies as-is — none of it is C++-specific. C++ examples of several already
appear above: [Facade](#pattern-3-facade-pattern), [Adapter](#isolating-third-party-libraries-adapter).

---

## Operational Logging & Centralized Error Strategy ☁️

### Centralized Error Handling 🛡️

A base exception hierarchy plus one top-level `catch` at the application/request
boundary — the business logic itself stays exception-free of boilerplate.

```cpp
// errors.h
class AppError : public std::runtime_error {
public:
    explicit AppError(const std::string& msg) : std::runtime_error(msg) {}
    virtual int StatusCode() const = 0;
};

class ResourceNotFoundError : public AppError {
public:
    ResourceNotFoundError(const std::string& resource_name, const std::string& resource_id)
        : AppError(resource_name + " with ID '" + resource_id + "' was not found.") {}
    int StatusCode() const override { return 404; }
};

class PermissionDeniedError : public AppError {
public:
    PermissionDeniedError() : AppError("Action not permitted.") {}
    int StatusCode() const override { return 403; }
};

// request_handler.cc — the one place exceptions are caught and translated
Response HandleRequest(const Request& request) {
    try {
        return Dispatch(request);   // business logic — no try/catch inside it
    } catch (const AppError& e) {
        return Response{.status_code = e.StatusCode(), .body = e.what()};
    } catch (const std::exception& e) {
        return Response{.status_code = 500, .body = "Internal Server Error"};
    }
}
```

Create **custom, semantic exception types** (`InsufficientStockError`, not a
bare `std::runtime_error`) so the centralized handler knows exactly how to
respond.

### Structured Contextual Logging (JSON) ⚙️

The [3 pillars of structured logging](../general/architecture-principles-detailed.md#operational-logging--centralized-error-strategy-)
via `spdlog` with its JSON formatting pattern:

```cpp
#include <spdlog/spdlog.h>
#include <spdlog/sinks/stdout_sinks.h>

class OrderService {
public:
    void PlaceOrder(const std::string& user_id, int item_count) {
        // structured key-value fields via spdlog's fmt-based formatting
        spdlog::info(R"({{"msg": "Order placement initiated", "user_id": "{}", "items": {}}})",
                      user_id, item_count);
    }
};
```

```json
{
  "timestamp": "2026-08-17T00:35:00Z",
  "level": "info",
  "msg": "Order placement initiated",
  "user_id": "42",
  "items": 3
}
```

**Log levels:** `debug` (dev only) → `info` (routine) → `warn` (recoverable) →
`error`/`critical` (alertable) — the same 4-tier shape as the
[general logging guidance](../general/architecture-principles-detailed.md#operational-logging--centralized-error-strategy-).

---

## Security Fundamentals 🔒

The [general security fundamentals](../general/architecture-principles-detailed.md#security-fundamentals-)
(AuthN vs. AuthZ, the OWASP Top 10 checklist, transport/rate-limiting) apply
as-is. C++ adds one more class of concern most memory-safe languages don't have:

### Memory Safety Is Part of Your Security Surface

Buffer overflows, use-after-free, and uninitialized reads are exploitable
vulnerabilities, not just crashes. RAII and smart pointers (from the Coding
guide) aren't just a style preference here — they're a security control.
`-fsanitize=address,undefined` in CI and `clang-tidy`'s security-oriented checks
catch entire vulnerability classes other languages don't need to think about.

### Injection Prevention

```cpp
// ❌ Classic SQL injection — untrusted input concatenated straight into the query.
std::string query = "SELECT * FROM users WHERE email = '" + email + "'";

// ✅ Prepared statements — never string-concatenate untrusted input into SQL.
txn.exec_params("SELECT * FROM users WHERE email = $1", email);
```

The CI-stage dependency scanning the OWASP checklist references maps to tools
like `OWASP Dependency-Check` or `Trivy` against your `vcpkg`/`conan` lockfile.

---

## CI/CD, Deployment & Observability 🚀📈

The [general pipeline stages](../general/architecture-principles-detailed.md#cicd-deployment--observability-)
apply unchanged — in C++, stage 1 is the compiler at `-Wall -Wextra -Werror` plus
`clang-tidy`, and stages 2/4/6 are covered in the [Testing Guide](./testing-guide-detailed.md).

### Containerization Basics

```dockerfile
# Dockerfile — multi-stage build: the compiler toolchain never ships to prod.
FROM gcc:13 AS builder
WORKDIR /src
COPY . .
RUN cmake -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel

FROM debian:bookworm-slim
WORKDIR /app
COPY --from=builder /src/build/my_service ./my_service
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser
CMD ["./my_service"]
```

Follows the [general containerization rules](../general/architecture-principles-detailed.md#cicd-deployment--observability-)
(pinned base image, non-root user, multi-stage build — critical here since the
build stage alone can be gigabytes with a full toolchain).

### Database Migrations

Managed by a dedicated migration tool independent of the C++ service itself
(e.g. `sqitch`, Flyway, or plain versioned SQL files run by a deploy script) —
never applied by hand against production. Follow the
[expand–contract pattern](../general/architecture-principles-detailed.md#cicd-deployment--observability-)
for zero-downtime schema changes.

### Observability Beyond Logging

The [general observability guidance](../general/architecture-principles-detailed.md#cicd-deployment--observability-)
via `prometheus-cpp` and the OpenTelemetry C++ SDK:

**Metrics** (RED method):

```cpp
#include <prometheus/counter.h>
#include <prometheus/histogram.h>
#include <prometheus/registry.h>

class RequestMetrics {
public:
    explicit RequestMetrics(prometheus::Registry& registry)
        : request_count_(prometheus::BuildCounter()
                              .Name("http_requests_total")
                              .Help("Total HTTP requests")
                              .Register(registry)),
          request_latency_(prometheus::BuildHistogram()
                                .Name("http_request_duration_seconds")
                                .Help("Request latency")
                                .Register(registry)) {}

private:
    prometheus::Family<prometheus::Counter>& request_count_;
    prometheus::Family<prometheus::Histogram>& request_latency_;
};
```

**Health checks** (liveness vs. readiness):

```cpp
struct HealthStatus {
    bool healthy;
    std::string detail;
};

HealthStatus LivenessCheck() {
    return {.healthy = true, .detail = "ok"};  // no dependency checks — just "am I running"
}

HealthStatus ReadinessCheck(Database& db) {
    if (!db.Ping()) {
        return {.healthy = false, .detail = "Database unavailable"};
    }
    return {.healthy = true, .detail = "ready"};
}
```

---

## Background Work & Task Queues

Offload slow, resource-intensive operations to a thread pool (in-process) or a
message queue (cross-process, e.g. RabbitMQ/ZeroMQ) so the request-handling
thread isn't blocked:

```cpp
// thread_pool.h — a minimal in-process background worker pool
class ThreadPool {
public:
    explicit ThreadPool(size_t num_threads);

    void Submit(std::function<void()> task) {
        {
            std::lock_guard<std::mutex> lock(queue_mutex_);
            tasks_.push(std::move(task));
        }
        condition_.notify_one();
    }

private:
    std::queue<std::function<void()>> tasks_;
    std::mutex queue_mutex_;
    std::condition_variable condition_;
    std::vector<std::thread> workers_;
};

// usage
void ResizeImageTask(const std::string& image_id, int width, int height) {
    auto image_record = GetImageFromDb(image_id);   // pass IDs, not objects/pointers
    ResizeImage(image_record.path, width, height);
    MarkImageAsProcessed(image_id);
}

thread_pool.Submit([image_id, width, height] {
    ResizeImageTask(image_id, width, height);
});
```

Same principles as any queue system: **pass IDs, not objects** (a raw/smart
pointer captured by a lambda outlives the object it points to only if you're
careful — an ID sidesteps the whole lifetime question); design tasks to be
**idempotent**; use a **dead-letter queue or retry-with-backoff** for
cross-process queues; **structured logging** bound to a job ID.

---

## Software Engineering Rules

Language-agnostic — see the [general 10 rules](../general/architecture-principles-detailed.md#software-engineering-rules).

---

## What Is a "Component" in C++?

The [general "component" concept](../general/architecture-principles-detailed.md#what-is-a-component)
in C++, concretely:

- **A single class** — for narrow responsibilities, its public methods are the interface.
- **A namespace + CMake library target (very common)** — a directory of related translation units behind one public header, built as its own CMake target (`add_library(user_service ...)`); other targets link against it and only see the public header.
- **A main class within a library** — a primary entry-point/facade class relying on sibling implementation files; the *library target* is still the component, not any single class inside it.

---

## Core Engineering Acronyms Reference 📜

Language-agnostic — see the [general acronyms reference](../general/architecture-principles-detailed.md#core-engineering-acronyms-reference-).
