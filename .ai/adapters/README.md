# Adapters

Templates and notes for tool-specific wiring the generator applies.

- `cursor-rule.mdc.tmpl` — shape of a `.cursor/rules/*.mdc` file (only emitted when
  `cursor_mdc = true` in the manifest). Cursor also reads the root `AGENTS.md`
  natively, so mdc is opt-in for glob-scoped, per-language rules.

Everything else the generator wires via symlink to the single generated `AGENTS.md`
(CLAUDE.md, GEMINI.md, .github/copilot-instructions.md) or to the submodule
(`.claude/skills`, `.claude/commands`, `.agents/skills`), so there is exactly one
source of truth and nothing to keep in sync by hand.
