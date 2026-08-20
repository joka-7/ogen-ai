## Swift

- Value types (`struct`, `enum`) by default. Reach for `class` only when reference semantics
  or identity are genuinely required.
- No force-unwrap (`!`) or `try!` outside tests and previews. Use `guard let`/`if let`,
  nil-coalescing (`??`), or optional chaining, and handle the `nil`/failure case deliberately.
- Model a type's states with an `enum` carrying associated values rather than several optional
  or boolean properties that describe the same entity — make illegal combinations unrepresentable.
- Concurrency: `async`/`await` and structured concurrency (`Task`, task groups) over
  completion-handler callbacks in new code. Mark UI-touching types `@MainActor` and keep
  shared mutable state out of concurrency domains that can race on it.
- Protocol-oriented design: shared behavior via protocols with default implementations in
  extensions, rather than deep class hierarchies.
- Errors conform to `Error` and are thrown, not returned as sentinel values; handle with
  `do`/`catch` or `try?` deliberately, matching the caller's actual ability to recover.
- Prefer `let` over `var`; minimize mutable and shared-mutable state.
- Baseline tooling: SwiftLint, SwiftFormat, `swift test`/XCTest.
