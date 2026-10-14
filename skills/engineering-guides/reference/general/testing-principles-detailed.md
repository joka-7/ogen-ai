# General Testing Principles (Detailed)

Language-agnostic testing philosophy: what makes a test *good*, how test code
should be organized, and how to reason about a test suite's shape — independent
of any specific test framework. For the condensed version, see
[testing-principles-short.md](./testing-principles-short.md).

> **Language-specific framework mechanics** (pytest, Jest/Vitest, Google Test)
> live in each language's own testing guide:
> [Python](../python/testing-guide-detailed.md) ·
> [TypeScript](../typescript/testing-guide-detailed.md) ·
> [C++](../cpp/testing-guide-detailed.md)

> Related general guides: [Coding Principles](./coding-principles-detailed.md) ·
> [Architecture Principles](./architecture-principles-detailed.md)

## Table of Contents

1. [Core Principles of Unit Testing](#core-principles-of-unit-testing)
2. [The Mirror Rule & Naming Conventions](#the-mirror-rule--naming-conventions)
3. [The Anatomy of a Good Unit Test: AAA Pattern](#the-anatomy-of-a-good-unit-test-aaa-pattern)
4. [Assertions, in Concept](#assertions-in-concept)
5. [Fixtures & Test Lifecycle, in Concept](#fixtures--test-lifecycle-in-concept)
6. [Test Doubles & Mocking, in Concept](#test-doubles--mocking-in-concept)
7. ["Hard to Write Unit Tests" = Code Design Flaws](#hard-to-write-unit-tests--code-design-flaws)
8. [The Testing Pyramid 🔺](#the-testing-pyramid-)
9. [Code Coverage](#code-coverage)

---

## Core Principles of Unit Testing

A **unit test** is a small, automated test that verifies the correctness of a
single, isolated piece of code — a function, method, or small class — completely
independent of external dependencies like databases, networks, or filesystems.
Four properties make a unit test *good*, in every language:

- **Isolation 🛡️** — a unit test must not interact with anything outside its own code path. Every external dependency is replaced with a test double.
- **Fast ⚡** — tests run in milliseconds. A fast suite gets run constantly, catching bugs while they're cheap to fix.
- **Repeatable 🔄** — a test produces the same result every single run, regardless of execution environment, order, or the machine it runs on.
- **Self-Contained 📦** — each test sets up its own required state and cleans up after itself, never relying on state left behind by another test.

---

## The Mirror Rule & Naming Conventions

The **Mirror Rule** (Parallel Directory Structure) enforces strict structural and
functional symmetry between production source code and test code — a convention,
not a language feature, so it applies the same way regardless of what you're
writing tests in.

```text
src/
└── app/
    └── services/order_processor

tests/
└── app/
    └── services/order_processor   <-- mirrored, same relative path
```

### The 4 Strict Rules of Mirroring

1. **File Mirroring (1 file ↔ 1 test file):** every production source file has exactly one corresponding test file at the same relative path under the test root.
2. **Class Mirroring (1 class ↔ 1 test group):** every production class maps to a dedicated test group named after it (a test class, a `describe` block, a test suite — whatever the language's framework calls it).
3. **Public Method Mirroring (1 public method ↔ 1 test case):** every public method/function has exactly one corresponding test case.
4. **All Scenarios Consolidated:** every validation path, edge case, success case, and exception for that one method lives inside that *single* test case — via parameterized/table-driven testing or sequential AAA blocks — rather than being scattered across many loosely-related test cases.

> Concrete naming conventions per language: [Python](../python/testing-guide-detailed.md#the-unit-test-mirror-rule--naming-conventions)
> (`test_module.py` / `TestClass` / `test_method`) ·
> [TypeScript](../typescript/testing-guide-detailed.md) (`module.test.ts` / `describe` / `it`) ·
> [C++](../cpp/testing-guide-detailed.md) (`module_test.cpp` / `TEST(ClassTest, Method)`)

---

## The Anatomy of a Good Unit Test: AAA Pattern

The **Arrange-Act-Assert (AAA)** pattern provides a clear, readable structure for
every test, in every language:

1. **Arrange ✅** — set up preconditions and inputs: create objects, prepare test data, configure test doubles.
2. **Act 🎬** — execute the single unit of behavior under test. Ideally one line.
3. **Assert ⚖️** — verify the outcome: a return value, a state change, or that a collaborator was called correctly.

```text
test calculate_total_with_tax:
    # 1. ARRANGE
    calculator = TaxCalculator(taxRate: 0.20)

    # 2. ACT
    total = calculator.calculateTotal(100.0)

    # 3. ASSERT
    assert total == 120.0
```

---

## Assertions, in Concept

Every test framework provides some version of the same core assertion shapes:

- **Equality / identity** — "is this value exactly this?" (and a `null`/`None`/`nil`-specific check, since identity and equality aren't the same thing in every language).
- **Collection membership** — "does this collection contain/have this length/equal that set?"
- **Floating-point comparison with tolerance** — raw `==` on floats is unsafe (`0.1 + 0.2 != 0.3` in essentially every language using IEEE 754 floats); assert with an explicit tolerance instead.
- **Exception/error assertions** — "does this call throw/raise the expected error type (and optionally message)?"

> Concrete assertion APIs per language: [Python](../python/testing-guide-detailed.md#assertions--introspection-in-depth)
> (`assert`, `pytest.approx`, `pytest.raises`) ·
> [TypeScript](../typescript/testing-guide-detailed.md) (`expect().toBe()`, `toBeCloseTo()`, `toThrow()`) ·
> [C++](../cpp/testing-guide-detailed.md) (`EXPECT_EQ`, `EXPECT_NEAR`, `EXPECT_THROW`)

---

## Fixtures & Test Lifecycle, in Concept

Every framework provides some mechanism for reusable setup/teardown logic, scoped
to different lifetimes:

| Scope | Lifetime | Best used for |
|---|---|---|
| Per-test | Re-created for every single test case (the default, and usually the right choice) | Isolated object state and test doubles |
| Per-group/class | Created once per test group | Shared, read-only group-level configuration |
| Per-file/module | Created once per test file | Read-only data loading |
| Per-suite/session | Created once for the entire run | A genuinely global, expensive-to-build test resource |

The **setup-then-yield-then-teardown** shape (code before the test body runs is
setup, code after is teardown, even if the test fails in between) is the most
common implementation of this across frameworks.

**Parameterized / table-driven testing** — running one test case body against a
table of `(input, expected)` pairs — is the standard way to satisfy Mirror Rule #4
(consolidating every scenario for one method into one test case) without repeating
the AAA structure by hand for each case.

---

## Test Doubles & Mocking, in Concept

A **test double** replaces a real dependency during a test. The classic taxonomy,
useful vocabulary regardless of framework:

| Kind | What it does |
|---|---|
| **Dummy** | Passed to satisfy a signature; never actually used. |
| **Stub** | Returns canned answers to calls made during the test; no behavior beyond that. |
| **Fake** | A working, simplified implementation (e.g. an in-memory database instead of a real one). |
| **Mock** | A stub that also records how it was called, so the test can assert on those calls. |
| **Spy** | Wraps a *real* implementation while recording calls — the real behavior still happens. |

### The General Principle: Design for Injectability

The single biggest lever for making mocking easy is architectural, not
mechanical: **pass dependencies in (constructor/parameter injection) instead of
having a component construct or reach out for its own dependencies.** A component
built this way can be tested by simply passing a test double in — no special
tooling required.

Some languages/ecosystems also support **monkey-patching** — replacing a name at
runtime without changing the production code's construction pattern (Python's
`unittest.mock.patch` is the best-known example). This is powerful but comes with
its own gotcha (patch where a name is *looked up*, not where it's *defined* — see
the [Python testing guide](../python/testing-guide-detailed.md#-the-golden-rule-patch-where-used-not-where-defined)
for the full explanation). Languages without an equivalent runtime-patching
mechanism (C++ is the clearest example) lean on dependency injection by
necessity — which is, not coincidentally, the more robust approach in every
language anyway.

---

## "Hard to Write Unit Tests" = Code Design Flaws

> **Golden Rule:** Difficulty writing a unit test points directly to
> architectural design flaws in production code — not a testing problem.

| Symptom | Architectural disease | Refactoring solution |
|---|---|---|
| Test requires a real DB or network | Tight coupling & hidden dependencies | Apply **Dependency Injection** |
| Test file is massive for one function | SRP violation | Refactor into small, single-purpose functions |
| Cannot check output (returns nothing observable) | Unobservable side-effects | Convert to **pure functions** returning values |

---

## The Testing Pyramid 🔺

- **Level 1 — Unit Tests (base):** fast, isolated, no external dependencies. Should be numerous.
- **Level 2 — Integration Tests (middle):** verify several real components work together correctly (e.g. a route → service → data-access chain against a real test database). Slower, but crucial for verifying wiring.
- **Level 3 — End-to-End Tests (peak):** simulate a full user journey through the running system. Very slow and brittle — use sparsely, for critical paths only.

> **Note:** the pyramid is the right default for typical backend/service systems.
> It's not the only accepted model — for UI-heavy or integration-heavy systems,
> some teams deliberately invest more in the middle layer (Kent C. Dodds'
> "Testing Trophy"). Pick the shape that matches where your system's bugs
> actually tend to live.

**Async code** (wherever the language has it) still follows Level 1 rules — it's
still a unit test — it just needs the test framework's async-aware entry point and
async-aware test doubles so `await`ing a fake doesn't throw a type error.

**Integration tests**, in concept: exercise the real wiring between components
against a real (test) instance of the boundary being crossed — most often a real,
disposable test database — instead of mocking that boundary away. A disposable,
production-like dependency spun up per test run (the "Testcontainers" pattern,
regardless of which language's library implements it) is preferable to a
long-lived shared test instance, which accumulates state and flakiness over time.

**E2E tests**, in concept: drive the entire running application the way a user
would, against a staging or ephemeral preview environment — never production.
Keep this suite to critical user journeys only, and run it on a separate,
lighter CI cadence than unit/integration tests, since it's inherently the
slowest and most failure-prone layer.

---

## Code Coverage

Code coverage measures the percentage of source statements executed during test
runs. Every mainstream language has a coverage tool for its primary test
framework.

> **Takeaway:** Coverage is a **quantitative** metric (how much code executes),
> not a **qualitative** one (how thoroughly the logic is actually validated). A
> line can be "covered" by a test that asserts nothing meaningful about it.
> Target a strong majority (roughly 85%–95% is a reasonable band) rather than
> chasing a fragile 100% — the last few percent is usually generated code,
> defensive branches, or genuinely untestable glue, and forcing coverage there
> produces tests that exist only to move the number.
