## Testing

- Test behavior and contracts, not implementation details. A refactor that preserves behavior shouldn't break tests.
- Arrange–Act–Assert; one logical assertion focus per test. Test names state the scenario and expected outcome.
- Cover the edges that actually break: boundaries, empty/null, error paths, concurrency where relevant. Don't chase coverage % on trivial getters.
- No network, clock, filesystem, or randomness in unit tests — inject/fake them. Keep unit tests deterministic and fast.
- Prefer real objects over mocks; mock only at true I/O boundaries. Over-mocked tests test the mocks.
- Every bug fix starts with a failing test that reproduces it.
- Keep fixtures minimal and local; a reader should understand a test without scrolling elsewhere.
