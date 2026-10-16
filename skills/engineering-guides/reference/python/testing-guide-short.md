# Python — Testing Guide (Short)

Cheat sheet for writing fast, isolated, repeatable unit tests with pytest.
Full explanations and code samples: [testing-guide-detailed.md](./testing-guide-detailed.md).
Language-agnostic version: [General Testing Principles](../general/testing-principles-short.md).

## 4 Core Principles

- **Isolation 🛡️** — no real DB/network/filesystem; mock every external dependency.
- **Fast ⚡** — milliseconds, so the suite runs constantly.
- **Repeatable 🔄** — same result every run, any environment.
- **Self-Contained 📦** — each test sets up and cleans up its own state.

## The Mirror Rule

1 source file ↔ 1 `test_<module>.py`, at the same relative path under `tests/`.
1 class ↔ 1 `Test<Class>`. 1 public method ↔ 1 `test_<method>()`, with **every**
scenario (success, edge cases, errors) consolidated into that one test method via
`@pytest.mark.parametrize` or sequential AAA blocks.

| Production | Test |
|---|---|
| `payment.py` | `test_payment.py` |
| `PaymentGateway` | `TestPaymentGateway` |
| `charge_card()` | `test_charge_card()` |

## AAA Pattern

**Arrange** (set up inputs/mocks) → **Act** (call the one method, one line) →
**Assert** (check return value, state, or mock calls).

## Assertions

```python
assert result == 42
assert 0.1 + 0.2 == pytest.approx(0.3)          # floats
with pytest.raises(ZeroDivisionError, match="division by zero"):
    divide(10, 0)
```

## Fixtures

```python
@pytest.fixture
def temp_database():
    db = connect_test_db()
    db.create_tables()
    yield db                    # setup above, teardown below
    db.drop_tables()
    db.close()
```

| Scope | Lifetime |
|---|---|
| `function` (default) | Per test |
| `class` | Per test class |
| `module` | Per test file |
| `session` | Per suite run |

Built-ins: `capsys` (stdout/stderr), `tmp_path` (temp dir), `monkeypatch` (env/attr
override), `mocker` (pytest-mock's `MagicMock` wrapper).

Use `@pytest.mark.parametrize("a,b,expected", [...])` to run one test method over
many scenarios.

## Mocking — the Golden Rule

**Patch where the name is used, not where it's defined.**

```python
# src/services.py does: from src.notifier import Notifier
@patch('src.services.Notifier')     # ✅ correct
def test_x(mock_notifier): ...

@patch('src.notifier.Notifier')     # ❌ wrong — no effect on services.py
def test_y(mock_notifier): ...
```

Three ways to patch: `@patch(...)` decorator (injects mock arg), `with patch(...)`
context manager (scoped), or manual `patcher.start()`/`.stop()` in
`setup_method`/`teardown_method`. Stacked decorators inject **bottom-up**.
`mocker.MagicMock(spec=...)` (pytest-mock) keeps the test signature clean; `@patch`
is best for direct module-import replacement.

## Hard-to-Test Code = Design Flaw

| Symptom | Fix |
|---|---|
| Needs a real DB/network | Dependency Injection |
| One test method is huge | Split — SRP violation |
| Can't observe the result | Return values instead of hidden side-effects |

## Testing Pyramid 🔺

**Unit** (base, fast, isolated, many) → **Integration** (modules + test DB, fewer) →
**E2E** (full app, slowest/brittlest, sparse — critical paths only).

## Async, Integration & E2E

- **Async:** mark tests `@pytest.mark.asyncio`, `await` the code under test; mock async collaborators with `AsyncMock` (not plain `MagicMock`) and assert with `assert_awaited_once_with(...)`.
- **Integration:** hit the real route → service → repository against a real test DB (fixture creates schema, yields a session, tears down after). Use **Testcontainers** for a disposable, production-like DB instead of a shared one.
- **E2E:** drive the whole app like a user would (Playwright/Selenium), against staging — never prod. Critical paths only; run on a separate, slower CI schedule than unit/integration.

## Coverage

```bash
pytest --cov=src --cov-report=html
```

Coverage is **quantitative** (how much ran), not **qualitative** (how well it was
checked). Target **85%–95%**, not a fragile 100%.
