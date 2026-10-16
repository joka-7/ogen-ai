# Python — Testing Guide (Detailed)

pytest and `unittest.mock` mechanics for writing fast, isolated, repeatable unit
tests in Python, plus practical integration/E2E/async/background-task testing.
For the condensed version, see [testing-guide-short.md](./testing-guide-short.md).

> **This guide assumes the [General Testing Principles](../general/testing-principles-detailed.md)** —
> it shows how those language-agnostic concepts look with pytest. Read that first
> for the "why"; this guide is the "how, in Python."

> Related Python guides: [Coding Guide](./coding-guide-detailed.md) ·
> [Architecture Guide](./architecture-guide-detailed.md)

## Table of Contents

1. [The Unit Test Mirror Rule & Naming Conventions](#the-unit-test-mirror-rule--naming-conventions)
2. [The Anatomy of a Good Unit Test: AAA Pattern](#the-anatomy-of-a-good-unit-test-aaa-pattern)
3. [Assertions & Introspection in Depth](#assertions--introspection-in-depth)
4. [Pytest Fixtures & Lifecycle Management](#pytest-fixtures--lifecycle-management)
5. [Mocking & @patch Mechanics in Depth](#mocking--patch-mechanics-in-depth)
6. ["Hard to Write Unit Tests" = Code Design Flaws](#hard-to-write-unit-tests--code-design-flaws)
7. [The Testing Pyramid 🔺](#the-testing-pyramid-)
8. [Complete Practical Example (Mirror Rule Applied)](#complete-practical-example-mirror-rule-applied)
9. [Testing Async Code](#testing-async-code)
10. [Integration Testing in Practice](#integration-testing-in-practice)
11. [End-to-End (E2E) Testing in Practice](#end-to-end-e2e-testing-in-practice)
12. [Testing Background Tasks (Celery)](#testing-background-tasks-celery)
13. [Code Coverage (pytest-cov)](#code-coverage-pytest-cov)

---

## The Unit Test Mirror Rule & Naming Conventions

The [general Mirror Rule](../general/testing-principles-detailed.md#the-mirror-rule--naming-conventions),
with pytest's specific naming conventions:

```text
src/
└── app/
    ├── services.py          <-- Source file
    └── user_service.py
tests/
└── app/
    ├── test_services.py     <-- Mirrored test file
    └── test_user_service.py
```

### The 4 Strict Rules of Mirroring

1. **File Mirroring (1 file ↔ 1 test file):** every `<module>.py` in `src/` has exactly one `test_<module>.py` at the same relative path in `tests/`.
2. **Class Mirroring (1 class ↔ 1 test class):** every production class maps to a dedicated `Test`-prefixed test class (`OrderProcessor` ↔ `TestOrderProcessor`).
3. **Public Method Mirroring (1 public method ↔ 1 test method):** every public method has exactly one `test_`-prefixed test method (`process_order()` ↔ `test_process_order()`).
4. **All Scenarios Consolidated:** every validation path, edge case, success case, and exception for that public method lives inside that *single* test method — via `@pytest.mark.parametrize` or sequential AAA blocks.

### Naming Conventions

| Entity | Production source | Test equivalent | Example |
|---|---|---|---|
| Directory | `src/domain/services/` | `tests/domain/services/` | Matching path relative to root |
| Module file | `payment.py` | `test_payment.py` | Prefixed with `test_` |
| Class | `PaymentGateway` | `TestPaymentGateway` | Prefixed with `Test` |
| Public method | `charge_card()` | `test_charge_card()` | Prefixed with `test_` |

---

## The Anatomy of a Good Unit Test: AAA Pattern

The [general AAA pattern](../general/testing-principles-detailed.md#the-anatomy-of-a-good-unit-test-aaa-pattern)
in pytest:

```python
def test_calculate_total_with_tax():
    # 1. ARRANGE
    calculator = TaxCalculator(tax_rate=0.20)
    item_price = 100.0

    # 2. ACT
    total = calculator.calculate_total(item_price)

    # 3. ASSERT
    assert total == 120.0
```

---

## Assertions & Introspection in Depth

Pytest uses plain `assert` statements, enriched with detailed failure introspection.

### Basic & Identity Assertions

```python
assert result == 42
assert is_active is True
assert error_message is None

assert "admin" in user_roles
assert len(items) == 3
assert set(received_ids) == {1, 2, 3}
```

### Floating-Point Comparisons (`pytest.approx`)

Standard float arithmetic introduces precision inaccuracies (`0.1 + 0.2 != 0.3`).

```python
import pytest

assert 0.1 + 0.2 == pytest.approx(0.3)
assert calculate_interest(1000, 0.05) == pytest.approx(50.0, rel=1e-3)
```

### Exception Testing (`pytest.raises`)

```python
import pytest

def test_divide_by_zero_raises_exception():
    with pytest.raises(ZeroDivisionError, match="division by zero"):
        divide(10, 0)
```

---

## Pytest Fixtures & Lifecycle Management

Fixtures provide reusable, modular setup/teardown logic.

### Custom Fixture Definition

```python
import pytest

@pytest.fixture(scope="function")
def sample_user():
    """Provides a fresh user instance for each test."""
    return User(id=1, username="test_user", status="ACTIVE")
```

### Fixture Lifecycle Scopes

| Scope | Lifetime | Best used for |
|---|---|---|
| `function` (default) | Re-created for every test | Isolated object state and mocks |
| `class` | Once per test class | Shared class-level configuration |
| `module` | Once per test file | Read-only data loading |
| `session` | Once per test suite run | Global test container/setup |

### Setup & Teardown with `yield`

Code before `yield` is setup (Arrange); code after `yield` is teardown/cleanup.

```python
@pytest.fixture
def temp_database():
    # --- SETUP ---
    db = connect_test_db()
    db.create_tables()

    yield db  # Test executes here

    # --- TEARDOWN ---
    db.drop_tables()
    db.close()
```

### Parameterized Testing

Runs a single test method multiple times with different datasets — essential for
Mirror Rule #4 (grouping every scenario into one test method).

```python
@pytest.mark.parametrize("status, amount, expected_discount", [
    ("REGULAR", 100, 0.0),
    ("SILVER", 100, 10.0),
    ("GOLD", 100, 20.0),
])
def test_calculate_discount(status, amount, expected_discount):
    processor = DiscountProcessor()
    assert processor.calculate_discount(status, amount) == expected_discount
```

### Essential Built-In Fixtures

| Fixture | Description | Example usage |
|---|---|---|
| `capsys` | Captures stdout/stderr | `captured = capsys.readouterr()` |
| `tmp_path` | Temporary `pathlib.Path` unique to the test | `file = tmp_path / "test.txt"` |
| `monkeypatch` | Safely overrides attrs/env vars/dict items | `monkeypatch.setenv("ENV", "TEST")` |
| `mocker` (pytest-mock) | Wraps `unittest.mock` | `mock_obj = mocker.MagicMock(spec=Notifier)` |

---

## Mocking & @patch Mechanics in Depth

Mocking isolates the unit under test by replacing real dependencies with
controllable fakes (`MagicMock`).

### What Is a Mock?

A `MagicMock` records every interaction (calls, args, counts) and lets you
pre-define return values or side effects.

```python
from unittest.mock import MagicMock

mock_notifier = MagicMock(spec=Notifier)
mock_notifier.send_confirmation.return_value = True
```

### Common Mock Assertions

```python
mock_notifier.send_confirmation.assert_called_once_with(order_id=101)
mock_notifier.send_confirmation.assert_called_with(order_id=101)
mock_notifier.send_confirmation.assert_not_called()

assert mock_notifier.send_confirmation.call_count == 1
```

### 📍 The Golden Rule: "Patch Where Used, Not Where Defined"

Always patch the dependency where it is **imported and used by the module under
test**, not where it was originally defined.

```python
# Production Code (src/services.py) imports Notifier from src.notifier
from src.notifier import Notifier

# ❌ INCORRECT (patching where defined) — has no effect on src/services.py
@patch('src.notifier.Notifier')
def test_process_order_wrong(mock_notifier_class):
    ...

# ✅ CORRECT (patching where used, inside src/services.py)
@patch('src.services.Notifier')
def test_process_order_right(mock_notifier_class):
    ...
```

### Three Ways to Apply `@patch`

**Style 1 — Decorator:** injects the mock as a function argument.

```python
from unittest.mock import patch

@patch('src.services.Notifier')
def test_process_order(mock_notifier_class):
    mock_instance = mock_notifier_class.return_value
    # Execute test...
```

**Style 2 — Context manager:** scopes the mock strictly to the `with` block.

```python
def test_process_order_context():
    with patch('src.services.Notifier') as mock_notifier_class:
        mock_instance = mock_notifier_class.return_value
```

**Style 3 — Manual `start()`/`stop()`:** useful when a mock spans multiple test methods.

```python
class TestOrderService:
    def setup_method(self):
        self.patcher = patch('src.services.Notifier')
        self.mock_notifier = self.patcher.start()

    def teardown_method(self):
        self.patcher.stop()
```

### Stacking `@patch` Decorators

Mock arguments are injected **bottom-up**:

```python
@patch('src.services.audit_logger')   # injected SECOND -> mock_audit
@patch('src.services.email_gateway')  # injected FIRST  -> mock_email
def test_complex_flow(mock_email, mock_audit):
    assert mock_email is not None
    assert mock_audit is not None
```

### `@patch` Decorator vs. `mocker` Fixture

| Feature | `@patch` decorator | `mocker` fixture (pytest-mock) |
|---|---|---|
| Import required | `from unittest.mock import patch` | None (builtin plugin fixture) |
| Injection style | Appends extra arguments to the test | Scoped within the function body |
| Primary use case | Patching direct module imports | Injecting mocks into DI parameters |
| Function signature | Alters argument list | Keeps argument list clean |

```python
# Approach 1: mocker fixture (clean signature)
def test_with_mocker(mocker):
    mock_notifier = mocker.MagicMock(spec=Notifier)
    processor = OrderProcessor()
    processor.process_order(Order(id=1, status="PENDING"), notifier=mock_notifier)
    mock_notifier.send_confirmation.assert_called_once_with(order_id=1)

# Approach 2: @patch decorator (direct import replacement)
@patch('src.services.Notifier')
def test_with_patch(mock_notifier_class):
    mock_instance = mock_notifier_class.return_value
    processor = OrderProcessor()
    # Code relying on internal Notifier instantiation
```

---

## "Hard to Write Unit Tests" = Code Design Flaws

Language-agnostic — see the [general diagnosis table](../general/testing-principles-detailed.md#hard-to-write-unit-tests--code-design-flaws).
The fix in Python is almost always [Dependency Injection](./architecture-guide-detailed.md#pattern-1-dependency-injection-di).

---

## The Testing Pyramid 🔺

Language-agnostic — see the [general Testing Pyramid](../general/testing-principles-detailed.md#the-testing-pyramid-)
(including the Testing Trophy note). Python's three layers, concretely: pytest
unit tests (below), [integration tests against a real test DB](#integration-testing-in-practice),
and [Playwright E2E tests](#end-to-end-e2e-testing-in-practice).

---

## Complete Practical Example (Mirror Rule Applied)

### Production Source Code (`src/services.py`)

```python
from dataclasses import dataclass

@dataclass
class Order:
    id: int
    status: str = "PENDING"

class Notifier:
    def send_confirmation(self, order_id: int) -> None:
        """Sends a confirmation message for an order."""
        print(f"Sending confirmation for order {order_id}...")

class OrderProcessor:
    def process_order(self, order: Order, notifier: Notifier) -> None:
        """Processes a pending order and notifies the user."""
        if order.status != "PENDING":
            raise ValueError("Order has already been processed.")

        order.status = "PROCESSED"
        notifier.send_confirmation(order_id=order.id)
```

### Mirrored Test File (`tests/test_services.py`)

```python
from unittest.mock import MagicMock
import pytest
from src.services import Order, Notifier, OrderProcessor

class TestNotifier:
    def test_send_confirmation(self, capsys):
        """
        Tests all scenarios for Notifier.send_confirmation:
        1. Executes confirmation print statement for given order ID.
        """
        notifier = Notifier()
        notifier.send_confirmation(order_id=101)

        captured = capsys.readouterr()
        assert "Sending confirmation for order 101..." in captured.out

class TestOrderProcessor:
    def test_process_order(self):
        """
        Tests all scenarios for OrderProcessor.process_order in one method:
        1. Success Path: valid pending order updates status and triggers notification.
        2. Error Path: non-pending order raises ValueError and halts notification.
        """
        processor = OrderProcessor()

        # --- Scenario 1: Success Path ---
        mock_notifier_success = MagicMock(spec=Notifier)
        valid_order = Order(id=123, status="PENDING")

        processor.process_order(order=valid_order, notifier=mock_notifier_success)

        assert valid_order.status == "PROCESSED"
        mock_notifier_success.send_confirmation.assert_called_once_with(order_id=123)

        # --- Scenario 2: Error Path (Already Processed) ---
        mock_notifier_failure = MagicMock(spec=Notifier)
        completed_order = Order(id=456, status="COMPLETED")

        with pytest.raises(ValueError, match="Order has already been processed."):
            processor.process_order(order=completed_order, notifier=mock_notifier_failure)

        mock_notifier_failure.send_confirmation.assert_not_called()
```

---

## Testing Async Code

`async def` functions need an event loop running under them — a plain `def test_x():`
can't `await` anything. Add the `pytest-asyncio` plugin and mark the test:

```python
# src/services.py
import asyncio

async def fetch_user(user_id: int) -> dict:
    await asyncio.sleep(0.1)
    return {"id": user_id, "name": "Alice"}
```

```python
# tests/test_services.py
import pytest
from src.services import fetch_user

@pytest.mark.asyncio
async def test_fetch_user_returns_expected_shape():
    # Arrange / Act
    result = await fetch_user(1)

    # Assert
    assert result == {"id": 1, "name": "Alice"}
```

Mocking an async collaborator needs an async-aware mock so `await mock(...)` doesn't
raise `TypeError: object MagicMock can't be used in 'await' expression`:

```python
from unittest.mock import AsyncMock

async def test_process_order_awaits_notifier():
    mock_notifier = AsyncMock(spec=AsyncNotifier)

    await process_order_async(order_id=1, notifier=mock_notifier)

    mock_notifier.send.assert_awaited_once_with(order_id=1)
```

`MagicMock(spec=...)` auto-detects async methods on the spec'd class and returns
`AsyncMock`s for them since Python 3.8 — but reach for `AsyncMock` explicitly when
mocking a bare async function/callable with no class to infer a spec from.

---

## Integration Testing in Practice

[Integration testing, in concept](../general/testing-principles-detailed.md#the-testing-pyramid-) —
a real test-DB fixture with FastAPI's `TestClient`:

```python
# tests/integration/test_user_registration_flow.py
import pytest
from fastapi.testclient import TestClient
from src.app import create_app
from src.db import Base, engine, SessionLocal
from src.models import User

@pytest.fixture
def test_db():
    """Creates a fresh schema in a real test database for each test, then tears it down."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    return TestClient(create_app())

def test_register_user_persists_to_database(client, test_db):
    # Act — hits the real route -> service -> repository -> test database
    response = client.post(
        "/users", json={"email": "alice@example.com", "password": "SecurePass123!"}
    )

    # Assert — verify both the HTTP contract and the actually persisted row
    assert response.status_code == 201
    saved_user = test_db.query(User).filter_by(email="alice@example.com").first()
    assert saved_user is not None
    assert saved_user.password_hash != "SecurePass123!"   # never stored in plaintext
```

For a database that behaves exactly like production — not a SQLite stand-in — spin
up a real, disposable instance per test run with **Testcontainers**
(`testcontainers-python`) instead of a long-lived shared test database:

```python
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16") as postgres:
        yield postgres.get_connection_url()
```

---

## End-to-End (E2E) Testing in Practice

[E2E testing, in concept](../general/testing-principles-detailed.md#the-testing-pyramid-) —
a Playwright walkthrough against staging:

```python
# tests/e2e/test_registration_journey.py
from playwright.sync_api import Page, expect

def test_user_can_register_and_see_welcome_page(page: Page):
    page.goto("https://staging.example.com/register")

    page.fill("input[name='email']", "alice@example.com")
    page.fill("input[name='password']", "SecurePass123!")
    page.click("button[type='submit']")

    expect(page.get_by_text("Welcome, Alice!")).to_be_visible()
```

Because this layer is slow and can be flaky on shared infrastructure, run it on a
separate CI schedule from unit/integration tests (e.g. on merge to main, or
nightly) rather than gating every commit on it.

---

## Testing Background Tasks (Celery)

A unit test for a background task should verify the task's **logic**, not the real
database/network/library it depends on — mock every collaborator.

```python
# src/tasks/image_task.py
from celery import shared_task
from PIL import Image

@shared_task(bind=True, max_retries=3)
def image_task(self, image_id: int, width: int, height: int):
    """Background task to resize an image."""
    try:
        image_record = get_image_from_db(image_id)
        img = Image.open(image_record.path)
        img = img.resize((width, height))
        img.save(f"resized_{image_record.filename}")
        mark_image_as_processed(image_id)
        return True
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

```python
# tests/tasks/test_image_task.py
from unittest.mock import patch
from tasks.image_task import image_task

@patch('tasks.image_task.get_image_from_db')
@patch('tasks.image_task.mark_image_as_processed')
@patch('tasks.image_task.Image')  # mock Pillow's Image
def test_image_task_success(mock_image, mock_mark, mock_get_db):
    # 1. Arrange
    mock_get_db.return_value.path = "test.jpg"
    mock_get_db.return_value.filename = "test.jpg"

    # 2. Act
    result = image_task(image_id=1, width=100, height=100)

    # 3. Assert
    assert result is True
    mock_get_db.assert_called_once_with(1)
    mock_mark.assert_called_once_with(1)
    mock_image.open.return_value.resize.assert_called_once_with((100, 100))
```

This is fast (milliseconds, no real DB/network calls), reliable, and focused purely
on the task's own logic.

---

## Code Coverage (pytest-cov)

See the [general coverage philosophy](../general/testing-principles-detailed.md#code-coverage)
(quantitative vs. qualitative, target ~85–95%). In Python:

```bash
# Terminal summary report
pytest --cov=src

# Interactive HTML inspection report
pytest --cov=src --cov-report=html
```
