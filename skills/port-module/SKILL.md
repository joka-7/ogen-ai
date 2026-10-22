---
name: port-module
description: Port a module from one language to another (for example JS or Python to TypeScript, Python to Go, Java to Kotlin) — translate its public API, types, and error handling to the target language's rules in this config while preserving behavior exactly. Use whenever the user asks to port, convert, or migrate a file or module to another language, or asks "what would this look like in Go/TS/Rust" — even if they only name the source file.
---

# Port Module

Port one module's behavior into idiomatic code in a target language. This is a port, not a
rewrite: the output must do exactly what the source does. Improvements you notice along the way
are recommendations, not something to slip into the diff.

Invoke as `port-module <source-file> <target-language>`. If the target is missing, ask for it.

## Steps

1. **Read the source module in full** and list its public surface: exports, function
   signatures, and the types implied by how each value is constructed and used — the source
   language's own annotations if present, otherwise infer from usage.
2. **Load the target language's rules.** Read `rules/languages/<target>.md` (or the matching
   section of the project's `AGENTS.md`) and the destination project's own build config
   (`tsconfig.json`, `go.mod`, `Cargo.toml`, `build.gradle.kts`, `Package.swift`). The project's
   actual strictness settings win over the baseline. If no rule exists for the target, say so and
   use the destination project's own conventions, read from a sibling file.
3. **Translate structure before syntax.** Map the source's shape onto the target's idiom rather
   than transliterating line by line: data shapes to the target's record/struct/interface type,
   exceptions to the target's error model, collections and iteration to its idioms, naming to its
   casing convention. Typical mappings:
   - JS → TS: add types incrementally, no `any`; convert `require`/`module.exports` to ESM only
     if a sibling file already uses ESM.
   - Python → TS: `Optional[X]` → `X | undefined`; `dataclass`/`TypedDict` → `interface`;
     custom exceptions → classes extending `Error`; comprehensions → `map`/`filter`.
   - Python/JS → Go: exceptions → returned `error` values; classes → structs plus methods;
     dynamic dicts → typed structs or `map[K]V`; `None`/`undefined` → zero values or pointers.
   - Java → Kotlin: nullable types over `Optional`; data classes for value objects; checked
     exceptions become ordinary exceptions or sealed results.
4. **Port the module's own tests alongside it**, using the test runner the destination project
   already uses — don't invent a new one.
5. **Apply the target language's error-handling and logging rules** from step 2.
6. **Verify**: run the target's compile/type-check and the ported tests. Report failures as
   failures — don't silently adjust the ported logic to make a test pass without understanding
   why it failed.

## Rules

- **Behavior parity is the whole point.** Port the logic as it exists; do not fix a bug or
  improve an algorithm while porting. If you notice one, name it in the output instead.
- Never invent an API or library that doesn't exist in the destination project's dependencies.
  If the source relied on a library with no equivalent already present, say so and ask rather
  than picking one.
- Renaming for convention is expected, but list every renamed symbol explicitly — a caller
  updating references needs the mapping, not just the diff.
- Leave the original source file in place. Don't delete it until the ported version passes its
  tests and the user confirms the port replaces it.
- Follow the target language's rule fragment exactly, including its strictness and typing
  requirements.

## Output

Print: the ported file(s), the symbol-rename mapping if any, which tests were ported and their
result, and the exact commands to re-verify. Note anything you could not port faithfully (a
source-language feature with no clean equivalent) rather than papering over it.
