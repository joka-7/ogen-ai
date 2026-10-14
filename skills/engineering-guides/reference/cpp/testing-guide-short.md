# C++ — Testing Guide (Short)

Cheat sheet for writing fast, isolated, repeatable unit tests with Google
Test/gMock. Full explanations and code samples: [testing-guide-detailed.md](./testing-guide-detailed.md).
Language-agnostic version: [General Testing Principles](../general/testing-principles-short.md).

## 4 Core Principles

- **Isolation 🛡️** — no real DB/network/filesystem; every dependency is a mock via an interface.
- **Fast ⚡** — milliseconds, so the suite runs constantly.
- **Repeatable 🔄** — same result every run, any environment.
- **Self-Contained 📦** — each test sets up and cleans up its own state.

## The Mirror Rule

1 source file ↔ 1 `*_test.cc` at the same relative path under `tests/`. 1 class
↔ 1 `TEST_F` fixture (`OrderProcessor` ↔ `OrderProcessorTest`). 1 public method
↔ named test cases grouped under its prefix, with **every** scenario
consolidated via `TEST_P` or sequential `TEST_F`s.

| Production | Test |
|---|---|
| `payment_gateway.cc` | `payment_gateway_test.cc` |
| `class PaymentGateway` | `PaymentGatewayTest` fixture |
| `ChargeCard()` | `TEST_F(PaymentGatewayTest, ChargeCard_...)` |

## AAA Pattern

**Arrange** (set up inputs/mocks) → **Act** (call the one method, one line) →
**Assert** (`EXPECT_*`, one behavior).

## Assertions

```cpp
EXPECT_EQ(result, 42);
EXPECT_NEAR(CalculateInterest(1000, 0.05), 50.0, 0.01);   // floats — explicit tolerance
EXPECT_THROW(Divide(10, 0), std::invalid_argument);
```

`ASSERT_*` aborts the test on failure (fatal); `EXPECT_*` records and continues.
Default to `EXPECT_*`; use `ASSERT_*` only when continuing would be meaningless
(e.g. about to dereference a null result).

## Fixtures

```cpp
class OrderRepositoryTest : public ::testing::Test {
protected:
    void SetUp() override { db_ = ConnectTestDb(); db_.CreateTables(); }
    void TearDown() override { db_.DropTables(); db_.Close(); }
    TestDatabase db_;
};
```

`SetUp`/`TearDown` (per test, default) vs. `SetUpTestSuite`/`TearDownTestSuite`
(once per fixture, for expensive shared setup). `TEST_P` + `INSTANTIATE_TEST_SUITE_P`
for table-driven tests.

## Mocking with gMock

No runtime patching in C++ — constructor injection is the whole model.

```cpp
class MockNotifier : public Notifier {
public:
    MOCK_METHOD(bool, Send, (const std::string&, const std::string&), (override));
};

EXPECT_CALL(mock_notifier, Send("a@b.com", "Order confirmed")).Times(1);
```

`::testing::_` matches any argument; `.Times(n)`/`AtLeast(n)` for call counts;
`.WillOnce(::testing::Return(...))` for a return value.

## Hard-to-Test Code = Design Flaw

| Symptom | Fix |
|---|---|
| Needs a real DB/network | Dependency Injection (abstract base class + constructor) |
| One test case is huge | Split — SRP violation |
| Can't observe the result | Return values instead of hidden side-effects |

## Testing Pyramid 🔺

**Unit** (Google Test, base, many) → **Integration** (real test DB, fewer) →
**System-level black-box** (real binary + real external interface — C++'s E2E
layer, since UI-driving tools don't apply the way they do for a web app).

## Concurrency, Integration & Background Tasks

- **Concurrency:** don't test with sleeps — wait on a real synchronization primitive (`std::future`/condition variable) with a bounded timeout. Extract concurrency-free logic and test it in isolation.
- **Integration:** hit the real repository → service against a real test DB (fixture migrates schema, resets after). Use **Testcontainers for C++** for a disposable, production-like DB.
- **Background tasks:** pass fakes for every collaborator; test the task's processor function/logic directly, not real queue infrastructure.

## Coverage

```bash
# GCC: --coverage + lcov/genhtml
# Clang: -fprofile-instr-generate -fcoverage-mapping + llvm-cov
```

Coverage is **quantitative** (how much ran), not **qualitative** (how well it
was checked). Target ~85%–95%, not a fragile 100%.
