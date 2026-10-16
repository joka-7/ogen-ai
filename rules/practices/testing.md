## Testing

- Test behavior and contracts, not implementation details. A refactor that preserves behavior shouldn't break tests.
- Arrange–Act–Assert; one logical assertion focus per test. Test names state the scenario and expected outcome.
- Mirror the source: one test file per source file at the same relative path, one test group per class/type, one test case per public method — consolidate every scenario for that method (success, edges, errors) into it via parametrized/table-driven cases rather than scattering separate ad-hoc tests.
- Cover the edges that actually break: boundaries, empty/null, error paths, concurrency where relevant. Don't chase coverage % on trivial getters.
- No network, clock, filesystem, or randomness in unit tests — inject/fake them. Keep unit tests deterministic and fast.
- Prefer real objects over mocks; mock only at true I/O boundaries. Over-mocked tests test the mocks.
- Every bug fix starts with a failing test that reproduces it.
- Keep fixtures minimal and local; a reader should understand a test without scrolling elsewhere.
- Isolation is by design, not tooling: take dependencies as constructor/parameter arguments so a test passes a fake with no patching. Runtime patching (`unittest.mock.patch`, `vi.mock`) is an escape hatch for code you can't inject into — patch where the name is *used*, not where it's defined.
- Hard to test means badly designed: needing a real DB/network → inject it; one huge test → split the unit (SRP); can't observe the result → return values instead of hidden side-effects.
- Know the doubles: dummy (placeholder), stub (canned answers), fake (working simplified implementation), mock (records and verifies calls), spy (real implementation that records). Prefer fakes and stubs; assert on mock calls only at true I/O boundaries.
- Floats compare with an explicit tolerance (`pytest.approx`, `toBeCloseTo`, `EXPECT_NEAR`), never raw equality. Exception tests assert the type and message.
- Fixtures set up and tear down even on failure; default scope is per-test, widen only for genuinely expensive setup.
- Pyramid: many fast unit tests → fewer integration tests against a real, disposable DB (Testcontainers) → sparse end-to-end tests on critical paths, run against staging and never prod, on a slower CI schedule. Don't test concurrency with sleeps; wait on a real synchronization primitive with a bounded timeout.
- Coverage measures how much ran, not how well it was checked. Target roughly 85–95%, not a fragile 100%.
- New features go RED (failing test against the contract) → GREEN (implement) → refactor.
