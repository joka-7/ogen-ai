# Adapters

Templates and notes for tool-specific wiring the generator applies.

- `cursor-rule.mdc.tmpl` — shape of a `.cursor/rules/*.mdc` file (only emitted when
  `cursor_mdc = true` in the manifest). Cursor also reads the root `AGENTS.md`
  natively, so mdc is opt-in for glob-scoped, per-language rules.
- Command and agent ports to other platforms have no template files — each is a text/format
  transform living entirely in `bin/ai-sync`, since a template substitution isn't expressive
  enough for a frontmatter-shape or tool-name-mapping change. Every `emit_*` function's own
  docstring states what it's confirmed against (a primary doc, real example files, or a
  community reference) — read it before relying on the port in a real project:
  `emit_cursor_commands`/`emit_cursor_agents` (`.cursor/`, opt-in via `cursor_commands`/
  `cursor_agents`), `emit_gemini_commands`/`emit_gemini_agents` (`.gemini/`, via
  `gemini_commands`/`gemini_agents` — the best-sourced pair, confirmed against Gemini's own
  docs), `emit_copilot_prompts`/`emit_copilot_agents` (`.github/`, via `copilot_commands`/
  `copilot_agents`), `emit_windsurf_workflows` (`.windsurf/workflows/`, via
  `windsurf_commands` — no Windsurf agent port exists; see `docs/DESIGN.md` §11 for why).
  All three agent ports skip `tracker`/`docs-sync` outright rather than port them: those two
  carry `mcp__atlassian__*` tools, and none of the three platforms' tool maps has a confirmed
  mapping for Claude Code's `mcp__` naming — see `docs/DESIGN.md` §12.
- `claude-agent-permissions.json` — `permissions.deny` rules that harden the read-only
  role agents. **Not emitted by the generator**, unlike the mdc template: a project's
  `.claude/settings.json` is hand-maintained, so writing it would either clobber the
  file or be skipped by the no-clobber invariant. Merge it by hand; see the README.

Everything else the generator wires via symlink to the single generated `AGENTS.md`
(CLAUDE.md, GEMINI.md, .github/copilot-instructions.md) or to the submodule
(`.claude/skills`, `.agents/skills`, `.cursor/skills`, `.github/skills`, `.codex/skills`,
`.claude/commands`, and `.claude/agents` when `claude_agents = true`), so there is
exactly one source of truth and nothing to keep in sync by hand.

`.codex/skills` is the one case where wiring the files isn't sufficient by itself: Codex
only reads skills from `$CODEX_HOME/skills` (default `~/.codex/skills`, the user's home
directory), so a project targeting `codex` also needs `CODEX_HOME=<project-root>/.codex`
set in its environment — outside anything `ai-sync` can do, since it can't mutate the
invoking shell. No command or agent port exists for Codex; see `docs/DESIGN.md` §11.
