# Python — Architecture & Framework Design Guide (Detailed)

Higher-level system architecture, boundaries, developer experience, HLD/LLD design
documents, design patterns, and operational standards — implemented in Python
(Django/FastAPI/Celery). For the condensed version, see
[architecture-guide-short.md](./architecture-guide-short.md).

> **This guide assumes the [General Architecture Principles](../general/architecture-principles-detailed.md)** —
> it shows how those language-agnostic concepts look in a Python stack. Read that
> first for the "why"; this guide is the "how, in Python."

> Related Python guides: [Coding Guide](./coding-guide-detailed.md) ·
> [Testing Guide](./testing-guide-detailed.md)

## Table of Contents

1. [Design Principles at the System Level](#design-principles-at-the-system-level)
2. [Abstract vs. Implementation 🔌](#abstract-vs-implementation-)
3. [Data Flow Strategy 🗺️](#data-flow-strategy-)
4. [Integration Patterns: DI, Events & Facade 🔌🚪](#integration-patterns-di-events--facade-)
5. [Designing for Testability](#designing-for-testability)
6. [Design Documents: HLD & LLD 🗺️📜](#design-documents-hld--lld-)
7. [Design Patterns & Anti-Patterns 💡](#design-patterns--anti-patterns-)
8. [Operational Logging & Centralized Error Strategy ☁️](#operational-logging--centralized-error-strategy-)
9. [Security Fundamentals 🔒](#security-fundamentals-)
10. [CI/CD, Deployment & Observability 🚀📈](#cicd-deployment--observability-)
11. [Background Tasks (Celery)](#background-tasks-celery)
12. [Software Engineering Rules](#software-engineering-rules)
13. [What Is a "Component" in Python?](#what-is-a-component-in-python)
14. [Core Engineering Acronyms Reference 📜](#core-engineering-acronyms-reference-)

---

## Design Principles at the System Level

The [general architecture principles](../general/architecture-principles-detailed.md#design-principles-at-the-system-level) —
Beautiful/Explicit/Readable/Simple/Scalable/Consistent — as they typically show up
in a Python stack:

| Principle | In a Python stack |
|---|---|
| **Beautiful ✨** | An API Gateway with a pluggable plugin architecture — a declarative YAML route definition adds a service, no re-compilation. |
| **Explicit 🎯** | A DI container at startup (`main.py`) constructs repositories and injects them into service constructors, instead of relying on auto-discovery. |
| **Readable 📖** | Domain-driven service names (`UserService`, `PaymentGatewayService`) paired with typed Pydantic models instead of nested untyped dicts. |
| **Simple 👌** | Micro-frameworks (Flask/FastAPI) that start with one lightweight endpoint and modularize into blueprints/routers only as complexity grows. |
| **Scalable 🚀** | Offloading slow operations (PDF generation, email) to Celery/Redis worker queues so endpoints return an instant `202 Accepted`. |
| **Consistent 🔄** | Standardized paths (`GET /api/v1/products/`), noun conventions, and uniform JSON error wrappers across every service. |

---

## Abstract vs. Implementation 🔌

Python's shape for the [general abstract-vs-implementation principle](../general/coding-principles-detailed.md#abstract-vs-implementation-):
an `abc.ABC` with `@abstractmethod` as the contract, concrete subclasses as the
implementations.

```python
# 1. The Abstract Part (interfaces.py)
from abc import ABC, abstractmethod

class Notifier(ABC):
    """Abstract contract defining WHAT a notifier must do."""
    @abstractmethod
    def send(self, recipient: str, message: str) -> bool:
        pass

# 2. The Implementation Part (providers.py)
class EmailNotifier(Notifier):
    def send(self, recipient: str, message: str) -> bool:
        print(f"Sending SMTP email to {recipient}: {message}")
        return True

class SmsNotifier(Notifier):
    def send(self, recipient: str, message: str) -> bool:
        print(f"Sending Twilio SMS to {recipient}: {message}")
        return True

class LogNotifier(Notifier):
    def send(self, recipient: str, message: str) -> bool:
        print(f"LOG ONLY -> {recipient}: {message}")
        return True

# 3. Business Logic depending on Abstraction (services.py)
def register_new_user(user_data: dict, notifier: Notifier):
    print(f"Creating user {user_data['email']}...")
    notifier.send(recipient=user_data['email'], message="Welcome!")

# 4. Application Assembly Entry Point (main.py)
import os

provider = LogNotifier() if os.environ.get("APP_ENV") == "development" else EmailNotifier()
register_new_user({"email": "alice@example.com"}, notifier=provider)
```

---

## Data Flow Strategy 🗺️

The [general data flow strategy](../general/architecture-principles-detailed.md#data-flow-strategy-)
worked through a real Django + Pydantic + Argon2 stack:

### User Registration Data Flow (step by step)

1. **Origin (browser):** password in plaintext memory, sent over HTTPS (encrypted in transit).
2. **API Gateway / edge:** TLS terminates; raw JSON forwarded to the app server.
3. **Validation layer:** deserialized and validated via schema (Pydantic); fails fast if invalid.
4. **Service layer:** password undergoes irreversible one-way hashing (Argon2id, OWASP's current top recommendation — bcrypt remains an acceptable alternative); plaintext discarded.
5. **Data access layer:** email and `password_hash` persisted via ORM — plaintext password never touches storage.

```python
# models.py — database schema
from django.db import models

class User(models.Model):
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)   # Argon2's encoded hash is longer than bcrypt's
    created_at = models.DateTimeField(auto_now_add=True)

# data_access.py — Step 5: Data Access Layer
from .models import User

def create_user_in_db(email: str, hashed_password: str) -> User:
    """Persists user record. Direct database interaction is isolated here."""
    return User.objects.create(email=email, password_hash=hashed_password)

# services.py — Step 4: Business Logic Layer
from argon2 import PasswordHasher
from pydantic import BaseModel, EmailStr, Field
from .data_access import create_user_in_db
from .models import User

_password_hasher = PasswordHasher()   # Argon2id by default (argon2-cffi)

class UserRegistrationSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class UserService:
    def register_user(self, registration_data: UserRegistrationSchema) -> User:
        hashed_pw = _password_hasher.hash(registration_data.password)
        return create_user_in_db(email=registration_data.email, hashed_password=hashed_pw)
```

---

## Integration Patterns: DI, Events & Facade 🔌🚪

### Pattern 1: Dependency Injection (DI)

Inject dependencies via constructors rather than hardcoding instantiations inside classes.

```python
class RegistrationService:
    def __init__(self, notifier, workspace_svc):
        self.notifier = notifier
        self.workspace_svc = workspace_svc

    def register_user(self, email: str):
        user_id = 123
        self.notifier.send_welcome_email(email)
        self.workspace_svc.create_default_workspace(user_id)
```

### Pattern 2: Immutable Event-Driven Decoupling

Frozen, read-only data structures for event communication across service boundaries
prevent accidental mutation.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class OrderPlacedEvent:
    order_id: int
    user_id: int
    total_amount: float

def handle_analytics(event: OrderPlacedEvent):
    # event.total_amount = 0  <-- raises FrozenInstanceError!
    print(f"Analytics updated for order {event.order_id}")
```

### Pattern 3: Facade Pattern

A single, simplified gateway over a complex, multi-service subsystem.

```python
class NotificationFacade:
    def __init__(self, template_mgr, email_gw, user_svc):
        self.template_mgr = template_mgr
        self.email_gw = email_gw
        self.user_svc = user_svc

    def send_welcome(self, email: str):
        name = self.user_svc.get_user_name(email)
        template = self.template_mgr.get_template("welcome")
        body = template.replace("{{name}}", name)
        self.email_gw.send(email, "Welcome!", body)
```

### Isolating Third-Party Libraries (Adapter)

Wrap a third-party SDK behind your own interface — only the adapter module ever
imports the vendor library.

```python
# interfaces.py — your application's generic contract
from abc import ABC, abstractmethod
from decimal import Decimal

class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, amount: Decimal, token: str) -> str:
        """Charges a card and returns a transaction ID. Raises PaymentDeclinedError."""

class PaymentDeclinedError(Exception):
    pass

# adapters/stripe_gateway.py — the only file that imports `stripe`
import stripe
from ..interfaces import PaymentGateway, PaymentDeclinedError

class StripeGateway(PaymentGateway):
    """Uses the PaymentIntents API — Stripe's current recommended flow.
    The older Charges API (stripe.Charge.create) is deprecated and doesn't
    support SCA/3-D Secure, which most card payments now require."""

    def __init__(self, api_key: str):
        stripe.api_key = api_key

    def charge(self, amount: Decimal, token: str) -> str:
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),   # Stripe expects the smallest currency unit (cents)
                currency="usd",
                payment_method=token,
                confirm=True,
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            )
            return intent.id
        except stripe.error.CardError as e:
            raise PaymentDeclinedError(f"Card declined by Stripe: {e}")
```

---

## Designing for Testability

The DI, separation of concerns, and adapter isolation above are what make Python
components testable with `pytest` + `unittest.mock` in the first place — see
[Designing for Testability](../general/architecture-principles-detailed.md#designing-for-testability)
for the RED/GREEN/BLUE workflow and the [Testing Guide](./testing-guide-detailed.md#hard-to-write-unit-tests--code-design-flaws)
for the "hard to test = design flaw" diagnosis table.

This loop keeps the design decision (the contract) separate from implementation
detail, and forces every new feature to be verifiably testable before it's
considered done.

---

## Design Documents: HLD & LLD 🗺️📜

The [general HLD/LLD guide](../general/architecture-principles-detailed.md#design-documents-hld--lld-)
covers the concepts (the "architect's blueprint" vs. "construction plan for one
room" mental model, the full HLD checklist, and the 8-part LLD checklist) in
detail. Two Python-specific concretizations of the LLD's static view and DI
wiring:

1. **Static View — Class Diagrams & Method Signatures.** Python's `abc.ABC` +
   `@abstractmethod` for interfaces, a service class depending only on those
   interfaces:

   ```python
   # interfaces.py
   from abc import ABC, abstractmethod
   from typing import Optional

   class UserRepository(ABC):
       @abstractmethod
       def find_by_email(self, email: str) -> Optional["User"]: ...
       @abstractmethod
       def save(self, user: "User") -> "User": ...

   class PasswordHasher(ABC):
       @abstractmethod
       def hash(self, password: str) -> str: ...
       @abstractmethod
       def verify(self, password: str, hashed: str) -> bool: ...

   # services.py
   class UserService:
       def __init__(self, repo: UserRepository, hasher: PasswordHasher):
           self._repo = repo
           self._hasher = hasher

       def register_user(self, email: str, plaintext_password: str) -> "User":
           """Registers a new user after validating input and business rules."""
   ```

2. **Integration & Concrete DI Wiring** — how the interfaces above get concrete
   implementations at the application's entry point:

   ```python
   user_repository = PostgresUserRepository(db_url=config.DATABASE_URL)
   password_hasher = BcryptPasswordHasher()
   user_service = UserService(repo=user_repository, hasher=password_hasher)
   ```

The remaining 6 parts of the LLD checklist (dynamic view/pseudocode, I/O schemas,
config keys, error contracts, logging plan, unit test plan) follow the same shape
shown in the [general guide's worked example](../general/architecture-principles-detailed.md#design-documents-hld--lld-) —
nothing about them is Python-specific beyond the syntax already shown above.

### Case Study: LLD for `NotificationFacade`

Same case study as the [general guide](../general/architecture-principles-detailed.md#design-documents-hld--lld-) —
the class diagram, pseudocode, and sequence are language-neutral. The one
Python-specific artifact is the interface shape, matching the `Notifier`
[Abstract vs. Implementation](#abstract-vs-implementation-) example and the
`NotificationFacade` [Facade pattern](#pattern-3-facade-pattern) example above.

---

## Design Patterns & Anti-Patterns 💡

The [general design patterns & anti-patterns reference](../general/architecture-principles-detailed.md#design-patterns--anti-patterns-)
(Factory Method, Singleton, Builder, Adapter, Decorator, Facade, Observer,
Strategy, Template Method; God Object, Spaghetti Code, Lava Flow, Boat Anchor)
applies as-is to Python — none of it is Python-specific. Python examples of
several of these already appear above: [Facade](#pattern-3-facade-pattern),
[Adapter](#isolating-third-party-libraries-adapter).

---

## Operational Logging & Centralized Error Strategy ☁️

### Centralized Error Handling 🛡️

FastAPI's `@app.exception_handler` for the general pattern of
[centralized error handling](../general/architecture-principles-detailed.md#operational-logging--centralized-error-strategy-):

```python
# exceptions.py
class AppError(Exception):
    """Base class for all domain errors."""

class ResourceNotFoundError(AppError):
    def __init__(self, resource_name: str, resource_id: str):
        self.message = f"{resource_name} with ID '{resource_id}' was not found."
        super().__init__(self.message)

class PermissionDeniedError(AppError):
    pass

# main.py — FastAPI centralized handlers
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
    return JSONResponse(status_code=404, content={"error": "Not Found", "detail": exc.message})

@app.exception_handler(PermissionDeniedError)
async def permission_denied_handler(request: Request, exc: PermissionDeniedError):
    return JSONResponse(status_code=403, content={"error": "Forbidden", "detail": "Action not permitted."})

# views.py — clean endpoints, no try/except boilerplate
@app.get("/users/{user_id}")
async def get_user_endpoint(user_id: str):
    user = user_service.get_user_by_id(user_id)
    return {"id": user.id, "email": user.email}
```

Create **custom, semantic exceptions** (`InsufficientStockError`, not a bare
`ValueError`) so centralized handlers know exactly how to respond, and endpoints
stay free of `try/except` blocks.

### Structured Contextual Logging (JSON) ⚙️

`structlog` bound to FastAPI middleware, implementing the
[3 pillars of structured logging](../general/architecture-principles-detailed.md#operational-logging--centralized-error-strategy-):

```python
import structlog
from fastapi import FastAPI, Request
import uuid

logger = structlog.get_logger()
app = FastAPI()

@app.middleware("http")
async def logging_context_middleware(request: Request, call_next):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=str(uuid.uuid4()))
    return await call_next(request)

class OrderService:
    def place_order(self, user_id: int, item_count: int):
        logger.info("Order placement initiated", user_id=user_id, items=item_count)
```

```json
{
  "timestamp": "2026-08-17T00:35:00Z",
  "level": "INFO",
  "logger": "myapp.services.order_service",
  "message": "Order placement initiated",
  "request_id": "req-987a-654b",
  "user_id": 42,
  "items": 3
}
```

**Log levels:**

| Level | Meaning |
|---|---|
| `DEBUG` | Highly detailed development info — disabled in production. |
| `INFO` | Routine events/milestones — app behaving as expected. |
| `WARNING` | Unexpected but recoverable, non-critical event. |
| `ERROR` | Critical failure that prevented an operation — should trigger alerts. |

---

## Security Fundamentals 🔒

The [general security fundamentals](../general/architecture-principles-detailed.md#security-fundamentals-)
(AuthN vs. AuthZ, the OWASP Top 10 checklist, transport/rate-limiting) apply as-is.
Two Python-specific concretizations:

### Enforce Authorization at the Boundary, Not in Business Logic

```python
# FastAPI dependency-based authorization — enforced once, at the route boundary.
from fastapi import Depends, HTTPException, status

def require_role(required_role: str):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if required_role not in current_user.roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return dependency

@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, admin: User = Depends(require_role("admin"))):
    ...
```

### Injection Prevention

Never build queries by string-formatting untrusted input:

```python
# ❌ Classic SQL injection — untrusted input concatenated straight into the query.
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")

# ✅ Parameterized queries (or an ORM, which does this for you automatically).
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
```

The [OWASP Top 10 checklist](../general/architecture-principles-detailed.md#security-fundamentals-)
and transport/rate-limiting guidance apply unchanged in Python; the CI-stage
dependency scanning it references is `pip-audit`/`Dependabot` for this ecosystem.

---

## CI/CD, Deployment & Observability 🚀📈

The [general pipeline stages](../general/architecture-principles-detailed.md#cicd-deployment--observability-)
(lint/type-check → unit → build → integration → staging → smoke/E2E → promote)
apply unchanged — in Python, stage 1 is Ruff/Black + mypy, and stages 2/4/6 are
covered in the [Testing Guide](./testing-guide-detailed.md).

### Containerization Basics

```dockerfile
# Dockerfile — multi-stage build: smaller final image, no build toolchain shipped to prod.
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry \
    && poetry export -f requirements.txt -o requirements.txt \
    && pip install --no-cache-dir -r requirements.txt --target=/install

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local/lib/python3.12/site-packages
COPY . .
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Follows the [general containerization rules](../general/architecture-principles-detailed.md#cicd-deployment--observability-)
(pinned base image, non-root user, multi-stage build) using `pip`/Poetry.

### Database Migrations

Managed by a dedicated tool (Alembic for SQLAlchemy, or Django's built-in
migrations), run as an explicit pipeline step — never applied by hand against
production. Follow the [expand–contract pattern](../general/architecture-principles-detailed.md#cicd-deployment--observability-)
for zero-downtime schema changes.

### Observability Beyond Logging

The [general observability guidance](../general/architecture-principles-detailed.md#cicd-deployment--observability-)
(metrics, tracing, liveness vs. readiness) via `prometheus_client`, OpenTelemetry,
and FastAPI:

**Metrics** (RED method):

```python
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "Request latency", ["path"])

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    with REQUEST_LATENCY.labels(path=request.url.path).time():
        response = await call_next(request)
    REQUEST_COUNT.labels(method=request.method, path=request.url.path, status=response.status_code).inc()
    return response
```

**Tracing** (correlated with the same `request_id` used in [Structured Contextual Logging](#structured-contextual-logging-json-)):

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

class OrderService:
    def place_order(self, user_id: int, item_count: int):
        with tracer.start_as_current_span("place_order") as span:
            span.set_attribute("user_id", user_id)
            # ... business logic ...
```

**Health checks** (liveness vs. readiness):

```python
@app.get("/healthz")
async def liveness():
    """Is the process alive? No dependency checks — just 'am I running'."""
    return {"status": "ok"}

@app.get("/readyz")
async def readiness():
    """Am I ready to serve traffic? Checks the dependencies this app actually needs."""
    try:
        await database.execute("SELECT 1")
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")
```

---

## Background Tasks (Celery)

Offload slow, resource-intensive operations (thumbnail generation, CSV import) so
the main request/response cycle isn't blocked.

**Organization:** one task module per concern (SRP applies to background jobs too):

```text
project_root/
├── celery_app.py
├── views.py
└── tasks/
    ├── __init__.py
    ├── image_task.py    <-- image processing tasks
    └── email_task.py    <-- email sending tasks
```

```python
# celery_app.py — auto-discovers tasks defined anywhere under tasks/
app.autodiscover_tasks(['tasks'])
```

```python
# tasks/image_task.py
from celery import shared_task
from PIL import Image

@shared_task(bind=True, max_retries=3)
def image_task(self, image_id: int, width: int, height: int):
    """Background task to resize an image."""
    try:
        image_record = get_image_from_db(image_id)          # fetch by ID
        img = Image.open(image_record.path)
        img = img.resize((width, height))
        img.save(f"resized_{image_record.filename}")
        mark_image_as_processed(image_id)
        return True
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)              # resilient retry
```

**Best practices:**

- **Pass IDs, not objects** — task queues serialize as JSON; complex objects don't serialize well, and the DB record may have changed by the time the worker runs.
- **Idempotency** — a task must be safe to run more than once.
- **Resilience & retries** — configure `max_retries` for transient failures.

**Structured logging in a task:**

```python
import structlog
from celery import shared_task

logger = structlog.get_logger()

@shared_task(bind=True)
def import_csv_task(self, job_id, file_path):
    log = logger.bind(job_id=job_id)
    log.info("Starting CSV import task")
    try:
        rows = read_csv(file_path)
        for row_num, row in enumerate(rows):
            try:
                process_row(row)
            except ValueError as e:
                log.warning(f"Row {row_num} failed validation", error=str(e), row_data=row)
        log.info("CSV import completed successfully")
    except FileNotFoundError as e:
        log.error("Import failed: File not found", exc_info=True)
        raise self.retry(exc=e, countdown=60)
```

`INFO` for routine progress, `WARNING` for expected/non-critical row failures,
`ERROR` (with `exc_info=True`) for critical unexpected failures.

---

## Software Engineering Rules

Language-agnostic — see the [general 10 rules](../general/architecture-principles-detailed.md#software-engineering-rules).

---

## What Is a "Component" in Python?

The [general "component" concept](../general/architecture-principles-detailed.md#what-is-a-component)
in Python, concretely:

- **A single class** — for narrow responsibilities, its public methods are the interface (e.g. `SimpleImageResizer`).
- **A Python package (very common)** — a directory with `__init__.py` groups related modules into one cohesive unit. Internal modules are "private"; the public interface is whatever `__init__.py` re-exports.
- **A main class within a package** — a primary entry-point/facade class relying on sibling helper modules; the *package* is still the component, not any single class.

---

## Core Engineering Acronyms Reference 📜

Language-agnostic — see the [general acronyms reference](../general/architecture-principles-detailed.md#core-engineering-acronyms-reference-).
| **HLD** | High-Level Design | Overall architecture and inter-component design. |
| **LLD** | Low-Level Design | Detailed internal class, method, and schema design. |
