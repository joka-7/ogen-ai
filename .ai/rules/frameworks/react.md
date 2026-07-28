## React

- Function components + hooks only. One responsibility per component; extract when a component does layout *and* data *and* logic.
- Separate concerns: UI state (`useState`/`useReducer`) vs server state (a data-fetching library like TanStack Query) vs global app state. Don't hand-roll caching that a query library already does.
- Encapsulate non-trivial logic and side effects in custom hooks (`useThing`) so components stay declarative.
- `useEffect` is for synchronizing with external systems, not for deriving state — compute derived values during render. Every effect that subscribes/listens returns a cleanup. Keep dependency arrays complete and honest; don't silence the linter.
- Performance: reach for `useMemo`/`useCallback` only when there's a measured need or a referential-stability contract (deps of an effect, props to a memoized child). Don't wrap everything preemptively. Don't define components inside other components.
- Keys must be stable and identity-based, never array index for dynamic lists.
- Prefer composition (children/slots) over prop-drilling; use context for genuinely cross-cutting values, not as a state manager.
- Accessibility is not optional: semantic elements, labels, focus management for interactive UI.
- With TypeScript: type props explicitly, avoid `React.FC`, no `any` on event handlers.
