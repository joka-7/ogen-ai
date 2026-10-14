# Python — Coding Implementation Guide (Detailed)

This is the detailed reference for writing clean, readable, and maintainable Python
code at the line-by-line, function, and class level. For the condensed version, see
[coding-guide-short.md](./coding-guide-short.md).

> **This guide assumes the [General Coding Principles](../general/coding-principles-detailed.md)** —
> it shows how those language-agnostic principles look in idiomatic Python. Read
> that first if you haven't; the "why" behind each principle below lives there.

> Related Python guides: [Architecture Guide](./architecture-guide-detailed.md) ·
> [Testing Guide](./testing-guide-detailed.md)

## Table of Contents

1. [Principles of Coding](#principles-of-coding)
2. [Guidelines](#guidelines)
3. [Naming Conventions](#naming-conventions)
4. [Names to Avoid](#names-to-avoid-)
5. [Pythonic Code](#pythonic-code)
6. [Async I/O (asyncio)](#async-io-asyncio)

---

## Principles of Coding

How the [six general principles](../general/coding-principles-detailed.md#the-6-principles-of-coding)
look in idiomatic Python.

### Beautiful ✨

Prefer **declarative** code over **imperative** code — let the framework handle
the boilerplate.

**Less beautiful — manual, imperative Django view:**

```python
# Manually handles HTTP methods, serialization, and responses. Verbose and mixes concerns.
def user_view(request, user_id):
    if request.method == 'GET':
        try:
            user = User.objects.get(pk=user_id)
            user_data = {"id": user.id, "username": user.username, "email": user.email}
            return JsonResponse(user_data, status=200)
        except User.DoesNotExist:
            return JsonResponse({"error": "Not Found"}, status=404)
        # ... must add similar blocks for POST, PUT, DELETE
```

**More beautiful — declarative Django REST Framework ViewSet:**

```python
from rest_framework import viewsets, permissions
from .models import User
from .serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    """API endpoint that allows users to be viewed or edited."""
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
```

One `ModelViewSet` transparently handles `GET /users/`, `GET /users/{id}/` (incl.
404), `POST`, `PUT`, `DELETE` — the `ViewSet` connects URL → model → serializer,
the `Serializer` defines the JSON shape and validation, and the framework owns
HTTP mechanics. Change exposed fields in one place (the serializer) instead of
hunting every manual dict construction.

### Readable 📖

Data structures that enforce a schema (Pydantic models, dataclasses) beat raw
dict access — the shape is documented by the type, not by convention.

```python
# Less readable — what is the shape of user_data? Typos like "emial" fail silently.
def process_user_payment(user_data: dict):
    print(f"Processing payment for user: {user_data['profile']['name']}")
    if user_data.get('payment_info') and user_data['payment_info'].get('is_active'):
        card_number = user_data['payment_info']['details']['card_num']

# More readable — self-documenting, IDE-assisted, validated.
from pydantic import BaseModel
from typing import Optional

class PaymentDetails(BaseModel):
    card_num: str
    expiry_date: str

class UserProfile(BaseModel):
    name: str
    email: str

class UserPaymentData(BaseModel):
    profile: UserProfile
    payment_info: Optional[PaymentDetails] = None
    is_active: bool

def process_user_payment(user_data: UserPaymentData):
    print(f"Processing payment for user: {user_data.profile.name}")
    if user_data.is_active and user_data.payment_info:
        card_number = user_data.payment_info.card_num
```

### Explicit 🎯

"Explicit is better than implicit" (Zen of Python).

```python
# Less explicit — hidden dependency on an env var, fails unexpectedly at runtime.
import os

class DatabaseConnection:
    def __init__(self):
        self.db_url = os.environ.get("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL not set!")

# More explicit — configuration is built once, validated fail-fast, and injected.
# (See the Architecture guide's Configuration Management Strategy for the full pattern.)
from pydantic_settings import BaseSettings

class AppConfig(BaseSettings):
    database_url: str    # matches env var DATABASE_URL (case-insensitive by default)
    secret_key: str       # matches env var SECRET_KEY

class DatabaseConnection:
    def __init__(self, config: AppConfig):
        self.db_url = config.database_url

config = AppConfig()   # raises a clear ValidationError at startup if either is missing
db_conn = DatabaseConnection(config=config)
```

### Simple 👌

"Simple is better than complex" (KISS).

```python
# More complex — manual SQL: verbose, injection-prone, couples app logic to schema.
def get_active_users(min_posts: int):
    conn = psycopg2.connect(...)
    cur = conn.cursor()
    sql = """
        SELECT u.id, u.username, p.post_count
        FROM users u
        JOIN (SELECT author_id, COUNT(*) AS post_count
              FROM posts GROUP BY author_id) p ON u.id = p.author_id
        WHERE u.is_active = TRUE AND p.post_count >= %s;
    """
    cur.execute(sql, (min_posts,))
    users = [{"id": r[0], "username": r[1], "posts": r[2]} for r in cur.fetchall()]
    cur.close()
    conn.close()
    return users

# Simpler — an ORM handles SQL generation and connection management.
from django.db.models import Count
from .models import User

def get_active_users(min_posts: int):
    return User.objects.filter(is_active=True) \
                       .annotate(post_count=Count('posts')) \
                       .filter(post_count__gte=min_posts) \
                       .values('id', 'username', 'post_count')
```

### Scalability 🚀

Offload slow, synchronous work to background task queues instead of making the
caller wait.

```python
# Less scalable — the user waits for a slow email send inside the request.
def register_user(request):
    user = User.objects.create(...)
    send_mail('Welcome!', 'Thank you for registering.', 'from@example.com', [user.email])
    return JsonResponse({"message": "User registered"}, status=201)

# More scalable — offload to a background worker (e.g. Celery); respond instantly.
from celery import shared_task

@shared_task
def send_welcome_email_task(user_email: str):
    send_mail('Welcome!', 'Thank you for registering.', 'from@example.com', [user_email])

def register_user(request):
    user = User.objects.create(...)
    send_welcome_email_task.delay(user.email)          # fast — just queues a message
    return JsonResponse({"message": "Registration processing"}, status=202)
```

### Consistent 🔄

Same naming, URL, and response-envelope conventions everywhere in the codebase.

```text
# Inconsistent
GET    /api/get_all_products/         # verb in URL, trailing slash
GET    /api/user-profile?id=123       # different naming, query parameter
POST   /api/addNewItem                # camelCase, no slash

# Consistent
GET    /api/v1/products/              # plural nouns, versioned
GET    /api/v1/users/123/             # resource ID in path
POST   /api/v1/products/              # same endpoint, different method
```

```jsonc
// Consistent JSON: every success response uses "data", snake_case fields
{ "data": [{ "name": "Laptop", "price": 1200 }] }
{ "data": { "id": 123, "username": "alex" } }
```

---

## Guidelines

Community-standard rules (largely PEP 8) that make code predictable to any Python
developer.

### Code Layout

| Aspect | Rule |
|---|---|
| **Indentation** | 4 spaces per level. Never mix tabs and spaces. |
| **Line length** | ≤ 79 chars for code, ≤ 72 for docstrings/comments. Break with parentheses, not backslashes. |
| **Line breaks** | Two blank lines between top-level functions/classes; one blank line between methods; blank lines sparingly inside functions for logical grouping. |
| **Imports** | Order: (1) standard library, (2) third-party, (3) local application — alphabetized within each group. Avoid `from module import *`. |
| **Strings** | Pick single or double quotes and stay consistent per project; use triple quotes for docstrings/multi-line strings. |
<!-- markdownlint-disable-next-line MD038 --><!-- the trailing space is the point: it shows the `# ` comment prefix -->
| **Comments** | Block comments precede code at the same indent, each line starts with `# `. Inline comments are separated by ≥ 2 spaces, used sparingly. |
| **Docstrings** | Triple double-quoted. First line: short summary. Blank line, then details (Args/Returns/Raises). |
| **Annotations** | Type-hint variables, parameters, and return values. |

> **Note:** 79/72 are PEP 8's own defaults. Many real-world Python codebases instead
> standardize on a formatter's line length (Black's 88, or a team standard of
> 99–120) — align this rule with whatever formatter config (`pyproject.toml`, etc.)
> your project actually enforces, rather than treating 79 as a universal law.

```python
# Imports — correct order
import os
import sys

import numpy as np
import requests

from my_package import my_module
from . import sibling_module
```

```python
def calculate_area(radius: float) -> float:
    """Calculate the area of a circle.

    Args:
        radius: The radius of the circle (must be positive).

    Returns:
        The area of the circle.

    Raises:
        ValueError: If the radius is not positive.
    """
    if radius <= 0:
        raise ValueError("Radius must be positive.")
    return 3.14159 * radius * radius
```

### Whitespace

- Two blank lines between top-level defs; one between methods.
- Surround binary operators (`=`, `==`, `+`, `and`, `in`, …) with a single space.
- No space directly inside `()`, `[]`, `{}`; no space before `,`/`:`/`;`.
- No space before the `(` of a call or the `[` of an index/slice.
- No spaces around `=` for keyword args / default parameter values.

```python
# Good
result = my_function(arg1, arg2, kwarg1='foo', kwarg2='bar')
item = my_list[0]
slice_of_list = my_list[1:3]

def func(param1, param2='default_value'):
    pass
```

---

## Naming Conventions

Method names should describe **usage**, not internal detail, so implementation can
change without breaking the interface:

```python
class UserData:
    # Better — describes usage, hides how data is actually fetched.
    def get_user_details(self, user_id: int) -> dict:
        return {"id": user_id, "name": "Jane Doe", "email": "jane@example.com"}
```

### Naming Styles (PEP 8)

| Entity | Style | Example |
|---|---|---|
| Variables | `snake_case` | `user_name`, `is_active` |
| Methods/functions | `snake_case` | `calculate_sum()`, `get_user_profile()` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_CONNECTIONS`, `DEFAULT_TIMEOUT` |
| Classes | `CapWords` (PascalCase) | `UserProfile`, `HttpRequest` |
| Dunders | `__dunder_name__` | `__init__()`, `__str__()` |
| Name-mangled attrs | `_ClassName__attr` | `self.__mangled` → `self._MyClass__mangled` |
| Exceptions | `CapWords`, often ending `Error` | `ValueError`, `InvalidInputError` |
| Enums | Class: `CapWords`; members: `UPPER_SNAKE_CASE` | `Color.RED` |
| TypeVar | Short `CapWords` | `T`, `K`, `V` |
| Packages | short, all-lowercase | `mypackage`, `utilities` |
| Modules | `snake_case`, short | `db_utils.py`, `string_helpers.py` |

```python
from enum import Enum, auto

class Color(Enum):
    RED = auto()
    GREEN = auto()
    BLUE = auto()
```

---

## Names to Avoid 🚫

Same [general rules](../general/coding-principles-detailed.md#names-to-avoid-),
Python-flavored:

| Issue | Why | Fix |
|---|---|---|
| Ambiguous letters `l`, `O`, `I` | Easily confused with `1` / `0` | `length`, `offset_value`, `identity_matrix` |
| Unclear single-letter names | Loses meaning outside tight loops/math | `calculate_revenue(days_worked, daily_charge)` instead of `process(d, c)` |
| Redundant suffixes | `_list`, `_dict`, `_data` add no signal when type hints exist | `names: List[str]` instead of `names_list` |
| Shadowing builtins/keywords | Breaks `list()`, `str()`, `sum()`, etc. | `my_list`, `my_string`, `total_sum` |

---

## Pythonic Code

Idioms that make code feel natural to experienced Python developers.

### Iteration

```python
for index, fruit in enumerate(my_list):
    print(f"{index}: {fruit}")

for fruit, quantity in zip(fruits, quantities):
    print(f"We have {quantity} {fruit}(s).")

for key, value in my_dict.items():   # preferred for key-value pairs
    print(key, value)
```

### Immutable Data: Dataclasses over Dicts

`@dataclass(frozen=True)` creates safe, self-documenting, immutable data contracts —
ideal for events flowing through a system, since a fact that already happened should
never be mutated.

```python
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class OrderPlaced:
    """Event fired when a customer successfully places an order."""
    order_id: int
    user_id: int
    total_amount: Decimal
    item_count: int

def send_confirmation_email(event: OrderPlaced):
    try:
        event.order_id = 99999          # raises FrozenInstanceError — data is protected
    except Exception as e:
        print(f"Could not modify event: {type(e).__name__}")
```

Why this is superior to plain dicts:

1. **Data integrity** — mutation attempts raise `FrozenInstanceError`.
2. **Self-documentation** — `event.order_id` beats `event['order_id']`; IDE autocompletion works.
3. **Predictability** — every consumer sees the exact same state the event was created with.
4. **Type safety** — `isinstance(event, OrderPlaced)` reliably routes events to handlers.

### Truthiness & Conditions

```python
if not my_list:      # empty list/sequence is falsy
    ...
if name:              # non-empty string is truthy
    ...
if not count:         # zero is falsy
    ...

status = "adult" if age >= 18 else "minor"   # ternary for concise assignment

# Avoid: if x == True / if len(my_list) == 0 / if name != ""
```

### Comprehensions

```python
squares_of_evens = [x * x for x in numbers if x % 2 == 0]
unique_squares = {x * x for x in [-1, 1, -2, 2, 3]}
num_to_square = {x: x * x for x in numbers}
large_range_squares = (x * x for x in range(1_000_000))   # generator — lazy, memory efficient
```

### Context Managers

```python
with open("example.txt", "w") as f:
    f.write("Hello, Pythonic world!\n")
# f is closed automatically, even if an exception occurred inside the block.

from contextlib import contextmanager
import time

@contextmanager
def timer(label: str):
    start = time.time()
    try:
        yield
    finally:
        print(f"{label}: {time.time() - start:.4f} seconds")
```

### Decorators

```python
import functools
import time

def timing_decorator(func):
    @functools.wraps(func)              # preserves the original function's metadata
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.perf_counter() - start:.6f}s")
        return result
    return wrapper

@timing_decorator
def greet(name: str, greeting: str = "Hello"):
    return f"{greeting}, {name}!"
```

### Properties

```python
class Circle:
    def __init__(self, radius: float):
        self._radius = radius

    @property
    def radius(self) -> float:
        return self._radius

    @radius.setter
    def radius(self, value: float):
        if value < 0:
            raise ValueError("Radius cannot be negative.")
        self._radius = value

    @property
    def area(self) -> float:
        import math
        return math.pi * (self._radius ** 2)
```

### Dunders (Magic Methods)

```python
class ShoppingList:
    def __init__(self, items: list = None):
        self._items = items if items is not None else []

    def __str__(self) -> str:
        return "Shopping List:\n" + "\n".join(f"- {i}" for i in self._items)

    def __repr__(self) -> str:
        return f"ShoppingList(items={self._items!r})"

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: int) -> str:
        return self._items[index]

    def __contains__(self, item: str) -> bool:
        return item in self._items
```

### Lambdas

```python
points.sort(key=lambda point: point[1])
squared = list(map(lambda x: x * x, numbers))
evens = list(filter(lambda x: x % 2 == 0, numbers))
```

### Third-Party Libraries 🧩

Don't reinvent the wheel — lean on the ecosystem (`requests`, `numpy`, `pandas`, …).

```python
import requests

try:
    response = requests.get("https://api.github.com/users/python")
    response.raise_for_status()
    print(response.json().get('public_repos'))
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
```

### Metaclasses 🤖 (advanced)

Metaclasses are "the classes of classes" — they control how classes themselves
behave, often used to enforce conventions in frameworks (e.g. requiring every plugin
subclass to define a specific attribute). `type` is the default metaclass; reach for
a custom one only when a simpler pattern (mixin, decorator, `__init_subclass__`)
won't do.

---

## Async I/O (`asyncio`)

`async`/`await` is for **I/O-bound concurrency** — juggling many things that spend
most of their time *waiting* (network calls, DB queries, file I/O) on a single
thread. It is not parallelism and does not speed up CPU-bound work.

### The Basics

```python
import asyncio

async def fetch_user(user_id: int) -> dict:
    await asyncio.sleep(0.1)          # simulates a non-blocking I/O call
    return {"id": user_id, "name": "Alice"}

async def main():
    user = await fetch_user(1)
    print(user)

asyncio.run(main())                   # the one place a sync entry point starts the event loop
```

### Running Things Concurrently

`await` on its own is still sequential — one call finishes before the next starts.
Use `asyncio.gather` to run independent awaitables concurrently:

```python
async def fetch_all_users(user_ids: list[int]) -> list[dict]:
    return await asyncio.gather(*(fetch_user(uid) for uid in user_ids))
```

### The Cardinal Sin: Blocking the Event Loop

`asyncio` is single-threaded and cooperative — one blocking call inside an
`async def` freezes *every other* coroutine on that event loop, not just the caller.

```python
# ❌ requests is synchronous — this blocks the entire event loop for the call's duration.
async def get_report(report_id: int) -> bytes:
    response = requests.get(f"https://api.example.com/reports/{report_id}")
    return response.content

# ✅ Use an async-native client so the event loop stays free to run other coroutines.
import httpx

async def get_report(report_id: int) -> bytes:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/reports/{report_id}")
        return response.content
```

The same trap applies to `time.sleep()` (use `await asyncio.sleep()`), synchronous
DB drivers (use an async driver, e.g. `asyncpg`/`databases`, or the ORM's async
mode), and any other call that isn't explicitly async-aware.

### `async with` and `async for`

Async context managers and async iterators follow the same shape as their sync
counterparts, with `async` in front:

```python
async def stream_rows(query: str):
    async with db_pool.acquire() as conn:
        async for row in conn.cursor(query):
            yield row
```

### Choosing the Right Concurrency Model

Async isn't always the answer. Match the tool to the workload:

| Workload | Use |
|---|---|
| I/O-bound, high concurrency (web requests, many open connections, DB calls) | `asyncio`, with async-native libraries |
| I/O-bound, but the only available library is sync-only | `threading` / `ThreadPoolExecutor` (or `loop.run_in_executor`) |
| CPU-bound (image processing, heavy computation) | `multiprocessing` / `ProcessPoolExecutor`, or offload to a background worker — see the [Architecture guide's Celery section](./architecture-guide-detailed.md#background-tasks-celery) |

```python
# CPU-bound work still blocks the single event-loop thread — hand it to a process pool.
from concurrent.futures import ProcessPoolExecutor

async def resize_image_async(path: str) -> None:
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as pool:
        await loop.run_in_executor(pool, resize_image_cpu_heavy, path)
```

### Testing Async Code

Unit tests for `async def` functions need `pytest-asyncio` (or an equivalent
plugin) — see the [Testing Guide](./testing-guide-detailed.md#testing-async-code)
for a worked example.
