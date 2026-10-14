# TypeScript — Testing Guide (Short)

Cheat sheet for writing fast, isolated, repeatable unit tests with Vitest/Jest.
Full explanations and code samples: [testing-guide-detailed.md](./testing-guide-detailed.md).
Language-agnostic version: [General Testing Principles](../general/testing-principles-short.md).

## 4 Core Principles

- **Isolation 🛡️** — no real DB/network/filesystem; every dependency is a test double.
- **Fast ⚡** — milliseconds, so the suite runs constantly.
- **Repeatable 🔄** — same result every run, any environment.
- **Self-Contained 📦** — each test sets up and cleans up its own state.

## The Mirror Rule

1 source file ↔ 1 `*.test.ts` (co-located or mirrored under `tests/`). 1 class ↔
1 `describe("ClassName", ...)`. 1 public method ↔ 1 nested `describe`/`it`, with
**every** scenario consolidated via `it.each`.

| Production | Test |
|---|---|
| `payment-gateway.ts` | `payment-gateway.test.ts` |
| `class PaymentGateway` | `describe("PaymentGateway", ...)` |
| `chargeCard()` | `describe("chargeCard", ...)` |

## AAA Pattern

**Arrange** (set up inputs/mocks) → **Act** (call the one method, one line) →
**Assert** (`expect(...)`, one behavior).

## Assertions

```typescript
expect(result).toBe(42);
expect(0.1 + 0.2).toBeCloseTo(0.3);                     // floats
expect(() => divide(10, 0)).toThrow("division by zero");
await expect(fetchUser("x")).rejects.toThrow(NotFoundError); // async
```

## Fixtures

```typescript
beforeEach(async () => {
  db = await connectTestDb();
  await db.createTables();
});

afterEach(async () => {
  await db.dropTables();
  await db.close();
});
```

`beforeEach`/`afterEach` (per test, default) vs. `beforeAll`/`afterAll` (once per
suite, for genuinely expensive setup). `it.each([...])` for table-driven tests.

## Mocking — Prefer Injection Over Patching

TypeScript's edge over Python here: **inject the dependency via the
constructor/parameter**, and there's nothing to patch — just pass a mock.

```typescript
const mockNotifier: Notifier = { send: vi.fn().mockResolvedValue(true) };
const processor = new OrderProcessor(mockNotifier);   // no patching needed

expect(mockNotifier.send).toHaveBeenCalledWith("a@b.com", "Order confirmed");
```

When a dependency truly can't be constructor-injected (a legacy module-level
import), `vi.mock("./module-path")` (Jest: `jest.mock`) replaces the whole
module — the closest equivalent to Python's `@patch`, with the same "mock where
it's imported" caveat. `vi.spyOn(obj, "method")` wraps a *real* implementation
while recording calls.

## Hard-to-Test Code = Design Flaw

| Symptom | Fix |
|---|---|
| Needs a real DB/network | Dependency Injection |
| One test case is huge | Split — SRP violation |
| Can't observe the result | Return values instead of hidden side-effects |

## Testing Pyramid 🔺

**Unit** (Vitest/Jest, base, many) → **Integration** (real test DB, fewer) →
**E2E** (Playwright, staging only, sparse — critical paths only).

## Async, Integration & E2E

- **Async:** just `await` — Vitest/Jest support async test functions natively (no plugin needed, unlike Python's `pytest-asyncio`). Mock async calls with `vi.fn().mockResolvedValue(...)` / `.mockRejectedValue(...)`.
- **Integration:** hit the real app → service → repository against a real test DB (fixture migrates schema, resets after). Use **Testcontainers** for a disposable, production-like DB.
- **E2E:** Playwright — TypeScript-native. Drive the whole app like a user would, against staging — never prod. Critical paths only; separate, slower CI schedule.

## Coverage

```bash
vitest run --coverage   # or: jest --coverage
```

Coverage is **quantitative** (how much ran), not **qualitative** (how well it was
checked). Target ~85%–95%, not a fragile 100%.
