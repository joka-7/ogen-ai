# General Testing Principles (Short)

Cheat sheet for language-agnostic testing philosophy. Full explanations:
[testing-principles-detailed.md](./testing-principles-detailed.md).

> Framework mechanics per language: [Python](../python/testing-guide-short.md) ·
> [TypeScript](../typescript/testing-guide-short.md) · [C++](../cpp/testing-guide-short.md)

## 4 Core Principles

- **Isolation 🛡️** — no real DB/network/filesystem; every dependency is a test double.
- **Fast ⚡** — milliseconds, so the suite runs constantly.
- **Repeatable 🔄** — same result every run, any environment.
- **Self-Contained 📦** — each test sets up and cleans up its own state.

## The Mirror Rule

1 source file ↔ 1 test file, same relative path. 1 class ↔ 1 test group. 1 public
method ↔ 1 test case, with **every** scenario (success, edge cases, errors)
consolidated into that one test case via parameterized/table-driven testing.

## AAA Pattern

**Arrange** (set up inputs/doubles) → **Act** (call the one unit, one line) →
**Assert** (check return value, state, or collaborator calls).

## Assertions (concept)

Equality/identity · collection membership · floating-point **with tolerance**
(never raw `==` on floats) · exception/error type (+ message).

## Fixtures & Lifecycle

Setup → yield/run test → teardown, even on failure. Scopes: per-test (default) →
per-group → per-file → per-suite. Use parameterized/table-driven tests to satisfy
the Mirror Rule's "consolidate every scenario" requirement.

## Test Doubles

| Dummy | Stub | Fake | Mock | Spy |
|---|---|---|---|---|
| Unused placeholder | Canned answers | Working simplified impl | Stub + records calls | Real impl + records calls |

**The general principle:** design for **injectability** (pass dependencies in via
constructor/parameter) so tests need no special tooling to substitute a double.
Runtime monkey-patching (Python's `unittest.mock.patch`) is a language-specific
escape hatch, not the general solution — DI is.

## Hard-to-Test = Design Flaw

| Symptom | Fix |
|---|---|
| Needs a real DB/network | Dependency Injection |
| One test case is huge | Split — SRP violation |
| Can't observe the result | Return values instead of hidden side-effects |

## Testing Pyramid 🔺

**Unit** (base, fast, isolated, many) → **Integration** (real components + test DB,
fewer) → **E2E** (full app, slowest/brittlest, sparse — critical paths only, staging
only). Testing Trophy is a legitimate alternative shape for UI/integration-heavy
systems.

## Coverage

**Quantitative** (how much ran), not **qualitative** (how well it was checked).
Target ~85%–95%, not a fragile 100%.
