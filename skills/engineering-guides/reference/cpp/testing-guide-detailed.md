# C++ — Testing Guide (Detailed)

Google Test / Google Mock (gMock) mechanics for writing fast, isolated,
repeatable unit tests in modern C++, plus practical integration/concurrency/
background-task testing. For the condensed version, see
[testing-guide-short.md](./testing-guide-short.md).

> **This guide assumes the [General Testing Principles](../general/testing-principles-detailed.md)** —
> it shows how those language-agnostic concepts look with Google Test/gMock.
> Read that first for the "why"; this guide is the "how, in C++."

> Related C++ guides: [Coding Guide](./coding-guide-detailed.md) ·
> [Architecture Guide](./architecture-guide-detailed.md)

## Table of Contents

1. [The Unit Test Mirror Rule & Naming Conventions](#the-unit-test-mirror-rule--naming-conventions)
2. [The Anatomy of a Good Unit Test: AAA Pattern](#the-anatomy-of-a-good-unit-test-aaa-pattern)
3. [Assertions & Introspection in Depth](#assertions--introspection-in-depth)
4. [Test Fixtures & Lifecycle Management](#test-fixtures--lifecycle-management)
5. [Mocking with gMock](#mocking-with-gmock)
6. ["Hard to Write Unit Tests" = Code Design Flaws](#hard-to-write-unit-tests--code-design-flaws)
7. [The Testing Pyramid 🔺](#the-testing-pyramid-)
8. [Complete Practical Example (Mirror Rule Applied)](#complete-practical-example-mirror-rule-applied)
9. [Testing Concurrent Code](#testing-concurrent-code)
10. [Integration Testing in Practice](#integration-testing-in-practice)
11. [System-Level (E2E) Testing in Practice](#system-level-e2e-testing-in-practice)
12. [Testing Background Tasks](#testing-background-tasks)
13. [Code Coverage](#code-coverage)

---

## The Unit Test Mirror Rule & Naming Conventions

The [general Mirror Rule](../general/testing-principles-detailed.md#the-mirror-rule--naming-conventions),
with Google Test's specific naming conventions:

```text
src/
└── services/
    ├── order_processor.h
    ├── order_processor.cc        <-- Source file
    └── user_service.cc
tests/
└── services/
    ├── order_processor_test.cc   <-- Mirrored test file
    └── user_service_test.cc
```

### The 4 Strict Rules of Mirroring

1. **File Mirroring (1 file ↔ 1 test file):** every `<module>.cc` has exactly one `<module>_test.cc` at the same relative path under `tests/`.
2. **Class Mirroring (1 class ↔ 1 test fixture):** every production class maps to a dedicated `TEST_F` fixture named after it (`OrderProcessor` ↔ `OrderProcessorTest`).
3. **Public Method Mirroring (1 public method ↔ 1 named test case):** every public method has a test case named for it (`TEST_F(OrderProcessorTest, ProcessOrder_...)`).
4. **All Scenarios Consolidated:** every validation path, edge case, success case, and exception for that method lives inside test cases grouped under that method's naming prefix — via `TEST_P` (parameterized) or sequential AAA blocks across several `TEST_F`s sharing the fixture.

### Naming Conventions

| Entity | Production source | Test equivalent | Example |
|---|---|---|---|
| File | `payment_gateway.cc` | `payment_gateway_test.cc` | Suffixed with `_test.cc` |
| Class | `PaymentGateway` | `PaymentGatewayTest` (fixture) | Suffixed with `Test` |
| Public method | `ChargeCard()` | `TEST_F(PaymentGatewayTest, ChargeCard_...)` | Method name as the test-case prefix |

---

## The Anatomy of a Good Unit Test: AAA Pattern

The [general AAA pattern](../general/testing-principles-detailed.md#the-anatomy-of-a-good-unit-test-aaa-pattern)
in Google Test:

```cpp
#include <gtest/gtest.h>
#include "tax_calculator.h"

TEST(TaxCalculatorTest, CalculatesTotalIncludingTax) {
    // 1. ARRANGE
    TaxCalculator calculator(0.20);
    double item_price = 100.0;

    // 2. ACT
    double total = calculator.CalculateTotal(item_price);

    // 3. ASSERT
    EXPECT_DOUBLE_EQ(total, 120.0);
}
```

---

## Assertions & Introspection in Depth

### `ASSERT_*` vs. `EXPECT_*`

`ASSERT_*` macros abort the current test function immediately on failure (a
fatal assertion); `EXPECT_*` macros record the failure and let the test
continue, so later assertions still run and report. Default to `EXPECT_*`
unless a failed check makes the rest of the test meaningless to continue (e.g.
a null pointer you're about to dereference) — then use `ASSERT_*`.

```cpp
TEST(UserServiceTest, RegisterUser_ReturnsValidUser) {
    auto user = service.RegisterUser("alice@example.com", "password123");

    ASSERT_TRUE(user.has_value());       // fatal: nothing else makes sense to check if this fails
    EXPECT_EQ(user->email, "alice@example.com");
    EXPECT_FALSE(user->id.empty());
}
```

### Basic & Identity Assertions

```cpp
EXPECT_EQ(result, 42);
EXPECT_TRUE(is_active);
EXPECT_FALSE(has_error);
EXPECT_EQ(error_message, std::nullopt);

EXPECT_THAT(user_roles, ::testing::Contains("admin"));
EXPECT_EQ(items.size(), 3);
```

### Floating-Point Comparisons

Raw `==` on floats is unsafe (`0.1 + 0.2 != 0.3` under IEEE 754) — use the
floating-point-aware matchers:

```cpp
EXPECT_DOUBLE_EQ(0.1 + 0.2, 0.3);                     // exact ULP-based comparison — can still be too strict
EXPECT_NEAR(CalculateInterest(1000, 0.05), 50.0, 0.01); // explicit tolerance — usually what you want
```

### Exception Testing

```cpp
TEST(DivideTest, ThrowsOnDivideByZero) {
    EXPECT_THROW(Divide(10, 0), std::invalid_argument);
}

// To also check the exception's message:
TEST(DivideTest, ThrowsWithExpectedMessage) {
    try {
        Divide(10, 0);
        FAIL() << "Expected std::invalid_argument";
    } catch (const std::invalid_argument& e) {
        EXPECT_STREQ(e.what(), "division by zero");
    }
}
```

---

## Test Fixtures & Lifecycle Management

### Custom Fixture Definition

```cpp
class OrderRepositoryTest : public ::testing::Test {
protected:
    void SetUp() override {          // runs before every test in this fixture
        db_ = ConnectTestDb();
        db_.CreateTables();
    }

    void TearDown() override {       // runs after every test, even if it failed
        db_.DropTables();
        db_.Close();
    }

    TestDatabase db_;
};

TEST_F(OrderRepositoryTest, PersistsANewOrder) {
    OrderRepository repo(db_);
    auto order = repo.Save(Order{.id = "1", .status = "PENDING"});
    EXPECT_EQ(order.id, "1");
}
```

| Hook | Scope |
|---|---|
| `SetUp()` / `TearDown()` | Runs before/after **every** `TEST_F` using this fixture — the default, and usually the right choice |
| `SetUpTestSuite()` / `TearDownTestSuite()` (static) | Runs **once** for the whole fixture's test suite — for genuinely expensive, shareable setup |

### Parameterized Testing

`TEST_P` runs one test body against a table of cases — satisfies Mirror Rule #4:

```cpp
class DiscountTest : public ::testing::TestWithParam<std::tuple<std::string, double, double>> {};

TEST_P(DiscountTest, CalculatesCorrectDiscount) {
    auto [status, amount, expected_discount] = GetParam();
    DiscountProcessor processor;
    EXPECT_DOUBLE_EQ(processor.CalculateDiscount(status, amount), expected_discount);
}

INSTANTIATE_TEST_SUITE_P(
    DiscountTiers, DiscountTest,
    ::testing::Values(
        std::make_tuple("REGULAR", 100.0, 0.0),
        std::make_tuple("SILVER", 100.0, 10.0),
        std::make_tuple("GOLD", 100.0, 20.0)));
```

---

## Mocking with gMock

### Defining a Mock

`MOCK_METHOD` generates a mock implementation of an interface — the class under
test receives it via constructor injection, exactly as it would receive the
real implementation.

```cpp
#include <gmock/gmock.h>
#include "notifier.h"

class MockNotifier : public Notifier {
public:
    MOCK_METHOD(bool, Send, (const std::string& recipient, const std::string& message), (override));
};
```

### Setting Expectations

```cpp
TEST(OrderProcessorTest, NotifiesCustomerOnSuccess) {
    MockNotifier mock_notifier;
    OrderProcessor processor;
    Order order{.id = "123", .status = "PENDING", .customer_email = "a@b.com"};

    EXPECT_CALL(mock_notifier, Send("a@b.com", "Order confirmed"))
        .Times(1)
        .WillOnce(::testing::Return(true));

    processor.ProcessOrder(order, mock_notifier);

    EXPECT_EQ(order.status, "PROCESSED");
}
```

Because C++ has no runtime module-patching mechanism (unlike Python's
`unittest.mock.patch`), gMock's whole model is **constructor injection** — the
same story as TypeScript: design the class to take its dependency as a
parameter, and there's nothing to patch.

### Common Matchers & Cardinalities

```cpp
EXPECT_CALL(mock_repo, FindByEmail(::testing::_))       // `_` matches any argument
    .Times(::testing::AtLeast(1))
    .WillRepeatedly(::testing::Return(std::nullopt));

EXPECT_CALL(mock_notifier, Send(::testing::_, ::testing::_))
    .Times(0);   // asserts Send is never called
```

---

## "Hard to Write Unit Tests" = Code Design Flaws

Language-agnostic — see the [general diagnosis table](../general/testing-principles-detailed.md#hard-to-write-unit-tests--code-design-flaws).
The fix in C++ is almost always [Dependency Injection](./architecture-guide-detailed.md#pattern-1-dependency-injection-di) —
an abstract base class + constructor injection sidesteps needing to link real
infrastructure into a unit test binary at all.

---

## The Testing Pyramid 🔺

Language-agnostic — see the [general Testing Pyramid](../general/testing-principles-detailed.md#the-testing-pyramid-).
C++'s three layers, concretely: Google Test unit tests (above), [integration
tests against a real test DB](#integration-testing-in-practice), and
system-level black-box tests for the E2E layer (see below).

---

## Complete Practical Example (Mirror Rule Applied)

### Production Source Code (`src/services/order_processor.h` / `.cc`)

```cpp
// order_processor.h
struct Order {
    std::string id;
    std::string status = "PENDING";
};

class Notifier {
public:
    virtual ~Notifier() = default;
    virtual void SendConfirmation(const std::string& order_id) = 0;
};

class ConsoleNotifier : public Notifier {
public:
    void SendConfirmation(const std::string& order_id) override;
};

class OrderProcessor {
public:
    void ProcessOrder(Order& order, Notifier& notifier);
};
```

```cpp
// order_processor.cc
#include "order_processor.h"
#include <iostream>
#include <stdexcept>

void ConsoleNotifier::SendConfirmation(const std::string& order_id) {
    std::cout << "Sending confirmation for order " << order_id << "...\n";
}

void OrderProcessor::ProcessOrder(Order& order, Notifier& notifier) {
    if (order.status != "PENDING") {
        throw std::runtime_error("Order has already been processed.");
    }
    order.status = "PROCESSED";
    notifier.SendConfirmation(order.id);
}
```

### Mirrored Test File (`tests/services/order_processor_test.cc`)

```cpp
#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "services/order_processor.h"

class MockNotifier : public Notifier {
public:
    MOCK_METHOD(void, SendConfirmation, (const std::string& order_id), (override));
};

TEST(OrderProcessorTest, ProcessOrder_UpdatesStatusAndNotifiesOnPendingOrder) {
    OrderProcessor processor;
    MockNotifier mock_notifier;
    Order valid_order{.id = "123", .status = "PENDING"};

    EXPECT_CALL(mock_notifier, SendConfirmation("123")).Times(1);

    processor.ProcessOrder(valid_order, mock_notifier);

    EXPECT_EQ(valid_order.status, "PROCESSED");
}

TEST(OrderProcessorTest, ProcessOrder_ThrowsAndDoesNotNotifyWhenAlreadyProcessed) {
    OrderProcessor processor;
    MockNotifier mock_notifier;
    Order completed_order{.id = "456", .status = "COMPLETED"};

    EXPECT_CALL(mock_notifier, SendConfirmation(::testing::_)).Times(0);

    EXPECT_THROW(processor.ProcessOrder(completed_order, mock_notifier), std::runtime_error);
}
```

---

## Testing Concurrent Code

Multi-threaded code resists naive testing — sleep-based timing assumptions
produce flaky tests, not deterministic ones. Two reliable strategies:

**1. Test the synchronization primitive's contract, not timing.** Use
condition variables/futures to *wait for* an event instead of sleeping a fixed
duration:

```cpp
TEST(ThreadPoolTest, SubmittedTaskEventuallyRuns) {
    ThreadPool pool(2);
    std::promise<void> task_ran;
    auto future = task_ran.get_future();

    pool.Submit([&task_ran] { task_ran.set_value(); });

    // Waits for the actual event, with a bounded timeout — not a guessed sleep.
    ASSERT_EQ(future.wait_for(std::chrono::seconds(1)), std::future_status::ready);
}
```

**2. Extract the concurrency-free logic and test that in isolation.** Keep the
threading/locking machinery as thin as possible, and put the actual business
logic in plain, synchronously-testable functions/classes — the same "hard to
test = design flaw" principle applies here too.

---

## Integration Testing in Practice

[Integration testing, in concept](../general/testing-principles-detailed.md#the-testing-pyramid-) —
a real test-DB fixture:

```cpp
class UserRegistrationIntegrationTest : public ::testing::Test {
protected:
    void SetUp() override {
        db_ = ConnectTestDatabase();  // a real Postgres instance, e.g. via Testcontainers
        db_.RunMigrations();
    }

    void TearDown() override {
        db_.Reset();
    }

    TestDatabase db_;
};

TEST_F(UserRegistrationIntegrationTest, PersistsUserToDatabase) {
    PostgresUserRepository repo(db_.Connection());
    UserService service(std::make_shared<PostgresUserRepository>(repo));

    auto user = service.RegisterUser("alice@example.com", "SecurePass123!");

    auto saved = repo.FindByEmail("alice@example.com");
    ASSERT_TRUE(saved.has_value());
    EXPECT_NE(saved->password_hash, "SecurePass123!");  // never stored in plaintext
}
```

For a database that behaves exactly like production, spin up a real, disposable
instance per test run via **Testcontainers for C++** (or an equivalent
Docker-Compose-driven test harness) instead of a long-lived shared test
database.

---

## System-Level (E2E) Testing in Practice

Full end-to-end UI-driving tools (Playwright/Selenium) don't apply to most
C++ services the way they do for a web app — the equivalent E2E layer for a
C++ service is a **black-box system test**: build the real binary, run it, and
drive it through its real external interface (an HTTP client, a CLI, gRPC):

```cpp
TEST(SystemTest, UserCanRegisterViaHttpApi) {
    // Assumes the service binary is already running against a staging environment.
    httplib::Client client("staging.example.com", 443);

    auto response = client.Post("/users", R"({"email":"alice@example.com","password":"SecurePass123!"})",
                                 "application/json");

    ASSERT_TRUE(response);
    EXPECT_EQ(response->status, 201);
}
```

Keep this suite to critical paths only, run it against staging (never
production), and run it on a separate, slower CI schedule than unit/integration
tests — same as any other language's E2E layer.

---

## Testing Background Tasks

A unit test for a background/queued task should verify the task's **logic**,
not real infrastructure — pass fakes for every collaborator.

```cpp
TEST(ImageTaskTest, ResizesImageAndMarksProcessed) {
    MockImageRepository mock_repo;
    MockImageResizer mock_resizer;

    EXPECT_CALL(mock_repo, GetImage("1")).WillOnce(::testing::Return(ImageRecord{.path = "test.jpg"}));
    EXPECT_CALL(mock_resizer, Resize("test.jpg", 100, 100)).Times(1);
    EXPECT_CALL(mock_repo, MarkProcessed("1")).Times(1);

    ProcessImageTask("1", 100, 100, mock_repo, mock_resizer);
}
```

This is fast (no real filesystem/network I/O), reliable, and focused purely on
the task's own logic — the queue infrastructure itself (thread pool, message
broker) is tested separately, once, not per-task.

---

## Code Coverage

See the [general coverage philosophy](../general/testing-principles-detailed.md#code-coverage)
(quantitative vs. qualitative, target ~85–95%). In C++, via `gcov`/`lcov` or
LLVM's source-based coverage:

```bash
# GCC + gcov/lcov
cmake -B build -DCMAKE_CXX_FLAGS="--coverage"
cmake --build build
ctest --test-dir build
lcov --capture --directory build --output-file coverage.info
genhtml coverage.info --output-directory coverage_html

# Clang's source-based coverage
cmake -B build -DCMAKE_CXX_FLAGS="-fprofile-instr-generate -fcoverage-mapping"
cmake --build build
LLVM_PROFILE_FILE="test.profraw" ctest --test-dir build
llvm-profdata merge -sparse test.profraw -o test.profdata
llvm-cov show ./build/my_tests -instr-profile=test.profdata
```
