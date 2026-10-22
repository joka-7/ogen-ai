# General Coding Principles (Short)

Cheat sheet for language-agnostic code quality. Full explanations:
[coding-principles-detailed.md](./coding-principles-detailed.md).

> Language-specific idioms: [Python](../python/coding-guide-short.md) ·
> [TypeScript](../typescript/coding-guide-short.md) · [C++](../cpp/coding-guide-short.md)

## The 6 Principles

| Principle | In one line |
|---|---|
| **Beautiful ✨** | Declarative over imperative — state intent, let the language/library do the work. |
| **Readable 📖** | Code is read more than written — typed structures over loosely-typed maps accessed by key. |
| **Explicit 🎯** | No magic — dependencies and config are visible and passed in, not globally inferred. |
| **Simple 👌** | Simplest solution that works — prefer high-level built-ins over manual reimplementation. |
| **Scalable 🚀** | Don't block on slow work — offload it so callers aren't stuck waiting. |
| **Consistent 🔄** | Same naming/formatting/structure everywhere — 100% consistent beats "slightly better" + inconsistent. |

## Abstract vs. Implementation 🔌

Separate the contract (interface/abstract class/trait — **what**) from the concrete
class (**how**). Business logic depends only on the contract, never a concrete
implementation directly. Enables swapping implementations, simplifies orchestration,
and makes testing with fakes trivial.

## Naming

- Name for **usage** (`getUserDetails`), not internal detail (`getUserAsList`).
- Casing itself is per-language (see each language guide) — the universal rule is **100% consistency** within a category (variables, functions, types, constants), not which convention you picked.

## Names to Avoid 🚫

Ambiguous chars (`l`/`O`/`I`) · unclear single letters outside tight scopes ·
redundant type-suffixes (`_list`, `_dict`) when a type already says it · shadowing
built-ins.

## Formatting & Docs

- Formatting is enforced by an autoformatter in CI, never by memory/review nitpicks.
- Imports/includes grouped: standard lib → third-party → local.
- Comments explain **why**, not what — the code already says what.
- Public APIs are documented at their declaration, not left for callers to infer from the implementation.
- Type/declare public signatures — don't leave the reader to infer types.

## Core Acronyms

KISS · DRY · YAGNI · SOLID · SLAP · LoD · CQS — full definitions in the
[detailed guide](./coding-principles-detailed.md#core-engineering-acronyms).
