# General Coding Principles (Detailed)

Language-agnostic principles for writing clean, readable, maintainable code —
what "good code" means before any particular language's syntax enters the
picture. Every principle here applies whether you're writing Python, TypeScript,
C++, or anything else. For the condensed version, see
[coding-principles-short.md](./coding-principles-short.md).

> **Language-specific idioms and syntax** live in each language's own coding
> guide: [Python](../python/coding-guide-detailed.md) ·
> [TypeScript](../typescript/coding-guide-detailed.md) ·
> [C++](../cpp/coding-guide-detailed.md)

> Related general guides: [Architecture Principles](./architecture-principles-detailed.md) ·
> [Testing Principles](./testing-principles-detailed.md)

## Table of Contents

1. [The 6 Principles of Coding](#the-6-principles-of-coding)
2. [Abstract vs. Implementation](#abstract-vs-implementation-)
3. [Naming Philosophy](#naming-philosophy)
4. [Names to Avoid](#names-to-avoid-)
5. [Formatting & Documentation Philosophy](#formatting--documentation-philosophy)
6. [Core Engineering Acronyms](#core-engineering-acronyms)

---

## The 6 Principles of Coding

Good code is more than functional — it's an art. Six principles make code easier
to understand, maintain, and scale, regardless of language.

### Beautiful ✨

Code should be elegant and pleasing to read: concise yet expressive. Prefer
**declarative** code (stating *what* you want) over **imperative** code (spelling
out every step). A framework or standard library that handles a common task
declaratively — routing, serialization, validation — replaces dozens of lines of
manual, repetitive instructions with a clear statement of intent. That's beauty:
not decoration, but the absence of unnecessary ceremony.

> See it in practice: [Python](../python/coding-guide-detailed.md#beautiful-) ·
> [TypeScript](../typescript/coding-guide-detailed.md#beautiful-) ·
> [C++](../cpp/coding-guide-detailed.md#beautiful-)

### Readable 📖

Code is read far more often than it's written — prioritize clarity over
cleverness. Data structures that enforce a schema (a typed model, a struct, a
class with named fields) beat loosely-typed maps/dicts/arrays accessed by string
key or index, because the shape of the data is documented by the type itself
instead of by convention the reader has to trust.

### Explicit 🎯

"Explicit is better than implicit." Dependencies and configuration should be
visible and traceable, not magically inferred from global state, ambient
environment lookups scattered through the codebase, or hidden framework
conventions. If a component needs something to function, that need should be
declared where the component is defined (a constructor parameter, a function
argument) — not discovered by reading the implementation.

### Simple 👌

Aim for the simplest solution that actually works; avoid unnecessary complexity
(KISS). This usually means preferring the language's or a well-established
library's built-in high-level constructs (comprehensions, ORMs, standard
collection operations) over manually reimplementing the same logic with explicit
loops and low-level plumbing — not because manual code is wrong, but because it
adds moving parts a reader has to verify are correct.

### Scalable 🚀

Design code that can handle growth in data, users, or features without a
rewrite. At the code level, this most often means **not blocking** on slow
operations: offload anything that doesn't need to happen synchronously (sending
an email, generating a report) to a background queue or async task, so the
calling code returns immediately instead of making a caller wait on work it
doesn't need to wait on.

### Consistent 🔄

Use uniform naming, formatting, and structural patterns throughout a project so
different parts feel like they were written by the same disciplined team — even
when they weren't. Consistency compounds: once a reader learns the pattern in
one place, they can predict it everywhere else, which is worth more than any
individual naming choice being "more correct."

---

## Abstract vs. Implementation 🔌

Separate the contract (**what** something should do) from the code that executes
it (**how** it's done). Think of a **wall socket** — the abstract interface
defines: *"Any plug with standard prongs and voltage gets electricity."* It
doesn't matter whether you plug in a lamp, a charger, or a vacuum; those are
concrete implementations behind a fixed contract.

**Why this separation is crucial:**

- **Flexibility & decoupling** — swap one implementation for another (a different payment provider, a different notification channel) without touching the code that depends on the contract.
- **Simplified high-level logic** — orchestrating code deals with one uniform interface instead of every implementation's individual quirks.
- **Enforced consistency** — the interface guarantees every implementation exposes the same shape (same method names, same argument types, same return contract).
- **Improved testability 🧪** — swap in a fake/mock implementation during tests without touching real infrastructure (a database, a network, a payment gateway).

**Generic shape** (every mainstream language has some version of this — an
interface, an abstract class/protocol, a trait):

```text
interface Notifier:
    send(recipient, message) -> success: bool

class EmailNotifier implements Notifier:
    send(recipient, message):
        # sends via SMTP
        return true

class SmsNotifier implements Notifier:
    send(recipient, message):
        # sends via SMS gateway
        return true

# Business logic depends on the abstraction, never a concrete class:
function registerUser(userData, notifier: Notifier):
    createUser(userData)
    notifier.send(userData.email, "Welcome!")

# The concrete implementation is chosen once, at the application's entry point,
# and injected everywhere the abstraction is needed.
```

> Concrete code: [Python](../python/coding-guide-detailed.md) (ABCs) ·
> [TypeScript](../typescript/coding-guide-detailed.md) (interfaces) ·
> [C++](../cpp/coding-guide-detailed.md) (abstract base classes)

---

## Naming Philosophy

Good names are the cheapest form of documentation a codebase has.

### Name for Usage, Not Implementation

Name things based on what they do from the *caller's* perspective, not how they
happen to work internally. That way the implementation can change — swap a list
for a database call, a in-memory cache for a remote one — without the name lying
to every caller.

```text
# Less ideal — exposes an implementation detail (a list) in the name.
getUserAsList(userId)

# Better — describes usage; the caller doesn't need to know or care how it's fetched.
getUserDetails(userId)
```

### Casing Is a Per-Language Convention, Consistency Is the Universal Rule

Every language has its own idiomatic casing (Python: `snake_case`; TypeScript:
`camelCase`/`PascalCase`; C++: often `snake_case` or `PascalCase` depending on
house style) — see each language's coding guide for its specific naming-style
table. The principle that transfers across all of them: **pick the convention
for each category of name (variables, functions, types, constants) and apply it
with zero exceptions across the whole codebase.** A codebase that's 90%
consistent is worse than one that picked a slightly less popular convention and
applied it 100% of the time — the inconsistency itself is the cost, not the
specific choice.

---

## Names to Avoid 🚫

These four traps show up in every language:

| Issue | Why | Fix |
|---|---|---|
| Ambiguous characters (`l`, `O`, `I` in languages that allow them as identifiers) | Easily confused with `1` / `0` | Use a descriptive name instead (`length`, `offset`, `identityMatrix`) |
| Unclear single-letter names outside a tight, obvious scope | Loses meaning the moment the reader isn't looking at the 3 lines around it | Reserve single letters for very short loops/math contexts (`i`, `j`, `x`, `y`); name everything else |
| Redundant type-in-name suffixes (`_list`, `_dict`, `_array`, `...Object`) | Adds no signal once the type system or a type hint already says it | Let the type declare the shape; name the *thing*, not its container |
| Shadowing built-ins or reserved/standard-library names | Silently breaks or shadows a name every reader assumes still means the built-in thing | Never reuse a language's built-in type/function names for your own variables |

---

## Formatting & Documentation Philosophy

The exact numbers (line length, indent width) are project/language conventions —
what's universal is the *shape* of the discipline:

- **Formatting is enforced by tooling, not memory.** Every mainstream language has an autoformatter (Black/Ruff for Python, Prettier for TypeScript, clang-format for C++) — run it in CI so formatting is never a code-review discussion.
- **Imports/includes are ordered and grouped** — standard library, then third-party, then local/project code — so a reader can tell a dependency's origin at a glance.
- **Comments explain *why*, not *what*.** The code already says what it does; a comment earns its place by adding context the code can't express (a business reason, a non-obvious constraint, a link to the ticket that explains a workaround).
- **Public APIs are documented at their declaration** — a docstring, a doc-comment, a Javadoc-style block — so a caller never has to read the implementation to know how to use something.
- **Type information is declared, not left to inference by the reader.** Every one of the three languages this guide covers has some form of static or gradual typing (Python type hints, TypeScript's type system, C++'s native static typing) — use it on public signatures at minimum.

---

## Core Engineering Acronyms

The most load-bearing ones for code-level design (the full reference, including
architecture/data acronyms, lives in the
[Architecture Principles guide](./architecture-principles-detailed.md#core-engineering-acronyms-reference-)):

| Acronym | Full Form | Core Focus |
|---|---|---|
| **KISS** | Keep It Simple, Stupid | Avoid unnecessary design complexity. |
| **DRY** | Don't Repeat Yourself | Abstract duplicate logic into reusable functions/modules. |
| **YAGNI** | You Ain't Gonna Need It | Don't build unrequested future capabilities. |
| **SOLID** | OO Design Principles | Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion. |
| **SLAP** | Single Level of Abstraction Principle | Keep every statement in a function at the same conceptual detail level. |
| **LoD** | Law of Demeter | "Don't talk to strangers" — avoid chaining calls across distant objects (`a.b().c().d()`). |
| **CQS** | Command-Query Separation | A function either mutates state (command) or returns data (query) — never both. |
