## Working agreement

- Match the conventions already present in the file/module you're editing over any preference stated here. Consistency beats correctness-in-the-abstract.
- Make the smallest change that fully solves the task. Don't opportunistically refactor, rename, or reformat unrelated code.
- Before a large or structural change (new dependency, new module boundary, data-model change, >~50 lines moved), state the plan and wait for confirmation.
- Never invent APIs, flags, config keys, or file paths. If you're unsure something exists, check the codebase or say so — don't guess plausibly.
- Prefer the standard library and already-present dependencies. Adding a dependency is a decision, not a default.

## Code quality

- Fail loudly and early. Validate inputs at boundaries; don't swallow errors or return silent `null`/empty on failure.
- No dead code, commented-out blocks, or `TODO` without an owner/context. Delete rather than comment out.
- Names describe intent, not type or implementation. Functions do one thing; if a name needs "and", split it.
- Keep functions short enough to hold in your head. Extract when nesting passes ~3 levels.

## Safety

- Never hardcode secrets, tokens, or credentials — not even placeholders that look real. Read from env/secret stores.
- Never log secrets, PII, or full request/response bodies containing them.
- Treat all external input as hostile until validated.

## Output discipline

- When editing, show only what changed unless asked for the full file.
- Don't add explanatory comments narrating what the code obviously does. Comment *why*, not *what*.
- If a request is ambiguous in a way that changes the result, ask one sharp question instead of assuming.
