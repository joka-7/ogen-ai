# Python — Coding Implementation Guide (Short)

Cheat sheet for line-by-line, function, and class-level Python code quality.
Full explanations and code samples: [coding-guide-detailed.md](./coding-guide-detailed.md).
Language-agnostic rationale: [General Coding Principles](../general/coding-principles-short.md).

## 6 Principles of Coding

| Principle | In one line |
|---|---|
| **Beautiful ✨** | Declarative over imperative — state intent, let the framework/abstraction do the work. |
| **Readable 📖** | Code is read more than written — use typed models (Pydantic/dataclass) over raw dict access. |
| **Explicit 🎯** | No magic — dependencies and config are visible and injected, not hidden in globals/env lookups. |
| **Simple 👌** | Simplest solution that works — prefer comprehensions/ORMs over manual loops/SQL. |
| **Scalable 🚀** | Offload slow, synchronous work to background queues (Celery); don't block the request. |
| **Consistent 🔄** | Same naming, URL, and response-envelope conventions everywhere in the codebase. |

## Guidelines (PEP 8 essentials)

- **Indentation:** 4 spaces, never tabs.
- **Line length:** ≤ 79 chars code / ≤ 72 docstrings (PEP 8 default — many teams use Black's 88 or 99–120 instead; match your formatter config).
- **Blank lines:** 2 between top-level defs/classes, 1 between methods.
- **Imports:** stdlib → third-party → local, alphabetized within each group; never `import *`.
- **Strings:** pick one quote style per project, be consistent.
- **Comments:** block comments above code; inline comments ≥ 2 spaces after statement, used sparingly.
- **Docstrings:** `"""One-line summary, then blank line, then Args/Returns/Raises."""`
- **Type hints:** annotate variables, parameters, and return types.
- **Whitespace:** space around binary operators; none inside `()`/`[]`/`{}`; none before `,`/`:`; none around `=` for kwargs/defaults.

## Naming Cheat Sheet

| Entity | Style | Example |
|---|---|---|
| Variables / functions | `snake_case` | `user_name`, `get_user_profile()` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_CONNECTIONS` |
| Classes / Exceptions | `CapWords` | `UserProfile`, `InvalidInputError` |
| Dunders | `__name__` | `__init__`, `__str__` |
| Modules / packages | short lowercase | `db_utils.py`, `utilities` |

Name methods for **usage**, not internal detail (`get_user_details()`, not `get_user_as_list()`).

**Avoid:** `l`/`O`/`I` as identifiers, unclear single letters outside tight loops, redundant
`_list`/`_dict`/`_data` suffixes, and shadowing builtins (`list`, `str`, `sum`, `type`).

## Pythonic Idioms

- **Iterate:** `enumerate()` for index+value, `zip()` for parallel sequences, `.items()` for dicts.
- **Immutability:** `@dataclass(frozen=True)` for events/DTOs — self-documenting and mutation-safe.
- **Truthiness:** `if not my_list:` / `if name:` / `if not count:` — never `== True` / `== False`.
- **Comprehensions:** list/set/dict comprehensions and generator expressions over manual `for`-append loops.
- **Context managers:** `with open(...) as f:` — guarantees cleanup even on error; `@contextmanager` for custom ones.
- **Decorators:** `@functools.wraps` when wrapping functions to preserve metadata.
- **Properties:** `@property` / `@x.setter` for validated or computed attributes.
- **Dunders:** implement `__str__`, `__repr__`, `__len__`, `__getitem__`, `__contains__` to integrate with builtins.
- **Lambdas:** short, single-expression callbacks for `sorted()`, `map()`, `filter()`.
- **Reuse libraries:** don't reinvent `requests`, `numpy`, `pandas`, etc.
- **Metaclasses:** advanced/rare — prefer mixins, decorators, or `__init_subclass__` first.

## Async I/O Cheat Sheet

- `async`/`await` = **I/O-bound concurrency** on one thread — not parallelism, doesn't speed up CPU-bound work.
- Entry point: `asyncio.run(main())`. Run independent awaitables concurrently with `asyncio.gather(...)`.
- **Never block the event loop** — one sync/blocking call (`requests`, `time.sleep`, a sync DB driver) inside an `async def` freezes every other coroutine on it. Use async-native libraries (`httpx`, `asyncpg`, …) and `await asyncio.sleep()`.
- `async with` / `async for` — same shape as sync context managers/iterators, `async` in front.
- **Pick the right tool:** `asyncio` for I/O-bound + async-native libs; `ThreadPoolExecutor` for I/O-bound + sync-only libs; `ProcessPoolExecutor` (or a background worker) for CPU-bound work.
- Test with `pytest-asyncio` — see the [testing guide](./testing-guide-short.md).
