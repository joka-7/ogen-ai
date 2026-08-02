# Adapters

Templates and notes for tool-specific wiring the generator applies.

- `cursor-rule.mdc.tmpl` — shape of a `.cursor/rules/*.mdc` file (only emitted when
  `cursor_mdc = true` in the manifest). Cursor also reads the root `AGENTS.md`
  natively, so mdc is opt-in for glob-scoped, per-language rules.
- `claude-agent-permissions.json` — `permissions.deny` rules that harden the read-only
  role agents. **Not emitted by the generator**, unlike the mdc template: a project's
  `.claude/settings.json` is hand-maintained, so writing it would either clobber the
  file or be skipped by the no-clobber invariant. Merge it by hand; see the README.

Everything else the generator wires via symlink to the single generated `AGENTS.md`
(CLAUDE.md, GEMINI.md, .github/copilot-instructions.md) or to the submodule
(`.claude/skills`, `.claude/commands`, `.agents/skills`, and `.claude/agents` when
`claude_agents = true`), so there is exactly one source of truth and nothing to keep
in sync by hand.
