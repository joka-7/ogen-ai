# TypeScript — Testing Guide (Detailed)

Vitest/Jest mechanics for writing fast, isolated, repeatable unit tests in
TypeScript, plus practical integration/E2E/async/background-task testing. The
examples use the `describe`/`it`/`expect` API shared by both Vitest and Jest —
where APIs diverge (mocking namespaces, mainly), both are shown. For the
condensed version, see [testing-guide-short.md](./testing-guide-short.md).

> **This guide assumes the [General Testing Principles](../general/testing-principles-detailed.md)** —
> it shows how those language-agnostic concepts look with Vitest/Jest. Read that
> first for the "why"; this guide is the "how, in TypeScript."

> Related TypeScript guides: [Coding Guide](./coding-guide-detailed.md) ·
> [Architecture Guide](./architecture-guide-detailed.md)

## Table of Contents

1. [The Unit Test Mirror Rule & Naming Conventions](#the-unit-test-mirror-rule--naming-conventions)
2. [The Anatomy of a Good Unit Test: AAA Pattern](#the-anatomy-of-a-good-unit-test-aaa-pattern)
3. [Assertions & Introspection in Depth](#assertions--introspection-in-depth)
4. [Test Lifecycle & Fixtures](#test-lifecycle--fixtures)
5. [Mocking Mechanics in Depth](#mocking-mechanics-in-depth)
6. ["Hard to Write Unit Tests" = Code Design Flaws](#hard-to-write-unit-tests--code-design-flaws)
7. [The Testing Pyramid 🔺](#the-testing-pyramid-)
8. [Complete Practical Example (Mirror Rule Applied)](#complete-practical-example-mirror-rule-applied)
9. [Testing Async Code](#testing-async-code)
10. [Integration Testing in Practice](#integration-testing-in-practice)
11. [End-to-End (E2E) Testing in Practice](#end-to-end-e2e-testing-in-practice)
12. [Testing Background Tasks (BullMQ)](#testing-background-tasks-bullmq)
13. [Code Coverage](#code-coverage)

---

## The Unit Test Mirror Rule & Naming Conventions

The [general Mirror Rule](../general/testing-principles-detailed.md#the-mirror-rule--naming-conventions),
with TypeScript's specific naming conventions:

```text
src/
└── services/
    ├── order-processor.ts     <-- Source file
    └── user-service.ts
tests/                          <-- or co-located as *.test.ts next to the source
└── services/
    ├── order-processor.test.ts  <-- Mirrored test file
    └── user-service.test.ts
```

### The 4 Strict Rules of Mirroring

1. **File Mirroring (1 file ↔ 1 test file):** every `<module>.ts` has exactly one `<module>.test.ts` (co-located or at the same relative path under `tests/`).
2. **Class/Module Mirroring (1 class ↔ 1 `describe` block):** every production class maps to a dedicated `describe("ClassName", ...)` block.
3. **Public Method Mirroring (1 public method ↔ 1 `describe`/`it` group):** every public method has its own nested `describe` (or a clearly-named `it`).
4. **All Scenarios Consolidated:** every validation path, edge case, success case, and exception for that method lives inside that method's `describe` block — via `it.each`/`test.each` or sequential AAA blocks.

### Naming Conventions

| Entity | Production source | Test equivalent | Example |
|---|---|---|---|
| File | `payment-gateway.ts` | `payment-gateway.test.ts` | Suffixed with `.test.ts` (or `.spec.ts`) |
| Class | `PaymentGateway` | `describe("PaymentGateway", ...)` | Matches the class name |
| Public method | `chargeCard()` | `describe("chargeCard", ...)` or `it("charges the card...")` | Matches the method name or describes behavior |

---

## The Anatomy of a Good Unit Test: AAA Pattern

The [general AAA pattern](../general/testing-principles-detailed.md#the-anatomy-of-a-good-unit-test-aaa-pattern)
in Vitest/Jest:

```typescript
import { describe, it, expect } from "vitest"; // or "@jest/globals"

describe("TaxCalculator", () => {
  it("calculates the total including tax", () => {
    // 1. ARRANGE
    const calculator = new TaxCalculator(0.2);
    const itemPrice = 100.0;

    // 2. ACT
    const total = calculator.calculateTotal(itemPrice);

    // 3. ASSERT
    expect(total).toBe(120.0);
  });
});
```

---

## Assertions & Introspection in Depth

Vitest/Jest use a fluent `expect(...).matcher(...)` API instead of bare `assert`
statements.

### Basic & Identity Assertions

```typescript
expect(result).toBe(42);              // strict equality (===)
expect(user).toEqual({ id: 1, name: "Alice" }); // deep equality for objects/arrays
expect(isActive).toBe(true);
expect(errorMessage).toBeNull();

expect(userRoles).toContain("admin");
expect(items).toHaveLength(3);
expect(new Set(receivedIds)).toEqual(new Set([1, 2, 3]));
```

### Floating-Point Comparisons

```typescript
expect(0.1 + 0.2).toBeCloseTo(0.3);                    // default precision: 2 decimals
expect(calculateInterest(1000, 0.05)).toBeCloseTo(50.0, 1);
```

### Exception Testing

```typescript
it("throws when dividing by zero", () => {
  expect(() => divide(10, 0)).toThrow("division by zero");
});

// For async functions, await the rejection instead:
it("rejects when the user is not found", async () => {
  await expect(fetchUser("missing-id")).rejects.toThrow(UserNotFoundError);
});
```

---

## Test Lifecycle & Fixtures

### Setup & Teardown Hooks

```typescript
import { beforeEach, afterEach, describe, it, expect } from "vitest";

describe("OrderRepository", () => {
  let db: TestDatabase;

  beforeEach(async () => {
    db = await connectTestDb();
    await db.createTables();
  });

  afterEach(async () => {
    await db.dropTables();
    await db.close();
  });

  it("persists a new order", async () => {
    const repo = new OrderRepository(db);
    const order = await repo.save({ id: "1", status: "PENDING" });
    expect(order.id).toBe("1");
  });
});
```

| Hook | Scope |
|---|---|
| `beforeEach` / `afterEach` | Runs before/after **every** test in the enclosing `describe` — the default, and usually the right choice |
| `beforeAll` / `afterAll` | Runs **once** before/after all tests in the enclosing `describe` — for genuinely expensive, shareable setup |

### Parameterized Testing

`it.each` (or `test.each`) runs one test body against a table of cases — the
TypeScript equivalent of `@pytest.mark.parametrize`, satisfying Mirror Rule #4:

```typescript
it.each([
  ["REGULAR", 100, 0.0],
  ["SILVER", 100, 10.0],
  ["GOLD", 100, 20.0],
])("applies the correct discount for %s tier", (status, amount, expectedDiscount) => {
  const processor = new DiscountProcessor();
  expect(processor.calculateDiscount(status, amount)).toBe(expectedDiscount);
});
```

---

## Mocking Mechanics in Depth

### Creating a Mock

```typescript
import { vi } from "vitest"; // Jest: use `jest` instead of `vi` — same API shape

const mockNotifier: Notifier = {
  send: vi.fn().mockResolvedValue(true),
};
```

### Common Mock Assertions

```typescript
expect(mockNotifier.send).toHaveBeenCalledOnce();
expect(mockNotifier.send).toHaveBeenCalledWith("alice@example.com", "Welcome!");
expect(mockNotifier.send).not.toHaveBeenCalled();

expect(mockNotifier.send).toHaveBeenCalledTimes(1);
```

### Module Mocking

Unlike Python's runtime `unittest.mock.patch` (which needs the "patch where
used, not where defined" rule because Python resolves the imported name at call
time), TypeScript's module system makes this simpler: **inject the dependency
via the constructor**, and there's nothing to patch at all — pass the mock
directly.

```typescript
// The component takes its dependency as a constructor parameter...
class OrderProcessor {
  constructor(private readonly notifier: Notifier) {}

  async processOrder(order: Order): Promise<void> {
    if (order.status !== "PENDING") {
      throw new Error("Order has already been processed.");
    }
    order.status = "PROCESSED";
    await this.notifier.send(order.customerEmail, "Order confirmed");
  }
}

// ...so the test just passes a mock in. No patching required.
it("notifies the customer when an order is processed", async () => {
  const mockNotifier: Notifier = { send: vi.fn().mockResolvedValue(true) };
  const processor = new OrderProcessor(mockNotifier);

  await processor.processOrder({ id: "1", status: "PENDING", customerEmail: "a@b.com" });

  expect(mockNotifier.send).toHaveBeenCalledWith("a@b.com", "Order confirmed");
});
```

When a dependency genuinely can't be constructor-injected (a module-level
import, e.g. a legacy or third-party module), `vi.mock("./module-path")` (Jest:
`jest.mock(...)`) replaces the entire module for the test file — the closest
TypeScript equivalent to Python's `@patch`, and it has the same "mock where it's
imported" caveat.

```typescript
vi.mock("./email-gateway", () => ({
  sendEmail: vi.fn().mockResolvedValue(undefined),
}));
```

### Spies on Real Implementations

```typescript
import { vi } from "vitest";

const logger = { info: (msg: string) => console.log(msg) };
const spy = vi.spyOn(logger, "info");

logger.info("hello");

expect(spy).toHaveBeenCalledWith("hello"); // the real implementation still ran
```

---

## "Hard to Write Unit Tests" = Code Design Flaws

Language-agnostic — see the [general diagnosis table](../general/testing-principles-detailed.md#hard-to-write-unit-tests--code-design-flaws).
The fix in TypeScript is almost always [Dependency Injection](./architecture-guide-detailed.md#pattern-1-dependency-injection-di) —
constructor injection specifically sidesteps the need for module mocking entirely.

---

## The Testing Pyramid 🔺

Language-agnostic — see the [general Testing Pyramid](../general/testing-principles-detailed.md#the-testing-pyramid-).
TypeScript's three layers, concretely: Vitest/Jest unit tests (above), [integration
tests against a real test DB](#integration-testing-in-practice), and
[Playwright E2E tests](#end-to-end-e2e-testing-in-practice).

---

## Complete Practical Example (Mirror Rule Applied)

### Production Source Code (`src/services/order-processor.ts`)

```typescript
export interface Order {
  id: string;
  status: "PENDING" | "PROCESSED" | "COMPLETED";
}

export interface Notifier {
  sendConfirmation(orderId: string): void;
}

export class ConsoleNotifier implements Notifier {
  sendConfirmation(orderId: string): void {
    console.log(`Sending confirmation for order ${orderId}...`);
  }
}

export class OrderProcessor {
  processOrder(order: Order, notifier: Notifier): void {
    if (order.status !== "PENDING") {
      throw new Error("Order has already been processed.");
    }
    order.status = "PROCESSED";
    notifier.sendConfirmation(order.id);
  }
}
```

### Mirrored Test File (`src/services/order-processor.test.ts`)

```typescript
import { describe, it, expect, vi } from "vitest";
import { OrderProcessor, ConsoleNotifier, type Order, type Notifier } from "./order-processor";

describe("ConsoleNotifier", () => {
  it("sendConfirmation logs a confirmation message", () => {
    const logSpy = vi.spyOn(console, "log").mockImplementation(() => {});
    const notifier = new ConsoleNotifier();

    notifier.sendConfirmation("101");

    expect(logSpy).toHaveBeenCalledWith("Sending confirmation for order 101...");
    logSpy.mockRestore();
  });
});

describe("OrderProcessor", () => {
  describe("processOrder", () => {
    it("updates status and notifies on a pending order", () => {
      const processor = new OrderProcessor();
      const mockNotifier: Notifier = { sendConfirmation: vi.fn() };
      const validOrder: Order = { id: "123", status: "PENDING" };

      processor.processOrder(validOrder, mockNotifier);

      expect(validOrder.status).toBe("PROCESSED");
      expect(mockNotifier.sendConfirmation).toHaveBeenCalledWith("123");
    });

    it("throws and does not notify when the order is already processed", () => {
      const processor = new OrderProcessor();
      const mockNotifier: Notifier = { sendConfirmation: vi.fn() };
      const completedOrder: Order = { id: "456", status: "COMPLETED" };

      expect(() => processor.processOrder(completedOrder, mockNotifier)).toThrow(
        "Order has already been processed.",
      );
      expect(mockNotifier.sendConfirmation).not.toHaveBeenCalled();
    });
  });
});
```

---

## Testing Async Code

Unlike Python (which needs the `pytest-asyncio` plugin), Vitest and Jest support
`async` test functions natively — just `await` the code under test:

```typescript
async function fetchUser(userId: string): Promise<{ id: string; name: string }> {
  await new Promise((resolve) => setTimeout(resolve, 10));
  return { id: userId, name: "Alice" };
}

it("returns the expected shape", async () => {
  const result = await fetchUser("1");
  expect(result).toEqual({ id: "1", name: "Alice" });
});
```

Mocking an async collaborator just needs the mock function to return a resolved
(or rejected) `Promise`:

```typescript
it("awaits the notifier", async () => {
  const mockNotifier = { send: vi.fn().mockResolvedValue(true) };

  await processOrderAsync("1", mockNotifier);

  expect(mockNotifier.send).toHaveBeenCalledWith("1");
});

it("propagates a notifier failure", async () => {
  const mockNotifier = { send: vi.fn().mockRejectedValue(new Error("SMTP down")) };

  await expect(processOrderAsync("1", mockNotifier)).rejects.toThrow("SMTP down");
});
```

---

## Integration Testing in Practice

[Integration testing, in concept](../general/testing-principles-detailed.md#the-testing-pyramid-) —
a real test-DB fixture:

```typescript
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { createApp } from "../src/app";
import { connectTestDb, type TestDatabase } from "./test-db";

describe("POST /users", () => {
  let db: TestDatabase;
  let app: ReturnType<typeof createApp>;

  beforeEach(async () => {
    db = await connectTestDb();
    await db.migrate();
    app = createApp(db);
  });

  afterEach(async () => {
    await db.reset();
    await db.close();
  });

  it("persists a new user to the database", async () => {
    const response = await app.request("/users", {
      method: "POST",
      body: JSON.stringify({ email: "alice@example.com", password: "SecurePass123!" }),
    });

    expect(response.status).toBe(201);
    const savedUser = await db.users.findByEmail("alice@example.com");
    expect(savedUser).not.toBeNull();
    expect(savedUser?.passwordHash).not.toBe("SecurePass123!"); // never stored in plaintext
  });
});
```

For a database that behaves exactly like production — not an in-memory
stand-in — spin up a real, disposable instance per test run with
**Testcontainers** (`testcontainers` npm package) instead of a long-lived shared
test database.

---

## End-to-End (E2E) Testing in Practice

TypeScript is Playwright's native language — a critical-path E2E test against
staging:

```typescript
import { test, expect } from "@playwright/test";

test("user can register and see the welcome page", async ({ page }) => {
  await page.goto("https://staging.example.com/register");

  await page.fill("input[name='email']", "alice@example.com");
  await page.fill("input[name='password']", "SecurePass123!");
  await page.click("button[type='submit']");

  await expect(page.getByText("Welcome, Alice!")).toBeVisible();
});
```

Because this layer is slow and can be flaky on shared infrastructure, run it on
a separate CI schedule from unit/integration tests rather than gating every
commit on it.

---

## Testing Background Tasks (BullMQ)

A unit test for a queue worker should verify the job's **logic**, not the real
Redis/queue infrastructure — test the worker's processor function directly.

```typescript
// src/queues/image-worker.ts
export async function processImageJob(
  data: { imageId: string; width: number; height: number },
  deps: { getImage: typeof getImageFromDb; resize: typeof resizeImage; markProcessed: typeof markImageAsProcessed },
): Promise<void> {
  const imageRecord = await deps.getImage(data.imageId);
  await deps.resize(imageRecord.path, data.width, data.height);
  await deps.markProcessed(data.imageId);
}
```

```typescript
// src/queues/image-worker.test.ts
import { describe, it, expect, vi } from "vitest";
import { processImageJob } from "./image-worker";

describe("processImageJob", () => {
  it("resizes the image and marks it processed", async () => {
    const deps = {
      getImage: vi.fn().mockResolvedValue({ path: "test.jpg" }),
      resize: vi.fn().mockResolvedValue(undefined),
      markProcessed: vi.fn().mockResolvedValue(undefined),
    };

    await processImageJob({ imageId: "1", width: 100, height: 100 }, deps);

    expect(deps.getImage).toHaveBeenCalledWith("1");
    expect(deps.resize).toHaveBeenCalledWith("test.jpg", 100, 100);
    expect(deps.markProcessed).toHaveBeenCalledWith("1");
  });
});
```

Passing collaborators as an explicit `deps` parameter (rather than importing
them at module scope) is the same constructor-injection idea applied to a
standalone function — it's what makes this test possible without any module
mocking.

---

## Code Coverage

See the [general coverage philosophy](../general/testing-principles-detailed.md#code-coverage)
(quantitative vs. qualitative, target ~85–95%). In TypeScript:

```bash
# Vitest
vitest run --coverage

# Jest
jest --coverage
```
