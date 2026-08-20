## Rust

- `Result<T, E>` for recoverable errors; reserve `panic!`/`.unwrap()`/`.expect()` for invariants
  that truly must hold, and say why in a comment when used outside tests. Propagate with `?`.
- No `unsafe` without a comment stating the invariant it upholds and why the compiler can't
  verify it itself. Keep `unsafe` blocks as small and isolated as possible.
- Prefer borrowing (`&T`, `&mut T`) over cloning. Clone when ownership genuinely needs to move
  or ambiguity would otherwise cost more than the clone.
- Make invalid states unrepresentable with the type system: enums over stringly-typed values,
  newtypes for domain concepts that shouldn't mix with a raw primitive.
- Generics over `dyn Trait` unless runtime polymorphism or a heterogeneous collection is
  actually needed — static dispatch is the default, not the exception.
- Library code returns typed errors (`thiserror`); reserve `anyhow` for application binaries
  at the top level, not inside a library that other code depends on.
- Iterator chains over manual indexing and intermediate `Vec` allocation when a lazy chain
  expresses the same transformation.
- Baseline tooling: `cargo clippy -- -D warnings`, `cargo fmt --check`, `cargo test`.
