## Coding principles

- Six principles, in priority order of what to check in review: **Beautiful** (declarative over imperative — state intent, let the language or library do the work), **Readable** (typed structures over loosely-typed maps accessed by string key), **Explicit** (dependencies and config are visible and passed in, never inferred from globals), **Simple** (the simplest thing that works; prefer built-ins over reimplementation), **Scalable** (don't block callers on slow work), **Consistent** (100% consistent beats "slightly better" and inconsistent).
- Separate contract from implementation: business logic depends on an interface/abstract class/trait, never a concrete class. That is what makes swapping implementations and testing with fakes cheap.
- Name for usage, not internal detail (`getUserDetails`, not `getUserAsList`). Casing is per-language; the universal rule is one convention per category (variables, functions, types, constants), applied everywhere.
- Avoid: ambiguous characters (`l`, `O`, `I`), unclear single letters outside tight scopes, redundant type suffixes (`user_list`, `config_dict`) when a type already says it, and shadowing built-ins.
- Formatting is enforced by an autoformatter in CI, never by review nitpicks. Imports are grouped standard library → third-party → local.
- Document public APIs at their declaration; comments explain *why*, never *what*.
- Full language-specific idioms and worked examples: the `engineering-guides` skill.
