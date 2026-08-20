## Go

- Check every error explicitly (`if err != nil`); never discard one with `_` unless the call
  genuinely cannot fail. Wrap with context using `fmt.Errorf("doing X: %w", err)`, not string
  concatenation, so `errors.Is`/`errors.As` keep working up the stack.
- Small interfaces defined by the consumer, not the producer. Accept interfaces, return
  concrete types. Don't build an interface for a type with one implementation "just in case".
- `context.Context` as the first parameter of anything that can be cancelled or time out;
  never store one in a struct field.
- Zero values should be useful. Prefer a type whose zero value works over one that requires a
  constructor for trivial cases.
- Concurrency: prefer channels for orchestration between goroutines, mutexes for protecting
  shared state — don't mix the two idioms for the same problem. Know how every goroutine you
  start exits; an unbounded or unreachable goroutine is a leak.
- Panic only for programmer errors and invariant violations that should crash, never for
  expected/recoverable failures — those return an `error`.
- Table-driven tests as the default shape; subtests via `t.Run` for clear failure output.
- Baseline tooling: `go vet`, `golangci-lint`, `gofmt`/`goimports` (non-negotiable formatting),
  `go test ./...`.
