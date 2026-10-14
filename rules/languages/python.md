## Python

- Target 3.11+. Use modern typing: `list[str]`, `dict[str, int]`, `X | None`, no `typing.List`/`Optional` imports for these.
- Full type hints on every function signature and dataclass field. Code should pass `mypy --strict` (or `pyright` strict). No bare `Any`; use `object` or a `Protocol`/`TypeVar` if the type is genuinely open.
- Docstrings on public modules, classes, and functions: one-line summary, blank line, then `Args`/`Returns`/`Raises` as needed. Document at the declaration — don't leave callers to infer the contract from the body.
- Prefer `dataclasses` (or `pydantic` when validation/serialization is needed) over ad-hoc dicts for structured data.
- Use `pathlib.Path`, not `os.path`. Use f-strings, not `%` or `.format()`.
- Errors: raise specific exceptions; define a small custom exception hierarchy per package rooted at one base class. Never `except:` bare or `except Exception` without re-raising or handling deliberately. Never swallow.
- Async: don't mix blocking I/O into `async` code paths. No `time.sleep` in coroutines; use `asyncio.sleep`. Don't create fire-and-forget tasks without holding a reference.
- Prefer comprehensions and generators over manual accumulation loops; prefer generators for large/streamed data.
- Structure: keep business logic out of I/O/framework layers. Pure functions where feasible for testability.
- Logging: stdlib `logging` only — never `print` in library/service code. One `logger = logging.getLogger(__name__)` per module; libraries attach only a `NullHandler`, and only the application entry point configures handlers/levels (`logging.config.dictConfig`). F-strings in log calls are fine (`logger.info(f"x {x}")`) — enforce with ruff `T20` (no `print`) and `LOG`, keep `G004` off; just don't build expensive strings in hot `DEBUG` paths. `logger.exception(...)` inside `except` to keep the traceback; pass context via `extra=` / `contextvars` + a `Filter`, and emit JSON in production (`python-json-logger` or `structlog` wrapping stdlib). Never log secrets or PII.
- Tooling baseline: `ruff` (lint + format), `mypy`/`pyright`, `pytest`. Assume these run in CI; write code that passes them.
- Idioms: `enumerate()`/`zip()`/`.items()` over index loops; truthiness (`if not items:`) never `== True`; context managers for anything needing cleanup; `@functools.wraps` on decorators; `@dataclass(frozen=True)` for events/DTOs; properties for validated/computed attributes. No `import *`; imports stdlib → third-party → local. Don't shadow builtins (`list`, `str`, `type`) or use `l`/`O`/`I` as names. Naming: `snake_case` functions/variables, `CapWords` classes and exceptions, `UPPER_SNAKE_CASE` constants.
- Concurrency model: `asyncio` for I/O-bound with async-native libraries (`httpx`, `asyncpg`); `ThreadPoolExecutor` for I/O-bound with sync-only libraries; `ProcessPoolExecutor` or a background worker for CPU-bound. One blocking call (`requests`, a sync DB driver) inside `async def` stalls every coroutine. Run independent awaitables with `asyncio.gather`.
- Config: validated at startup with `pydantic.BaseSettings` (secrets manager > env > `.env` > defaults); fail fast on a missing value.
